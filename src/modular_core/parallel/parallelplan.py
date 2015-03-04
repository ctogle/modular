import modular_core.fundamental as lfu
import modular_core.data.batch_target as dba
import modular_core.settings as lset

import pdb,sys,time,types
import numpy as np
import multiprocessing as mp

if __name__ == 'modular_core.parallel.parallelplan':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
if __name__ == '__main__':print 'parallelplan of modular_core'

###############################################################################
### a parallel_plan provides multiprocessing support to an ensemble
###############################################################################

class parallel_plan(lfu.plan):

    def _string(self):
        return '\tworkers : ' + str(self.worker_count)

    def __init__(self,*args,**kwargs):
        self._default('name','parallel plan',**kwargs)
        use_plan = lset.get_setting('multiprocessing')
        self._default('use_plan',use_plan,**kwargs)
        self.worker_count = lset.get_setting('worker_processes')
        lfu.plan.__init__(self,*args,**kwargs)

    # determine the number of runs to execute based on remaining
    # necessary runs and the number of worker processes being used
    def _runs_this_round(self,pcnt,rmax,r):
        rleft = rmax - r
        if rleft >= pcnt:return pcnt
        else:return rleft % pcnt

    # handles the case of one parameter 
    # space location with any number of runs
    def _run_flat(self,data_pool,ensem):
        pcnt = int(self.worker_count)
        ensem._run_params_to_location_prepoolinit()
        ensem._run_params_to_location()
        pool = mp.Pool(processes = pcnt)

        pplan = ensem.postprocess_plan
        usepplan = pplan.use_plan
        if usepplan:zeroth = pplan._init_processes(None)

        simu = ensem.module.simulation
        max_run = ensem.num_trajectories
        run = 0
        def _cb_(*args):
            for a in args[0]:
                data_pool._trajectory(a)
        while run < max_run:
            rtr = self._runs_this_round(pcnt,max_run,run)
            run += rtr
            args = [ensem.module.sim_args]*rtr
            #result = pool.map_async(simu,args,callback = _cb_)
            result = pool.map_async(simu,args,callback = data_pool._trajectory)
            result.wait()
            print 'simulated trajectory:',run,'/',max_run

        pool.close()
        pool.join()
        if usepplan:pplan._enact_processes(zeroth,data_pool)
        return data_pool

    # handles the case of any number of parameter space locations with
    # any number of trajectories associated with each
    def _run_nonflat(self,data_pool,ensem):
        pcnt = int(self.worker_count)
        ensem._run_params_to_location_prepoolinit()
        init = ensem._run_params_to_location
        pool = mp.Pool(processes = pcnt,initializer = init)

        requiresimdata = ensem._require_simulation_data()

        arc = ensem.cartographer_plan.trajectory
        arc_length = len(arc)
        #move_to = ensem.cartographer_plan._move_to
        #simu = ensem.module.simulation
        #ptargets = ensem.run_params['plot_targets']

        max_run = arc[0].trajectory_count
        stow_needed = ensem._require_stow(max_run,arc_length)

        tcnt = len(self.parent.simulation_plan.plot_targets)
        ccnt = self.parent.simulation_plan._capture_count()

        pplan = ensem.postprocess_plan
        usepplan = pplan.use_plan
        if usepplan:pplan._init_processes(arc)

        arc_dex = 0
        while loc < arc_length:
            #move_to(arc_dex)
            pool._initializer()
            #run = 0
            
            max_run = arc[loc].trajectory_count
            dshape = (max_run,tcnt,ccnt)
            loc_pool = ensem._run_pspace_location(arc_dex)
            #loc_pool = dba.batch_node(dshape = dshape,targets = ptargets)  
            #def _cb_(*args):
            #    for a in args[0]:
            #        loc_pool._trajectory(a)
            while run < max_run:
                rtr = self._runs_this_round(pcnt,max_run,run)
                run += rtr
                pool._initializer()
                args = [ensem.module.sim_args]*rtr
                result = pool.map_async(simu,args,callback = loc_pool._trajectory)
                result.wait()
                print 'location:',arc_dex,'run:',run,'/',max_run

            arc_dex += 1
            if usepplan:
                zeroth = pplan.zeroth
                pplan._enact_processes(zeroth,loc_pool)
            if requiresimdata:
                data_pool._add_child(loc_pool)
                if stow_needed:data_pool._stow_child(-1)

        pool.close()
        pool.join()
        return data_pool

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin'], 
                initials = [[self.worker_count]], 
                minimum_values = [[1]], 
                maximum_values = [[1000]],
                instances = [[self]], 
                rewidget = [[True]], 
                keys = [['worker_count']], 
                box_labels = ['Number of worker processes']))
        lfu.plan._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################










