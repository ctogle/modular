import modular_core.fundamental as lfu
import modular_core.settings as lset

import modular_core.io.libfiler as lf

import pdb,traceback,sys,os,time,random,types,math,fnmatch
import numpy as np
from copy import deepcopy as copy
from scipy.integrate import simps as integrate
                                         
if __name__ == 'modular_core.datacontrol':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'datacontrol of modular_core'

###############################################################################
### utility functions
###############################################################################

# remove data_pools which won't be used again from the os specific
# directory modular uses to store data
# this is typically called on startup of modular
def clean_data_pools(ext = 'hdf5'):
    dp_path = lfu.get_data_pool_path()
    pool_matches = []
    for root,dirnames,filenames in os.walk(dp_path):
        [pool_matches.append(os.path.join(root,finame)) for 
            finame in fnmatch.filter(filenames,'data_pool.*.'+ext)]
    for pool in pool_matches:os.remove(pool)

###############################################################################
###############################################################################

###############################################################################
### data_mobject is smart container for abstract data from simulations/processes
###############################################################################

# sometimes i need to hold one list of scalars - simplest data
#   this constitutes one "target"
# sometimes i need to hold a batch of lists of scalars, 1-1 - simplest trajectory
#   this is one to one with a list of targets
# sometimes i need to hold batches of batches of lists of scalars - 
#   nonflat batch of trajectories
#   

# theres data objects for a single target
# data objects for a batch of targets
# and data objects for batches of the above
# in every case i want a hierarchy of single target data objects

###############################################################################

class data_mobject(lfu.data_container):

    def __init__(self,*args,**kwargs):
        self._default('name','data container',**kwargs)
        self._default('tag','data.mobject',**kwargs)
        lfu.data_container.__init__(self,*args,**kwargs)

    def _copy(self):
        new = self.__class__(**self.__dict__)
        pdb.set_trace()
        return new

###############################################################################
###############################################################################

# new and unused...
class mdatabase(lfu.mobject):

    def __init__(self,*args,**kwargs):

        date = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        self.creation_date = date

        lfu.mobject.__init__(self,*args,**kwargs)











###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################




### NOT PORTED TO 3.0
class surface_vector(object):

    def __init__(self, surfs, 
    #def __init__(self, surfs, surf_labels, axis_labels, axis_values, 
            label = 'another surface vector'):
        self.tag = 'surface_vector'
        self.name = name

        rng = np.arange(surfs.shape[0], dtype = float)
        self.axis_labels = ['surface_index']
        self.axis_values = [
            scalars(name = 'surface_index', scalars = rng)]
        self.axis_defaults = [da.scalars[0] for da in self.axis_values]

        #self.surf_targets = surf_labels
        self.data = surfs

    def make_surface(self, *args, **kwargs):
        xleng = self.data.shape[1]
        yleng = self.data.shape[2]
        x = np.arange(xleng)
        y = np.arange(yleng)
        s_dex = self.axis_defaults[0]
        surf = self.data[s_dex]
        return (x, y, surf)
        #if surf_target == self.label: return True
        #else: return False






