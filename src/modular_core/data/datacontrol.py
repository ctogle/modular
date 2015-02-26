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
def clean_data_pools():

    def pool_name(ensem):
        pa = os.path.join(os.getcwd(),ensem)
        en = lf.load_pkl_object(pa)
        return en.data_pool_pkl

    dp_path = lfu.get_data_pool_path()

    pool_matches = []
    ensem_matches = []
    for root,dirnames,filenames in os.walk(dp_path):
        [pool_matches.append(os.path.join(root,finame)) for 
            finame in fnmatch.filter(filenames,'data_pool.*.pkl')]

    enpkldir = lset.get_setting('ensempkl_directory')
    if not enpkldir is None and not enpkldir == 'none':
        print 'pdir',enpkldir
        pdb.set_trace()
        for root,dirnames,filenames in os.walk(enpkldir):
            [ensem_matches.append(os.path.join(root,finame)) for 
                finame in fnmatch.filter(filenames,'*.ensempkl')]

    saved_pools = [pool_name(en) for en in ensem_matches]
    del_pools = [item for item in pool_matches if 
        os.path.join(os.getcwd(),item) not in saved_pools]

    for pool in del_pools:os.remove(pool)

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






class bin_vector(object):
#Note: inheriting from lfu.modular_object here makes things SLOW!

    def __init__(self, bins, name = 'another bin vector'):
        self.tag = 'bin_vector'
        self.name = name

        rng = np.arange(bins.shape[0], dtype = float)
        self.axis_labels = ['bin_index']
        self.axis_values = [
            scalars(name = 'bin_index', scalars = rng)]
        self.axis_defaults = [da.scalars[0] for da in self.axis_values]

        self.data = bins

    def make_bins(self, *args, **kwargs):
        xleng = self.data.shape[1]
        x = np.arange(xleng + 1)
        s_dex = self.axis_defaults[0]
        bins = self.data[s_dex]
        return (x, bins)

class voxel_vector(object):

    def __init__(self, cubes, name = 'another voxel vector'):
        self.tag = 'voxel_vector'
        self.name = name

        rng = np.arange(cubes.shape[0], dtype = float)
        self.axis_labels = ['cube_index']
        self.axis_values = [
            scalars(name = 'cube_index', scalars = rng)]
        self.axis_defaults = [da.scalars[0] for da in self.axis_values]

        self.data = cubes

    def make_cube(self, *args, **kwargs):
        xleng = self.data.shape[1]
        yleng = self.data.shape[2]
        zleng = self.data.shape[3]
        s_dex = self.axis_defaults[0]
        cube = self.data[s_dex]
        uniq = np.unique(cube)
        if len(uniq) > 4:
            print 'voxel vector is incomplete!!'
            pdb.set_trace()
        colors = ['r', 'g', 'b']
        markers = ['o', 'o', 'o']
        scatter = []
        for un in uniq:
            if un == 0.0: continue
            locs = np.where(cube == un)
            #locs = zip(*np.where(cube == un))
            if locs:
                c = colors.pop()
                m = markers.pop()
                scatter.append((c, m, locs))
        # return [(color, marker, list_of_coords), ...]
        return scatter

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






