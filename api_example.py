import modular_core.libfundamental as lfu
lfu.using_gui = True
from modular_core.libensemble import ensemble_manager

import os,sys,pdb

def run_mcfg(mcfg):
    mcfg = os.path.join(os.getcwd(),mcfg)
    mnger = ensemble_manager()
    ensem = mnger._add_ensemble(module = 'chemical')
    ensem._run_mcfg(mcfg)
    ensem._output()

if __name__ == '__main__':
    try:
	fi = sys.argv[1]
	if os.path.isfile(fi): run_mcfg(fi)
	else: print 'file', fi, 'is not a file!'
    except IndexError: print 'must provide mcfg file!'

