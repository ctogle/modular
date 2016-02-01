import sim_anneal.anneal as sa
import sim_anneal.forms as sf

import profiling

import matplotlib.pyplot as plt
import unittest,random,numpy,os

import pdb

#python -m unittest discover -v ./ "*tests.py"

class test_anneal(unittest.TestCase):

    def plot(self,x,f,a,g,r):
        plt.plot(x,f(x,*a),color = 'g',label = 'actual')
        plt.plot(x,f(x,*g),color = 'b',label = 'initial')
        plt.plot(x,f(x,*r),color = 'r',label = 'result')
        plt.show()

    def expo(self,x,p,i):
        f = sf.exponential
        for j in range(i):
            y = f(x,*p)
        return y

    def expo_buff(self,x,b,p,i):
        f = sf.exponential_buffered
        s = x.size
        for j in range(i):
            f(s,x,b,*p)
        return b

    #def bell(self,x,actual,guess):

    #def atest_distribution(self):

    #def atest_expo(self):

    #def atest_bell(self):

    def atest_expo_profile(self):
        params = (5.0,-5.0)
        domain = numpy.linspace(0,1000,1000)
        s = profiling.profile_function(self.expo,domain,params,100000)
        #print 'exponential profile stats:',actual,res
        s.strip_dirs().sort_stats('time').print_stats()

    def test_expo_buff_profile(self):
        params = (5.0,-5.0)
        domain = numpy.linspace(0,1000,1000)
        buff = numpy.zeros(domain.shape,domain.dtype)
        s = profiling.profile_function(self.expo_buff,domain,buff,params,100000)
        #print 'exponential profile stats:',actual,res
        s.strip_dirs().sort_stats('time').print_stats()

    #def atest_bell_profile(self):

if __name__ == '__main__':unittest.main()





