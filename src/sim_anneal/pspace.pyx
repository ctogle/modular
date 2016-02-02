# cython: profile=True
# acython: wraparound=False
# acython: boundscheck=False
# acython: nonecheck=False

cimport numpy as np
import numpy as np
import random



__doc__ = '''parameter space implementation for simulated annealing'''



cpdef float reflect(float p,float a,float b):
    '''force p to be on the interval [a,b] using reflective boundaries'''
    if p < a:p = a + (a - p)
    if p > b:p = b - (p - b)
    return p
        
cpdef float wraparound(float p,float a,float b):
    '''force p to be on the interval [a,b] using periodic boundaries'''
    if p < a:p = b - (a - p)
    if p > b:p = a + (p - b)
    return p

class pspace(object):
    '''data structure for a parameter space'''

    def move(self,ng):
        '''set and return the current position in the parameter space'''
        self.current = ng
        return self.current
    
    def span(self,a):
        '''provide the maximum step size for axis a'''
        spansizer = 1.0
        return (self.bounds[a][1]-self.bounds[a][0])/spansizer

    def delta(self):
        '''find the delta step between the last and current positions'''
        dg = tuple(g1-g2 for g1,g2 in zip(self.current,self.last))
        return dg

    def trim(self):
        '''trim the bounds of the space based on the current position'''
        def trim(p,m):
            r = (m[1]-m[0])/3
            m0 = m[0] if p-m[0] < r else p - r
            m1 = m[1] if m[1]-p < r else p + r
            return m0,m1
        self.bounds = tuple(trim(g,m) for g,m in zip(self.current,self.bounds))
        return self

    def move_initial(self,ni):
        '''set and return the inital position in the parameter space'''
        self.initial = ni[:]
        return self.initial

    def __init__(self,bounds,initial,discrete = None):
        self.dims = len(bounds)
        
        self.bounds = bounds
        self.initial = initial[:]

        self.current = initial[:]
        self.last = initial[:]

        self.nonedg = tuple(None for k in self.initial)
        if discrete is None:discrete = self.nonedg
        self.discrete = discrete

        self.spans = tuple(self.span(x) for x in range(self.dims))

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

    def step_axis(self,a,t,d = None):
        '''provide a new parameter value for axis index a'''
        if not self.step_roll(d):delp = 0
        else:delp = self.step_direction(d)*t*random.random()*self.spans[a]

        #if not d is None:
        #    delp *= 0.01

        p = self.current[a] + delp
        return self.step_boundary(p,self.bounds[a])

    def step(self,t,dg = None):
        '''provide a new parameter space position'''
        if dg is None:dg = self.nonedg
        self.last = self.current
        new = tuple(self.step_axis(a,t,dg[a]) for a in range(self.dims))
        return new





