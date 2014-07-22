import unittest

import modular_core.libfundamental as lfu
lfu.USING_GUI = False
from modular_core.libsimcomponents import ensemble_manager

import os

class mngerTestCase(unittest.TestCase):
	"""Tests for `libsimcomponents.py`."""
	simple_mcfg = os.path.join(os.getcwd(), 
				'stringchemical_dep_mcfgs', 
				'MM_kinetics_boring.mcfg')

	def test_can_run_ensemble(self):
		"""Is an ensemble successfully run?"""
		mnger = ensemble_manager()
		ensem = mnger.add_ensemble()
		self.assertTrue(ensem.run_mcfg(self.simple_mcfg))

if __name__ == '__main__':
    unittest.main()

