import dispy,random,time,socket

def test(n):
    #time.sleep(n)
    print 'i would sleep?',n
    host = socket.gethostname()
    return (host,n)

def run():
    cluster = dispy.JobCluster(test,nodes = ['10.0.0.5','10.0.0.8'])
    jobs = []
    for n in range(10):
        job = cluster.submit(random.randint(5,20))
        job.id = n
        jobs.append(job)
    for job in jobs:
        host,n = job()
        print '%s executed job %s at %s with %s'%(host,job.id,job.start_time,n)
    cluster.stats()


run()


