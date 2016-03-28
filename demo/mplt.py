#!/usr/bin/env python
import modular4.base as mb
import modular4.ensemble as me
import modular4.output as mo
import modular4.mplt as mt

import sim_anneal.pspace as st

import matplotlib
import matplotlib.pyplot as plt
matplotlib.rcParams['pdf.fonttype'] = 42

import argparse,sys,os,time,numpy,cPickle

import pdb





###############################################################################
###############################################################################

def correl_res_demo():
    #reorgfile = '/srv/4.0/latitude/corrdemo/ensemble/bypsp_output.pkl'
    reorgfile = '/srv/4.0/enterprise/bypsp_output.pkl'
    x,y = 'lambda1','x1,x2-correlation'

    mp = mt.mplot(wspace = 0.2,hspace = 0.2)
    mp.open_data(reorgfile)
    
    msub1 = mp.subplot('111',
        xlab = 'lambda1',ylab = 'correlation coefficient',ymin = 0,ymax = 1,
        plab = 'Correlation Resonance',legendloc = 'lower right')
    msub1.add_line(x,y,color = 'red',name = 'lambda2 = 10',width = 2)
    msub1.add_line(x,y,color = 'blue',name = 'lambda2 = 25',width = 2)
    msub1.add_line(x,y,color = 'green',name = 'lambda2 = 40',width = 2)
    msub1.add_line([10,10],[-1,1],name = '',color = 'black',width = 2,style = '--')
    msub1.add_line([25,25],[-1,1],name = '',color = 'black',width = 2,style = '--')
    msub1.add_line([40,40],[-1,1],name = '',color = 'black',width = 2,style = '--')

    mp.render()

###############################################################################
###############################################################################





###############################################################################

if __name__ == '__main__':
    correl_res_demo()
    plt.show()





