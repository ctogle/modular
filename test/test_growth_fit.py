#!/usr/bin/env python
import modular4.base as mb
import modular4.ensemble as me
import modular4.fitting as mf
import modular4.output as mo
import modular4.mpi as mmpi

import os,sys,numpy,unittest
import matplotlib.pyplot as plt

import pdb



class test_fitting(unittest.TestCase):

    gw_mcfg = os.path.join(os.getcwd(),'mcfgs','growth.mcfg')
    fd_file = os.path.join(os.getcwd(),'data','converteddata.pkl')

    def test_fit_growth(self):
        e = me.ensemble(module = 'dstoolm',datascheme = 'none')
        e.parse_mcfg(self.gw_mcfg).simmodule.overrides['prepare'](e)
        skws = {
            'iterations':100,'heatrate':3.0,'mstep':max(mmpi.size()-1,1),
            'plotfinal':False,'plotbetter':False,
                }

        moup = mo.loadpkl(self.fd_file)
        for pg in moup.pages:
            if moup.inform:moup.inform(e,pg)
            yd,yt,ye = pg
            e.set_annealer(yd,**skws)
            r = e.run()
            res,err = r

        ro = e.output(True)
        for o in ro:o()

if __name__ == '__main__':
    unittest.main()





