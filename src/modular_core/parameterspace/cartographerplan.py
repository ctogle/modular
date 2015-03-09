import modular_core.fundamental as lfu
import modular_core.settings as lset

import modular_core.io.libfiler as lf
import modular_core.parameterspace.parameterspaces as lpsp
import modular_core.parameterspace.metamap as mmap

import pdb,sys,os,traceback,time,math,itertools,types,random
import numpy as np

if __name__ == 'modular_core.parameterspace.parameterspaces':
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
### cartographer plan manages parameter space information
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
        self._default('parent',None,**kwargs)
        self._default('use_plan',use,**kwargs)
        self._default('parameter_space',None,**kwargs)
        self._default('key_path',None,**kwargs)
        #self._default('num_trajectories',1,**kwargs)
        self._default('trajectory',[],**kwargs)

        meta = lset.get_setting('metamapparameterspace')
        self._default('maintain_pspmap',meta,**kwargs)
        self._default('mapfile','pspmap.mmap',**kwargs)
        lfu.plan.__init__(self,*args,**kwargs)

        #self.controller_ref = None
        #self.trajectory_string = ''

    def _metamap(self):
        self.metamap = mmap.metamap(parent = self,mapfile = self.mapfile,
            uniqueness = self.parent.module._metamap_uniqueness())

    # record meta data about zeroth post processes/loc_pool
    #   must be sufficient to recover to reprocess
    def _record_persistent(self,arc_dex,zeroth,loc_pool):
        location = self._print_friendly_pspace_location(arc_dex)
        self.metamap._log(location,zeroth,loc_pool)

    def _print_friendly_pspace_location(self,ldex):
        traj = self.trajectory
        loc = traj[ldex]
        axs = self.parameter_space.axes
        prnt = []
        for a,l in zip(axs,loc):
            prnt.append(a.name+' : '+str(l))
        return ' || '.join(prnt)

    def _print_pspace_location(self,ldex):
        traj = self.trajectory
        loc = traj[ldex]
        locline = [str(l) for l in loc.location]
        return '\t'.join(locline)

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
        self.parameter_space = lpsp.parameter_space(axes = axes)
        #if axes:self.parameter_space = parameter_space(axes = axes)
        #else:lgd.message_dialog(None,'No parameter space axes!','Problem')
        self._initialize_trajectory()
        self._rewidget(True)
        return self.parameter_space

    def _initialize_trajectory(self):
        location = [sp._value() for sp in self.parameter_space.axes]
        self.trajectory = [lpsp.pspace_location(location = location)]

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












