import modular_core.libfundamental as lfu

import pstats, cProfile
import cPickle as pickle

import os, traceback, sys

import pdb

def profile_function(func_):
    #cProfile.runctx('lchem.simulate()',
    cProfile.runctx('func_()',globals(),locals(),'profile.prof')
    s = pstats.Stats('profile.prof')
    s.strip_dirs().sort_stats('time').print_stats()
    os.remove('profile.prof')

if __name__ == '__main__':
    print 'this is a library!'

if __name__ == 'libs.modular_core.libprofile':
    if lfu.gui_pack is None: lfu.find_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb


