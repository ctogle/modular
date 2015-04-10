import modular_core.data.batch_target as dba
import modular_core.parameterspace.parameterspaces as lpsp

import random,time

from mpi4py import MPI

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
        #self.prereqs = [p.job_id for p in prereqs]
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
                #zp.data._stow_child(-1,v = False)

    def _work(self):
        #if self.inputs:
        #    print 'my inputs',self.inputs,'from',self.job_id
        #print 'doing work',self.work,self.wargs
        r = None
        if self.work == 'batch_run':r = self._runbatch()
        elif self.work == 'zeroth':r = self._zeroth()
        elif self.work == 'pass':pass
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

def delegate_per_node(setup):
    pdb.set_trace()

def delegate(root,jobs,setup = None):
    comm = MPI.COMM_WORLD
    ncnt = comm.size

    if not setup is None:delegate_per_node(setup)

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
            print 'rank:',rank,'received job:',job.job_id
            job._work()
            job.rank = rank
            job.host = host
        comm.send(job,dest = root)
    print 'listener quit',rank,'on',host

###############################################################################

def host_ranks(root):
    comm = MPI.COMM_WORLD
    ncnt = comm.size
    rnks = [x for x in range(ncnt)]

    # ask every rank what their host is
    # keep one rank per host in a list and return

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

def setup_node_setup_mjob(ensem):
    
    pdb.set_trace()

    prepoolargs = (ensem,)
    setup = [mjob([],'prepoolinit',prepoolargs) for x in range(hcnt)]

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

    # run a function on one core of each node which does this locally
    ensem._run_params_to_location_prepoolinit()

    meta = False

    arc = cplan.trajectory
    arc_length = len(arc)
    if pplan.use_plan:pplan._init_processes(arc)

    from modular_core.ensemble import ensemble_manager
    mnger = ensemble_manager()
    with open(ensem.mcfg_path,'r') as mh:mcfgstring = mh.read()

    mjobs = []
    zjobs = []

    arc_dex = 0
    if trj_per_job is None:trj_per_job = traj_cnt/ncores
    while arc_dex < arc_length:
        anensem = mnger._add_ensemble(module = ensem.module_name)
        anensem._parse_mcfg(mcfgstring = mcfgstring)
        anensem.module.parsers = None
        anensem.multiprocess_plan.use_plan = False
        if anensem.postprocess_plan.use_plan:
            anensem.postprocess_plan._init_processes(arc)
        #
        anensem.module._increment_extensionname()
        #
        if not mappspace:
            pspace = anensem.cartographer_plan._parameter_space([])
            trj = anensem.cartographer_plan.trajectory
            ntrj = anensem.num_trajectories
            lpsp.trajectory_set_counts(trj,ntrj)

        traj_cnt,targ_cnt,capt_cnt,ptargets = anensem._run_init(arc_dex)
        anensem.cartographer_plan._move_to(arc_dex)
        anensem._run_params_to_location()
        anensem.parent = None

        brun_jcnt = traj_cnt/trj_per_job
        remainder = traj_cnt - brun_jcnt*trj_per_job

        brun_args = (anensem,trj_per_job,targ_cnt,capt_cnt)
        brun_mjobs = [mjob([],'batch_run',brun_args) for x in range(brun_jcnt)]
        if remainder > 0:
            brun_args = (anensem,remainder,targ_cnt,capt_cnt)
            brun_mjobs.append(mjob([],'batch_run',brun_args))
        mjobs.extend(brun_mjobs)
        print 'make some jobs for this location:%d/%d'%(arc_dex,arc_length)

        zero_args = (anensem,traj_cnt,targ_cnt,capt_cnt,meta)
        brun_jdxs = [mjobs.index(j) for j in brun_mjobs]
        zero_mjob = mjob(brun_jdxs,'zeroth',zero_args)
        zjobs.append(zero_mjob)

        arc_dex += 1

    mjobs.extend(zjobs)
    aggr_args = (ensem,arc_length)
    zero_jdxs = [mjobs.index(j) for j in zjobs]
    aggr_mjob = mjob(zero_jdxs,'aggregate',aggr_args)
    aggr_mjob.root_only = True
    mjobs.append(aggr_mjob)
    return mjobs

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










