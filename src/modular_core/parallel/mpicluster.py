import modular_core.data.batch_target as dba
import modular_core.parameterspace.parameterspaces as lpsp

import random,time

from mpi4py import MPI
from cStringIO import StringIO

import pdb,os,sys,numpy

unused_mjob_id = 0
class mjob(object):

    def _id(self):
        global unused_mjob_id
        if not hasattr(self,'job_id'):
            self.job_id = unused_mjob_id
            unused_mjob_id += 1
        return self.job_id

    def __init__(self,prereqs,work,wargs = ()):
        self._id()
        self.prereqs = prereqs
        self.dependants = []
        self.work = work
        self.wargs = wargs
        self.root_only = False

    def _initialize(self,jobs):
        self.inputs = []
        selfdex = jobs.index(self)
        for pr in self.prereqs:
            preq = jobs[pr]
            preq.dependants.append(selfdex)
            preq.input_id = len(self.inputs)
            self.inputs.append(None)

    def _ready(self):
        prcnt = len(self.prereqs)
        if prcnt == 0:return True
        else:return False

    def _runbatch(self):
        ensem,trjcnt,tgcnt,cptcnt = self.wargs
        dshape = (trjcnt,tgcnt,cptcnt)
        r = ensem._run_batch_np(trjcnt,dshape,pfreq = None)
        return r

    def _gather_zeroth_inputs(self,ptargets,meta = False):
        inputs = self.inputs
        ishape = inputs[0].shape
        agshape = (len(inputs)*ishape[0],ishape[1],ishape[2])
        aggregate = numpy.zeros(agshape,dtype = numpy.float)
        for idx in range(len(inputs)):
            i0 = idx*ishape[0]
            i1 = (idx+1)*ishape[0]
            aggregate[i0:i1,:,:] = inputs[idx][:,:]
        loc_pool = dba.batch_node(metapool = meta,
            data = aggregate,targets = ptargets)
        return loc_pool

    def _zeroth(self):
        ensem,trjcnt,tgcnt,cptcnt,meta = self.wargs
        ptargets = ensem.simulation_plan.plot_targets
        loc_pool = self._gather_zeroth_inputs(ptargets,meta)
        ensem.postprocess_plan._enact_zeroth_processes(loc_pool)
        r = dba.batch_node(metapool = meta)
        for z in ensem.postprocess_plan.zeroth:
            r._add_child(z.data.children[0])
        return r

    def _aggregate(self):
        ensem,arc_length = self.wargs
        zeroth = ensem.postprocess_plan.zeroth
        zcount = len(zeroth)
        for adx in range(arc_length):
            l0p = self.inputs[adx]
            #if cplan.maintain_pspmap:
            #    mloc = l0p.metalocation
            #    mstr = mloc.location_string
            #    cplan.metamap.entries[mstr] = mloc
            #    cplan.metamap.location_strings.append(mstr)
            for zdx in range(zcount):
                zp = zeroth[zdx]
                zpdata = l0p.children[zdx]
                zp.data._add_child(zpdata)
                zp.data._stow_child(-1,v = False)

    def _prepoolinit(self):
        silence()
        ensem = self.wargs[0]
        ensem._run_params_to_location_prepoolinit()
        vocalize()
        print 'finished prepoolinit work'

    def _work(self):
        #if self.inputs:
        #    print 'my inputs',self.inputs,'from',self.job_id
        #print 'doing work',self.work,self.wargs
        r = None
        if self.work == 'batch_run':r = self._runbatch()
        elif self.work == 'zeroth':r = self._zeroth()
        elif self.work == 'aggregate':r = self._aggregate()
        elif self.work == 'prepoolinit':r = self._prepoolinit()
        elif self.work == 'pass':r = None
        else:print 'UNKNOWN WORK REQUEST!',self.work
        self.result = r

    def _release(self,jobs):
        if self.work == 'pass':return
        result = self.result
        selfdex = self.selfdex
        for d in self.dependants:
            dep = jobs[d]
            if selfdex in dep.prereqs:
                dep.prereqs.remove(selfdex)
                dep.inputs[self.input_id] = result

###############################################################################

def select_mjob(jobs,jcnt):
    for jdx in range(jcnt):
        if jobs[jdx]._ready():
            return jdx

def host_lookup(root):
    comm = MPI.COMM_WORLD
    ncnt = comm.size
    hosts = {}
    passjob = mjob([],'pass')
    for c in range(ncnt):
        if c == root:hosts['root'] = c
        else:
            comm.send(passjob,dest = c)
            reply = comm.recv(source = c)
            host = reply.host
            if host in hosts.keys():hosts[host].append(c)
            else:hosts[host] = [c]
    return hosts

def delegate_per_node(hosts,setup):
    comm = MPI.COMM_WORLD
    nonroots = hosts.keys()
    nonroots.remove('root')
    print 'delegating setup to nodes:',nonroots
    for h in nonroots:comm.send(setup,dest = hosts[h][0])
    print 'sent setup jobs to hosts:',nonroots
    for h in nonroots:
        print 'nonroot',h,'receiving'
        reply = comm.recv(source = hosts['root'])
        print 'host',h,'received reply',reply
    print 'received setup jobs from hosts:',nonroots

def delegate(root,jobs,setup = None):
    comm = MPI.COMM_WORLD
    ncnt = comm.size

    hosts = host_lookup(root)
    print 'performing node setup...'
    if not setup is None:delegate_per_node(hosts,setup)
    print 'finished node setup...'

    free = [x for x in range(ncnt)]
    occp = []
    free.remove(root)

    passjob = mjob([],'pass')
    remaining_jobs = jobs[:]
    for j in jobs:j._initialize(jobs)
    jobcount = len(jobs)
    jobstodo = jobcount
    jobsdone = 0
    while jobsdone < jobcount:
        swap = []
        for f in free:
            if jobstodo > 0:
                jdx = select_mjob(remaining_jobs,jobstodo)
                if jdx is None:break
                j = remaining_jobs.pop(jdx)
                if j.root_only:
                    print 'executing root only job:',j.job_id
                    j._work()
                    comm.send(passjob,dest = f)
                else:
                    j.selfdex = jobs.index(j)
                    comm.send(j,dest = f)
                swap.append(f)
                jobstodo -= 1
            else:break
        for f in swap:
            free.remove(f)
            occp.append(f)
    
        anyreply = comm.recv(source = MPI.ANY_SOURCE)
        anyreply._release(jobs)
        nowfree = anyreply.rank
        print 'job returned',nowfree
        jobsdone += 1
        free.append(nowfree)
        occp.remove(nowfree)

    for f in free:comm.send('quit',dest = f)

def listen(root):
    comm = MPI.COMM_WORLD
    host = MPI.Get_processor_name()
    rank = comm.rank
    quit = False
    print 'listener starting',rank,'on',host
    while not quit:
        job = comm.recv(source = root)
        if job == 'quit':quit = True
        else:
            print 'rank:',rank,'received job:',job.job_id,'with work:',job.work
            job._work()
            job.rank = rank
            job.host = host
            print 'rank:',rank,'finished job:',job.job_id,'with work:',job.work
        comm.send(job,dest = root)
    print 'listener quit',rank,'on',host

###############################################################################

def setup_node_setup_mjob(ensem):
    from modular_core.ensemble import ensemble_manager
    mnger = ensemble_manager()

    mcfgstring = ensem._mcfg_string()
    anensem = mnger._add_ensemble(module = ensem.module_name)
    anensem._parse_mcfg(mcfgstring = mcfgstring)
    anensem.module.parsers = None
    anensem.multiprocess_plan.use_plan = False
    anensem.parent = None

    prepoolargs = (anensem,)
    setup = mjob([],'prepoolinit',prepoolargs)
    return setup

def setup_pspace_mjobs(mjobs,zjobs,mnger,modname,mstring,arc,arc_dex,tpj,meta):
    anensem = mnger._add_ensemble(module = modname)
    anensem._parse_mcfg(mcfgstring = mstring)
    anensem.module.parsers = None
    anensem.multiprocess_plan.use_plan = False
    if anensem.postprocess_plan.use_plan:
        anensem.postprocess_plan._init_processes(arc)
    #
    anensem.module._increment_extensionname()
    #
    cplan = anensem.cartographer_plan
    pspace = cplan.parameter_space
    mappspace = cplan.use_plan and pspace
    if not mappspace:
        pspace = anensem.cartographer_plan._parameter_space([])
        trj = anensem.cartographer_plan.trajectory
        ntrj = anensem.num_trajectories
        lpsp.trajectory_set_counts(trj,ntrj)

    traj_cnt,targ_cnt,capt_cnt,ptargets = anensem._run_init(arc_dex)
    anensem.cartographer_plan._move_to(arc_dex)
    anensem._run_params_to_location()
    anensem.parent = None

    brun_jcnt = traj_cnt/tpj
    remainder = traj_cnt - brun_jcnt*tpj

    brun_args = (anensem,tpj,targ_cnt,capt_cnt)
    brun_mjobs = [mjob([],'batch_run',brun_args) for x in range(brun_jcnt)]
    if remainder > 0:
        brun_args = (anensem,remainder,targ_cnt,capt_cnt)
        brun_mjobs.append(mjob([],'batch_run',brun_args))
    mjobs.extend(brun_mjobs)

    zero_args = (anensem,traj_cnt,targ_cnt,capt_cnt,meta)
    brun_jdxs = [mjobs.index(j) for j in brun_mjobs]
    zero_mjob = mjob(brun_jdxs,'zeroth',zero_args)
    zjobs.append(zero_mjob)

def setup_ensemble_mjobs(ensem,trj_per_job = None):
    comm = MPI.COMM_WORLD
    ncores = comm.size

    requiresimdata = ensem._require_simulation_data()
    pplan = ensem.postprocess_plan
    cplan = ensem.cartographer_plan
    pspace = cplan.parameter_space
    mappspace = cplan.use_plan and pspace
    if not mappspace:
        pspace = cplan._parameter_space([])
        trj,ntrj = cplan.trajectory,ensem.num_trajectories
        lpsp.trajectory_set_counts(trj,ntrj)

    meta = False

    arc = cplan.trajectory
    arc_length = len(arc)
    if pplan.use_plan:pplan._init_processes(arc)

    from modular_core.ensemble import ensemble_manager
    mnger = ensemble_manager()
    mcfgstring = ensem._mcfg_string()

    mjobs = []
    zjobs = []

    arc_dex = 0
    if trj_per_job is None:trj_per_job = traj_cnt/ncores
    silence()
    while arc_dex < arc_length:
        spargs = (mjobs,zjobs,mnger,ensem.module_name,
            mcfgstring,arc,arc_dex,trj_per_job,meta)
        setup_pspace_mjobs(*spargs)
        arc_dex += 1
        print 'make some jobs for this location:%d/%d'%(arc_dex,arc_length)
    vocalize()

    mjobs.extend(zjobs)
    aggr_args = (ensem,arc_length)
    zero_jdxs = [mjobs.index(j) for j in zjobs]
    aggr_mjob = mjob(zero_jdxs,'aggregate',aggr_args)
    aggr_mjob.root_only = True
    mjobs.append(aggr_mjob)
    return mjobs

def silence():
    sys.stdout = StringIO()
    sys.stderr = StringIO()

def vocalize():
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

###############################################################################

def test_ensemble():
    gillm_mcfgpath = os.path.join('/','home','cogle','dev','modular','tests')
    correl_mcfg = os.path.join(gillm_mcfgpath,'correl_demo.mcfg')

    from modular_core.ensemble import ensemble_manager
    mnger = ensemble_manager()
    ensem = mnger._add_ensemble(module = 'gillespiem')
    ensem.mcfg_path = correl_mcfg
    ensem._parse_mcfg()
    ensem.output_plan.targeted = ensem.run_params['plot_targets'][:]
    ensem.output_plan._target_settables()
    return ensem

def test():
    comm = MPI.COMM_WORLD
    root = 0
    if comm.rank == root:
        ensem = test_ensemble()
        jobs = setup_ensemble_mjobs(ensem,1000)

    if comm.rank == root:delegate(root,jobs)
    else:listen(root)

###############################################################################

if __name__ == '__main__':
    test()

###############################################################################










