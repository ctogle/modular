import numpy as np
import random,pdb



__doc__ = '''parameter space implementation for simulated annealing'''



def reflect(p,a,b):
    '''force p to be on the interval [a,b] using reflective boundaries'''
    if p < a:p = a + (a - p)
    if p > b:p = b - (p - b)
    return p
        
def wraparound(p,a,b):
    '''force p to be on the interval [a,b] using periodic boundaries'''
    if p < a:p = b - (a - p)
    if p > b:p = a + (p - b)
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
            self.discrete = tuple(logspan(*b) if d else d for d,b in dbzip)
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

        self.nonedg = tuple(None for k in self.initial)
        if discrete is None:
            self.discrete = self.nonedg
            self.disc_loc = None
        else:
            if discrete == True:
                self.discrete = tuple(logspan(*b) for b in self.bounds)
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
        #if d is None:m = random.random > 0.5
        #else:m = True
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





