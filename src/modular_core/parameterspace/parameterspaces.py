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

# make a discrete space using just orders of magnitude for each axis
def magnitude_space(axes):
    coarse_axes = [ax._coarse() for ax in axes]
    pspace = parameter_space(axes = coarse_axes)
    return pspace

# make a discrete space using 10 values per order of magnitude for each axis
def decimated_space(axes):
    decimated_axes = [ax._decimate() for ax in axes]
    pspace = parameter_space(axes = decimated_axes)
    return pspace

# given the current value of each axis, and the range of its discrete values
# provide a parameter space which increase state density near the current
# pspace location (be removing states far from the current location)
def trimmed_space(axes):
    trimmed_axes = [ax._concentrate() if not ax.locked else ax for ax in axes]
    pspace = parameter_space(axes = trimmed_axes)
    return pspace

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
        self._default('discrete',None,**kwargs)
        self._default('caste',float,**kwargs)
        lfu.mobject.__init__(self,*args,**kwargs)

    def _discretize(self):
        if not self.continuous:
            span = self.bounds[1]-self.bounds[0]
            if self.increment == 0.0:self.increment = span
            num = int(span/self.increment)+1
            self.discrete = list(np.linspace(
                self.bounds[0],self.bounds[1],num))
        else:self.discrete = None

    def _coarse(self):
        it = self.instance
        ke = self.key
        b0 = lfu.coerce_float_magnitude(self.bounds[0])
        b1 = lfu.coerce_float_magnitude(self.bounds[1])
        bs = [b0,b1]
        ic = lfu.coerce_float_magnitude(self.increment)
        coarse = pspace_axis(instance = it,key = ke,
            bounds = bs,increment = ic,continuous = False,
            permanent_bounds = self.permanent_bounds)
        coarse.discrete = lfu.order_span(*coarse.bounds)
        return coarse

    def _decimate(self):
        b0 = lfu.coerce_float_magnitude(self.bounds[0])
        b1 = lfu.coerce_float_magnitude(self.bounds[1])
        relev_mags = lfu.order_span(b0,b1)
        deciax = self._decimate_range(relev_mags)
        it = self.instance
        ke = self.key
        bs = [b0,b1]
        deciax = lfu.uniqfy(deciax)
        decimated = pspace_axis(instance = it,key = ke,
            bounds = bs,increment = None,continuous = False,
            permanent_bounds = self.permanent_bounds)
        decimated.discrete = deciax
        return decimated

    def _concentrate(self):
        wheres = range(len(self.discrete))
        where = lfu.nearest_index(self._value(),self.discrete)
        cut = int(len(wheres)/6)
        if cut > 0:
            if where in wheres[2*cut:-2*cut]:keep = self.discrete[cut:-cut]
            elif where in wheres[:-2*cut]:keep = self.discrete[:-cut]
            elif where in wheres[2*cut:]:keep = self.discrete[cut:]
        else:
            keep = self.discrete[:]
            side = self._on_edge()
            if side == 'left':
                keep.insert(0,lfu.coerce_float_magnitude(self.bounds[0])/10.0)
                keep.pop(-1)
            elif side == 'right':
                keep.append(lfu.coerce_float_magnitude(self.bounds[1])*10.0)
                keep.pop(0)
            keep = self._decimate_range(self.discrete[:],6)

        b0,b1 = keep[0],keep[-1]
        bs = [b0,b1]
        it = self.instance
        ke = self.key
        concentrated = pspace_axis(instance = it,key = ke,
            bounds = bs,increment = None,continuous = False,
            permanent_bounds = self.permanent_bounds)
        concentrated.discrete = keep
        return concentrated

    def _on_edge(self):
        cv = self._value()
        span = float(len(self.discrete))
        spos = float(lfu.nearest_index(cv,self.discrete))/span
        print 'onedge',spos
        if spos > 0.6:return 'right'
        if spos < 0.4:return 'left'
        else:return False

    def _decimate_range(self,rng,num_values = 10):
        def create_subrange(dex,num_values):
            lower,upper = rng[dex-1:dex+1]
            new = np.linspace(lower,upper,num_values)
            return [np.round(val,20) for val in new]

        if len(rng) <= 1:deci = rng
        else:
            deci = []
            for dex in range(1,len(rng)):
                subd = create_subrange(dex,num_values)
                deci.extend(subd)
        deci = lfu.uniqfy(deci)
        return deci

    def _move_to(self,value):
        self.instance.__dict__[self.key] = self.caste(value)

    def _value(self):
        return float(self.instance.__dict__[self.key])

    def _validate_continuous(self,step):
        old_value = float(self._value())
        if old_value + step < self.bounds[0]:
            over_the_line = abs(step) - abs(old_value - self.bounds[0])
            step = over_the_line - old_value
        elif old_value + step > self.bounds[1]:
            over_the_line = abs(step) - abs(self.bounds[1] - old_value)
            step = self.bounds[1] - over_the_line - old_value
        return step

    def _validate_discrete(self,step):
        if len(self.discrete) == 1:
            print 'vacuous validation...'
            return 0
        old_value = float(self._value())
        space_leng = len(self.discrete)
        val_dex_rng = range(space_leng)
        if old_value in self.discrete:
            val_dex = self.discrete.index(old_value)
        else:val_dex = lfu.nearest_index(old_value,self.discrete)

        if val_dex + step > (len(val_dex_rng) - 1):
            over = val_dex + step - (len(val_dex_rng) - 1)
            step = (len(val_dex_rng) - 1) - val_dex - over
        if val_dex + step < 0:
            over = abs(val_dex + step)
            step = over - val_dex
        
        ret = self.discrete[val_dex + step] - old_value
        return self.discrete[val_dex + step] - old_value

    def _validate_step(self,step):
        if self.continuous:step = self._validate_continuous(step)
        else:step = self._validate_discrete(step)
        step = np.round(step,20)
        return step

    def _sample(self,norm = 3.0,fact = 1.0,direct = None):
        if self.continuous:leng = self.bounds[1] - self.bounds[0]
        else:leng = len(self.discrete)

        sig = leng/norm
        if direct is None:direct = random.choice([-1.0,1.0])
        raw_step = random.gauss(sig,sig)

        if self.continuous:step = abs(raw_step)*fact*direct
        else:step = int(max([1,abs(raw_step*fact)])*direct)

        step = self._validate_step(step)
        return step

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
### used by fitting routines to navigate the parameter space
###############################################################################

class pspace_step(object):

    def __init__(self,location = [],initial = [],final = []):
        self.location = location
        self.initial = initial
        self.final = final

    def _forward(self):
        for k in range(len(self.location)):
            i,ke = self.location[k]
            i.__dict__[ke] = float(self.final[k])

    def _backward(self):
        for k in range(len(self.location)):
            i,ke = self.location[k]
            i.__dict__[ke] = float(self.initial[k])

###############################################################################
###############################################################################

###############################################################################
### parameter_spaces consist of pspace_axis objects and methods for managing axes
###############################################################################

class parameter_space(lfu.mobject):

    def _move_to(self,location):
        for adx in range(self.dimensions):
            self.axes[adx]._move_to(location[adx])
    
    def _position(self):
        locvals = [ax._value() for ax in self.axes]
        pos = pspace_location(location = locvals)
        return pos

    def _lock_singular_axes(self):
        unlocked = 0
        for ax in self.axes:
            if ax.bounds[1] - ax.bounds[0] < 10**-20:
                ax.locked = True
                print 'ax is locked:',ax.name
            else:
                ax.locked = False
                unlocked += 1
                if not ax.discrete:ax._discretize()
        self.unlocked_axes = unlocked

    def __init__(self,*args,**kwargs):
        self._default('axes',[],**kwargs)
        self.dimensions = len(self.axes)
        self._default('step_normalization',5.0,**kwargs)
        lfu.mobject.__init__(self,*args,**kwargs)

    def _undo_step(self):
        if not self.steps:print 'no pspace_steps to undo...'
        else:
            newstep = pspace_step(
                location = self.steps[-1].location, 
                initial = self.steps[-1].final,
                final = self.steps[-1].initial)
            self.steps.append(newstep)
            self.steps[-1]._forward()

    # take a multidimensional parameter step proportional to factor
    def _proportional_step(self,factor,many_steps = 3,last_ax_pairs = None):
        lookup = self._lookup(last_ax_pairs)
        param_dexes = self._distinct_lookup(lookup,many_steps)

        last_axes = [];last_direcs = []
        if last_ax_pairs:last_axes,last_direcs = zip(*last_ax_pairs)

        self.steps.append(pspace_step(location = [],initial = [],final = []))
        for param_dex in param_dexes:
            if param_dex in last_axes:
                direc = last_direcs[last_axes.index(param_dex)]
                if direc is None:direc = random.choice([-1.0, 1.0])
            else:direc = random.choice([-1.0, 1.0])
            self._prep_step(param_dex,factor,direc)
        self.steps[-1]._forward()

    # _biased_step is a wrapper for _proportional_step
    # use less step to determine bias
    def _biased_step(self,factor = 1.0,bias = 100.0):
        if not self.steps:return self._proportional_step(factor)

        def direction(dex):
            delta = self.steps[-1].final[dex]-float(self.steps[-1].initial[dex])
            if delta:return delta/abs(delta)
            else:return None

        objs = [ax.instance for ax in self.axes]
        step_objs = [local[0] for local in self.steps[-1].location]
        last_ax_dexes = [objs.index(obj) for obj in step_objs]
        last_ax_direcs = [direction(k) for k in range(len(self.steps[-1].initial))]
        last_ax_pairs = zip(last_ax_dexes,last_ax_direcs)
        many = len(last_ax_pairs)
        self._proportional_step(factor,many,last_ax_pairs)

    #bias_axis is the index of the subspace in subspaces
    #bias is the number of times more likely that axis is than the rest
    def _lookup(self,bias_axis = None,bias = 1000.0):
        lookup = [0.0]
        if bias_axis is None:biaxes = []
        else:biaxes = [b[0] for b in bias_axis]
        for d in range(self.dimensions):
            ax = self.axes[d]
            if not ax.locked:lookup.append(lookup[-1]+1.0)
            else:lookup.append(lookup[-1])
            if d in biaxes:lookup[-1] *= bias
        lookup.pop(0)
        lookup = lfu.normalize(lookup,20)
        return lookup

    # lookup represents the probability distribution for pspace axes
    # using monotonic normalized lookup method also used in gillespiem...
    def _distinct_lookup(self,lookup,many_steps):
        dexes = []
        dexgoal = min([self.unlocked_axes,many_steps])
        for x in range(dexgoal):
            if len(dexes) == dexgoal:break
            rand = random.random()
            for d in range(self.dimensions):
                if d in dexes:continue
                look = lookup[d]
                if rand < lookup[d]:
                    dexes.append(d)
                    clook = lookup[d]
                    if d > 1:clook -= lookup[d-1]
                    for a in range(d,self.dimensions):
                        lookup[a] -= clook
                    lookup = lfu.normalize(lookup)
                    break
        return dexes

    # continue to prepare for the next pspace step by setting up axis adx
    def _prep_step(self,adx,factor,direct):
        ax = self.axes[adx]
        old_value = float(ax._value())
        norm = self.step_normalization
        step = ax._sample(norm,factor,direct)

        self.steps[-1].location.append((ax.instance,ax.key))
        self.steps[-1].initial.append(old_value)
        self.steps[-1].final.append(step+old_value)

###############################################################################
###############################################################################










