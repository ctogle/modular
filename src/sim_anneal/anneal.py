import metric
import pspace

import matplotlib.pyplot as plt
import numpy as np
import random,inspect

import pdb



__doc__ = '''typical entry point for annealing'''



class annealer(object):
    '''extensible class which performs annealing'''

    def plot(self,g):
        '''plot some fit data with the input data and initial fit data'''
        ya = self.y
        yi = self.f(self.x,*self.psp.initial)
        yb = self.f(self.x,*g)
        plt.plot(self.x,ya,color = 'r',label = 'data')
        plt.plot(self.x,yi,color = 'b',label = 'init')
        plt.plot(self.x,yb,color = 'g',label = 'best')
        plt.show()

    def __call__(self,*kws):
        '''consider input settings and run annealing loop'''
        for k in kws:self.__setattr__(k,kws[k])
        return self.anneal()

    def __def(self,k,v,**kws):
        if not hasattr(self,k):
            if not k in kws:self.__setattr__(k,v)
            else:self.__setattr__(k,kws[k])

    ###########################################################################
    # f (n,x,b,*g) -> function that creates test data
    #   n - the number of elements in x
    #   x - the domain of the measurement
    #   b - an array to hold the result
    #   g - a tuple of parameter values

    # x -> domain over which fit is performed
    # y -> input data to compare test data to

    # initial -> tuple of initial parameter values
    # bounds -> tuples representing pspace axes bounds
    # iterations -> the maximum number of fitting iterations
    # tolerance -> a limit for exiting fit routine early
    ###########################################################################
    def __init__(self,f,x,y,i,b,**kws):
        '''
        constructor for an annealer object

        param f: function to fit with
        param x: domain to fit over
        param y: input data to fit to
        param i: initial parameter values
        param b: bounds for parameters
        '''

        self.f,self.x,self.y = f,x,y
        self.initial,self.bounds = i,b
        
        self.__def('iterations',100000,**kws)
        self.__def('tolerance',0.00001,**kws)
        self.__def('buffered',False,**kws)
        self.__def('heatrate',10.0,**kws)
        self.__def('discrete',None,**kws)

        self.psp = pspace.pspace(self.bounds,self.initial,self.discrete)
        self.heat(self.heatrate)

        if self.buffered:
            self.buff()
            self.meas = self.measure_buffered
        else:self.meas = self.measure

        if len(y.shape) == 1:self.metric = metric.least_squares
        elif len(y.shape) == 2:self.metric = metric.least_squares_2d
        if len(y.shape) == 1:self.error = metric.percent_error
        elif len(y.shape) == 2:self.error = metric.percent_error_2d
        else:raise ValueError

    def heat(self,b):
        '''initialize an appropriate temperature curve'''
        hx = np.linspace(0,self.iterations,self.iterations)
        self.hc = np.exp(-1.0*b*hx/hx.max())
        return self.hc

    def buff(self):
        '''initialize an array to hold current measurement data'''
        self.measurebuffer = np.zeros(self.x.shape,dtype = self.x.dtype)
        self.fmeas = self.measure_buffered

    def measure_buffered(self,g):
        '''measure a parameter space location using a buffered method'''
        self.f(self.x.size,self.x,self.measurebuffer,*g)
        m = self.metric(self.measurebuffer,self.y)  
        return m

    def measure(self,g):
        '''measure a parameter space location'''
        fofy = self.f(self.x,*g)
        m = self.metric(fofy,self.y)  
        return m

    def complete(self,j,m):
        '''determine if the annealing loop is complete'''
        complete = j >= self.iterations or m < self.tolerance
        return complete

    def better(self,best,new):
        '''determine if the newest measurement is more fit than the best measurement'''
        return new < best

    # measurement, pspace step, completion test, fitness test
    def anneal(self):
        '''perform the annealing loop'''
        self.heat(self.heatrate)
        m = self.meas(self.psp.initial)
        sg = self.psp.step(self.hc[0])
        j = 0
        while not self.complete(j,m):
            sm = self.meas(sg)
            if self.better(m,sm):
                m = sm
                dg = self.psp.delta()
                self.psp.move(sg)

                print 'iteration:',j,'/',self.iterations
                #self.plot(g)

            else:dg = None
            sg = self.psp.step(self.hc[j],dg)
            j += 1

        if j < self.iterations:print 'exited early:',j,'/',self.iterations
        else:print 'didnt exited early:',j,'/',self.iterations

        err = self.error(self.f(self.x,*self.psp.current),self.y)
        return self.psp.current,err

    def anneal_iter(self,i):
        '''perform a loop of annealing and pspace trimming'''
        for j in range(i):
            best,err = self.anneal()
            if j == i - 1:break
            self.heatrate += 2*(j+1)
            self.psp.move_initial(best)
            self.psp.trim()
        return best,err

    def anneal_auto(self,i):
        '''perform a smart loop of annealing and pspace trimming'''
        for j in range(i):
            best,err = self.anneal()
            #if j == i - int(i/2.0):
            if j == i - 3:
                self.psp.become_continuous()
                print 'BECOME CONTINOUS!'
            if j == i - 1:break
            self.heatrate += 2*(j+1)
            self.psp.move_initial(best)
            print 'pretrim',self.psp.bounds
            self.psp.trim()
            print 'posttrim',self.psp.bounds
        return best,err

def run(f,x,y,b = None,i = None,it = 1,**ekwgs):
    '''
    utility function to fit parameter for f,x,y
    return the best fit parameters given:

    param f : function to fit with
    param x : domain to fit over
    param y : input data to fit to
    param b : parameters bounds (can be None)
    param i : initial parameters (can be None)
    '''
    if b is None:
        dim = len(inspect.getargspec(f)[0])-1
        b = tuple(bound(f,x,10**3,j,dim) for j in range(dim))
    if i is None:i = tuple(sum(bd)/2.0 for bd in b)
    anlr = annealer(f,x,y,i,b,**ekwgs)

    result,error = anlr.anneal()
    #result,error = anlr.anneal_iter(it)
    #result,error = anlr.anneal_auto(it)

    return result,error

# determine the proper boundary of an axis 
def bound(f,x,d,ax,dim):
    '''construct boundaries for f considering parity of each axis'''
    r = random.random
    ap = tuple(r() for j in range(dim))
    an = tuple(r if j != ax else -r for j,r in enumerate(ap))
    if (f(x,*ap) == f(x,*an)).all():b = (0,d)
    else:b = (-d,d)
    return b

# return a random position in parameter space
def random_position(bounds):
    '''create a random position given bounds'''
    rpos = tuple(b[0]+random.random()*(b[1]-b[0]) for b in bounds)
    return rpos





