import numpy as np
import random,numpy,pdb

import itertools as it



__doc__ = '''parameter space implementation for simulated annealing'''



def reflect(p,a,b):
    '''force p to be on the interval [a,b] using reflective boundaries'''
    if p < a:p = a + (a - p)
    if p > b:p = b - (p - b)
    return p
        
def wraparound(p,a,b):
    '''force p to be on the interval [a,b] using periodic boundaries'''
    while a > p or p > b:
        if p < a:p = b - (a - p) 
        if p > b:p = a + (p - b) 
    #if p < a:p = b - (a - p)
    #if p > b:p = a + (p - b)
    return p

def locate(ax,v):
    '''find the index of the nearest value in a sequence to a given value'''
    delv = tuple(abs(a-v) for a in ax)
    px = delv.index(min(delv))
    return px

def orderofmag(v):
    '''determine the order of magnitude of a value'''
    return int(np.log10(abs(v)))

def logspan(f,c,n = 10):
    '''create an acceptable discrete sequence for an axis'''
    lspan = tuple(np.exp(np.linspace(np.log(f),np.log(c),n)))
    return lspan

def trim_continuous(p,m):
    '''return trimmed bounds for a continuous axis based on the current position'''
    r = (m[1]-m[0])/3
    m0 = m[0] if p-m[0] < r else p - r
    m1 = m[1] if m[1]-p < r else p + r
    return m0,m1

def trim_discrete(p,d):
    '''return trimmed bounds for a discrete axis based on the current position'''
    rng = tuple(range(len(d)))
    loc = locate(d,p)
    #if loc == rng[0]:m0,m1 = d[rng[0]]/2.0,d[rng[-2]]
    #elif loc == rng[-1]:m0,m1 = d[rng[1]],d[rng[-1]]*2.0
    #elif loc in rng[:int(len(rng)/2.0)]:m0,m1 = d[rng[0]],d[rng[-2]]
    if loc in rng[:int(len(rng)/2.0)]:m0,m1 = d[rng[0]],d[rng[-2]]
    elif loc in rng[int(len(rng)/2.0):]:m0,m1 = d[rng[1]],d[rng[-1]]
    else:m0,m1 = d[rng[1]],d[rng[-2]]
    return m0,m1

class pspace(object):
    '''data structure for a parameter space'''

    def move(self,ng):
        '''set and return the current position in the parameter space'''
        self.current = ng
        dczip = zip(self.discrete,self.current)
        self.disc_loc = tuple(locate(d,c) if d else None for d,c in dczip)
        self.trajectory.append(self.current[:])
        return self.current
    
    def span(self,a):
        '''provide the maximum step size for axis a'''
        spansizer = 1.0
        return (self.bounds[a][1]-self.bounds[a][0])/spansizer

    def delta(self):
        '''find the delta step between the last and current positions'''
        dg = tuple(g1-g2 for g1,g2 in zip(self.current,self.last))
        return dg

    def trim_axis(self,a):
        '''trim the bounds of a single axis'''
        c,b,d = self.current[a],self.bounds[a],self.discrete[a]
        if d is None:return trim_continuous(c,b)
        else:return trim_discrete(c,d)

    def trim(self):
        '''trim the bounds of the space based on the current position'''
        self.bounds = tuple(self.trim_axis(j) for j in range(self.dims))
        if not self.discrete == self.nonedg:
            dbzip = zip(self.discrete,self.bounds)
            self.discrete = tuple(
                logspan(b[0],b[1],self.disccount) if d else d 
                    for d,b in dbzip)
        return self

    def move_initial(self,ni):
        '''set and return the inital position in the parameter space'''
        self.initial = ni[:]
        return self.initial

    def become_continuous(self):
        '''rid discretization information to make the space continuous'''
        self.discrete = self.nonedg
        self.disc_loc = None

    def __init__(self,bounds,initial,discrete = None,axes = None,trajectory = None):
        self.dims = len(bounds)
        
        self.bounds = bounds
        self.initial = initial[:]

        self.current = initial[:]
        self.last = initial[:]

        if self.dims:
            steproll = tuple((-1,0,1) for d in range(self.dims))
            steproll = list(it.product(*steproll))
            steproll = [x for x in steproll if not (min(x) == max(x) == 0)]
        else:steproll = []
        self.steproll = steproll 

        self.nonedg = tuple(None for k in self.initial)
        self.disccount = 10
        if discrete is None:
            self.discrete = self.nonedg
            self.disc_loc = None
        else:
            if discrete == True:
                self.discrete = tuple(
                    logspan(b[0],b[1],self.disccount) 
                        for b in self.bounds)
            else:self.discrete = discrete
            dczip = zip(self.discrete,self.current)
            self.disc_loc = tuple(locate(d,c) for d,c in dczip)

        self.spans = tuple(self.span(x) for x in range(self.dims))
        if axes is None:self.axes = tuple(str(k) for k in range(self.dims))
        else:self.axes = axes

        if trajectory is None:self.trajectory = [self.initial[:]]
        else:self.trajectory = trajectory

    def step_direction(self,d = None):
        '''provide a sign for a new parameter value'''
        if d is None:s = random.choice((-1,1))
        else:s = np.sign(d)
        return s

    def step_boundary(self,p,b):
        '''provide a new parameter value within the axis interval b'''
        #p = reflect(p,b[0],b[1])
        p = wraparound(p,b[0],b[1])
        return p

    def step_roll(self,d = None):
        '''determine if an axis should change during a step'''
        m = random.random > 0.5
        return m

    def step_continous(self,a,t,d):
        '''return a randomized delp for a continuous axis'''
        delp = self.step_direction(d)*t*random.random()*self.spans[a]
        return delp

    def step_discrete(self,a,t,d):
        '''return a randomized delp for a discrete axis'''
        disc,bnd,loc = self.discrete[a],self.bounds[a],self.disc_loc[a]
        sdir = self.step_direction(d)
        delx = t*random.random()*len(disc)
        nloc = wraparound(loc+int(sdir*max(1,delx)),0,len(disc)-1)
        delp = disc[nloc] - disc[loc]
        return delp

    def step_axis(self,a,t,d = None):
        '''provide a new parameter value for axis index a'''
        if not self.step_roll(d):delp = 0
        elif self.discrete[a]:delp = self.step_discrete(a,t,d)
        else:delp = self.step_continous(a,t,d)
        p = self.current[a] + delp
        return self.step_boundary(p,self.bounds[a])

    def step(self,t,dg = None):
        '''provide a new parameter space position'''
        if dg is None:dg = self.nonedg
        self.last = self.current
        new = tuple(self.step_axis(a,t,dg[a]) for a in range(self.dims))
        return new

    def step_binary(self,a,n,t):
        '''provide a new parameter value for axis index a'''
        if n < 0:
            if self.discrete[a]:delp = self.step_discrete(a,t,-1)
            else:delp = self.step_continous(a,t,-1)
        elif n > 0:
            if self.discrete[a]:delp = self.step_discrete(a,t,1)
            else:delp = self.step_continous(a,t,1)
        else:delp = 0
        p = self.current[a] + delp
        return self.step_boundary(p,self.bounds[a])

    def step_spam(self,m,t,dg = None):
        rx = random.randint(0,len(self.steproll)-1)
        n = self.steproll[rx]
        v = int(m/self.dims)-n.count(0)
        if v == 0:e = 0
        else:e = m % v
        faket = numpy.linspace(0.000001,1.0,int(m/self.dims)+1)
        axs = tuple(tuple(self.step_axis(a,faket[j],d)
                for j in range(int(m/self.dims))) 
                    for a,d in zip(range(self.dims),n))
        sgs = list(set(list(it.product(*axs))))
        if len(sgs) > m:sgs = random.sample(sgs,m)
        else:sgs = [random.choice(sgs) for x in range(m)]
        return sgs

    def step_multi(self,m,t,dg = None):
        '''provide m distinct steps'''
        #if mmpi.size() > 1:
        if True:
            mstep = self.step_spam(m,t,dg)
            return tuple(mstep)
        else:
            mstep = []
            srolls = []
            for mx in range(m):
                if not self.steproll:self.steproll.extend(srolls)
                rx = random.randint(0,len(self.steproll)-1)
                srolls.append(self.steproll.pop(rx))
                anzip = zip(range(self.dims),srolls[-1])
                s = tuple(self.step_binary(a,n,t) for a,n in anzip)
                mstep.append(s)
            self.steproll.extend(srolls)
            return tuple(mstep)





