import unittest

import modular_core.fundamental as lfu
from modular_core.ensemble import ensemble_manager

import os, sys, pdb

class mngerTestCase(unittest.TestCase):
    gillm_mcfgpath = os.path.join(os.getcwd(),'gillespiemmcfgs')
    simple_mcfg = os.path.join(gillm_mcfgpath,'MM_kinetics_boring.mcfg')
    ext_signal_mcfg = os.path.join(gillm_mcfgpath,'ext_signal_example.mcfg')
    fitting_mcfg = os.path.join(gillm_mcfgpath,'MM_kinetics_fitting.mcfg')
    correl_mcfg = os.path.join(gillm_mcfgpath,'correl_demo.mcfg')
    correl_mcfg_nonmp = os.path.join(gillm_mcfgpath,'correl_demo_nonmp.mcfg')
    means_mcfg = os.path.join(gillm_mcfgpath,'MM_kinetics_means.mcfg')

    mnger = ensemble_manager()
    ensem = mnger._add_ensemble(module = 'gillespiem')

    def test_can_run_simple_ensemble(self):
        """ensemble successfully run the simple mcfg?"""
        self.assertTrue(self.ensem._run_mcfg(self.simple_mcfg))
        self.assertTrue(self.ensem._output())

    def test_can_run_with_external_signal(self):
        """ensemble successfully run the external signal mcfg?"""
        self.assertTrue(self.ensem._run_mcfg(self.ext_signal_mcfg))
        self.assertTrue(self.ensem._output())

    def atest_can_run_fitting(self):
        """ensemble successfully run the fitting mcfg?"""
        self.assertTrue(self.ensem._run_mcfg(self.fitting_mcfg))
        self.assertTrue(self.ensem._output())

    def test_can_run_correl_nonmp(self):
        """ensemble successfully run the non mp correl demo mcfg?"""
        self.assertTrue(self.ensem._run_mcfg(self.correl_mcfg_nonmp))
        self.assertTrue(self.ensem._output())

    def test_can_run_correl(self):
        """ensemble successfully run the correl demo mcfg?"""
        self.assertTrue(self.ensem._run_mcfg(self.correl_mcfg))
        self.assertTrue(self.ensem._output())

    def test_can_run_means(self):
        """ensemble successfully run the mm means mcfg?"""
        self.assertTrue(self.ensem._run_mcfg(self.means_mcfg))
        self.assertTrue(self.ensem._output())
        #self.assertTrue(self.ensem.run_mcfg(self.fitting_mcfg))
        #self.assertTrue(self.ensem.produce_output())

    def atest_can_run_many_times(self):
        #self.assertTrue(self.ensem.run_mcfg(self.correl_mcfg))
        #self.assertTrue(self.ensem.produce_output())
        self.assertTrue(self.ensem._run_mcfg(self.means_mcfg))
        self.assertTrue(self.ensem._output())
        self.assertTrue(self.ensem._run_mcfg(self.means_mcfg))
        self.assertTrue(self.ensem._output())
        self.assertTrue(self.ensem._run_mcfg(self.fitting_mcfg))
        self.assertTrue(self.ensem._output())
        self.assertTrue(self.ensem._run_mcfg(self.means_mcfg))
        self.assertTrue(self.ensem._output())

if __name__ == '__main__':unittest.main()










