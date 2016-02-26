#!/usr/bin/env python
import unittest

import modular4.ensemble as me

import pdb,os,sys



class test_ensemble(unittest.TestCase):

    mm_mcfg = os.path.join(os.getcwd(),'mcfgs','mm_kinetics.mcfg')
    cr_mcfg = os.path.join(os.getcwd(),'mcfgs','correl_demo.mcfg')
    rs_mcfg = os.path.join(os.getcwd(),'mcfgs','repress.mcfg')

    def _test_parse_run_correl(self):
        ekws = {'name':'correl_ensemble_test','module':'dstoolm'}
        r = me.ensemble(**ekws).parse_mcfg(self.cr_mcfg).run()
        for o in r:o()
        for o in r:o.join()

    def _test_parse_run_mmkinetics(self):
        ekws = {'name':'mm_ensemble_test','module':'dstoolm'}
        r = me.ensemble(**ekws).parse_mcfg(self.mm_mcfg).run()
        for o in r:o()
        for o in r:o.join()

    def test_parse_run_repress(self):
        ekws = {'name':'repress_ensemble_test','module':'dstoolm'}
        r = me.ensemble(**ekws).parse_mcfg(self.rs_mcfg).run()
        for o in r:o()
        for o in r:o.join()

if __name__ == '__main__':
    unittest.main()





