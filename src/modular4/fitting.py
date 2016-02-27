import sim_anneal.anneal as sa

import numpy as np
import pdb,os,sys



def make_run_func(e,ox = None):
    simf = e.simmodule.overrides['prepare'](e)
    def f(x,*p):
        px = e.pspacemap.new_location(p)
        e.pspacemap.set_location(px)
        sr = e.run_location(px,simf)
        # hack to return 1st trajectory only for now...
        return sr[0,:,btx:ttx]
    x = np.linspace(0,e.end,1+int(e.end/e.capture))
    if not ox is None:
        btx = -1
        for v in x:
            if v > ox.min():break
            else:btx += 1
        ttx = 0
        for v in x:
            if v > ox.max():break
            else:ttx += 1
        x = x[btx:ttx]
    else:btx,ttx = 0,x.size
    return f,x



