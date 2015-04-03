import modular_core.fundamental as lfu

import dispy,random,time,socket,pdb

from mpi4py import MPI
def test():
    comm = MPI.COMM_WORLD
    print 'hey, im rank %d from %d running in total:' % (comm.rank,comm.size)
    comm.Barrier()
    return comm.rank

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

    print 'dumb mpi clusterized!'
    test()
    return 'result'

    cluster = dispy.JobCluster(work,nodes = nodeips,
        depends = deps,setup = cluster_setup,cleanup = False)
    print 'node ips',nodeips
    jobs = start_cluster(cluster,args)
    print 'started cluster...'
    results = collect_cluster(jobs)
    print 'cluster finished...'
    cluster.stats()
    return results

if __name__ == '__main__':
    inpmobj = lfu.mobject(name = 'ensemble?')
    inpargs = [(inpmobj,x) for x in range(10)]
    nodes = ['127.0.0.1']
    #nodes = ['127.0.0.1','192.168.4.76']
    #nodes = ['127.0.0.1','hemlock.phys.vt.edu','192.168.4.76']
    #nodes = ['hemlock.phys.vt.edu','192.168.4.76']
    #nodes = ['127.0.0.1','192.168.4.76']
    results = clusterize(nodes,test,inpargs,[])

    pdb.set_trace()


