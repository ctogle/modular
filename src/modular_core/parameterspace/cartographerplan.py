import modular_core.fundamental as lfu
import modular_core.settings as lset

#import modular_core.io.libfiler as lf
import modular_core.parameterspace.parameterspaces as lpsp
import modular_core.parameterspace.metamap as mmap

import pdb,sys,os,traceback,time,math,itertools,types,random
import numpy as np

if __name__ == 'modular_core.parameterspace.cartographerplan':
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
        self._default('num_trajectories',1,**kwargs)
        self._default('trajectory',[],**kwargs)

        meta = lset.get_setting('metamapparameterspace')
        self._default('maintain_pspmap',meta,**kwargs)
        self._default('mapfile',None,**kwargs)
        self._default('mapdir',lfu.get_mapdata_pool_path(),**kwargs)
        lfu.plan.__init__(self,*args,**kwargs)

        self.current_tab_index = 0
        self.psptrajectory_controller_ref = None
        #self.trajectory_string = ''

    def _metamap(self):
        if not self.parameter_space is None:
            axes = self.parameter_space.axes
        else:axes = []
        self.metamap = mmap.metamap(axes = axes,
            parent = self,mapfile = self.mapfile,
            mcfgstring = self.parent._mcfg_string(),
            uniqueness = self.parent.module._metamap_uniqueness())
        self.children = [self.metamap]

    def _save_metamap(self):
        self.metamap.parent = None
        self.metamap._save()
        self.metamap.parent = self

    def _metamap_remaining(self,arc_dex,goal,dshape):
        location = self._print_friendly_pspace_location(arc_dex)
        done = self.metamap._trajectory_count(location,dshape)
        remain = goal - done
        if remain < 0:return 0,(0,)+dshape[1:]
        else:return remain,(remain,)+dshape[1:]

    # record meta data about zeroth post processes/loc_pool
    #   must be sufficient to recover to reprocess
    def _record_persistent(self,arc_dex,loc_pool):
        location = self._print_friendly_pspace_location(arc_dex)
        self.metamap._log(location,loc_pool)

    def _print_friendly_pspace_location(self,ldex):
        traj = self.trajectory
        loc = traj[ldex]
        axs = self.parameter_space.axes
        #numtraj = str(self.trajectory[ldex].trajectory_count)
        maxtime = str(self.parent.simulation_plan._max_time())
        captinc = str(self.parent.simulation_plan._capture_increment())
        prnt = []
        prnt.append('end : '+maxtime)
        prnt.append('inc : '+captinc)
        for a,l in zip(axs,loc):
            prnt.append(a.name+' : '+str(l))
        return ' || '.join(prnt)

    def _print_pspace_location(self,ldex):
        traj = self.trajectory
        loc = traj[ldex]
        locline = [str(l) for l in loc.location]
        return '\t'.join(locline)

    # if the location is not present, add it
    # return the index of the location in the trajectory
    def _confirm_location(self,location,goal):
        arc_len = len(self.trajectory)
        for locx in range(arc_len):
            loc = self.trajectory[locx]
            if location.location == loc.location:
                loc.trajectory_count = goal
                return locx
        self.trajectory.append(location)
        location.trajectory_count = goal
        return arc_len

    def _set_trajectory(self,newtraj):
        self.trajectory = newtraj
        #self._move_to(0)

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
        self._initialize_trajectory()
        self._rewidget(True)
        return self.parameter_space

    def _initialize_trajectory(self):
        location = [sp._value() for sp in self.parameter_space.axes]
        self.trajectory = [lpsp.pspace_location(location = location)]

    def _new_trajectory(self,window):
        def _new_traj():
            print 'make a new trajectory!'
            if self.parameter_space is None:
                lfu.complain('Trajectory requires parameter space!')
                return

            '''#
            selected = [self.parameter_space.get_start_position()]

            #traj_dlg = create_trajectory_dialog(
            #   parent = window, base_object = selected, 
            #           p_space = self.parameter_space)
            traj_dlg = lgd.trajectory_dialog(
                parent = window, base_object = selected, 
                        p_space = self.parameter_space)
            made = traj_dlg()
            if made:
                if method == 'modify':
                    self.on_delete_selected_pts(preselected = to_replace)
                    self.on_reset_trajectory_parameterization()

                self.on_append_trajectory(traj_dlg.result)
                self.trajectory_string = traj_dlg.result_string
            '''#

            return []
        print 'new trajectory not implemented!!'
        return lgb.create_reset_widgets_wrapper(window,_new_traj)

    # append new trajectory entries to the current trajectory
    def _add_locations(self,locations):
        self.trajectory.extend(locations)

    # remove selected pspace locations from the current trajectory
    def _remove_locations(self):
        print 'remove locations not implemented!!'
        pdb.set_trace()

        '''#
        if preselected is None:
            selected = [not value for value in 
                self.selected_locations_lookup()]

        else:
            selected = [not value for value in preselected]

        self.trajectory = self.positions_from_lookup(selected)
        self.on_reset_trajectory_parameterization()
        '''#
        self._rewidget(True)

    # output a key representing the current trajectory
    def _output_key(self):
        self.parent._output_trajectory_key()

    # update the trajectory to reflect the trajectory_count spin widget
    def _apply_trajectory_count(self):
        print 'apply t count not implemented!!'
        pdb.set_trace()

        '''#
        if all_:
            relevant_locations =\
                self.positions_from_lookup([True]*len(self.trajectory))

        else:
            relevant_locations = self.positions_from_lookup(
                            self.selected_locations_lookup())

        for locale in relevant_locations:
            locale[1].trajectory_count = self.traj_count
        '''#
        self._rewidget(True)

    # return widget templates associated with pspace/current trajectory
    def _pspace_widg_templates(self,window):
        pspacetemplates = []
        right_side = [lgm.interface_template_gui(
            layout = 'grid',
            layouts = ['vertical'], 
            widgets = ['button_set'],
            widg_positions = [(0, 0),(1, 0),(2, 0)], 
            bindings = [[
                #lgb.create_reset_widgets_wrapper(window,
                #    self.generate_parameter_space), 
                self._new_trajectory(window), 
                lgb.create_reset_widgets_wrapper(
                    window,self._remove_locations),
                self._output_key, 
                lgb.create_reset_widgets_wrapper(
                    window,self._apply_trajectory_count)]],
            labels = [[
                #'Generate Parameter Space', 
                'Create Trajectory',
                'Remove Selected Points',
                'Output Trajectory Key', 
                'Apply Trajectory Count\n to Selected']])]
        right_side[-1] += lgm.interface_template_gui(
            layouts = ['vertical'], 
            widgets = ['spin'], 
            instances = [[self]], 
            keys = [['num_trajectories']], 
            initials = [[self.num_trajectories]], 
            minimum_values = [[1]], 
            maximum_values = [[1000000000]], 
            box_labels = ['Trajectory Count'])
        split_widg_templates = [
            lgm.interface_template_gui(
                widgets = ['splitter'], 
                orientations = [['horizontal']], 
                templates = [right_side])]
        if not self.parameter_space is None:
            headers = [ax.name for ax in self.parameter_space.axes]+['']
            left_side = [lgm.interface_template_gui(
                widgets = ['list_controller'], 
                panel_position = (0,0), 
                panel_span = (3,2), 
                handles = [(self,'psptrajectory_controller_ref')], 
                labels = [['Index'.ljust(16),'Trajectory Count']+headers], 
                minimum_sizes = [[(500,300)]], 
                entries = [self.trajectory], 
                box_labels = ['Trajectory In Parameter Space'])]
            split_widg_templates[-1].templates = [left_side+right_side]
        pspacetemplates = [
            lgm.interface_template_gui(
                widgets = ['panel'], 
                templates = [split_widg_templates], 
                scrollable = [True], 
                box_labels = ['Parameter Space'])]
        return pspacetemplates

    def _widget(self,*args,**kwargs):
        window = args[0]
        self._sanitize(*args,**kwargs)
        psptemplates = self._pspace_widg_templates(window)
        mmap_templates =\
            [lgm.interface_template_gui(
                widgets = ['check_set'], 
                box_labels = ['Use Metamap Features'], 
                append_instead = [False],
                instances = [[self]], 
                keys = [['maintain_pspmap']], 
                labels = [['use metamap']])] +\
            self.metamap.widg_templates
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['tab_book'], 
                verbosities = [0], 
                #handles = [(self,'tab_ref')], 
                pages = [[
                    ('Parameter Space',psptemplates), 
                    ('Metamap',mmap_templates)]], 
                initials = [[self.current_tab_index]], 
                instances = [[self]], 
                keys = [['current_tab_index']]))
        lfu.mobject._widget(self,*args,from_sub = True)
        return

###############################################################################
###############################################################################












