#!/usr/bin/env python
import modular4.base as mb
import modular4.ensemble as me
import modular4.output as mo
import modular4.mpi as mmpi

import sys,os,time,numpy,logging

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
        st = time.time()
        mb.log(5,'begin loadpkl',mb.clock(st))

        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):p = sys.argv[1]
        else:p = os.getcwd()
        fs = os.listdir(p)
        r = []
        for f in fs:
            if f.endswith('.pkl'):
                o = mo.loadpkl(os.path.join(p,f))
                o.modes = ['plt']
                r.append(o)

        et = time.time()
        mb.log(5,'end loadpkl',mb.clock(et))
        mb.log(5,'ran loadpkl in %f seconds' % numpy.round(et-st,3))

        import modular4.qtgui as mg
        mg.init_figure()
        if mmpi.root():
            for o in r:o()

def run_serial(mcfg):
    s = time.time()
    try:locx,dfile = int(sys.argv[3]),sys.argv[4]
    except:
        mb.log(5,'serial submission called with invalid inputs!')
        raise ValueError
    r = me.ensemble(datascheme = 'none').parse_mcfg(mcfg).run_serial(locx,dfile)
    t = time.time()-s

def run_mcfg(mcfg):
    st = time.time()
    if mmpi.root():mb.log(5,'begin run',mb.clock(st))
    r = me.ensemble().parse_mcfg(mcfg).run()
    et = time.time()
    if mmpi.root():
        mb.log(5,'end mcfg run: %s' % mb.clock(et))
        mb.log(5,'ran mcfg in %f seconds' % numpy.round(et-st,3))
        return tuple(o() for o in r)

if __name__ == '__main__':
    if '-v' in sys.argv:logging.basicConfig(level = logging.INFO)
    elif '-V' in sys.argv:logging.basicConfig(level = logging.DEBUG)
    if '--modules' in sys.argv:run_set_modules()
    if '--plt' in sys.argv:run_pklplotter()
    elif len(sys.argv) > 1:
        mcfg = os.path.join(os.getcwd(),sys.argv[1])
        if not os.path.isfile(mcfg):
            mb.log(5,'COULD NOT LOCATE MCFG: %s' % mcfg)
        else:
            if '--serial' in sys.argv:run_serial(mcfg)
            else:run_mcfg(mcfg)
    else:run_gui()





