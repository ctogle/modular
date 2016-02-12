import sim_anneal.anneal as sa
import modular4.ensemble as me

import numpy as np
import pdb,os,sys



def make_run_func(e):
    simf = e.simmodule.overrides['prepare'](e)
    def f(x,*p):
        px = e.pspacemap.new_location(p)
        e.pspacemap.set_location(px)
        sr = e.run_location(px,simf)
        # hack to return 1st trajectory only for now...
        return sr[0]
    x = np.linspace(0,e.end,1+int(e.end/e.capture))
    return f,x

def run_mcfg(mcfg,y,**kws):
    e = me.ensemble().parse_mcfg(mcfg)
    simf = e.simmodule.overrides['prepare'](e)
    f,x = make_run_func(e)

    if not y.shape[1] == x.shape[0]:
        print('interpolation needs to be implemented!')
        # interpolate y so that it fits on x
        raise ValueError

    b = tuple(tuple(e.pspace.bounds[j]) for j in range(e.pspace.dims))
    i = tuple(e.pspace.current[j] for j in range(e.pspace.dims))
    result,error = sa.run(f,x,y,b,i,**kws)
    return result,error



