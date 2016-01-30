import sim_anneal.anneal as sa
import sim_anneal.forms as sf

import matplotlib.pyplot as plt
import unittest,numpy,math

import pdb

#python -m unittest discover -v ./ "*tests.py"

class test_anneal(unittest.TestCase):

    domain = numpy.linspace(0,1000,1000)

    def plot(self,x,f,a,g,r):
        plt.plot(x,f(x,*a),color = 'g')
        plt.plot(x,f(x,*g),color = 'b')
        plt.plot(x,f(x,*r),color = 'r')
        plt.show()

    def test_expo(self):
        bounds = ((-1000.0,1000.0),(-1000.0,1000.0))
        actual = (5.0,-5.0)
        guess = (1.0,1.0)
        maxiter = 100000
        tolerance = 0.01

        f = sf.exponential
        x = self.domain
        y = f(x,*actual)

        res = sa.simanneal(f,x,y,guess,bounds,maxiter,tolerance)
        self.plot(x,f,actual,guess,res)

        error = tuple(abs((r-a)/a) for r,a in zip(res,actual))
        self.assertTrue(max(error) < 0.01)

        print 'exponential error:',error,actual,res

if __name__ == '__main__':unittest.main()





