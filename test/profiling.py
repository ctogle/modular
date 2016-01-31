import pstats,cProfile,os

import pdb

def profile_function(f,*a,**kw):
    cProfile.runctx('f(*a,**kw)',globals(),locals(),'pf.prof')
    s = pstats.Stats('pf.prof')
    os.remove('pf.prof')
    return s

