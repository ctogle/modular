import modular_core.fundamental as lfu
import modular_core.fitting.routine_abstract as fab
import modular_core.io.liboutput as lo

import pdb,os,sys
import numpy as np

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as figure_canvas
import matplotlib.pyplot as plt

###############################################################################
### learner runs consecutive fitting routines, applying feedback of information
###############################################################################

class learner(fab.routine_abstract):

    def _iterate(self,ensem,pspace):
        pdb.set_trace()

    # overloaded to prompt user in the single plot query case
    # consider a measurement, undo or keep step?
    def _accept_step(self,information,ran):
        if not ran:return False

        pdb.set_trace()

    # prompt the user to select from a collection of plots
    def _feedback(self,information,ran,pspace):
        pdb.set_trace()
        #self._pspace_move(pspace,undo)

    def __init__(self,*args,**kwargs):
        self._default('name','a learner',**kwargs)

        self._default('max_runtime',300.0,**kwargs)
        self._default('max_iteration',10.0,**kwargs)
        self._default('onebyone',True,**kwargs)

        fab.routine_abstract.__init__(self,*args,**kwargs)
    
    def _initialize(self,*args,**kwargs):
        fab.routine_abstract._initialize(self,*args,**kwargs)
        if self.input_data:
            self.input_data._stow(v = False)
            self.input_friendly = self.input_data._plot_friendly()
            self._alias_input_data()
        else:self.input_friendly = []

    def _target_settables(self,*args,**kwargs):
        capture_targetable = self._targetables(*args,**kwargs)
        self.target_list = capture_targetable[:]
        self.capture_targets = self.target_list 
        fab.routine_abstract._target_settables(self,*args,**kwargs)

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self._target_settables(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        fab.routine_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

# return valid **kwargs for explorer based on msplit(line)
def parse_line(split,ensem,procs,routs):
    dpath = lfu.resolve_filepath(split[3])
    eargs = {
        'name':split[0],
        'variety':split[1],
        'pspace_source':split[2],
        'input_data_path':dpath, 
        'metamapfile':split[4], 
            }
    return eargs

###############################################################################

if __name__ == 'modular_core.fitting.learner':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lqg = lfu.gui_pack
    fab.routine_types['learning'] = (learner,parse_line)

###############################################################################










