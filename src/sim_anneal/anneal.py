import metric
import pspace
#import forms

import matplotlib.pyplot as plt
import numpy as np

import pdb



__doc__ = '''typical entry point for annealing'''



def simanneal(f,x,y,g,b,i,tol,buf = False):
    '''use an annealer object to return the best fit parameters'''
    ann = annealer(f,x,y,g,b,
        iterations = i,tolerance = tol,buffered = buf)
    return ann.anneal()



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
        self.__def('tolerance',0.000000001,**kws)
        self.__def('buffered',False,**kws)
        self.__def('heatrate',10.0,**kws)

        self.psp = pspace.pspace(self.bounds,self.initial)
        self.heat(self.heatrate)

        if self.buffered:
            self.buff()
            self.meas = self.measure_buffered
        else:self.meas = self.measure

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
        m = metric.least_squares(self.measurebuffer,self.y)  
        return m

    def measure(self,g):
        '''measure a parameter space location'''
        fofy = self.f(self.x,*g)
        m = metric.least_squares(fofy,self.y)  
        return m

    def complete(self,j,m):
        '''determine if the annealing loop is complete'''
        complete = j >= self.iterations or m < self.tolerance
        return complete

    def anneal(self):
        '''perform the annealing loop'''
        self.heat(self.heatrate)
        m = self.meas(self.psp.initial)
        sg = self.psp.step(self.hc[0])

        j = 0
        while not self.complete(j,m):
            sm = self.meas(sg)
            if sm < m:
                m = sm

                dg = self.psp.delta()
                self.psp.move(sg)

                #print 'iteration:',j,'/',self.iterations
                #self.plot(g)

            else:dg = None
            sg = self.psp.step(self.hc[j],dg)
            j += 1

        if j < self.iterations:print 'exited early:',j,'/',self.iterations
        #else:print 'didnt exited early:',j,'/',self.iterations

        return self.psp.current

    def anneal_iter(self,i):
        '''perform a loop of annealing and pspace trimming'''
        for j in range(i):
            best = self.anneal()
            if j == i - 1:break
            self.heatrate += 2*(j+1)
            self.psp.move_initial(best)
            self.psp.trim()
        return best





