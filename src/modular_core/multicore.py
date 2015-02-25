import modular_core.libfundamental as lfu
import modular_core.data.batch_target as dba
import modular_core.libsettings as lset

import pdb,sys,time,types
import numpy as np
import multiprocessing as mp

if __name__ == 'modular_core.multicore':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
if __name__ == '__main__':print 'multicore of modular_core'

###############################################################################
### a multiprocess_plan provides multiprocessing support to an ensemble
###############################################################################

class multiprocess_plan(lfu.plan):

    def _string(self):
        return '\tworkers : ' + str(self.worker_count)

    def __init__(self,*args,**kwargs):
        self._default('name','multiprocessing plan',**kwargs)
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
        #init = ensem._run_params_to_location
        ensem._run_params_to_location_prepoolinit()
        ensem._run_params_to_location()
        pool = mp.Pool(processes = pcnt)#,initializer = init)

        results = []
        simu = ensem.module.simulation
        max_run = ensem.num_trajectories
        run = 0
        while run < max_run:
            rtr = self._runs_this_round(pcnt,max_run,run)
            run += rtr
            #ensem._run_params_to_location_prepoolinit()
            #pool._initializer()
            args = [ensem.module.sim_args]*rtr
            result = pool.map_async(simu,args,callback = results.extend)
            result.wait()
            print 'simulated trajectory:',run,'/',max_run

        pool.close()
        pool.join()
        ptargets = ensem.run_params['plot_targets']
        for rundat in results:data_pool._trajectory(rundat,ptargets)
        return data_pool

    # handles the case of any number of parameter space locations with
    # any number of trajectories associated with each
    def _run_nonflat(self,data_pool,ensem):
        pcnt = int(self.worker_count)
        ensem._run_params_to_location_prepoolinit()
        init = ensem._run_params_to_location
        pool = mp.Pool(processes = pcnt,initializer = init)

        trajectory = ensem.cartographer_plan.trajectory
        move_to = ensem.cartographer_plan._move_to
        simu = ensem.module.simulation
        ptargets = ensem.run_params['plot_targets']

        max_loc = len(trajectory)
        loc = 0
        while loc < max_loc:
            move_to(loc)
            ensem._run_params_to_location_prepoolinit()
            pool._initializer()
            max_run = trajectory[loc].trajectory_count
            run = 0
            subresults = []
            while run < max_run:
                rtr = self._runs_this_round(pcnt,max_run,run)
                run += rtr
                pool._initializer()
                args = [ensem.module.sim_args]*rtr
                result = pool.map_async(simu,args,callback = subresults.extend)
                result.wait()
                print 'location:',loc,'run:',run,'/',max_run
            loc_pool = dba.batch_node()  
            for subr in subresults:loc_pool._trajectory(subr,ptargets)
            data_pool._add_child(loc_pool)
            data_pool._stow_child(-1)
            loc += 1

        pool.close()
        pool.join()
        return data_pool

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin'], 
                initials = [[self.worker_count]], 
                minimum_values = [[2]], 
                maximum_values = [[32]], single_steps = [[2]], 
                instances = [[self]], 
                rewidget = [[True]], 
                keys = [['worker_count']], 
                box_labels = ['Number of worker processes']))
        lfu.plan._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################










