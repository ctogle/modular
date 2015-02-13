import modular_core.libfundamental as lfu
import modular_core.libsettings as lset
import modular_core.gpu.lib_gpu as lgpu
import modular_core.libiteratesystem as lis

import multiprocessing as mp
import numpy as np
import pdb,sys,time,types

if __name__ == 'modular_core.libmultiprocess':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
if __name__ == '__main__':print 'libmultiprocess of modular_core'

class multiprocess_plan(lfu.plan):

    def _string(self):
        return '\tworkers : ' + str(self.worker_count)

    def __init__(self,*args,**kwargs):
        self._default('name','multiprocessing plan',**kwargs)
        use_plan = lset.get_setting('multiprocessing')
        self._default('use_plan',use_plan,**kwargs)
        self.worker_count = lset.get_setting('worker_processes')
        self.worker_report = []

        if lgpu.gpu_support: self.gpu_worker = lgpu.CL()

        lfu.plan.__init__(self,*args,**kwargs)

    def _runs_this_round(self,pcnt,rmax,r):
        rleft = rmax - r
        if rleft >= pcnt:return pcnt
        else:return rleft % pcnt

    def _run_flat(self,data_pool,ensem):
        pcnt = int(self.worker_count)
        init = ensem._run_params_to_location
        pool = mp.Pool(processes = pcnt,initializer = init)

        results = []
        simu = ensem.module.simulation
        max_run = ensem.num_trajectories
        run = 0
        while run < max_run:
            rtr = self._runs_this_round(pcnt,max_run,run)
            run += rtr
            pool._initializer()
            args = [ensem.module.sim_args]*rtr
            result = pool.map_async(simu,args,callback = results.extend)
            result.wait()
            print 'simulation runs completed:',run
        pool.close()
        pool.join()

        data_pool.batch_pool = np.array(results,dtype = np.float)
        return data_pool








    #args should start with 2 lists of equal length
    def gpu_1to1_operation(self, *args, **kwargs):
        return self.gpu_worker.execute(*args, **kwargs)

    def distribute_work(self, data_pool, ensem_reference, 
            target_processes = [], target_counts = [], args = []):
        try: processor_count = int(self.worker_count)
        except: 
            print 'defaulting to 4 workers...'
            processor_count = 8
        
        
        #ensem_reference.set_run_params_to_location()
        #pool = mp.Pool(processes = processor_count)
        pool = mp.Pool(processes = processor_count, 
            initializer = ensem_reference._run_params_to_location)

        move_to = target_processes[0]
        run_system = target_processes[1]
        worker_report = []
        dex0 = 0
        while dex0 < target_counts[0]:
            move_to(dex0)

            #ensem_reference.set_run_params_to_location()
            #pool = mp.Pool(processes = processor_count)

            #pdb.set_trace()
            pool._initializer()

            dex1 = 0
            sub_data_pool = []
            while dex1 < target_counts[1][dex0]:
                runs_left = target_counts[1][dex0] - dex1
                if runs_left >= processor_count: 
                    runs_this_round = processor_count
                else: runs_this_round = runs_left % processor_count
                check_time = time.time()
                result = pool.map_async(run_system, 
                            args[2]*runs_this_round, 
                    callback = sub_data_pool.extend)
                result.wait()
                dex1 += runs_this_round
                report = ' '.join(['location dex:', str(dex0), 
                    'runs this round:', str(runs_this_round), 'in:', 
                        str(time.time() - check_time), 'seconds'])
                worker_report.append(report)
                print 'multicore reported...', ' location: ', dex0

            data_pool.live_pool = np.array(
                sub_data_pool, dtype = np.float)
            data_pool._rid_pool_(dex0)
            dex0 += 1

            #pool.close()
            #pool.join()

        pool.close()
        pool.join()

        sub_data_pool = None
        self.worker_report = worker_report
        return data_pool





        
    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin'], 
                initials = [[self.worker_count]], 
                minimum_values = [[2]], 
                maximum_values = [[32]], 
                single_steps = [[2]], 
                instances = [[self]], 
                rewidget = [[True]], 
                keys = [['worker_count']], 
                box_labels = ['Number of worker processes']))
        lfu.plan._widget(self,*args,from_sub = True)




#def run_with_time_out(run_func, args, pool, time_out = 10):
def run_with_time_out(*args):
    #this function should not work if callback does not extend properly
    #print 'rwto', args
    args = args[0]
    run_func = args[0]
    sub_args = args[1]
    pool = args[2]
    time_out = args[3]
    begin = len(pool)
    worker_pool = mp.Pool(processes = 1)
    result = worker_pool.map_async(run_func, 
            sub_args, callback = pool.extend)
    worker_pool.close()
    start_time = time.time()
    time.sleep(0.1)
    timed_out = time.time() - start_time > time_out
    finished = len(pool) > begin
    while not timed_out and not finished:
        time.sleep(0.1)
        timed_out = time.time() - start_time > time_out
        finished = len(pool) > begin

    if timed_out:
        worker_pool.terminate()
        worker_pool.join()
        #print 'timed out...'
        return True

    else:
        worker_pool.join()
        return False









