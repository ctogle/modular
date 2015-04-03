import modular_core.fundamental as lfu
import modular_core.data.batch_target as dba
import modular_core.settings as lset
import modular_core.parallel.dispycluster as mdcl
import modular_core.parallel.mpicluster as mmcl

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
### a parallel_plan provides parallel support to an ensemble
###############################################################################

cluster_ips = [
    #'10.0.0.5',
    #'10.0.0.8',

    #'127.0.1.1', 

    #'192.168.4.86', 
    #'192.168.4.76', 
    #'192.168.4.87', 
    #'192.168.4.89',
    #'192.168.2.173', 

    #'hemlock.phys.vt.edu',
        ]

class parallel_plan(lfu.plan):

    def _string(self):
        dist = str(self.distributed)
        mstr = '\tworkers : %d\n\tdistributed : %s'%(self.worker_count,dist)

    def __init__(self,*args,**kwargs):
        self._default('name','parallel plan',**kwargs)
        use_plan = lset.get_setting('multiprocessing')
        self._default('use_plan',use_plan,**kwargs)
        self._default('cluster_type','mpi',**kwargs)
        self.worker_count = lset.get_setting('worker_processes')
        self.distributed = lset.get_setting('distributed')
        self.cluster_node_ips = cluster_ips
        lfu.plan.__init__(self,*args,**kwargs)

    def _cluster(self,nodes,work,wrgs,deps):
        print 'CLUSTERIZING...'
        if self.cluster_type == 'dispy':
            loc_0th_pools = mdcl.clusterize(nodes,work,wrgs,deps)
        elif self.cluster_type == 'mpi':
            loc_0th_pools = mmcl.clusterize(nodes,work,wrgs,deps)
            pdb.set_trace()
        print 'CLUSTERIZED...'
        return loc_0th_pools

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
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['check_set'], 
                append_instead = [False], 
                instances = [[self]], 
                keys = [['distributed']], 
                labels = [['run distributed']], 
                box_labels = ['Cluster']))
        lfu.plan._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################










