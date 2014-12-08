import unittest

import modular_core.libfundamental as lfu
from modular_core.libsimcomponents import ensemble_manager

import os, sys, pdb

log = open(os.path.join(os.getcwd(), 'test_ensemble.log'), 'w')
#sys.stdout = log

class mngerTestCase(unittest.TestCase):
    """Tests for `libsimcomponents.py`."""
    simple_mcfg = os.path.join(os.getcwd(), 
                'stringchemical_dep_mcfgs', 
                'MM_kinetics_boring.mcfg')
    ext_signal_mcfg = os.path.join(os.getcwd(), 
                'stringchemical_dep_mcfgs', 
                'ext_signal_example.mcfg')
    fitting_mcfg = os.path.join(os.getcwd(), 
                'stringchemical_dep_mcfgs', 
                'MM_kinetics_fitting.mcfg')
    correl_mcfg = os.path.join(os.getcwd(), 
                'stringchemical_dep_mcfgs', 
                'correl_demo.mcfg')
    correl_mcfg_nonmp = os.path.join(os.getcwd(), 
                'stringchemical_dep_mcfgs', 
                'correl_demo_nonmp.mcfg')
    means_mcfg = os.path.join(os.getcwd(), 
                'stringchemical_dep_mcfgs', 
                'MM_kinetics_means.mcfg')
    mnger = ensemble_manager()
    ensem = mnger.add_ensemble(module = 'chemical')

    def pause(self, *args, **kwargs):
        sys.stdout = sys.__stdout__
        pdb.set_trace()
        sys.stdout = log

    def test_can_make_ensemble(self):
        """ensemble successfully made?"""
        self.assertFalse(self.ensem == None)

    def test_can_run_simple_ensemble(self):
        """ensemble successfully run the simple mcfg?"""
        self.assertTrue(self.ensem.run_mcfg(self.simple_mcfg))
        self.assertTrue(self.ensem.produce_output())

    def test_can_run_with_external_signal(self):
        """ensemble successfully run the external signal mcfg?"""
        self.assertTrue(self.ensem.run_mcfg(self.ext_signal_mcfg))
        self.assertTrue(self.ensem.produce_output())

    def atest_can_run_fitting(self):
        """ensemble successfully run the fitting mcfg?"""
        self.assertTrue(self.ensem.run_mcfg(self.fitting_mcfg))
        self.assertTrue(self.ensem.produce_output())

    def test_can_run_correl_nonmp(self):
        """ensemble successfully run the non mp correl demo mcfg?"""
        #thread = self.mnger.run_threaded(self.ensem, 
        #   self.ensem.run_mcfg, args = (self.correl_mcfg,))
        #self.assertTrue(thread)
        self.assertTrue(self.ensem.run_mcfg(self.correl_mcfg_nonmp))
        self.assertTrue(self.ensem.produce_output())

    def Atest_can_run_correl(self):
        """ensemble successfully run the correl demo mcfg?"""
        #thread = self.mnger.run_threaded(self.ensem, 
        #   self.ensem.run_mcfg, args = (self.correl_mcfg,))
        #self.assertTrue(thread)
        self.assertTrue(self.ensem.run_mcfg(self.correl_mcfg))
        self.assertTrue(self.ensem.produce_output())

    def test_can_run_means(self):
        """ensemble successfully run the mm means mcfg?"""
        #thread = self.mnger.run_threaded(self.ensem, 
        #   self.ensem.run_mcfg, args = (self.means_mcfg,))     
        #self.assertTrue(thread)
        self.assertTrue(self.ensem.run_mcfg(self.means_mcfg))
        self.assertTrue(self.ensem.produce_output())
        #self.assertTrue(self.ensem.run_mcfg(self.fitting_mcfg))
        #self.assertTrue(self.ensem.produce_output())

    def atest_can_run_many_times(self):
        #self.assertTrue(self.ensem.run_mcfg(self.correl_mcfg))
        #self.assertTrue(self.ensem.produce_output())
        self.assertTrue(self.ensem.run_mcfg(self.means_mcfg))
        self.assertTrue(self.ensem.produce_output())
        self.assertTrue(self.ensem.run_mcfg(self.means_mcfg))
        self.assertTrue(self.ensem.produce_output())
        self.assertTrue(self.ensem.run_mcfg(self.fitting_mcfg))
        self.assertTrue(self.ensem.produce_output())
        self.assertTrue(self.ensem.run_mcfg(self.means_mcfg))
        self.assertTrue(self.ensem.produce_output())

    def test_can_produce_output(self):
        """ensemble successfully made output?"""
        ensem = self.ensem
        ensem.run_mcfg(self.simple_mcfg)
        self.assertTrue(ensem.produce_output())
        oplan = ensem.output_plan
        fi = os.path.join(oplan.save_directory, 
                    oplan.save_filename+'.pkl')
        self.assertTrue(os.path.exists(fi))

    def atest_can_run_two_ensembles(self):
        """2 ensembles can successfully run?"""
        ensem1 = self.mnger.add_ensemble()
        ensem2 = self.mnger.add_ensemble()
        ran1 = ensem1.run_mcfg(self.simple_mcfg)
        ran2 = ensem2.run_mcfg(self.simple_mcfg)
        self.assertTrue(ran1)
        self.assertTrue(ran2)

if __name__ == '__main__':
    unittest.main()










