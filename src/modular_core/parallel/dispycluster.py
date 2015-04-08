import modular_core.fundamental as lfu
import modular_core.data.batch_target as dba
import modular_core.parameterspace.parameterspaces as lpsp

import pdb,os,sys,numpy,dispy,random,time,socket,multiprocessing,traceback

def test(*args):
    mobj,jobdex = args

    import modular_core.fundamental as lfu
    data = lfu.mobject(name = 'jobmobj%d'%(jobdex))

    host = socket.gethostname()
    data.dispyhost = host
    data.dispyindex = jobdex
    return data

def start_cluster(cluster,args):
    jobs = []
    jobcount = len(args)
    for jobdex in range(jobcount):
        job = cluster.submit(*args[jobdex])
        time.sleep(1)
        job.id = jobdex
        jobs.append(job)
    return jobs

def cluster_setup():
    return 0

def collect_cluster(jobs):
    results = []
    for job in jobs:
        result = job()
        if result is None:print 'LIKELY EXCEPTION\n',job.exception
        else:
            host = result.dispyhost
            jobdex = result.dispyindex
            printargs = (host,job.id,job.start_time,jobdex)
            results.append(result)
            print '%s executed job %s at %s with %s'%printargs
    return results

def clusterize(nodeips,work,args,deps = []):
    cluster = dispy.JobCluster(work,nodes = nodeips,depends = deps)
    print 'node ips',nodeips
    jobs = start_cluster(cluster,args)
    print 'started cluster...'
    results = collect_cluster(jobs)
    print 'cluster finished...'
    cluster.stats()
    return results

###############################################################################
### new cluster code
###############################################################################

from threading import Thread

unused_mjob_id = 0
class mjob(Thread):

    def _abort(self):
        self.aborted = True
        self.process.terminate()

    def _initialize(self,dpcluster):
        self.dpcluster = dpcluster
        self.inputs = []
        for pr in self.prereqs:
            pr.dependants.append(self)
            pr.input_id = len(self.inputs)
            self.inputs.append(None)

    def _ready(self):
        prcnt = len(self.prereqs)
        if prcnt == 0:self.status = 'ready'
        return self.status == 'ready'

    def _release(self,result):
        for d in self.dependants:
            if self in d.prereqs:
                d.prereqs.remove(self)
                d.inputs[self.input_id] = result

    def _id(self):
        global unused_mjob_id
        if not hasattr(self,'job_id'):
            self.job_id = unused_mjob_id
            unused_mjob_id += 1
        return self.job_id

    def __init__(self,prereqs,work,wargs = (),interval = 0.1):
        Thread.__init__(self)
        self._id()
        self.prereqs = prereqs
        self.dependants = []
        self.interval = interval
        self.status = 'init'

        self.work = work
        self.wargs = wargs

        self.aborted = False
        self.abortable = False
        self.daemon = True

    def run(self):
        self.status = 'waiting'
        while not self._ready():
            time.sleep(self.interval)

        if self.abortable:
            self.process = multiprocessing.Process(
                target = self._work,args = self._wargs)
            self.process.start()
            self.process.join()
        else:
            wargs = (self.inputs,self.job_id,)+self.wargs
            if issubclass(self.dpcluster.__class__,dispy.SharedJobCluster):
                dpjob = self.dpcluster.submit(*wargs)
                # I NEEDED THIS IN THE PAST FOR SOME REASON?
                #time.sleep(1)
                dpresult = dpjob()
                stime = dpjob.start_time
            else:
                stime = time.time()
                dpresult = self.dpcluster(*wargs)
            if dpresult is None:
                print 'LIKELY EXCEPTION\n',dpjob.exception
                host,result = None,None
            else:
                host,result = dpresult
                printargs = (host,self.job_id,stime,self.work)
                print '%s executed job %s at %s doing work %s'%printargs

        if self.aborted:self.status = 'aborted'
        else:self.status = 'completed'
        self._release(result)

###############################################################################
# an mjob is meant to be either a batch of simulations
# or some post processing upon simulation results

# when its created, its given a list of other mjobs which must
# finish before it may run

def unbound_batch_run(*args):
    ##########
    import modular_core.fundamental as lfu
    lfu.using_gui = False
    import modular_core.ensemble as mce
    ##########
    inputs,job_id,ensem,trjcnt,tgcnt,cptcnt = args
    host = socket.gethostname()
    ##########
    dshape = (trjcnt,tgcnt,cptcnt)
    result = ensem._run_batch_np(trjcnt,dshape,pfreq = None)
    #print 'resultmax',trjcnt,dshape,result.max()
    return host,result

def unbound_zeroth(*args):
    import numpy
    # inputs is a list of numpy arrays, 
    # each for a batch of sim realizations
    inputs,job_id,ensem,trjcnt,tgcnt,cptcnt = args
    host = socket.gethostname()

    ishape = inputs[0].shape
    agshape = (len(inputs)*ishape[0],ishape[1],ishape[2])
    aggregate = numpy.zeros(agshape,dtype = numpy.float)
    for idx in range(len(inputs)):
        i0 = idx*ishape[0]
        i1 = (idx+1)*ishape[0]
        aggregate[i0:i1,:,:] = inputs[idx][:,:]

    meta = False
    dshape = (trjcnt,tgcnt,cptcnt)
    ptargets = ensem.simulation_plan.plot_targets
    loc_pool = dba.batch_node(metapool = meta,
        data = aggregate,dshape = dshape,targets = ptargets)
    pplan = ensem.postprocess_plan
    zeroth = pplan.zeroth

    pdb.set_trace()

    pplan._enact_processes(zeroth,loc_pool)
    pdata = dba.batch_node(metapool = meta)
    for z in zeroth:pdata._add_child(z.data.children[0])
    result = pdata
    return host,result

def unbound_aggregate(*args):
    inputs,job_id = args
    host = socket.gethostname()

    v = inputs[0][0,0]
    print 'what the hell',v

    pdb.set_trace()

###############################################################################

class mcluster(lfu.mobject):

    def _run_async(self):
        print 'starting cluster'
        self.process = multiprocessing.Process(
            target = self._clusterize,args = ())
        self.process.start()
        print 'started cluster'

    def __init__(self,*args,**kwargs):
        self._default('nodes',{},**kwargs)
        self._default('depends',[],**kwargs)
        self._default('workfunction',None,**kwargs)
        self._default('mjobs',[],**kwargs)
        self._default('runatonce',8,**kwargs)
        lfu.mobject.__init__(self,*args,**kwargs)

    def _initialize(self):
        self.ubound_work_functions = {
            'batch_run':unbound_batch_run,
            'zeroth':unbound_zeroth,
            'aggregate':unbound_aggregate,}
        self.clusters = {}

        ndips = self.nodes.values()
        for uwf in self.ubound_work_functions.keys():
            clargs = (self.ubound_work_functions[uwf],)
            clkwgs = {'nodes':ndips,'depends':self.depends}
            #if True:cluster = clargs[0]
            if uwf == 'aggregate':cluster = clargs[0]
            elif uwf == 'zeroth':cluster = clargs[0]
            else:cluster = dispy.SharedJobCluster(*clargs,**clkwgs)
            self.clusters[uwf] = cluster

        self.torun = self.mjobs[:]
        self.hasrun = []
        for j in self.torun:
            jcl = self.clusters[j.work]
            j._initialize(jcl)

    def _clusterize(self):
        self._initialize()
        print 'cluster initialized...'
        running = []
        while self.torun:
            time.sleep(0.1)
            nowdone = []
            for j in running:
                if j.status == 'completed':
                    nowdone.append(j)
                elif j.status == 'aborted':
                    print 'mjob',j.job_id,'aborted!!!'
                    pdb.set_trace()
                elif j.status == 'init':
                    print 'mjob',j.job_id,'has not started...'

            for nd in nowdone:
                running.remove(nd)
                self.torun.remove(nd)
                self.hasrun.append(nd)

            for j in self.torun:
                if j in running:continue
                if len(running) < self.runatonce:
                    if j._ready():
                        running.append(j)
                        j.start()
                        time.sleep(0.1)

        self.clusters.values()[0].stats()
        print 'cluster finished...'

def setup_mjobs(ensem,ncores = 20):
    requiresimdata = ensem._require_simulation_data()
    cplan = ensem.cartographer_plan
    pplan = ensem.postprocess_plan
    pspace = cplan.parameter_space
    mappspace = cplan.use_plan and pspace
    if not mappspace:
        pspace = cplan._parameter_space([])
        trj,ntrj = cplan.trajectory,ensem.num_trajectories
        lpsp.trajectory_set_counts(trj,ntrj)
    ensem._run_params_to_location_prepoolinit()

    arc = cplan.trajectory
    arc_length = len(arc)
    if pplan.use_plan:pplan._init_processes(arc)

    from modular_core.ensemble import ensemble_manager
    mnger = ensemble_manager()
    with open(ensem.mcfg_path,'r') as mh:mcfgstring = mh.read()

    mjobs = []
    zjobs = []

    #data_pool = dba.batch_node(metapool = meta)
    arc_dex = 0
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
        traj_cnt,targ_cnt,capt_cnt,ptargets = anensem._run_init(arc_dex)
        anensem.cartographer_plan._move_to(arc_dex)
        anensem._run_params_to_location()
        anensem.parent = None

        trjcntperbrun = traj_cnt/ncores
        brun_args = (anensem,trjcntperbrun,targ_cnt,capt_cnt)
        brun_mjobs = [mjob([],'batch_run',brun_args) for x in range(ncores)]
        mjobs.extend(brun_mjobs)
        print 'make some jobs for this location:%d/%d'%(arc_dex,arc_length)

        zero_args = (anensem,traj_cnt,targ_cnt,capt_cnt)
        zero_mjob = mjob(brun_mjobs,'zeroth',zero_args)
        zjobs.append(zero_mjob)

        arc_dex += 1

    mjobs.extend(zjobs)
    aggr_mjob = mjob(zjobs,'aggregate')
    mjobs.append(aggr_mjob)
    return mjobs

# replace the functionality of 
# ensem._run_distributed with a clusterized version
def mcluster_run(ensem):
    jobs = setup_mjobs(ensem)
    nodes = {
        'sierpenski':'192.168.4.89', 
        'latitude':'192.168.4.76', 
        'wizbox':'192.168.2.173', 
            }
    depends = ensem.module.dependencies
    cores = 20

    mckwgs = {
        'mjobs':jobs,
        'nodes':nodes,
        'depends':depends,
        'runatonce':cores,
            }
    mclust = mcluster(**mckwgs)
    mclust._clusterize()
    #mclust._run_async()

    pdb.set_trace()

    print '...successfully ran on mcluster...'
    dpool = dba.batch_node()
    return dpool

if __name__ == '__main__':
    gillm_mcfgpath = os.path.join('/','home','cogle',
        'dev','modular','tests','gillespiemmcfgs')
    correl_mcfg = os.path.join(gillm_mcfgpath,'correl_demo.mcfg')

    from modular_core.ensemble import ensemble_manager
    mnger = ensemble_manager()
    ensem = mnger._add_ensemble(module = 'gillespiem')
    ensem.mcfg_path = correl_mcfg
    ensem._parse_mcfg()
    ensem.output_plan.targeted = ensem.run_params['plot_targets'][:]
    ensem.output_plan._target_settables()
    #eran = ensem._run_specific()
    #ensem._output()

    testdpool = mcluster_run(ensem)

    pdb.set_trace()










