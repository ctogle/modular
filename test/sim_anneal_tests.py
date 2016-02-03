import sim_anneal.anneal as sa
import sim_anneal.forms as sf

import profiling

import matplotlib.pyplot as plt
import unittest,random,numpy,os,time

import pdb

#python -m unittest discover -v ./ "*tests.py"

def plot(x,f,a,g,r):
    plt.plot(x,f(x,*a),color = 'g',label = 'actual')
    plt.plot(x,f(x,*g),color = 'b',label = 'initial',linestyle = '--')
    plt.plot(x,f(x,*r),color = 'r',label = 'result',linestyle = '--')
    plt.show()

expo = lambda x,a,b : a*numpy.exp(b*x)
bell = lambda x,a,b,c : a*numpy.exp(-0.5*((x-b)/c)**2.0)

class test_anneal(unittest.TestCase):

    def runf(self,f,x,y,a,g,b,**kws):
        t = time.time()
        res = sa.run(f,x,y,b,g,**kws)
        error = tuple(abs((r-a)/a)*100.0 for r,a in zip(res,a))
        return res,error,time.time()-t

    def check(self,s,e,t,error_cutoff = 1.0,rtime_cutoff = 10.0):
        me = max(e)
        print s+' error:',e,me
        print s+' run time:',t
        self.assertTrue(me < error_cutoff)
        self.assertTrue(t < rtime_cutoff)

    def test_distribution(self):

        def d(b,c):
            data = numpy.random.normal(b,c,10000)
            y,bins = numpy.histogram(data,density = True,bins = 100)
            x = numpy.array([(bins[j-1]+bins[j])/2.0 for j in range(1,bins.size)])
            return x,y

        def f(x,b,c):
            a = 1/(2*numpy.pi*c**2)**(0.5)
            return a*numpy.exp(-0.5*((x-b)/c)**2)
    
        a = (20.0,10.0)
        i = (0.0,1.0)
        b = tuple((0,100) for z in range(len(a)))
        x,y = d(*a)
        ags = (f,x,y,a,i,b)
        kws = {
            'iterations':100000,
            'tolerance':0.0001}

        dist_res,dist_error,dist_rtime = self.runf(*ags,**kws)
        self.check('dist',dist_error,dist_rtime)
        plot(x,f,a,i,dist_res)

    def test_expo(self):
        a = (5.0,-5.0)
        i = (0.0,0.0)
        x = numpy.linspace(0,10,100)
        b = tuple((-100,100) for z in range(len(a)))

        y = expo(x,*a)

        ags = (expo,x,y,a,i,b)
        kws = {
            'iterations':10000,
            'tolerance':0.0001}

        expo_res,expo_error,expo_rtime = self.runf(*ags,**kws)
        self.check('expo',expo_error,expo_rtime)
        plot(x,expo,a,i,expo_res)

    def test_bell(self):
        a = (5.0,-3.0,10)
        i = (0,0,1)
        x = numpy.linspace(-100,100,100)
        b = tuple((-100,100) for z in range(len(a)))

        y = bell(x,*a)

        ags = (bell,x,y,a,i,b)
        kws = {
            'iterations':100000,
            'tolerance':0.0001}

        bell_res,bell_error,bell_rtime = self.runf(*ags,**kws)
        self.check('bell',bell_error,bell_rtime)
        plot(x,bell,a,i,bell_res)

if __name__ == '__main__':unittest.main()





