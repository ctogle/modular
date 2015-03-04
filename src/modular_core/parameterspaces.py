import modular_core.fundamental as lfu
import modular_core.settings as lset

import modular_core.io.libfiler as lf
import modular_core.data.datacontrol as ldc

import pdb,sys,os,traceback,time,math,itertools,types,random
import numpy as np
from scipy.integrate import simps as integrate

if __name__ == 'modular_core.parameterspaces':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'parameterspaces of modular_core'

###############################################################################
dicttype = types.DictionaryType
listtype = types.ListType
###############################################################################

###############################################################################
###############################################################################

class cartographer_plan(lfu.plan):

    ### NEEDS TO BE FIXED
    def _string(self):
        if self.trajectory:cnt = str(self.traj_count)
        else: cnt = '1'
        lines = [self.trajectory_string.replace('#',cnt)]
        return lines

    def __init__(self,*args,**kwargs):
        self._default('name','cartographer',**kwargs)
        use = lset.get_setting('mapparameterspace')
        self._default('use_plan',use,**kwargs)
        self._default('parameter_space',None,**kwargs)
        self._default('key_path',None,**kwargs)
        self._default('num_trajectories',1,**kwargs)
        self._default('trajectory',[],**kwargs)
        lfu.plan.__init__(self,*args,**kwargs)

        #self.iteration = 0
        #self.controller_ref = None
        #self.trajectory_string = ''

    def _set_trajectory(self,newtraj):
        self.trajectory = newtraj
        self._move_to(0)

    def _move_to(self,t):
        location = self.trajectory[t].location
        self.parameter_space._move_to(location)



    # append the apparently relevant pspace_axes to rpaxes
    # batch is a dict
    def _run_parameter_axes_dict(self,axes,attrs,rpaxes,batch):
        # must retain order defined by axes (as appears in mcfg...)
        for axname in axes:
            for sub_key in batch.keys():
                mobj = batch[sub_key]
                if not issubclass(mobj.__class__,lfu.run_parameter):continue
                if mobj.name == axname:
                    for pax in mobj.pspace_axes:
                        if pax.key in attrs:
                            rpaxes.append(pax)

    # append the apparently relevant pspace_axes to rpaxes
    # batch is a list
    def _run_parameter_axes_list(self,axes,attrs,rpaxes,batch):
        # must retain order defined by axes (as appears in mcfg...)
        for axname in axes:
            for mobj in batch:
                if not issubclass(mobj.__class__,lfu.run_parameter):continue
                if mobj.name == axname:
                    for pax in mobj.pspace_axes:
                        if pax.key in attrs:
                            rpaxes.append(pax)

    # return list of relevant pspace_axes
    def _run_parameter_axes(self,axes,attrs):
        run_params = self.parent.run_params
        rpaxes = []
        for key in run_params.keys():
            batch = run_params[key]
            if type(batch) is dicttype:
                self._run_parameter_axes_dict(axes,attrs,rpaxes,batch)
            elif type(batch) is listtype:
                self._run_parameter_axes_list(axes,attrs,rpaxes,batch)
        return rpaxes

    # create a parameter space from a list of pspace_axis objects
    def _parameter_space(self,axes):
        self.parameter_space = parameter_space(axes = axes)
        #if axes:self.parameter_space = parameter_space(axes = axes)
        #else:lgd.message_dialog(None,'No parameter space axes!','Problem')
        self._initialize_trajectory()
        self._rewidget(True)
        return self.parameter_space

    def _initialize_trajectory(self):
        location = [sp._value() for sp in self.parameter_space.axes]
        self.trajectory = [pspace_location(location = location)]

    def _widget(self,*args,**kwargs):
        window = args[0]
        self._sanitize(*args,**kwargs)

        lfu.mobject._widget(self,*args,from_sub = True)
        return


        right_side = [lgm.interface_template_gui(
                layout = 'grid', 
                panel_position = (0, 2), 
                widg_positions = [(0, 0), (1, 0), (2, 0)], 
                layouts = ['vertical', 'vertical', 'vertical'], 
                widgets = ['button_set', 'spin', 'full_path_box'], 
                initials = [None, [self.traj_count], 
                    [self.key_path, 'Possible Outputs (*.txt)']], 
                minimum_values = [None, [1], None], 
                maximum_values = [None, [100000], None], 
                instances = [None, [self], [self]], 
                keys = [None, ['traj_count'], ['key_path']], 
                bindings = [[lgb.create_reset_widgets_wrapper(
                        window, self.generate_parameter_space), 
                    self.generate_traj_diag_function(window, 'blank'), 
                    self.generate_traj_diag_function(window, 'modify'), 
                    lgb.create_reset_widgets_wrapper(window, 
                            self.on_delete_selected_pts), 
                    self.on_output_trajectory_key, 
                    lgb.create_reset_widgets_wrapper(window, 
                        self.on_assert_trajectory_count)], None, None], 
                labels = [['Generate Parameter Space', 
                    'Create Trajectory', 'Replace Selected Points', 
                    'Delete Selected Points', 'Output Trajectory Key', 
                    'Assert Trajectory Count\n to Selected'], None, 
                                            ['Choose File Path']], 
                box_labels = [None, 'Trajectory Count', 
                        'Trajectory Key File Path'])]
        split_widg_templates = [
            lgm.interface_template_gui(
                widgets = ['splitter'], 
                orientations = [['horizontal']], 
                templates = [right_side])]
        if not self.parameter_space is None:
            #a point consists of a list of 2 components
            #   the first is the index of the location
            #   the second is the values in 1-1 with 
            #   p-space subspaces
            headers = [subsp.name for subsp in 
                self.parameter_space.subspaces] + ['']
            #self.widg_templates.append(
            left_side = [lgm.interface_template_gui(
                    widgets = ['list_controller'], 
                    panel_position = (0, 0), 
                    panel_span = (3, 2), 
                    handles = [(self, 'controller_ref')], 
                    labels = [['Index'.ljust(16), 
                        'Trajectory Count'] + headers], 
                    minimum_sizes = [[(500, 300)]], 
                    entries = [self.trajectory], 
                    box_labels = ['Trajectory In Parameter Space'])]
            split_widg_templates[-1].templates =\
                        [left_side + right_side]

        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['panel'], 
                templates = [split_widg_templates], 
                scrollable = [True], 
                box_labels = ['Parameter Space']))

        lfu.mobject._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

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
        panel_x,panel_y = 256,256
        lfu.mobject._display(self,self.mason,(150,120,panel_x,panel_y))

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
        if lgm:self.mason = lgm.standard_mason(parent = self)
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












