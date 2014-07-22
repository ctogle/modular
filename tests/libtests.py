import modular_core.libfundamental as lfu
import modular_core.libmath as lm

import os, sys, traceback

import pdb

def get_mnger_ensem():
	import modular_core.libsimcomponents as lsc
	mnger = lsc.ensemble_manager()
	mnger.add_ensemble()
	ensem = mnger.ensembles[0]
	return mnger, ensem

def test_mnger_add():
	mnger, ensem = get_mnger_ensem()
	if ensem: test = True
	else: test = False
	return test

def make_path(fi):
	return os.path.join(os.getcwd(),'libs','modular_core','tests',fi)

def test_ensemble_run(ensem, fi):
	ensem.mcfg_path = make_path(fi)
	ensem_prep(ensem)
	return ensem.run()

def ensem_prep(ensem):
	ensem.load_module(True, True)
	ensem.run_params.partition['system']['plot_targets'] =\
							ensem.run_params['plot_targets']
	
def test_ensemble_output(ensem):
	ensem.provide_axes_manager_input()
	ensem.output_plan.targeted =\
		ensem.run_params['plot_targets']
	ensem.output_plan.outputs =\
		[ensem.run_params['plot_targets']]*4
	ensem.produce_output()
	return True

def run_ensem_test(test, mcfg):
	ensem = get_mnger_ensem()[1]
	try: val = test(ensem, mcfg)
	except:
		val = False
		traceback.print_exc(file=sys.stdout)
	return val

_tests_ = {
		'manager adds ensemble' : (test_mnger_add, ()), 
		'perform boring simulation' : (run_ensem_test, 
			(test_ensemble_run, 'MM_kinetics_boring.mcfg',)),  
		'perform multiprocessed simulation' : (run_ensem_test, 
				(test_ensemble_run, 'MM_kinetics_mp.mcfg',)), 
		'perform multiprocessed mapping simulation' : (run_ensem_test, 
				(test_ensemble_run, 'MM_kinetics_mp_mapping.mcfg',)), 
		'perform boring mapping simulation' : (run_ensem_test, 
			(test_ensemble_run, 'MM_kinetics_nonmp_mapping.mcfg',))
		#'perform multiprocessed simulation' : ensemble_run_test_mp, 
		#'perform multiprocessed mapping simulation' : ensemble_run_test_mp_mapping, 
		#'perform boring mapping simulation' : ensemble_run_test_nonmp_mapping, 
		#'ensemble can perform correl_demo simulation' : ensemble_run_test_correl, 
		#'perform output' : ensemble_output_test
		}

if __name__ == '__main__':
	print 'This is a library!'

if __name__ == 'libs.modular_core.libtests':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb


