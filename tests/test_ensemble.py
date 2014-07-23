import unittest

import modular_core.libfundamental as lfu
lfu.USING_GUI = False
from modular_core.libsimcomponents import ensemble_manager

import os, sys
#sys.stdout = os.devnull
sys.stdout = open(os.path.join(os.getcwd(), 'test_ensemble.log'), 'w')
#sys.__stdout__

class mngerTestCase(unittest.TestCase):
	"""Tests for `libsimcomponents.py`."""
	simple_mcfg = os.path.join(os.getcwd(), 
				'stringchemical_dep_mcfgs', 
				'MM_kinetics_boring.mcfg')
	mnger = ensemble_manager()
	ensem = mnger.add_ensemble()

	def test_can_make_ensemble(self):
		"""ensemble successfully made?"""
		self.assertFalse(self.ensem == None)

	def test_can_run_ensemble(self):
		"""ensemble successfully run?"""
		self.assertTrue(self.ensem.run_mcfg(self.simple_mcfg))

	def test_can_produce_output(self):
		"""ensemble successfully made output?"""
		ensem = self.ensem
		ensem.run_mcfg(self.simple_mcfg)
		self.assertTrue(ensem.produce_output())

	def test_can_run_two_ensembles(self):
		"""2 ensembles can successfully run?"""
		ensem1 = self.mnger.add_ensemble()
		ensem2 = self.mnger.add_ensemble()
		ran1 = ensem1.run_mcfg(self.simple_mcfg)
		ran2 = ensem2.run_mcfg(self.simple_mcfg)
		self.assertTrue(ran1)
		self.assertTrue(ran2)

if __name__ == '__main__':
    unittest.main()

