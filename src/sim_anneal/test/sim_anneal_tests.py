import sim_anneal.anneal as sa
import sim_anneal.pspace as spsp

import matplotlib.pyplot as plt
import unittest,random,numpy,os,sys,time

import pdb

#python -m unittest discover -v ./ "*tests.py"

def plot(x,f,a,g,r):
    plt.plot(x,f(x,*a),color = 'g',label = 'actual')
    plt.plot(x,f(x,*g),color = 'b',label = 'initial',linestyle = '--')
    plt.plot(x,f(x,*r),color = 'r',label = 'result',linestyle = '--')
    plt.show()

doplot = False

expo = lambda x,a,b : a*numpy.exp(b*x)
bell = lambda x,a,b,c : a*numpy.exp(-0.5*((x-b)/c)**2.0)

class test_anneal(unittest.TestCase):

    def runf(self,f,x,y,a,g,b,**kws):
        t = time.time()
        res,err = sa.run(f,x,y,b,g,**kws)
        perror = tuple(abs((r-a)/a)*100.0 for r,a in zip(res,a))
        return res,perror,err,time.time()-t

    def check(self,s,pe,de,rt,param_err = 1.0,data_err = 1.0,rtime = 10.0):
        me = max(pe)
        print s+' parameter/data error:',me,'/',de
        print s+' run time:',rt
        self.assertTrue(me < param_err or de < data_err)
        self.assertTrue(rt < rtime)

    def test_distribution(self):

        def data(b,c):
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
        x,y = data(*a)
        ags = (f,x,y,a,i,b)
        kws = {
            'iterations':10000,
            'tolerance':0.0001}

        res,perror,derror,rtime = self.runf(*ags,**kws)
        if doplot:plot(x,f,a,i,res)
        self.check('dist',perror,derror,rtime)

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

        res,perror,derror,rtime = self.runf(*ags,**kws)
        if doplot:plot(x,expo,a,i,res)
        self.check('expo',perror,derror,rtime)

    def test_bell(self):
        a = (5.0,-3.0,10)
        i = (0,0,1)
        x = numpy.linspace(-100,100,100)
        b = tuple((-100,100) for z in range(len(a)))

        y = bell(x,*a)

        ags = (bell,x,y,a,i,b)
        kws = {
            'iterations':10000,
            'tolerance':0.0001}

        res,perror,derror,rtime = self.runf(*ags,**kws)
        if doplot:plot(x,bell,a,i,res)
        self.check('bell',perror,derror,rtime)

    def test_expo_discrete(self):
        i = (0.0,0.0)
        x = numpy.linspace(0,10,100)
        b = tuple((-10000,10000) for z in range(2))
        d = True

        a = tuple(spsp.reflect(bd,-500,500) for bd in sa.random_position(b))
        y = expo(x,*a)

        ags = (expo,x,y,a,i,b)
        kws = {
            'it':20,
            'discrete':d,
            'iterations':10000,
            'tolerance':0.0001}

        res,perror,derror,rtime = self.runf(*ags,**kws)
        if doplot:plot(x,expo,a,i,res)
        self.check('disrete expo',perror,derror,rtime)

    def test_bell_discrete(self):
        i = (0.0,0.0,0.0)
        x = numpy.linspace(-100,100,100)
        b = tuple((-10000,10000) for z in range(3))
        d = True

        a = sa.random_position(b)
        y = bell(x,*a)

        ags = (bell,x,y,a,i,b)
        kws = {
            'it':10,
            'discrete':d,
            'iterations':10000,
            'tolerance':0.0001}

        res,perror,derror,rtime = self.runf(*ags,**kws)
        if doplot:plot(x,bell,a,i,res)
        self.check('disrete bell',perror,derror,rtime)

if __name__ == '__main__':
    unittest.main()





