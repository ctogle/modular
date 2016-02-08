#!/usr/bin/env python
import modular4.ensemble as me
import modular4.mpi as mmpi

import sys,os,time,numpy

import pdb



def run_gui():
    print('mainuserloop')
    pdb.set_trace()

def run_pklplotter():
    print('pltuserloop')
    pdb.set_trace()

def run_mcfg(mcfg):
    s = time.time()
    sdate = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(s))
    print('begin mcfg run at %s' % sdate)
    r = me.ensemble().parse_mcfg(mcfg).run()
    t = time.time()-s
    print('ran mcfg in %f seconds' % numpy.round(t,3))
    if mmpi.root():
        for o in r:o()

if __name__ == '__main__':
    if '--modules' in sys.argv:
        print('setmodulesloop')
    if '--plt' in sys.argv:run_pkl_plotter()
    elif len(sys.argv) > 1:
        print('runmcfgloop')
        mcfg = os.path.join(os.getcwd(),sys.argv[1])
        if not os.path.isfile(mcfg):
            print('COULD NOT LOCATE MCFG: %s' % mcfg)
        else:run_mcfg(mcfg)
    else:run_gui()




