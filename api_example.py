import modular_core.libfundamental as lfu
lfu.using_gui = True
from modular_core.ensemble import ensemble_manager

import os,sys,pdb

def run_mcfg(module,mcfg):
    mcfg = os.path.join(os.getcwd(),mcfg)
    mnger = ensemble_manager()
    ensem = mnger._add_ensemble(module = module)
    ensem._run_mcfg(mcfg)
    ensem._output()

if __name__ == '__main__':
    agcnt = len(sys.argv)
    if agcnt > 1:
	fi = sys.argv[1]
        if agcnt > 2:mo = sys.argv[2]
        else:mo = 'chemical'
	if os.path.isfile(fi): run_mcfg(mo,fi)
	else: print 'file', fi, 'is not a file!'
    else:print 'must provide mcfg file!'

