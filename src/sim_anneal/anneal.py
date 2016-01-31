import metric
import pspace
#import forms

import matplotlib.pyplot as plt
import numpy as np

def simanneal(f,x,y,g,b,i,tol,buf = False):
    ann = annealer(f,x,y,g,b,i,tol,buf)
    return ann.anneal()


'''
def simanneal_iter(f,x,y,n,g,m):
    for dn in range(n):
        g = simanneal(f,x,y,g,m)
        if dn < n - 1:
            print 'pretrim',m
            m = pspace.trimspace(f,x,y,g,m)
            print 'posttrim',m
    return g
'''


class annealer(object):

    # f -> function that creates test data
    # x -> domain over which fit is performed
    # y -> input data to compare test data to
    # initial -> tuple of initial parameter values
    # bounds -> tuples representing pspace axes bounds
    # iterations -> the maximum number of fitting iterations
    # tolerance -> a limit for exiting fit routine early

    def __init__(self,f,x,y,
            initial = None,bounds = None,
            iterations = 100000,tolerance = 0.001,
            buffered = False):

        self.f = f
        self.x = x
        self.y = y

        self.psp = pspace.pspace(bounds,initial)

        self.imax = iterations
        self.tol = tolerance
        self.buf = buffered

        self.heat()
        if self.buf:self.buff()

    def buff(self):
        self.measurebuffer = np.zeros(self.x.shape,dtype = self.x.dtype)

    def heat(self):
        a,b = 1.0,-3.0
        hx = np.linspace(0,self.imax,self.imax)
        self.hc = a*np.exp(b*hx/hx.max())
        return self.hc

    def measure_buffered(self,g):
        self.f(self.x.size,self.x,self.measurebuffer,*g)
        m = metric.least_squares(self.measurebuffer,self.y)  
        return m

    def measure(self,g):
        fofy = self.f(self.x,*g)
        m = metric.least_squares(fofy,self.y)  
        return m

    def complete(self,j,m):
        complete = j >= self.imax or m < self.tol
        return complete

    def plot(self,g):
        ya = self.y
        yi = self.f(self.x,*self.psp.initial)
        yb = self.f(self.x,*g)
        plt.plot(self.x,ya,color = 'r',label = 'data')
        plt.plot(self.x,yi,color = 'b',label = 'init')
        plt.plot(self.x,yb,color = 'g',label = 'best')
        plt.show()

    def anneal(self):
        if self.buf:meas = self.measure_buffered
        else:meas = self.measure

        m = meas(self.psp.initial)
        sg = self.psp.step(self.hc[0])

        j = 0
        while not self.complete(j,m):
            sm = meas(sg)
            if sm < m:
                m = sm

                dg = self.psp.delta()
                self.psp.move(sg)

                #print 'iteration:',j,'/',self.imax
                #self.plot(g)

            else:dg = None
            sg = self.psp.step(self.hc[j],dg)
            j += 1

        #if j < self.imax:print 'exited early:',j,'/',self.imax
        #else:print 'didnt exited early:',j,'/',self.imax

        return self.psp.current





