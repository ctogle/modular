import modular_core.fundamental as lfu
import modular_core.data.batch_target as dba
import modular_core.settings as lset
import modular_core.parallel.dispycluster as mdcl
import modular_core.parallel.mpicluster as mmcl

import pdb,sys,time,types
import numpy as np
import multiprocessing as mp

from mpi4py import MPI

if __name__ == 'modular_core.parallel.parallelplan':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
if __name__ == '__main__':print 'parallelplan of modular_core'

###############################################################################
### a parallel_plan provides parallel support to an ensemble
###############################################################################

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
        self._default('cluster_node_ips',[],**kwargs)
        lfu.plan.__init__(self,*args,**kwargs)

    #def _cluster(self,arc_length,work):
    def _cluster(self):
        ensem = self.parent
        cplan = ensem.cartographer_plan
        comm = MPI.COMM_WORLD
        if comm.rank == 0:print 'CLUSTERIZING...'
        if self.cluster_type == 'dispy':
            #nodes = self.cluster_node_ips
            nodes = {
                'sierpenski':'192.168.4.89', 
                #'latitude':'192.168.4.76', 
                #'wizbox':'192.168.2.173', 
                    }
            dpool = mdcl.mcluster_run(ensem,nodes)
            return dpool

            '''#
            with open(ensem.mcfg_path,'r') as mh:mcfgstring = mh.read()
            modulename = ensem.module_name
            wrgs = [(mcfgstring,modulename,x) for x in range(arc_length)]
            deps = ensem.module.dependencies
            loc_0th_pools = mdcl.clusterize(nodes,work,wrgs,deps)
            if comm.rank == 0:
                zeroth = ensem.postprocess_plan.zeroth
                zcount = len(zeroth)
                for adx in range(arc_length):
                    l0p = loc_0th_pools[adx]

                    if cplan.maintain_pspmap:
                        mloc = l0p.metalocation
                        mstr = mloc.location_string
                        cplan.metamap.entries[mstr] = mloc
                        cplan.metamap.location_strings.append(mstr)

                    for zdx in range(zcount):
                        zp = zeroth[zdx]
                        zpdata = l0p.children[zdx]
                        zpdata._unfriendly()
                        zp.data._add_child(zpdata)
                        zp.data._stow_child(-1,v = False)

                if cplan.maintain_pspmap:cplan._save_metamap()
            if comm.rank == 0:
                dpool = dba.batch_node()
                return dpool
            else:return None
            '''#




        elif self.cluster_type == 'mpi':


            print 'BROKEN'
            pdb.set_trace()


            comm = MPI.COMM_WORLD
            loc_0th_pools = mmcl.clusterize(ensem,arc_length)
            if comm.rank == 0:
                print 'CLUSTERIZED...'
                #pdb.set_trace()
        else:
            if comm.rank == 0:pdb.set_trace()
        #return loc_0th_pools

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










