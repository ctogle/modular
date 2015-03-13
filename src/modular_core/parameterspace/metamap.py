import modular_core.fundamental as lfu
import modular_core.io.pkl as pk
import modular_core.data.batch_target as dba
import modular_core.parameterspace.parameterspaces as lpsp

from cStringIO import StringIO
import pdb,os,sys,traceback

if __name__ == 'modular_core.parameterspace.metamap':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
if __name__ == '__main__':print 'metamap of modular_core'

###############################################################################
### a metamap helps maintain persistent mapping info for a model
###############################################################################

class metalocation(object):

    def _save(self,metas):
        # stow all data pools;output self in a readable format
        metas.write('\n'+'-'*100+'\nmetalocation : \n'+self.location_string)
        for dchild in self.simulation_pool.children:
            dchild._stow(v = False)
        #metas.write('\nsimulation_pool at : ')
        #pdb.set_trace()
        #metas.write('\n'+'='*100+'\n')

    def __init__(self,location_string,**kwargs):
        self.location_string = location_string
        self.simulation_pool = dba.batch_node(metapool = True)
    
    def _log_simulation_data(self,loc_pool):
        # if the shape of this loc_pool matches the shape of any previously
        # logged data pools, merge loc_pool with the existing pool
        # otherwise, add loc_pool as a new base pool for later sims
        for sp in self.simulation_pool.children:
            if not sp.dshape[1:] == loc_pool.dshape[1:]:continue
            if not sp.targets == loc_pool.targets:continue
            sp._merge_data(loc_pool)
            print 'merged some data'
            return
        self.simulation_pool._add_child(loc_pool)

class metamap(lfu.mobject):
    # metamap needs to know every possible axis for this model

    # uniqueness should be an object to compare to to verify model identity
    # it should be provided by the simulation module
    # it should change if the model of a simulation changes
    # it should not change if the models run_parameters vary
    # it is a pspace location independent representation of the model
    def __init__(self,*args,**kwargs):
        self._default('axes',[],**kwargs)
        self._default('uniqueness',None,**kwargs)
        self._default('mapfile','pspmap.mmap',**kwargs)
        self._default('mapdir',lfu.get_mapdata_pool_path(),**kwargs)
        self.mappath = os.path.join(self.mapdir,self.mapfile)
        self.children = self.axes
        lfu.mobject.__init__(self,**kwargs)
        self._load()

    def _load(self):
        self.mappath = os.path.join(self.mapdir,self.mapfile)
        if os.path.isfile(self.mappath):
            proxy = pk.load_pkl_object(self.mappath)
            if proxy is None:
                print 'metamap could not unpickle...'
                pdb.set_trace()
            if not proxy.uniqueness == self.uniqueness:
                print 'existing metamap file\'s uniqueness does not match!'
                print 'should prompt for new mapfilename?'
                print 'skipping metamap load...'
                self.entries = {}
                self.location_strings = []
            else:
                self.entries = proxy.entries
                self.location_strings = proxy.location_strings
        else:
            self.entries = {}
            self.location_strings = []
        self._rewidget(True)

    # output self in a recoverable, human readable format
    def _save(self):
        self.mappath = os.path.join(self.mapdir,self.mapfile)
        metastring = StringIO()
        for mloc in self.location_strings:
            self.entries[mloc]._save(metastring)
        self.metastring = metastring.getvalue()
        self._sanitize(propagate = True)
        pk.save_pkl_object(self,self.mappath)
        self._rewidget(True)

    def _log(self,loc_str,loc_pool):
        if not loc_str in self.location_strings:
            metaloc = metalocation(loc_str)
            self.entries[loc_str] = metaloc
            self.location_strings.append(loc_str)
        else:metaloc = self.entries[loc_str]
        metaloc._log_simulation_data(loc_pool)

    def _recover_location(self,loc_str,num_required = None):
        mloc = self.entries[loc_str]
        if not len(mloc.simulation_pool.children) == 1:
            print 'metamap incomplete... defaulting to something...'
        loc_pool = mloc.simulation_pool.children[0]
        if not num_required is None and loc_pool.dshape[0] > num_required:
            loc_pool = loc_pool._subset_pool(num_required)
        return loc_pool

    def _trajectory_count(self,loc_str,dshape):
        if loc_str in self.location_strings:
            mloc = self.entries[loc_str]
            for sp in mloc.simulation_pool.children:
                if dshape[1:] == sp.dshape[1:]:
                    return sp.dshape[0]
            return 0
        else:return 0

    # turn the list of location_strings into pspace_locations 
    # to make an interface
    def _location_from_location_string(self,loc_str):
        locaxs = lfu.msplit(loc_str,'||')
        locvls = []
        for lax in locaxs:locvls.append(float(lfu.msplit(lax,':')[-1]))
        newloc = lpsp.pspace_location(location = locvls)
        trjcnt = self.entries[loc_str].simulation_pool.children[0].dshape[0]
        newloc.trajectory_count = trjcnt
        return newloc

    def _selected_arc_dexes(self):
        def fail():
            self._rewidget(True)
            print 'update widgets...'
            return []
        try:
            ref_children = self.controller_ref[0].children()
            list_widg = None
            row_widg = None
            for c in ref_children:
                if issubclass(c.__class__,lgb.QtGui.QItemSelectionModel):
                    list_widg = c
                if issubclass(c.__class__,lgb.QtCore.QAbstractItemModel):
                    row_widg = c
            if list_widg is None:return fail()
            if row_widg is None:return fail()
            row_count = row_widg.rowCount()
            selected_rows = [r.row() for r in list_widg.selectedRows()]
            return lfu.intersect_lists(selected_rows,range(row_count))
        except:return fail()

    # if one selected:  run post processes on that location
    # if many selected: run post processes on those locations
    def _run_processes_on_locations(self):
        # this should be multithreaded!!
        arc_dexes = self._selected_arc_dexes()
        full_traj = self._trajectory()
        arc = [full_traj[a] for a in arc_dexes]
        ensem = self.parent.parent
        pplan = ensem.postprocess_plan
        zeroth = pplan._init_processes(arc)
        for lstrdex in arc_dexes:
            lstr = self.location_strings[lstrdex]
            loc_pool = self._recover_location(lstr)
            pplan._enact_processes(zeroth,loc_pool)
        pplan._walk_processes()
        ppool = pplan._data()
        ensem._output_postprocesses(ppool)

    # query the user (dialog or command line) for a number of trajectories
    def _query_trajectory_count(self):
        msg = 'How many trajectories should be extracted?\n\t'
        title = 'Specify Trajectory Count'
        count = lfu.gather_string(msg = msg,title = title)
        try:count = int(count)
        except:count = None
        return count

    # if 1 selected:  extract some number of trajectories to look at
    # if >1 selected: extract one trajectory from each location and output all
    def _extract_trajectories(self,plt = True):
        arc_dexes = self._selected_arc_dexes()
        ensem = self.parent.parent
        count = 1
        if len(arc_dexes) == 1:
            query = self._query_trajectory_count()
            if not query is None:count = query
            else:print 'invalid trajectory count input;defaulting to 1...'
        full_traj = self._trajectory()
        meta_locs = [self.entries[self.location_strings[x]] for x in arc_dexes]
        data_pool = dba.batch_node()
        for mloc in meta_locs:
            sps = mloc.simulation_pool.children
            if len(sps) > 1:print 'using first of 2+ simulation pools...'
            sp = sps[0]
            sp._recover()
            for cdx in range(count):
                print 'cdx',cdx
                site_pool = dba.batch_node(
                    dshape = sp.dshape[1:],targets = sp.targets)
                site_data = sp.data[cdx]
                site_pool._trajectory(site_data)
                data_pool._add_child(site_pool)
                data_pool._stow_child(-1,v = False)
        if plt:
            data_cont = lfu.data_container(data = data_pool)
            use = ensem.output_plan.writers[3].use
            ensem.output_plan.writers[3].use = True
            ensem.output_plan(data_cont)
            ensem.output_plan.writers[3].use = use
        return data_pool
    
    # select locations by supplying a trajectory
    # must also return info on completeness 
    #   of database for this trajectory
    # same interface as cplan._new_trajectory?
    def _search_locations(self):
        pdb.set_trace()

    def _trajectory(self):
        trajectory = []
        if len(self.location_strings) > 0:
            for locstr in self.location_strings:
                trajectory.append(self._location_from_location_string(locstr))
        return trajectory

    # want to be able to load/update the metamap
    # browse metamap locations
    # select either one or many metalocs at a time by location_strings
    def _widget(self,*args,**kwargs):
        window = args[0]
        self._sanitize(*args,**kwargs)
        trajectory = self._trajectory()
        headers = [ax.name for ax in self.axes]+['']
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['list_controller'], 
                panel_position = (0,0), 
                panel_span = (3,2), 
                handles = [(self,'controller_ref')], 
                labels = [['Index'.ljust(16),'Trajectory Count']+headers], 
                minimum_sizes = [[(500,300)]], 
                entries = [trajectory], 
                box_labels = ['Metamap Locations']))

        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['button_set'], 
                labels = [[
                    'Load Metamap',
                    'Process Locations',
                    'Extract Trajectories',
                    'Find Locations']],
                bindings = [[
                    lgb.create_reset_widgets_wrapper(window,self._load),
                    self._run_processes_on_locations,
                    self._extract_trajectories,
                    self._search_locations]]))
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['full_path_box'],
                box_labels = ['Metamap Filename'], 
                instances = [[self]],
                keys = [['mappath']],
                initials = [[self.mappath,'Map File (*.mmap)']], 
                labels = [['Set Map File']]))
        '''#
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['directory_name_box'],
                box_labels = ['Metamap Directory'], 
                instances = [[self]],
                keys = [['mapdir']],
                initials = [[self.mapdir]],
                labels = [['Choose Directory']]))
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['file_name_box'],
                box_labels = ['Metamap Filename'], 
                instances = [[self]],
                keys = [['mapfile']],
                initials = [[self.mapfile]],
                labels = [['Choose Filename']]))
        '''#
        lfu.mobject._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################










