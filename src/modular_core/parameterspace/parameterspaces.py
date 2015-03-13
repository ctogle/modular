import modular_core.fundamental as lfu
import modular_core.settings as lset

import modular_core.io.libfiler as lf
import modular_core.data.datacontrol as ldc

import pdb,sys,os,traceback,time,math,itertools,types,random
import numpy as np
from scipy.integrate import simps as integrate

if __name__ == 'modular_core.parameterspace.parameterspaces':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'parameterspaces of modular_core'

###############################################################################
### utility functions
###############################################################################

# given the list of arrays of possible values, 1-1 with the pspace axes,
#  create a trajectory of every possible set of values
def trajectory_product(variations):
    combos = itertools.product(*variations)
    trajectory = []
    for tup in combos:
        newloc = pspace_location(location = list(tup))
        trajectory.append(newloc)
    return trajectory




### THIS FUNCTION NEEDS WORK!!!
### THIS FUNCTION NEEDS WORK!!!
### THIS FUNCTION NEEDS WORK!!!
### THIS FUNCTION NEEDS WORK!!!
### THIS FUNCTION NEEDS WORK!!!
### THIS FUNCTION NEEDS WORK!!!
# given the list of arrays of possible values, 1-1 with the pspace axes,
#  create a trajectory using 1-1 sets of values in variations
def trajectory_zip(variations):
    pdb.set_trace()

    max_leng = max([len(variant) for variant in self.variations])
    if max_leng > self.max_locations:
       print ''.join(['WILL NOT MAKE', str(len(
                self.constructed)-1), '+LOCATIONS!'])
       return

    for dex in range(len(self.variations)):
        if self.variations[dex][0] is None:
            self.variations[dex] =\
                [self.base_object[0][dex]]*max_leng

        elif len(self.variations[dex]) < max_leng:
            leng_diff = max_leng - len(self.variations[dex])
            last_value = self.variations[dex][-1]
            [self.variations[dex].append(last_value) for k in
                                                range(leng_diff)]

    for dex in range(max_leng):
        locale = [var[dex] for var in self.variations] 
        self.constructed.append(parameter_space_location(
                                    location = locale))

    pdb.set_trace()
### THIS FUNCTION NEEDS WORK!!!
### THIS FUNCTION NEEDS WORK!!!
### THIS FUNCTION NEEDS WORK!!!
### THIS FUNCTION NEEDS WORK!!!
### THIS FUNCTION NEEDS WORK!!!
### THIS FUNCTION NEEDS WORK!!!




# set the trajectory_count of each place in trajectory to count
def trajectory_set_counts(trajectory,count):
    for locale in trajectory:
        locale.trajectory_count = count

###############################################################################
###############################################################################

def parse_pspace(plines,ensem):
    def read_steps(rng):
        if ';' in rng:return float(rng[rng.rfind(';')+1:])
        else:return 10

    header = plines[0]
    if header[0].count('<product_space>'):variety = 'product'
    elif header[0].count('<zip_space>'):variety = 'zip'
    elif header[0].count('<fitting_space>'):variety = 'fitting'

    axis_lines = plines[1:]
    rparams,attrs,rngs = zip(*axis_lines)
    increments = [read_steps(rng) for rng in rngs]
    rngs = [lfu.parse_range(rng) for rng in rngs]
    rng_bounds = [[rng[0],rng[-1]] for rng in rngs]

    pspaxes = ensem.cartographer_plan._run_parameter_axes(rparams,attrs)
    for rdx in range(len(rparams)):
        rpax = pspaxes[rdx]
        rpax.contribute = True
        rpax.increment = increments[rdx]
        rpax.bounds = rng_bounds[rdx]
        rpax.permanent_bounds = rng_bounds[rdx]
    pspace = ensem.cartographer_plan._parameter_space(pspaxes)

    if variety == 'fitting':pass #fit routines determine trajectory
    else:
        if variety == 'product':newtraj = trajectory_product(rngs)
        elif variety == 'zip':newtraj = trajectory_zip(rngs)
        trajectory_set_counts(newtraj,header[1])
        ensem.cartographer_plan._set_trajectory(newtraj)

###############################################################################
###############################################################################

###############################################################################
### a pspace_axis corresponds to one attribute on one run_parameter
###   it modifies the value held on the run_parameter which is then used
###   for subsequent simulations
###############################################################################

class pspace_axis(lfu.mobject):

    def _display(self):
        #panel_x = self.panel.sizeHint().width()*1.5
        #panel_y = self.panel.sizeHint().height()*1.25
        #panel_x,panel_y = min([panel_x,1600]),min([panel_y,900])
        if lgm:mason = lgm.standard_mason()
        panel_x,panel_y = 256,256
        lfu.mobject._display(self,mason,(150,120,panel_x,panel_y))

    def __init__(self,*args,**kwargs):
        self._default('instance',None,**kwargs)
        self._default('key',None,**kwargs)
        axname = self.instance.name + ' : ' + self.key
        self._default('name',axname,**kwargs)
        self._default('continuous',True,**kwargs)
        self._default('bounds',[0,1],**kwargs)
        self._default('permanent_bounds',[0,1],**kwargs)
        self._default('increment',0.1,**kwargs)
        self._default('contribute',False,**kwargs)
        lfu.mobject.__init__(self,*args,**kwargs)

    def _move_to(self,value):
        self.instance.__dict__[self.key] = value

    def _value(self):
        return self.instance.__dict__[self.key]

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['check_set','button_set'], 
                instances = [[self],None], 
                keys = [['contribute'],None], 
                labels = [['Contribute to Parameter Space'],['More Settings']],
                append_instead = [False,None], 
                bindings = [None,[self._display]], 
                box_labels = ['Parameter Space']))
        self.widg_dialog_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin','spin'], 
                doubles = [[True],[True]], 
                initials = [[self.bounds[0]],[self.bounds[1]]], 
                minimum_values = [[-sys.float_info.max],[-sys.float_info.max]],
                maximum_values = [[sys.float_info.max],[sys.float_info.max]], 
                instances = [[self.bounds],[self.bounds]], 
                keys = [[0],[1]], 
                box_labels = ['Subspace Minimum','Subspace Maximum'], 
                panel_label = 'Parameter Space'))
        lfu.mobject._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

###############################################################################
### pspace_locations are used to compose the cartographer_plans trajectory
###############################################################################

class pspace_location(lfu.mobject):

    def __init__(self,location = [],trajectory_count = 1):
        self.location = location
        self.trajectory_count = trajectory_count
        lfu.mobject.__init__(self)

    def __setitem__(self,key,value):
        self.location[key] = value

    def __getitem__(self,key):
        return self.location[key]

    def __len__(self):
        return len(self.location)

###############################################################################
###############################################################################

###############################################################################
### parameter_spaces consist of pspace_axis objects and methods for managing axes
###############################################################################

class parameter_space(lfu.mobject):

    def _move_to(self,location):
        for adx in range(self.dimensions):
            self.axes[adx]._move_to(location[adx])

    def __init__(self,*args,**kwargs):
        self._default('axes',[],**kwargs)
        self.dimensions = len(self.axes)
        lfu.mobject.__init__(self,*args,**kwargs)

        #self.set_simple_space_lookup()
        #self._default('steps',[],**kwargs)
        #self._default('step_normalization',5.0,**kwargs)

###############################################################################
###############################################################################












