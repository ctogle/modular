import modular_core.libfundamental as lfu
lfu.USING_GUI = False
import modular_core.libsimcomponents as lsc

import os, pdb

mcfg = os.path.join(os.getcwd(), 
	'stringchemical_dep_mcfgs', 
	'MM_kinetics_boring.mcfg')

mnger = lsc.ensemble_manager()
ensem = mnger.add_ensemble()
if ensem: ran = ensem.run_mcfg(mcfg)
else: print 'ensem was not made'; ran = False

print 'ensemble ran', ran
print '-'*50
if ran: print 'MM_kinetics_boring.mcfg test passed'
else: print 'MM_kinetics_boring.mcfg test failed'
print '-'*50


