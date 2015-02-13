import modular_core as mc
import modular_core.libfundamental as lfu
import modular_core.libsimcomponents as lsc
import modular_core.libmodcomponents as lmc
import modular_core.libgeometry as lgeo
import modular_core.libmultiprocess as lmp
import modular_core.libiteratesystem as lis
import modular_core.libsettings as lset

import modular_core.io.liboutput as lo
import modular_core.io.libfiler as lf
import modular_core.criteria.libcriterion as lc
import modular_core.fitting.libfitroutine as lfr
import modular_core.data.libdatacontrol as ldc
import modular_core.postprocessing.libpostprocess as lpp

import modular_core.postprocessing.meanfields as mfs

import pdb,os,sys,traceback,types,time,imp
import numpy as np
import importlib as imp

if __name__ == 'modular_core.libensemble':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'libensemble of modular_core'

###############################################################################
### an ensemble represents a collection of simulations and their analysis
###   each ensemble has:
###     exactly one simulation module
###     parameter space of any dimension
###     set of post processes and fitting routines
###     unique data pool held in an os safe place
###     output plans and those of its processes
###     a set of targets to capture data for
###     an interface nested within that of its associated ensemble_manager
###############################################################################

class ensemble(lfu.mobject):

    def _new_data_pool_id(self):
        return str(time.time())

    def __init__(self,*args,**kwargs):
        self._default('name','ensemble',**kwargs)
        self._default('mcfg_dir',lfu.get_mcfg_path(),**kwargs)
        self._default('mcfg_path','',**kwargs)
        self._default('skip_simulation',False,**kwargs)
        self._default('multithread_gui',False,**kwargs)
        num_traj = lset.get_setting('trajectory_count')
        self._default('num_trajectories',num_traj,**kwargs)

        self.simulation_plan = lsc.simulation_plan(parent = self)
        self.output_plan = lo.output_plan(
            parent = self,name = 'Simulation',flat_data = False)
        self.fitting_plan = lfr.fit_routine_plan(parent = self)
        self.cartographer_plan = lgeo.cartographer_plan(
            parent = self,name = 'Parameter Scan')
        self.postprocess_plan = lpp.post_process_plan(parent = self,
            name = 'Post Process Plan',always_sourceable = ['simulation'])
        self.multiprocess_plan = lmp.multiprocess_plan(parent = self)
        self.children = [
            self.simulation_plan,self.output_plan,self.fitting_plan,
            self.cartographer_plan,self.postprocess_plan,self.multiprocess_plan]
        lfu.mobject.__init__(self,*args,**kwargs)

        self.run_params = {}
        self.run_params['end_criteria'] = self.simulation_plan.end_criteria
        self.run_params['capture_criteria'] = self.simulation_plan.capture_criteria
        self.run_params['plot_targets'] = self.simulation_plan.plot_targets
        self.run_params['output_plans'] = {'Simulation' : self.output_plan}
        self.run_params['fit_routines'] = self.fitting_plan.routines
        self.run_params['post_processes'] = self.postprocess_plan.processes
        self.run_params['p_space_map'] = None
        self.run_params['multiprocessing'] = None
        self.capture_targets = self.run_params['plot_targets']

        self._select_module(**kwargs)
        self.module._reset_parameters()

        self.data_pool_descr = ''
        self.data_pool_id = self._new_data_pool_id()
        self.data_pool = self._data_scheme()

        self.aborted = False
        self.current_tab_index = 0

    def _select_module(self,**kwargs):
        self.cancel_make = False
        opts = kwargs['module_options']
        if len(opts) == 0:
            if lfu.using_gui:
                lgd.message_dialog(None,'No modules detected!','Problem')
            else: print 'Problem! : No modules detected!'
            self.cancel_make = True
            return
        elif len(opts) == 1: module = opts[0]
        else:
            if lfu.using_gui:
                module = lgd.create_dialog(
                    title = 'Choose Ensemble Module', 
                    options = opts, 
                    variety = 'radioinput')
                if not module: 
                    self.cancel_make = True
                    return
            else:
                if not 'module' in kwargs.keys():
                    mod_request = 'enter a module:\n\t'
                    for op in opts:mod_request += op + '\n\t'
                    mod_request += '\n'
                    module = raw_input(mod_request)
                else: module = None
        if not 'module' in kwargs.keys():
            print 'Problem! : No modules detected!'
            self.cancel_make = True
            return
        else: module = kwargs['module']
        self.module_name = module

        # if module has a simulation_module subclass use that
        # otherwise use the baseclass from lmc
        module = mc.modules.__dict__[self.module_name]
        if hasattr(module,'simulation_module'):
            self.module = module.simulation_module(parent = self)
        else:self.module = lmc.simulation_module(parent = self)
        self.children.append(self.module)

    # compute any information that changes only when the parameter space
    #  location changes
    def _run_params_to_location(self):
        self.module._set_parameters()

    # run a specific way depending on the settings of the ensemble
    def _run_specific(self,*args,**kwargs):
        start_time = time.time()
        stime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(start_time))
        print 'start time:',stime

        pspace = self.cartographer_plan.parameter_space
        mappspace = self.cartographer_plan.use_plan and pspace
        mpplan = self.multiprocess_plan.use_plan

        if self.skip_simulation:save,dpool = self._post_processing(load = True)
        else:
            save = True
            if self.fitting_plan.use_plan:dpool = self._run_fitting()
            elif mpplan and mappspace:dpool = self._run_map_mp()
            elif not mpplan and mappspace:dpool = self._run_map_nonmp()
            elif mpplan and not mappspace:dpool = self._run_nonmap_mp()
            elif not mpplan and not mappspace:dpool = self._run_nonmap_nonmp()
            print 'duration of simulations:',time.time() - start_time
            dum,dpool = self._post_processing(load = False,dpool = dpool)
        if save:self._save_data_pool(dpool)

        print 'finished simulations and analysis:exiting'
        print 'total run duration:',time.time() - start_time,'seconds'
        return True

    # NOT TESTED
    # use the fitting_plan to perform simulations
    def _run_fitting(self):
        dpool = self._data_scheme()
        if not self.cartographer_plan.parameter_space:
            print 'fitting requires a parameter space!'
        dpool = self.fitting_plan(self,dpool)
        return dpool

    #no multiprocessing, no parameter variation, and no fitting
    def _run_nonmap_nonmp(self):
        data_pool = self._data_scheme()
        simu = self.module.simulation
        self._run_params_to_location()
        sim_args = self.module.sim_args
        trajectory = 1
        while trajectory <= self.num_trajectories:
            rundat = simu(sim_args)
            data_pool.batch_pool.append(rundat)
            trajectory += 1
        return data_pool

    #multiprocessing, no parameter variation, no fitting
    def _run_nonmap_mp(self):
        data_pool = self._data_scheme()
        self._run_params_to_location()
        data_pool = self.multiprocess_plan._run_flat(data_pool,self)
        return data_pool

    # NOT TESTED
    #no multiprocessing, parameter variation, no fitting
    def _run_map_nonmp(self):
        data_pool = self._data_scheme()
        run_func = lis.run_system
        move_func = self.cartographer_plan.move_to
        arc_length = len(self.cartographer_plan.trajectory)
        iteration = self.cartographer_plan.iteration
        while iteration < arc_length:
            move_func(iteration)
            self._run_params_to_location()
            print 'set those params!'
            data_pool._prep_pool_(iteration)
            for dex in range(self.cartographer_plan.trajectory[
                                iteration][1].trajectory_count):
                ID = int(str(iteration) + str(dex))
                data_pool.live_pool.append(
                    run_func(self, identifier = ID))
                print 'location dex:', iteration, 'run dex:', dex
            iteration += 1

        data_pool._rid_pool_(iteration - 1)
        self.cartographer_plan.iteration = 0
        return data_pool

    # NOT TESTED
    #multiprocessing with parameter variation, no fitting
    def _run_map_mp(self):
        data_pool = self._data_scheme()
        #self.set_run_params_to_location()
        data_pool = self.multiprocess_plan.distribute_work(
            data_pool, self, target_processes =\
                [self.cartographer_plan.move_to, lis.run_system], 
                target_counts = [len(self.cartographer_plan.trajectory), 
                    [traj[1].trajectory_count for traj in 
                    self.cartographer_plan.trajectory], 1], 
                            args = [('dex'), (), (self,)])
        return data_pool

    # run post processes on new or pooled data
    def _post_processing(self,load = False,dpool = None):
        print 'performing post processing...'
        stime = time.time()
        if self.postprocess_plan.use_plan:
            if load:dpool = self._load_data_pool().data
            try:dpool = self.postprocess_plan(self,dpool)
            except:
                traceback.print_exc(file=sys.stdout)
                print 'failed to run post processes'
                return False,dpool
        print 'duration of post procs:',time.time() - stime
        return True,dpool

    # output data associated with post processes
    def _output_postprocesses(self,pool):
        if not pool.postproc_data is None:
            processes = self.postprocess_plan.processes
            for dex,proc in enumerate(processes):
                if proc.output._must_output():
                    pdata = pool.postproc_data[dex]
                    data = lfu.data_container(data = pdata)
                    proc._regime(self)
                    proc.output(data)

    # output data associated with fit routines
    def _output_fitroutines(self,pool):
        if not pool.routine_data is None:
            routines = self.fitting_plan.routines
            for dex,rout in enumerate(routines):
                if rout.output._must_output():
                    fdata = pool.routine_data[dex]
                    data = lfu.data_container(data = fdata)
                    rout.output(data)

    # start a qt application if one is not started already
    #   this allows api to call for the plot window
    #   without the rest of the gui initialized
    def _check_qt_application(self):
        outputs = [self.output_plan] +\
            [p.output for p in self.postprocess_plan.processes] +\
            [f.output for f in self.fitting_plan.routines]
        plt_flag = True in [o.writers[3].use for o in outputs]
        if plt_flag:
            app = lgb.QtGui.QApplication.instance()
            if app is None:print 'app was none!!'
            elif not lo.qapp_started_flag:
                app.exec_()
                lo.qapp_started_flag = True

    # output all data for the ensemble
    #   simulations,post processes,fit routines
    def _output(self):
        print 'producing output...'
        stime = time.time()
        pool = self._load_data_pool()
        data = lfu.data_container(data = pool.data)
        if self.output_plan._must_output():self.output_plan(data)
        self._output_postprocesses(pool)
        self._output_fitroutines(pool)
        print 'produced output:',time.time() - stime
        self._check_qt_application()

    # return the correct data_pool_pkl filename based on the data scheme
    def _data_pool_path(self):
        if self.data_scheme == 'smart_batch':
            data_pool.data.live_pool = []
            data_pool_pkl = os.path.join(lfu.get_data_pool_path(), 
                '.'.join(['data_pool','smart',self.data_pool_id,'pkl']))
        elif self.data_scheme == 'batch':
            data_pool_pkl = os.path.join(lfu.get_data_pool_path(), 
                '.'.join(['data_pool',self.data_pool_id,'pkl']))
        return data_pool_pkl

    # determine the correct data object for the ensemble run
    def _data_scheme(self):
        smart = lset.get_setting('use_smart_pool')
        smart = (smart is None or smart is True)
        mappspace = self.cartographer_plan.use_plan
        fitting = self.fitting_plan.use_plan
        ptargets = self.run_params['plot_targets']
        if smart and mappspace and not fitting:
            data_pool = ldc.batch_data_pool(ptargets,self.cartographer_plan)
            self.data_scheme = 'smart_batch'
        else:
            data_pool = ldc.batch_scalars(ptargets)
            self.data_scheme = 'batch'
        self.data_pool_pkl = self._data_pool_path()
        return data_pool


    # FIX THIS
    # FIX THIS
    # FIX THIS
    def _describe_data_pool(self,dpool):
        proc_pool = dpool.postproc_data
        try: sim_pool = dpool.data.batch_pool
        except AttributeError: sim_pool = '<couldnt read batch object>'
        if not dpool: self.data_pool_descr = 'Empty'
        else:
            try: sim_pool_count = len(sim_pool)
            except TypeError: sim_pool_count = 0
            try: proc_pool_count = len(proc_pool)
            except TypeError: proc_pool_count = 0
            self.data_pool_descr = ' '.join(['Data', 'Pool', 'Holds', 
                    str(sim_pool_count), 'Simulation', 'Trajectories', 
                        'and', str(proc_pool_count), 'Post', 
                                'Process', 'Pools'])
    # FIX THIS
    # FIX THIS
    # FIX THIS


    def _save_data_pool(self,dpool):
        print 'saving data pool...'
        stime = time.time()
        pplan = self.postprocess_plan
        if pplan.use_plan:pdata = [proc.data for proc in pplan.processes]
        else:pdata = None
        fplan = self.fitting_plan
        if fplan.use_plan:fdata = [rout.data for rout in fplan.routines]
        else:fdata = None
        data_pool = lfu.data_container(data = dpool, 
            postproc_data = pdata,routine_data = fdata)
        self._describe_data_pool(data_pool)
        self.data_pool_pkl = self._data_pool_path()
        lf.save_pkl_object(data_pool,self.data_pool_pkl)
        print 'saved data pool:',time.time() - stime

    def _load_data_pool(self):
        print 'loading data pool...'
        stime = time.time()
        self._data_scheme()
        dpool = lf.load_pkl_object(self.data_pool_pkl)
        self._describe_data_pool(dpool)
        print 'loaded data pool:',time.time() - stime
        return dpool

    def _run(self,*args,**kwargs):
        print 'running ensemble:',self.name
        self.multithread_gui = lset.get_setting('multithread_gui')
        try:
            self._sanitize()
            self._data_scheme()

            if self.multithread_gui:
                self.parent._run_threaded_ensemble(self,self._run_specific)
                # self._output() called from a qt event in lwt
            else:
                self._run_specific()
                self._output()

            time.sleep(1)
        except:
            traceback.print_exc(file=sys.stdout)
            lgd.message_dialog(None,'Failed to run ensemble!','Problem')
            time.sleep(2)

    def _save(self,save_dir = None):
        if save_dir is None:
            dirdlg = lgd.create_dialog('Choose File','File?','directory')
            save_dir = dirdlg()
        if save_dir:
            self._sanitize()
            manager = self.parent
            self.parent = None
            save_file = self.name + '.ensempkl'
            save_path = os.path.join(save_dir,save_file)
            lf.save_pkl_object(self,save_path)
            self.parent = manager
            print 'saved ensemble:',self.name

    # run an mcfg without producing the associated output
    def _run_mcfg(self,mcfg):
        self.mcfg_path = mcfg
        self._parse_mcfg()
        self.output_plan.targeted = self.run_params['plot_targets'][:]
        self.output_plan._target_settables()
        return self._run_specific()

    def _select_mcfg(self,file_ = None):
        if not file_ and not os.path.isfile(self.mcfg_path):
            fidlg = lgd.create_dialog('Choose File','File?','file', 
                    'Modular config files (*.mcfg)',self.mcfg_dir)
            file_ = fidlg()
        if file_:
            self.mcfg_path = file_
            self.mcfg_text_box_ref[0].setText(self.mcfg_path)

    def _parse_mcfg(self,*args,**kwargs):
        self.module._reset_parameters()
        try:self.module._parse_mcfg(self.mcfg_path,self)
        except:
            traceback.print_exc(file = sys.stdout)
            lgd.message_dialog(None,'Failed to parse file!','Problem')
        self.module._rewidget(True)

    def _write_mcfg(self,*args,**kwargs):
        self._select_mcfg(self.mcfg_path)
        try:self.module._write_mcfg(self.mcfg_path,self)
        except:
            traceback.print_exc(file = sys.stdout)
            lgd.message_dialog(None,'Failed to write file!','Problem')

    def _mcfg_widget(self,*args,**kwargs):
        window = args[0]
        config_text = lgm.interface_template_gui(
            layout = 'grid', 
            widg_positions = [(0, 0)],
            widg_spans = [(1, 2)], 
            widgets = ['text'], 
            tooltips = [['Current mcfg file']], 
            verbosities = [0], 
            handles = [(self,'mcfg_text_box_ref')], 
            keys = [['mcfg_path']], 
            instances = [[self]], 
            initials = [[self.mcfg_path]])
        config_buttons = lgm.interface_template_gui(
            widg_positions = [(1, 0),(1, 1),(2, 0)], 
            widgets = ['button_set'], 
            tooltips = [['Parse the contents of the mcfg file', 
                'Generate an mcfg file based on the\ncurrent run parameters']],
            verbosities = [0], 
            bindings = [[
                lgb.create_reset_widgets_wrapper(window,
                    [self._select_mcfg,self._parse_mcfg]), 
                lgb.create_reset_widgets_wrapper(window,self._write_mcfg)]], 
            labels = [['Parse mcfg File','Generate mcfg File']])
        return config_text + config_buttons

    def _sanitize(self,*args,**kwargs):
        self.data_pool = None
        lfu.mobject._sanitize(self,*args,**kwargs)

    def _widget(self,*args,**kwargs):
        window = args[0]
        self._sanitize(*args,**kwargs)
        config_file_box_template = self._mcfg_widget(*args,**kwargs)
        top_half_template =\
            lgm.interface_template_gui(
                widgets = ['text'],
                layout = 'grid',
                grid_spacing = 10,
                panel_scrollable = True, 
                layouts = ['vertical'],
                widg_positions = [(0,0)],
                box_labels = ['Ensemble Name'],
                verbosities = [0],
                instances = [[self]],
                keys = [['label']],
                initials = [[self.name]])
        top_half_template +=\
            lgm.interface_template_gui(
                widgets = ['button_set'],
                widg_positions = [(0, 3)],
                layouts = ['vertical'],
                verbosities = [[0, 0, 0, 5]], 
                labels = [['Run Ensemble',
                    'Save Ensemble','Update Ensemble']], 
                bindings = [[self.parent._run_current_ensemble,self._save]])
        top_half_template +=\
            lgm.interface_template_gui(
                widgets = ['check_set'],
                widg_positions = [(0, 1)], 
                layouts = ['vertical'],
                widg_spans = [(2, 1)],
                box_labels = ['Run Options'],
                verbosities = [0],
                append_instead = [False],
                instances = [[
                    self.fitting_plan,self.cartographer_plan, 
                    self.postprocess_plan,self.multiprocess_plan,self]],
                keys = [['use_plan']*4 + ['skip_simulation']], 
                labels = [['run fitting routines',
                    'map parameter space','use post processing', 
                    'use multiprocessing','skip simulation']])
        top_half_template +=\
            lgm.interface_template_gui(
                widg_positions = [(1, 2)],
                layouts = ['vertical'],
                box_labels = ['Number of Trajectories'],
                widgets = ['spin'],
                verbosities = [0],
                instances = [[self]],
                keys = [['num_trajectories']],
                initials = [[self.num_trajectories]], 
                minimum_values = [[1]],
                maximum_values = [[1000000]])
        top_half_template +=\
            lgm.interface_template_gui(
                widg_positions = [(1, 0)],
                layouts = ['vertical'],
                box_labels = ['Data Pool Description'], 
                widgets = ['text'],
                verbosities = [2],
                multiline = [True],
                read_only = [True],
                instances = [[self]],
                keys = [['data_pool_descr']],
                initials = [[self.data_pool_descr]]) 
        top_half_template +=\
            lgm.interface_template_gui(
                widg_positions = [(0, 2)], 
                layouts = ['vertical'],
                box_labels = ['Configuration File'], 
                widgets = ['panel'],
                verbosities = [0],
                templates = [[config_file_box_template]])
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['tab_book'], 
                verbosities = [0], 
                handles = [(self,'tab_ref')], 
                pages = [[('Main',[top_half_template]), 
                    ('Run Parameters',self.module.widg_templates)]], 
                initials = [[self.current_tab_index]], 
                instances = [[self]], 
                keys = [['current_tab_index']]))
        lfu.mobject._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

###############################################################################
### ensemble_manager is the top level object of modular simulator
###   it creates an interface for handling multiple ensembles
###############################################################################

class ensemble_manager(lfu.mobject):

    def _module_options(self):
        mods = []
        for mod in lfu.list_simulation_modules():
            plug = imp.import_module(mod[0]).main
            if plug.module_name == mod[0]:
                mc.modules.__dict__[mod[0]] = plug
                mods.append(plug.module_name)
        mc.modules.mods = mods
        return mc.modules.mods

    def _settings(self):
        self.settings_manager.display()

    def __init__(self,name = 'ensemble.manager',**kwargs):
        self._default('ensembles',[],**kwargs)
        self._default('worker_threads',[],**kwargs)
        lfu.mobject.__init__(self,
            name = name,children = self.ensembles)

        for m in self._module_options():
            print 'found simulation module:',m

        self.settings_manager = lset.settings_manager(
            parent = self,filename = 'modular_settings.txt')
        self.settings_manager.read_settings()
        if lset.get_setting('auto_clear_data_pools'):ldc.clean_data_pools()

        self.current_tab_index = 0

    def _run_ensembles(self):
        [ensem._run() for ensem in self.ensembles]

    def _run_current_ensemble(self):
        if self.current_tab_index > 0:
            current_ensem = self.ensembles[self.current_tab_index - 1]
            current_ensem._run()

    def _run_threaded_ensemble(self,ensem,run_,args = ()):
        self.worker_threads.append(lwt.worker_thread(
            ensem,run_,len(self.worker_threads),args = args))

    def _abort_ensembles(self):
        [thread.abort() for thread in self.worker_threads]
        self.worker_threads = []

    def _add_ensemble(self, module = 'chemical'):
        modopts = self._module_options()
        new = ensemble(parent = self,
            module_options = modopts,module = module)
        if new.cancel_make: return
        else: self.ensembles.append(new)
        self.current_tab_index = len(self.ensembles)
        self._rewidget(True)
        return new

    def _del_ensemble(self):
        select = self._selected_ensemble()
        if select: self.ensembles.remove(select)
        self._rewidget(True)

    def _selected_ensemble(self):
        edex = self.ensem_selector[0].currentIndex()
        if edex < len(self.ensembles):return self.ensembles[edex]

    def _save_ensemble(self):
        select = self._selected_ensemble()
        if select: select._save()

    def _load_ensemble(self):
        fidlg = lgd.create_dialog('Choose File','File?','file')
        file_ = fidlg()
        if not file_ is None:
            newensem = lf.load_pkl_object(file_)
            newensem.parent = self
            newensem._rewidget(True)
            #newensem._widget(newensem,self)
            self.ensembles.append(newensem)
            print 'loaded ensemble:',newensem.name

    def _select_mcfg(self):
        if self.current_tab_index > 0:
            current_ensem = self.ensembles[self.current_tab_index - 1]
            current_ensem._select_mcfg()

    def _read_mcfg(self):
        if self.current_tab_index > 0:
            current_ensem = self.ensembles[self.current_tab_index - 1]
            current_ensem._parse_mcfg()

    def _write_mcfg(self):
        if self.current_tab_index > 0:
            current_ensem = self.ensembles[self.current_tab_index - 1]
            current_ensem._write_mcfg()

    def _cycle_current_tab(self):
        self.current_tab_index += 1
        if self.current_tab_index >= self.tab_ref[0].count():
            self.current_tab_index = 0
        self.tab_ref[0].setCurrentIndex(self.current_tab_index)

    def _cycle_current_ensem_tab(self):
        current_ensem = self.ensembles[self.current_tab_index - 1]
        current_ensem.current_tab_index += 1
        if current_ensem.current_tab_index > 1:
            current_ensem.current_tab_index = 0
        if not current_ensem.tab_ref: current_ensem._rewidget(True)
        else:
            current_ensem.tab_ref[0].setCurrentIndex(
                    current_ensem.current_tab_index)

    def _expand_tree(self):
        if self.current_tab_index > 0:
            current_ensem = self.ensembles[self.current_tab_index - 1]
            if not current_ensem.module.tree_reference:self.refresh_()
            current_ensem.module.tree_reference[0].children()[0].expand_all()

    def _collapse_tree(self):
        if self.current_tab_index > 0:
            current_ensem = self.ensembles[self.current_tab_index - 1]
            if not current_ensem.module.tree_reference:self.refresh_()
            current_ensem.module.tree_reference[0].children()[0].collapse_all()

    def _tab_book_pages(self,*args,**kwargs):
        window = args[0]
        img_path = lfu.get_resource_path('gear.png')
        main_templates = []
        main_templates.append(
            lgm.interface_template_gui(
                layout = 'grid', 
                widg_positions = [  (0, 1), (1, 0), (2, 0), 
                                    (1, 2), (2, 2), (3, 2), 
                                    (4, 2), (1, 1), (2, 1), 
                                                    (5, 2)  ], 
                widgets = ['image', 'button_set', 'selector'], 
                verbosities = [1, 0, 0], 
                paths = [img_path, None, None], 
                handles = [None, None, (self, 'ensem_selector')], 
                labels = [None, ['Run All Ensembles', 'Abort Runs', 
                    'Add Ensemble', 'Remove Ensemble', 'Save Ensemble', 
                    'Load Ensemble', 'Update GUI', 'Clean Data Pools'], 
                            [ensem.name for ensem in self.ensembles]], 
                bindings = [None, 
                    [self._run_ensembles, self._abort_ensembles, 
                    lgb.create_reset_widgets_wrapper(window, self._add_ensemble),
                    lgb.create_reset_widgets_wrapper(window, self._del_ensemble), 
                    lgb.create_reset_widgets_wrapper(window,self._save_ensemble), 
                    lgb.create_reset_widgets_wrapper(window,self._load_ensemble), 
                    lgb.create_reset_widgets_function(window), 
                            ldc.clean_data_pools], [None]]))
        pages = [('Main',main_templates)]
        for ensem in self.ensembles:
            pages.append((ensem.name,ensem.widg_templates))
        return pages

    def _toolbars(self,*args,**kwargs):
        window = args[0]
        gear_icon = lfu.get_resource_path('gear.png')
        wrench_icon = lfu.get_resource_path('wrench_icon.png')
        save_icon = lfu.get_resource_path('save.png')
        center_icon = lfu.get_resource_path('center.png')
        make_ensemble = lfu.get_resource_path('make_ensemble.png')
        run_ensemble = lfu.get_resource_path('run.png')
        refresh = lfu.get_resource_path('refresh.png')
        nextpage = lfu.get_resource_path('next.png')
        expand = lfu.get_resource_path('expand.png')
        collapse = lfu.get_resource_path('collapse.png')
        openfile = lfu.get_resource_path('open.png')
        find = lfu.get_resource_path('find.png')
        generate = lfu.get_resource_path('generate.png')
        quit = lfu.get_resource_path('quit.png')

        settings_ = lgb.create_action(parent = window,label = 'Settings', 
            bindings = lgb.create_reset_widgets_wrapper(window,self._settings),
            icon = wrench_icon,shortcut = 'Ctrl+Shift+S',statustip = 'Settings')
        save_ = lgb.create_action(parent = window,label = 'Save',
            bindings = lgb.create_reset_widgets_wrapper(window,self._save_ensemble),
            icon = save_icon,shortcut =  'Ctrl+S',statustip = 'Save')
        open_file = lgb.create_action(parent = window,label = 'Open',
            bindings = lgb.create_reset_widgets_wrapper(window,self._load_ensemble),
            icon = openfile,shortcut = 'Ctrl+O',statustip = 'Open New File')
        quit_ = lgb.create_action(parent = window,label = 'Quit', 
            icon = quit,shortcut = 'Ctrl+Q',statustip = 'Quit the Application',
            bindings = window.on_close)
        center_ = lgb.create_action(parent = window,label = 'Center', 
            icon = center_icon,shortcut = 'Ctrl+C',statustip = 'Center Window',
            bindings = [window.on_resize,window.on_center])
        make_ensem_ = lgb.create_action(parent = window,label = 'Make Ensemble',
            icon = make_ensemble,shortcut = 'Ctrl+E',statustip = 'Make New Ensemble',
            bindings = lgb.create_reset_widgets_wrapper(window, self._add_ensemble))
        expand_ = lgb.create_action(parent = window,label = 'Expand Parameter Tree',
            icon = expand,shortcut = 'Ctrl+T',bindings = self._expand_tree, 
            statustip = 'Expand Run Parameter Tree (Ctrl+T)')
        collapse_ = lgb.create_action(parent = window, 
            label = 'Collapse Parameter Tree',icon = collapse,shortcut = 'Ctrl+W',
            bindings = self._collapse_tree,
            statustip = 'Collapse Run Parameter Tree (Ctrl+W)')
        find_mcfg_ = lgb.create_action(parent = window, 
            label = 'Find mcfg', icon = find, shortcut = 'Ctrl+M', 
            bindings = lgb.create_reset_widgets_wrapper(
                window, [self._select_mcfg, self._read_mcfg]), 
            statustip = 'Select *.mcfg file to parse (Ctrl+M)')
        make_mcfg_ = lgb.create_action(parent = window, 
            label = 'Generate mcfg', icon = generate, shortcut = 'Alt+M', 
            bindings = lgb.create_reset_widgets_wrapper(window,self._write_mcfg),
            statustip = 'Generate *.mcfg file from ensemble (Alt+M)')
        self.refresh_ = lgb.create_reset_widgets_function(window)
        update_gui_ = lgb.create_action(parent = window, 
            label = 'Refresh GUI', icon = refresh, shortcut = 'Ctrl+G', 
            bindings = self.refresh_,statustip = 'Refresh the GUI (Ctrl+G)')
        cycle_tabs_ = lgb.create_action(parent = window, 
            label = 'Next Tab', icon = nextpage, shortcut = 'Ctrl+Tab', 
            bindings = self._cycle_current_tab, 
            statustip = 'Display The Next Tab (Ctrl+Tab)')
        cycle_ensem_tabs_ = lgb.create_action(parent = window, 
            label = 'Next Tab', icon = nextpage, shortcut ='E+Tab', 
            bindings = self._cycle_current_ensem_tab, 
            statustip = 'Display The Ensemble\'s Next Tab (E+Tab)')
        run_current_ = lgb.create_action(parent = window, 
            label = 'Run Current Ensemble', icon = run_ensemble, 
            shortcut = 'Alt+R', bindings = self._run_current_ensemble, 
            statustip = 'Run The Current Ensemble (Alt+R)')

        self.menu_templates.append(
            lgm.interface_template_gui(
                menu_labels = ['&File']*12, 
                menu_actions = [settings_, center_, make_ensem_, 
                    run_current_, update_gui_, cycle_tabs_, expand_,
                    collapse_, find_mcfg_, make_mcfg_, open_file, quit_]))
        self.tool_templates.append(
            lgm.interface_template_gui(
                tool_labels = ['&Tools']*9 + ['&EnsemTools']*5,
                tool_actions = [settings_, save_, open_file, 
                        center_, make_ensem_, run_current_, 
                        update_gui_, cycle_tabs_, quit_, 
                        expand_, collapse_, cycle_ensem_tabs_, 
                        find_mcfg_, make_mcfg_]))

    def _widget(self,*args,**kwargs):
        window = args[0]
        self._sanitize(*args,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['tab_book'], 
                pages = [self._tab_book_pages(*args,**kwargs),None], 
                initials = [[self.current_tab_index],None], 
                handles = [(self, 'tab_ref')], 
                instances = [[self]], 
                keys = [['current_tab_index']]))
        self._toolbars(*args,**kwargs)
        lfu.mobject._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################










