import modular_core.fundamental as lfu
import modular_core.fitting.routine_abstract as fab
import modular_core.parameterspace.parameterspaces as lpsp
import modular_core.data.batch_target as dba
import modular_core.io.output as lo

import pdb,os,sys
import numpy as np

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as figure_canvas
import matplotlib.pyplot as plt

###############################################################################
# import other fitting routines to use as the "hammer"
import modular_core.fitting.annealing as fan
import modular_core.fitting.measurement as fme
###############################################################################
### learner runs consecutive fitting routines, applying feedback of information
###############################################################################

class learner(fab.routine_abstract):

    def _iterate_mpi(self,ensem,pspace):
        return self._iterate(ensem,pspace)

    # create a fitting routine and a parameter space and run it
    def _iterate(self,ensem,pspace):
        self.nail = self.hammer[0](*self.hammer[1],**self.hammer[2])
        #self.nail.simulations_per_iteration = self.simulations_per_iteration

        self.nail._initialize(prepoolinit = False)
        print 'nail starting at:',self.nail.parameter_space._position().location
        self.nail._run()
        print 'nail stopping at:',self.nail.parameter_space._position().location
        self.nail._finalize()

        meta = False
        loc_pool = dba.batch_node(metapool = meta)
        loc_pool._add_child(self.nail.data.children[-1])
        loc_pool._stow_child(-1,v = False)

        ran = True
        self.best = True
        return loc_pool,ran

    # always use last result; always accept the "step"
    def _accept_step(self,information,ran):
        return True

    # use the current position in pspace to create a new
    # pspace for the next routine
    def _feedback(self,information,ran,pspace):
        self.nail._move_to_best()

        pspace = self.nail.parameter_space
        print 'old parameter space:'
        for ax in pspace.axes:
            print '\tax:',ax.name,':',ax._value(),':',ax.bounds

        new_pspace = lpsp.trimmed_space(pspace.axes)
        print 'new parameter space:'
        for ax in new_pspace.axes:
            print '\tax:',ax.name,':',ax._value(),':',ax.bounds

        new_pspace.steps = []
        self.hammer[2]['parameter_space'] = new_pspace
        self.hammer[2]['max_iteration'] = 10000*(self.iteration+1)

    def __init__(self,*args,**kwargs):
        self._default('name','a learner',**kwargs)

        self._default('max_runtime',1800.0,**kwargs)
        self._default('max_iteration',100.0,**kwargs)
        self._default('hammer_string',None,**kwargs)
        self._default('nail',None,**kwargs)

        fab.routine_abstract.__init__(self,*args,**kwargs)
    
    def _initialize(self,*args,**kwargs):
        fab.routine_abstract._initialize(self,*args,**kwargs)
        self._set_hammer()
        #self.simulations_per_iteration = self.hammer[0].simulations_per_iteration
        #if self.input_data:
        #    self.input_data._stow(v = False)
        #    self.input_friendly = self.input_data._plot_friendly()
        #    self._alias_input_data()
        #else:self.input_friendly = []

    def _set_hammer(self):
        hspl = lfu.msplit(self.hammer_string)
        hvar = hspl[1]
        if hvar == 'annealing':
            self._set_hammer_annealing(hspl)
        elif hvar == 'measure':
            self._set_hammer_measure(hspl)

    def _set_hammer_annealing(self,hsplit):
        ensem = self.parent.parent
        mkwargs = fan.parse_line(hsplit,ensem,[],[])
        mkwargs['parent'] = self.parent
        margs = ()
        self.hammer = (fan.annealing,margs,mkwargs)

    def _set_hammer_measure(self,hsplit):
        ensem = self.parent.parent
        mkwargs = fme.parse_line(hsplit,ensem,[],[])
        mkwargs['parent'] = self.parent
        margs = ()
        self.hammer = (fme.measure,margs,mkwargs)

    def _finalize(self,*args,**kwargs):
        self.nail._move_to_best()
        self._record_position(self.nail.parameter_space)
        fab.routine_abstract._finalize(self,*args,**kwargs)
        print 'final position:',self.nail.parameter_space._position().location

        last = self.data.children[-1]
        print 'can add input data as subscalars?'
        #pdb.set_trace()

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
    mi,mr,mu,ml,si = split[3:8]
    hstring = split[8][split[8].find('<')+1:split[8].rfind('>')]
    hstring = hstring.replace('%',':').replace('&','%')
    eargs = {
        'name':split[0],
        'variety':split[1],
        'max_iteration':int(mi),
        'max_runtime':int(mr),
        'max_undos':int(mu),
        'max_last_best':int(ml),
        'simulations_per_iteration':int(si),
        'pspace_source':split[2],
        'hammer_string':hstring, 
        'metamapfile':split[9], 
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










