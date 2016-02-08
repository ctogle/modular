import modular4.qtgui as mg

import matplotlib.pyplot as plt
import sys,multiprocessing

import pdb





sepproc = True
def plt_window(**kws):
    '''
    start a qt application consisting of a single plot window
    run this application in a separate process
    '''
    if sepproc:
        process = multiprocessing.Process(target = mg.runapp,args = (pwindow,kws))
        process.start()
        return process
    else:mg.runapp(pwindow,kws)

class pwindow(mg.mwindow):

    def content(self,**kws):
        def f():print('bindcalled')
        fs = ((f,),('clicked',),('BIND',))
        bs = mg.buttons(*fs)
        tree = mg.tree_book(**kws)
        ws = [tree]+bs
        content = mg.layout(ws,'v')
        return content





