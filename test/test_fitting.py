#!/usr/bin/env python
import modular4.ensemble as me
import modular4.fitting as mf

import os,sys,numpy,unittest
import matplotlib.pyplot as plt

import pdb



def plot(mcfg,y,r):
    e = me.ensemble().parse_mcfg(mcfg)
    f,x = mf.make_run_func(e)
    init = f(x,*e.pspace.initial[:])
    data = y
    best = f(x,*r)
    ax = plt.gca()
    for j in range(best.shape[0]):
        ax.plot(x,init[j],color = 'b',label = 'initial fit')
        ax.plot(x,data[0][j],color = 'r',label = 'actual',linestyle = '--')
        ax.plot(x,best[j],color = 'g',label = 'best fit')
    ax.legend()
    plt.show()

class test_fitting(unittest.TestCase):

    mm_mcfg = os.path.join(os.getcwd(),'mcfgs','mm_kinetics_fitting.mcfg')

    def data(self,mcfg,a):
        e = me.ensemble().parse_mcfg(self.mm_mcfg)
        f,x = mf.make_run_func(e)
        y = f(None,*a)
        return y.reshape(1,y.shape[0],y.shape[1])

    def test_fit_mm_kinetics(self):
        # make data using actual parameters
        a = (1.0,0.01,800.0)
        y = self.data(self.mm_mcfg,a)

        # fit to that data given the mcfg
        kws = {
            'iterations' : 1000, 
            'heatrate' : 10.0, 
            'plotfinal' : True,
            'plotbetter' : False,
                }
        e = me.ensemble().parse_mcfg(self.mm_mcfg)
        e.set_annealer(y,**kws)
        res,err = e.run()

        # summarize the result of the fit
        print '-'*50
        print 'percentage fit error:',numpy.round(err,3)
        print 'result:',res
        print '-'*50
        plot(self.mm_mcfg,y,res)
        self.assertTrue(err < 1.0)

if __name__ == '__main__':
    unittest.main()





