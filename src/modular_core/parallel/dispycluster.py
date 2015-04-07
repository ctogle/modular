import modular_core.fundamental as lfu

import pdb,os,numpy,dispy,random,time,socket,multiprocessing

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



from threading import Thread

class mjob(Thread):

    # an mjob is meant to be either a batch of simulations
    # or some post processing upon simulation results

    # when its created, its given a list of other mjobs which must
    # finish before it may run

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
        #else:print 'job',self.job_id,'is not ready but waiting on',prcnt
        return self.status == 'ready'

    def _release(self,result):
        for d in self.dependants:
            if self in d.prereqs:
                d.prereqs.remove(self)
                d.inputs[self.input_id] = result

    def __init__(self,job_id,prereqs,work,interval = 0.1):
        Thread.__init__(self)
        self.job_id = job_id
        self.prereqs = prereqs
        self.dependants = []
        self.interval = interval
        self.status = 'init'

        self.work = work
        self._wargs = ()

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
            self._wargs = (self.inputs,self.job_id)
            dpjob = self.dpcluster.submit(*self._wargs)
            dpjob.id = self.job_id
            #time.sleep(1)# I NEEDED THIS IN THE PAST FOR SOME REASON?
            #self._work(*self._wargs)
            dpresult = dpjob()
            if dpresult is None:
                print 'LIKELY EXCEPTION\n',dpjob.exception
                host,result = None,None
            else:
                host,result = dpresult
                printargs = (host,dpjob.id,dpjob.start_time,self.dpcluster.mtype)
                print '%s executed job %s at %s doing work %s'%printargs

        if self.aborted:self.status = 'aborted'
        else:self.status = 'completed'
        self._release(result)

    def _work(self,*args):
        host = socket.gethostname()
        result = numpy.zeros((5,100),dtype = numpy.float)

        time.sleep(5)
        print 'I DID MY JOB!!',self.job_id,'with input',len(self.inputs)
        return host,result

def unbound_batch_run(*args):
    import numpy

    inputs,job_id = args
    host = socket.gethostname()

    result = numpy.zeros((5,100),dtype = numpy.float)

    time.sleep(2)
    print 'I DID MY JOB!!BAAAAAATCH',job_id,'with input',len(inputs)
    return host,result

def unbound_zeroth(*args):
    import numpy

    inputs,job_id = args
    host = socket.gethostname()

    result = numpy.zeros((5,100),dtype = numpy.float)

    time.sleep(5)
    print 'I DID MY JOB!!ZZZZZZERO',job_id,'with input',len(inputs)
    return host,result

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
                }
        self.clusters = {}

        ndips = self.nodes.values()
        for uwf in self.ubound_work_functions.keys():
            clargs = (self.ubound_work_functions[uwf],)
            clkwgs = {'nodes':ndips,'depends':self.depends}

            print 'cluster clargs',clargs,clkwgs

            cluster = dispy.SharedJobCluster(*clargs,**clkwgs)
            self.clusters[uwf] = cluster
            cluster.mtype = uwf

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
            #print 'cluster running',len(running),'of',self.runatonce
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
                #nd._release()
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

# replace the functionality of 
# ensem._run_distributed with a clusterized version
def mcluster_run(ensem):

    pdb.set_trace()

    wf1 = 'batch_run'
    wf2 = 'zeroth'

    js1 = [mjob(x,[],wf1) for x in range(50)]
    js2 = [mjob(x+len(js1),js1,wf2) for x in range(5)]
    jobs = js2+js1

    nodes = {
        #'sierpenski':'192.168.4.89', 
        #'latitude':'192.168.4.76', 
        'wizbox':'192.168.2.173', 
            }
    depends = []
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










