import modular4.qtgui as mg

import matplotlib.pyplot as plt
import sys

import pdb





def plt_window(kws):
    '''
    start a qt application consisting of a single plot window
    '''
    #mg.init_figure()
    mg.runapp(pwindow,kws)

class pwindow(mg.mwindow):

    def content(self,**kws):
        def f():print('bindcalled')
        fs = ((f,),('clicked',),('BIND',))
        bs = mg.buttons(*fs)
        tree = mg.tree_book(**kws)
        ws = [tree]+bs
        content = mg.layout(ws,'v')
        return content





