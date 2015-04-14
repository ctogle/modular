import random,time

from mpi4py import MPI
from cStringIO import StringIO

import pdb,os,sys,numpy

###############################################################################
### mjob is an abstract container for cluster work
### it must remain pickleable and should be 
### subclassed for actual computations
###
### no code here is aware of its function within modular_core
###############################################################################

unused_mjob_id = 0
class mjob(object):

    def _id(self):
        global unused_mjob_id
        if not hasattr(self,'job_id'):
            self.job_id = unused_mjob_id
            unused_mjob_id += 1
        return self.job_id

    def _np_reply(self):
        #return False
        np = hasattr(self.result,'shape')
        return np

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

    def _work(self):
        r = 'override work method of mjob'
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

def find_mjob(jobs,job_id):
    for j in jobs:
        if j.job_id == job_id:
            return j

def select_mjob(jobs,jcnt):
    for jdx in range(jcnt):
        if jobs[jdx]._ready():
            return jdx

def wait_for_mjob(root,jobs):
    comm = MPI.COMM_WORLD
    print 'waiting for mjobs'
    jrk,npr,jid,jshp = comm.recv(source = MPI.ANY_SOURCE)
    if npr:
        j = find_mjob(jobs,jid)
        j.result = numpy.empty(jshp,dtype = numpy.float)
        comm.Recv(j.result,source = jrk)
        j._release(jobs)
    else:
        jresult = comm.recv(source = jrk)
        jresult._release(jobs)
    return jrk

###############################################################################

def host_lookup(root):
    comm = MPI.COMM_WORLD
    ncnt = comm.size
    hosts = {}
    passjob = mjob([],'pass')
    for c in range(ncnt):
        if c == root:hosts['root'] = c
        else:
            comm.send(passjob,dest = c)
            jrk,npr,jid,jshp = comm.recv(source = c)
            reply = comm.recv(source = c)
            host = reply.host
            if host in hosts.keys():hosts[host].append(c)
            else:hosts[host] = [c]
    return hosts

###############################################################################

def delegate_per_node(hosts,setup):
    comm = MPI.COMM_WORLD
    nonroots = hosts.keys()
    nonroots.remove('root')
    print 'delegating setup to nodes:',nonroots
    for h in nonroots:comm.send(setup,dest = hosts[h][0])
    print 'sent setup jobs to hosts:',nonroots
    for h in nonroots:
        jrk,npr,jid,jshp = comm.recv(source = hosts[h][0])
        reply = comm.recv(source = hosts[h][0])
    print 'received setup replies from hosts:',nonroots

def delegate(root,jobs,setup = None):
    comm = MPI.COMM_WORLD
    ncnt = comm.size
    free = [x for x in range(ncnt)]
    occp = []
    free.remove(root)

    hosts = host_lookup(root)
    if not setup is None:delegate_per_node(hosts,setup)

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
        jrank = wait_for_mjob(root,jobs)
        free.append(jrank)
        occp.remove(jrank)
        jobsdone += 1

###############################################################################

def listen(root):
    comm = MPI.COMM_WORLD
    host = MPI.Get_processor_name()
    rank = comm.rank
    quit = False
    print 'listener starting',rank,'on',host
    while not quit:
        job = comm.recv(source = root)
        if job == 'quit':break
        else:
            print 'rank:',rank,'received job:',job.job_id,'with work:',job.work
            job._work()
            job.rank = rank
            job.host = host
            print 'rank:',rank,'finished job:',job.job_id,'with work:',job.work
        npreply = job._np_reply()
        if npreply:jshape = job.result.shape
        else:jshape = None
        comm.send((job.rank,npreply,job.job_id,jshape),dest = root)
        if npreply:comm.Send([job.result,MPI.FLOAT],dest = root)
        else:comm.send(job,dest = root)
    print 'listener quit',rank,'on',host

def stop_listeners(root):
    comm = MPI.COMM_WORLD
    ncnt = comm.size
    nodes = [x for x in range(ncnt) if not x == root]
    for f in nodes:comm.send('quit',dest = f)

###############################################################################

def silence():
    sys.stdout = StringIO()
    sys.stderr = StringIO()

def vocalize():
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

###############################################################################

if __name__ == '__main__':
    print 'modular_core.parallel.mpicluster'

###############################################################################










