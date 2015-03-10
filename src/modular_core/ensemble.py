import modular_core as mc
import modular_core.fundamental as lfu
import modular_core.endcaptureplan as lsc
import modular_core.simulationmodule as smd
import modular_core.parameterspace.parameterspaces as lpsp
import modular_core.parameterspace.cartographerplan as cplan
import modular_core.parallel.parallelplan as paral
import modular_core.settings as lset
import modular_core.parallel.threadwork as wt
import modular_core.parallel.cluster as mcl

import modular_core.io.liboutput as lo
import modular_core.io.libfiler as lf
import modular_core.fitting.fitplan as fpl
import modular_core.data.datacontrol as ldc
import modular_core.data.batch_target as dba
import modular_core.postprocessing.processplan as lpp

import modular_core.criteria.iterationlimit as lcit
import modular_core.criteria.timelimit as lcti
import modular_core.criteria.increment as lcin

import modular_core.postprocessing.meanfields as mfs
import modular_core.postprocessing.statistics as sst
import modular_core.postprocessing.pspace_reorganize as rog
import modular_core.postprocessing.conditional as cdl
import modular_core.postprocessing.correlation as crl
import modular_core.postprocessing.measurebin as bms
import modular_core.postprocessing.slices as slc

import pdb,os,sys,traceback,types,time,imp
import multiprocessing as mp
import numpy as np
import importlib as imp
from cStringIO import StringIO

if __name__ == 'modular_core.ensemble':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'ensemble of modular_core'

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

    # return the correct data_pool_pkl filename based on the data scheme
    def _data_pool_path(self):
        data_pool_pkl = os.path.join(lfu.get_data_pool_path(), 
            '.'.join(['data_pool',self.data_pool_id,'pkl']))
        return data_pool_pkl

    def _require_stow(self,runcount,psplocationcount):
        dptpertraj = self.simulation_plan._captures_per_trajectory()
        dptcount = dptpertraj * runcount * psplocationcount
        print 'data point count:',dptcount
        if dptcount > 500000000:
            print 'memory errors may occur; will stow'
            stow_needed = True
        else:
            print 'memory errors not expected; will not stow'
            stow_needed = False
        time.sleep(1)
        return stow_needed



    # FIX THIS
    # FIX THIS
    # FIX THIS
    def _describe_data_pool(self,dpool):
        if not dpool: self.data_pool_descr = 'Empty'
        else:
            proc_pool = dpool.postproc_data
            try: sim_pool = dpool.data.batch_pool
            except AttributeError: sim_pool = '<couldnt read batch object>'
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
        if pplan.use_plan:pdata = pplan._data()
        else:pdata = None

        fplan = self.fitting_plan
        if fplan.use_plan:fdata = [rout.data for rout in fplan.routines]
        else:fdata = None
        
        data_pool = lfu.data_container(data = dpool, 
            postproc_data = pdata,routine_data = fdata)
        self._describe_data_pool(data_pool)
        self.data_pool_pkl = self._data_pool_path()
        lf.save_mobject(data_pool,self.data_pool_pkl)
        print 'saved data pool:',time.time() - stime

    def _load_data_pool(self):
        print 'loading data pool...'
        stime = time.time()
        dpool = lf.load_mobject(self.data_pool_pkl)
        self._describe_data_pool(dpool)
        print 'loaded data pool:',time.time() - stime
        return dpool

    def __init__(self,*args,**kwargs):
        self._default('name','ensemble',**kwargs)
        self._default('mcfg_dir',lfu.get_mcfg_path(),**kwargs)
        self._default('mcfg_path','',**kwargs)
        self._default('skip_simulation',False,**kwargs)
        self._default('multithread_gui',False,**kwargs)
        num_traj = lset.get_setting('trajectory_count')
        self._default('num_trajectories',num_traj,**kwargs)

        self.simulation_plan = lsc.endcapture_plan(parent = self)
        self.output_plan = lo.output_plan(
            parent = self,name = 'Simulation',flat_data = False)
        self.fitting_plan = fpl.fit_routine_plan(parent = self)
        self.cartographer_plan = cplan.cartographer_plan(
            parent = self,name = 'Parameter Scan')
        self.postprocess_plan = lpp.post_process_plan(parent = self,
            name = 'Post Process Plan',always_sourceable = ['simulation'])
        self.multiprocess_plan = paral.parallel_plan(parent = self)
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
        if not hasattr(self,'module'):return
        self.module._reset_parameters()

        self.cartographer_plan._metamap()

        self.data_pool_descr = ''
        self.data_pool_id = self._new_data_pool_id()
        self.data_pool_pkl = self._data_pool_path()

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
            if 'module' in kwargs.keys() and kwargs['module']:
                module = kwargs['module']
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
                    mod_request = 'enter a module:\n\t'
                    for op in opts:mod_request += op + '\n\t'
                    mod_request += '\n'
                    module = raw_input(mod_request)

        self.module_name = module
        if module in mc.modules.__dict__.keys():
            module = mc.modules.__dict__[self.module_name]
        else:module = __import__(module)
        # if module has a simulation_module subclass use that
        # otherwise use the baseclass from smd
        if hasattr(module,'simulation_module'):
            self.module = module.simulation_module(parent = self)
        else:self.module = smd.simulation_module(parent = self)
        self.children.append(self.module)

    # compute any information that changes only when the parameter space
    #  location changes
    def _run_params_to_location(self):
        self.module._set_parameters()

    def _run_params_to_location_prepoolinit(self):
        self.module._set_parameters_prepoolinit()

    # determine if keeping the simulation data is necessary
    def _require_simulation_data(self):
        mustout = self.output_plan._must_output()
        mapping = self.cartographer_plan.use_plan
        if not mustout:
            print 'simulation data is not required for output...'
            print 'skipping simulation data aggregation...'
            return False
        elif mapping and mustout:
            print 'cannot output simulation data while mapping...'
            print 'skipping simulation data aggregation...'
            return False
        elif self.num_trajectories > 10000:
            print 'unwilling to output 10000+ simulation trajectories...'
            print 'skipping simulation data aggregation...'
            return False
        return True

    # run a specific way depending on the settings of the ensemble
    def _run_specific(self,*args,**kwargs):
        fullstime = time.time()
        stimepretty = time.strftime(
                '%Y-%m-%d %H:%M:%S',time.localtime(fullstime))
        pspace = self.cartographer_plan.parameter_space
        mappspace = self.cartographer_plan.use_plan and pspace
        distributed = self.multiprocess_plan.distributed

        if not self.skip_simulation:
            print 'simulation start time:',stimepretty
            if self.fitting_plan.use_plan:dpool = self._run_fitting()
            else:
                if distributed:dpool = self._run_distributed()
                else:
                    if mappspace:dpool = self._run_map()
                    else:dpool = self._run_nonmap()
            print 'duration of simulations:',time.time() - fullstime
            self.cartographer_plan._save_metamap()
        else:
            print 'skipping simulation implies metamap usage...'
            dpool = self._run_metamap_zeroth()

        print 'performing non-0th post processing...'
        procstime = time.time()
        if self.postprocess_plan.use_plan:
            self.postprocess_plan._walk_processes()
        print 'duration of non-0th post processes:',time.time() - procstime

        self._save_data_pool(dpool)
        self._output_trajectory_key()

        print 'finished simulations and analysis:exiting'
        print 'total run duration:',time.time() - fullstime,'seconds'
        return True

    # NOT TESTED
    # use the fitting_plan to perform simulations
    def _run_fitting(self):
        dpool = dba.batch_node()
        if not self.cartographer_plan.parameter_space:
            print '\nfitting requires a parameter space!\n'
        dpool = self.fitting_plan(self,dpool)
        return dpool

    def _run_metamap_zeroth(self):
        if not self.postprocess_plan.use_plan:return
        arc = self.cartographer_plan.trajectory
        zeroth = self.postprocess_plan._init_processes(arc)
        mmap = self.cartographer_plan.metamap
        for lstr in mmap.location_strings:
            loc_pool = mmap._recover_location(lstr)
            #mloc = mmap.entries[lstr]
            #if not len(mloc.simulation_pool.children) == 1:
            #    print 'metamap incomplete... defaulting to something...'
            #loc_pool = mloc.simulation_pool.children[0]
            self.postprocess_plan._enact_processes(zeroth,loc_pool)
        return dba.batch_node()

    #parameter variation, no fitting
    def _run_map(self):
        self._run_params_to_location_prepoolinit()
        if self.multiprocess_plan.use_plan:
            pcnt = int(self.multiprocess_plan.worker_count)
            pinit = self._run_params_to_location
            mppool = mp.Pool(processes = pcnt,initializer = pinit)
        else:mppool = None

        requiresimdata = self._require_simulation_data()

        cplan = self.cartographer_plan
        meta = cplan.maintain_pspmap
        arc = cplan.trajectory
        arc_length = len(arc)
        max_run = arc[0].trajectory_count
        stow_needed = self._require_stow(max_run,arc_length)

        usepplan = self.postprocess_plan.use_plan
        #if usepplan:self.postprocess_plan._init_processes(arc,meta)
        if usepplan:self.postprocess_plan._init_processes(arc)

        data_pool = dba.batch_node(metapool = meta)
        arc_dex = 0
        while arc_dex < arc_length:
            loc_pool = self._run_pspace_location(arc_dex,mppool,meta)
            arc_dex += 1
            print 'pspace locations completed:%d/%d'%(arc_dex,arc_length)
            if requiresimdata:
                data_pool._add_child(loc_pool)
                if stow_needed:data_pool._stow_child(-1)

        if self.multiprocess_plan.use_plan:
            mppool.close()
            mppool.join()
        return data_pool

    # use dispy to distribute work across a network
    def _run_distributed(self):
        pspace = self.cartographer_plan.parameter_space
        mappspace = self.cartographer_plan.use_plan and pspace
        self._run_params_to_location_prepoolinit()
        if mappspace:
            arc = self.cartographer_plan.trajectory
            arc_length = len(arc)

            usepplan = self.postprocess_plan.use_plan
            if usepplan:self.postprocess_plan._init_processes(arc)

            with open(self.mcfg_path,'r') as mh:mcfgstring = mh.read()
            modulename = self.module_name

            nodes = self.multiprocess_plan.cluster_node_ips
            work = _unbound_map_pspace_location
            wrgs = [(mcfgstring,modulename,x) for x in range(arc_length)]

            deps = [os.path.join(os.getcwd(),'gillespiemext_0.so')]

            print 'CLUSTERIZING...'
            loc_0th_pools = mcl.clusterize(nodes,work,wrgs,deps)
            print 'CLUSTERIZED...'
            zeroth = self.postprocess_plan.zeroth
            zcount = len(zeroth)
            for adx in range(arc_length):
                l0p = loc_0th_pools[adx]
                for zdx in range(zcount):
                    zp = zeroth[zdx]
                    zpdata = l0p.children[zdx]
                    zpdata._unfriendly()
                    zp.data._add_child(zpdata)

            dpool = dba.batch_node()
        else:dpool = self._run_nonmap()
        return dpool

    # use current parameters like a single position trajectory
    def _run_nonmap(self):
        requiresimdata = self._require_simulation_data()
        cplan = self.cartographer_plan
        pspace = cplan._parameter_space([])
        lpsp.trajectory_set_counts(cplan.trajectory,self.num_trajectories)
        data_pool = self._run_map()
        if requiresimdata:return data_pool._split_child()
        else:return dba.batch_node()

    # if mapping, ldex is the pspace location index, else ldex is None
    # if not ldex is None, move to the necessary location in pspace
    # run all simulations associated with this pspace location
    def _run_pspace_location(self,ldex = None,mppool = None,meta = False):
        traj_cnt,targ_cnt,capt_cnt,ptargets = self._run_init(ldex)
        dshape = (traj_cnt,targ_cnt,capt_cnt)

        pplan = self.postprocess_plan
        cplan = self.cartographer_plan
        if cplan.maintain_pspmap:
            print 'should only fill metamap data as required...'
            traj_cnt,dshape = cplan._metamap_remaining(ldex,traj_cnt,dshape)
            lstr = cplan._print_friendly_pspace_location(ldex)
            mmap = cplan.metamap

        if not traj_cnt == 0:
            loc_pool = dba.batch_node(metapool = meta,
                    dshape = dshape,targets = ptargets)

            if ldex:cplan._move_to(ldex)
            if self.multiprocess_plan.use_plan:mppool._initializer()
            else:self._run_params_to_location()
            if mppool:self._run_mpbatch(mppool,traj_cnt,loc_pool)
            else:self._run_batch(traj_cnt,loc_pool)
        
            if cplan.maintain_pspmap:
                print 'should record metamap data...'
                cplan._record_persistent(ldex,loc_pool)
                loc_pool = mmap._recover_location(lstr)
        else:
            loc_pool = mmap._recover_location(lstr)
        if pplan.use_plan:
            zeroth = pplan.zeroth
            pplan._enact_processes(zeroth,loc_pool)
        return loc_pool

    # helper function for common run info
    def _run_init(self,t = None):
        if t is None:ntraj = self.num_trajectories
        else:ntraj = self.cartographer_plan.trajectory[t].trajectory_count
        ptargs = self.run_params['plot_targets']
        ntarg = len(ptargs)
        ncapt = self.simulation_plan._capture_count()
        return (ntraj,ntarg,ncapt,ptargs)

    # run many simulations, adding the data to node pool
    # print the current trajectory/maxtrajectory at frequency pfreq
    def _run_batch(self,many,pool,pfreq = 100):
        simu = self.module.simulation
        sim_args = self.module.sim_args
        print 'batch run completed:%d/%d'%(0,many)
        for m in range(many):
            rundat = simu(sim_args)
            pool._trajectory(rundat)
            if m % pfreq == 0:
                print 'batch run completed:%d/%d'%(m+pfreq,many)

    # accomplish the same goal as _run_batch but using mp.Pool mppool
    def _run_mpbatch(self,mppool,many,pool,pfreq = 100):
        pcnt = int(self.multiprocess_plan.worker_count)
        simu = self.module.simulation
        m = 0
        print 'mpbatch run completed:%d/%d'%(0,many)
        while m < many:
            mleft = many - m
            if mleft >= pcnt:rtr = pcnt
            else:rtr = mleft % pcnt
            m += rtr

            mppool._initializer()
            args = [self.module.sim_args]*rtr
            result = mppool.map_async(simu,args,callback = pool._trajectorize)
            result.wait()
            if m % pfreq == 0:
                print 'mpbatch run completed:%d/%d'%(m,many)

    def _print_pspace_location(self,ldex):
        return self.cartographer_plan._print_pspace_location(ldex)

    # if either fitting or parameter sweeping is used
    # output a txt file describing the pspace trajectory
    def _output_trajectory_key(self):
        cplan = self.cartographer_plan
        fplan = self.fitting_plan
        if cplan.use_plan or fplan.use_plan:
            tkey = StringIO()
            traj = cplan.trajectory
            paxnames = [pax.name for pax in cplan.parameter_space.axes]
            paxnamelengs = [len(name) for name in paxnames]
            tkey.write('\n\t||\tTrajectory Key\t||\t\n')
            tkey.write('\nTrajectory number'.ljust(25))
            tkey.write('Trajectory Count'.ljust(25))
            nasnls = zip(paxnames,paxnamelengs)
            [tkey.write('\t'+na.ljust(nl+5)) for na,nl in nasnls]
            tkey.write('\n'+'-'*120+'\n')
            for ldex,loc in enumerate(traj):
                locline = [str(l).rjust(ln-5)+' '*10 for 
                    l,ln in zip(loc.location,paxnamelengs)]
                tkey.write('\n  Index:'+str(ldex).ljust(8)+' '*9)
                tkey.write(str(loc.trajectory_count).rjust(10)+' '*15)
                tkey.write('\t'.join(locline))
            keypath = os.path.join(os.getcwd(),'trajectory_key.txt')
            with open(keypath,'w') as ha:ha.write(tkey.getvalue())

    # output data associated with post processes
    def _output_postprocesses(self,pool):
        if not pool.postproc_data is None:
            processes = self.postprocess_plan.processes
            for dex,proc in enumerate(processes):
                if proc.output._must_output():
                    pdata = pool.postproc_data.children[dex]
                    data = lfu.data_container(data = pdata)
                    proc._regime(self)
                    proc.output(data)

    # output data associated with fit routines
    def _output_fitroutines(self,pool):
        if not pool.routine_data is None:
            routines = self.fitting_plan.routines
            for dex,rout in enumerate(routines):
                if rout.output._must_output():
                    fdata = pool.routine_data.children[dex]
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
        requiresimdata = self._require_simulation_data()
        if requiresimdata and pool.data._stowed():pool.data._recover()
        data = lfu.data_container(data = pool.data)
        if self.output_plan._must_output():self.output_plan(data)
        self._output_postprocesses(pool)
        self._output_fitroutines(pool)
        print 'produced output:',time.time() - stime
        self._check_qt_application()
        return True


    def _run(self,*args,**kwargs):
        print 'running ensemble:',self.name
        self.multithread_gui = lset.get_setting('multithread_gui')
        try:
            self._sanitize()

            if self.multithread_gui:
                self.parent._run_threaded_ensemble(self,self._run_specific)
                # self._output() called from a qt event in wt
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
            lf.save_mobject(self,save_path)
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
        try:self.module._parse_mcfg(self,self.mcfg_path,**kwargs)
        except:
            traceback.print_exc(file = sys.stdout)
            lfu.log(trace = True)
            if lfu.using_gui:
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

    # must project rewidget state onto module.rewidget...
    def _rewidget(self,*args,**kwargs):
        lfu.mobject._rewidget(self,*args,**kwargs)
        self.module._rewidget(self.rewidget)

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
                verbosities = [[0, 0, 0]], 
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
                maximum_values = [[1000000000]])
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
        self.worker_threads.append(wt.worker_thread(
            ensem,run_,len(self.worker_threads),args = args))

    def _abort_ensembles(self):
        [thread.abort() for thread in self.worker_threads]
        self.worker_threads = []

    def _add_ensemble(self,module = None):
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
            newensem = lf.load_mobject(file_)
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
            if ensem.rewidget:ensem._widget(*args,**kwargs)
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

def _unbound_map_pspace_location(mcfgstring,modulename,arc_dex):
    import modular_core.fundamental as lfu
    lfu.using_gui = False
    import modular_core.ensemble as mce
    import modular_core.data.batch_target as dba

    mnger = mce.ensemble_manager()
    ensem = mnger._add_ensemble(module = modulename)

    ensem._parse_mcfg(mcfgstring = mcfgstring)
    ensem.multiprocess_plan.use_plan = False

    ensem.module._increment_extensionname()

    pplan = ensem.postprocess_plan
    if pplan.use_plan:pplan._init_processes(None)

    loc_pool = ensem._run_pspace_location(arc_dex)
    loc_pool._stow()

    if pplan.use_plan:zeroth = ensem.postprocess_plan.zeroth
    host = socket.gethostname()
    pdata = dba.batch_node()
    for z in zeroth:
        pdata._add_child(z.data.children[0])
        pdata._stow_friendly_child(-1)
        pdata._stow_child(-1)
    pdata.dispyhost = host
    pdata.dispyindex = arc_dex
    psplocstr = ensem._print_pspace_location(arc_dex)
    lfu.log('\n\ncluster psp-location: %d - %s'%(arc_dex,psplocstr))
    return pdata

###############################################################################









