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

import pdb,os,sys,traceback,types,time,imp
import numpy as np
import importlib as imp

if __name__ == 'modular_core.libensemble':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':pass

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
        self.output_plan = lo.output_plan(parent = self,name = 'Simulation')
        self.fitting_plan = lfr.fit_routine_plan(parent = self)
        self.cartographer_plan = lgeo.cartographer_plan(
            parent = self,name = 'Parameter Scan')
        self.postprocess_plan = lpp.post_process_plan(parent = self,
            name = 'Post Process Plan',_always_sourceable_ = ['simulation'])
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
        self.run_params['post_processes'] = self.postprocess_plan.post_processes
        self.run_params['p_space_map'] = None
        self.run_params['multiprocessing'] = None
        self.capture_targets = self.run_params['plot_targets']

        self._select_module(**kwargs)
        self.module._reset_parameters(self)

        self.data_scheme = None
        self.data_pool = None
        self.data_pool_descr = ''
        self.data_pool_id = self._new_data_pool_id()
        self.data_pool_pkl = os.path.join(lfu.get_data_pool_path(), 
                '.'.join(['data_pool', self.data_pool_id, 'pkl']))

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

    def _run_mcfg(self,mcfg):
        self.mcfg_path = mcfg
        self._parse_mcfg()

        self.output_plan.targeted = self.run_params['plot_targets'][:]
        self.output_plan.set_target_settables()
        return self.run()

    def _select_mcfg(self,file_ = None):
        if not file_ and not os.path.isfile(self.mcfg_path):
            fidlg = lgd.create_dialog('Choose File','File?','file', 
                    'Modular config files (*.mcfg)',self.mcfg_dir)
            file_ = fidlg()
        if file_:
            self.mcfg_path = file_
            self.mcfg_text_box_ref[0].setText(self.mcfg_path)

    def _parse_mcfg(self,*args,**kwargs):
        self.module._reset_parameters(self)
        try:self.module._parse_mcfg(self.mcfg_path,self)
        except:
            traceback.print_exc(file = sys.stdout)
            lgd.message_dialog(None,'Failed to parse file!','Problem')
        self._rewidget(True)

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
                labels = [[
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

        #self.widg_templates.append(top_half_template)
        #lfu.mobject._widget(self,*args,from_sub = True)
        #tree_half_template = self.module.widg_templates[0]
        '''#
        temp_gen = self.module._generate_gui_templates
        main_templates,sub_templates,sub_labels = temp_gen(window,self)
        run_param_keys = self.module.run_parameter_keys
        tree_half_template = lgm.interface_template_gui(
                widgets = ['tree_book'], 
                verbosities = [1], 
                handles = [(self, 'tree_reference')], 
                initials = [[self.treebook_memory]], 
                instances = [[self]], 
                keys = [['treebook_memory']], 
                pages = [[(page_template,template_list,param_key,sub_labels) 
                    for page_template,template_list,param_key,sub_labels in 
                        zip(main_templates,sub_templates, 
                            run_param_keys,sub_labels)]], 
                headers = [['Ensemble Run Parameters']])
        '''#
        #self.module._widget(window,self,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['tab_book'], 
                verbosities = [0], 
                handles = [(self, 'tab_ref')], 
                pages = [[('Main',[top_half_template]), 
                    ('Run Parameters',self.module.widg_templates)]], 
                    #('Run Parameters',[tree_half_template])]], 
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
        if lset.get_setting('auto_clear_data_pools'):ldc.clean_data_pools()

        self.current_tab_index = 0

    def _run_ensembles(self):
        [ensem.on_run() for ensem in self.ensembles]

    def _run_current_ensemble(self):
        if self.current_tab_index > 0:
            current_ensem = self.ensembles[self.current_tab_index - 1]
            current_ensem.on_run()

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


















