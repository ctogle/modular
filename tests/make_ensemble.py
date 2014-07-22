import modular_core.libfundamental as lfu
lfu.USING_GUI = False
import modular_core.libsimcomponents as lsc

mnger = lsc.ensemble_manager()
ensem = mnger.add_ensemble()
if not ensem: print 'mnger did not make ensemble : test failed'
else: print 'mnger made ensemble : test passed'

