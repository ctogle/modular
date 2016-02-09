#!/usr/bin/env python
import modular4.ensemble as me
import modular4.output as mo
import modular4.mpi as mmpi

import sys,os,time,numpy

import pdb



def run_set_modules():
    if mmpi.root():
        print('setmodulesloop')
        raise NotImplementedError

def run_gui():
    if mmpi.root():
        print('mainuserloop')
        raise NotImplementedError

def run_pklplotter():
    if mmpi.root():
        s = time.time()
        sdate = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(s))
        print('begin loadpkl at %s' % sdate)
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):p = sys.argv[1]
        else:p = os.getcwd()
        fs = os.listdir(p)
        r = []
        for f in fs:
            if f.endswith('.pkl'):
                o = mo.loadpkl(os.path.join(p,f))
                o.modes = ['plt']
                r.append(mo.loadpkl(os.path.join(p,f)))
        t = time.time()-s
        print('ran loadpkl in %f seconds' % numpy.round(t,3))
        import modular4.qtgui as mg
        mg.init_figure()
        if mmpi.root():
            for o in r:o()

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
    if '--modules' in sys.argv:run_set_modules()
    if '--plt' in sys.argv:run_pklplotter()
    elif len(sys.argv) > 1:
        mcfg = os.path.join(os.getcwd(),sys.argv[1])
        if not os.path.isfile(mcfg):
            print('COULD NOT LOCATE MCFG: %s' % mcfg)
        else:run_mcfg(mcfg)
    else:run_gui()




