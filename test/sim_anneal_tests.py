import sim_anneal.anneal as sa
import sim_anneal.forms as sf

import matplotlib.pyplot as plt
import unittest,numpy,pstats,cProfile,os,time

import pdb

#python -m unittest discover -v ./ "*tests.py"

def profile_function(f,*a,**kw):
    cProfile.runctx('f(*a,**kw)',globals(),locals(),'pf.prof')
    s = pstats.Stats('pf.prof')
    os.remove('pf.prof')
    return s

class test_anneal(unittest.TestCase):

    def plot(self,x,f,a,g,r):
        plt.plot(x,f(x,*a),color = 'g',label = 'actual')
        plt.plot(x,f(x,*g),color = 'b',label = 'initial')
        plt.plot(x,f(x,*r),color = 'r',label = 'result')
        plt.show()

    def expo(self,x,actual,guess):
        bounds = ((-1000.0,1000.0),(-1000.0,1000.0))
        maxiter = 100000
        tolerance = 0.01
        f = sf.exponential
        y = f(x,*actual)
        res = sa.simanneal(f,x,y,guess,bounds,maxiter,tolerance)
        return res

    def bell(self,x,actual,guess):
        bounds = ((-1000.0,1000.0),(0.0,1000.0),(-1000.0,1000.0))
        maxiter = 100000
        tolerance = 0.0001
        f = sf.bell
        y = f(x,*actual)
        res = sa.simanneal(f,x,y,guess,bounds,maxiter,tolerance)
        return res

    def test_expo(self):
        actual = (5.0,-5.0)
        guess = (1.0,1.0)
        domain = numpy.linspace(0,1000,1000)
        res = self.expo(domain,actual,guess)
        self.plot(domain,sf.exponential,actual,guess,res)
        error = tuple(abs((r-a)/a) for r,a in zip(res,actual))
        print 'exponential error:',actual,res
        self.assertTrue(max(error) < 0.01)

    def test_bell(self):
        actual = (20.0,10.0,8.0)
        guess = (-1.0,1.0,0.1)
        domain = numpy.linspace(-100,100,200)
        res = self.bell(domain,actual,guess)
        self.plot(domain,sf.bell,actual,guess,res)
        error = tuple(abs((r-a)/a) for r,a in zip(res,actual))
        print 'bell error:',actual,res
        self.assertTrue(max(error) < 0.01)

    def _test_expo_profile(self):
        actual = (5.0,-5.0)
        guess = (1.0,1.0)
        domain = numpy.linspace(0,1000,1000)
        s = profile_function(self.expo,domain,actual,guess)
        print 'exponential profile stats:',actual,res
        s.strip_dirs().sort_stats('time').print_stats()

    def _test_bell_profile(self):
        actual = (20.0,10.0,8.0)
        guess = (-1.0,1.0,0.1)
        domain = numpy.linspace(-100,100,200)
        s = profile_function(self.bell,domain,actual,guess)
        print 'bell profile stats:',actual,res
        s.strip_dirs().sort_stats('time').print_stats()

if __name__ == '__main__':unittest.main()





