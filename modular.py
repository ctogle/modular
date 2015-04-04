#!/usr/bin/env python
import modular_core.fundamental as lfu
lfu.using_gui = True

from modular_core.ensemble import ensemble_manager

import os,sys,pdb,argparse

from mpi4py import MPI

def run_gui():
    lfu.set_gui_pack('modular_core.gui.libqtgui_modular')
    lfu.gui_pack.initialize()

def run_pklplotter():
    lfu.set_gui_pack('modular_core.gui.libqtgui_pklplotter')
    lfu.gui_pack.initialize()

def run_mcfg(module,mcfg):
    comm = MPI.COMM_WORLD
    mcfg = os.path.join(os.getcwd(),mcfg)
    mnger = ensemble_manager()
    ensem = mnger._add_ensemble(module = module)
    ensem._run_mcfg(mcfg)
    comm.Barrier()
    if comm.rank == 0:ensem._output()
    return comm.rank

if __name__ == '__main__':
    agcnt = len(sys.argv)
    if agcnt > 1:
        fi = sys.argv[1]
        if fi == '--modules':lfu.handle_modules()
        elif fi == '--plt':run_pklplotter()
        else:
            if agcnt > 2:mo = sys.argv[2]
            else:mo = 'gillespiem'
            if os.path.isfile(fi):run_mcfg(mo,fi)
            else: print 'file',fi,'is not a file!'
    else:run_gui()





