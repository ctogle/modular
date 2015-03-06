import modular_core.fundamental as lfu

import dispy,random,time,socket,pdb

def test(*args):
    mobj,jobdex = args

    import modular_core.fundamental as lfu
    data = lfu.mobject(name = 'jobmobj%d'%(jobdex))

    host = socket.gethostname()
    data.dispyhost = host
    data.dispyindex = jobdex
    return data

cluster_ips = [
    #'10.0.0.5',
    #'10.0.0.8',
    #'127.0.1.1', 
    '192.168.4.87', 
    '192.168.4.89',
        ]

def start_cluster(cluster,args):
    jobs = []
    jobcount = len(args)
    for jobdex in range(jobcount):
        job = cluster.submit(*args[jobdex])
        time.sleep(1)
        job.id = jobdex
        jobs.append(job)
    return jobs

def _cluster_setup():
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

def clusterize(work,args,deps = []):
    cluster = dispy.JobCluster(work,
        nodes = cluster_ips,depends = deps,
        setup = _cluster_setup,cleanup = False)
    print 'node ips',cluster_ips
    jobs = start_cluster(cluster,args)
    results = collect_cluster(jobs)
    cluster.stats()
    return results

if __name__ == '__main__':
    inpmobj = lfu.mobject(name = 'ensemble?')
    inpargs = [(inpmobj,x) for x in range(10)]
    results = clusterize(test,inpargs)

    pdb.set_trace()


