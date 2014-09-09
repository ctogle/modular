import modular_core.libfundamental as lfu
import modular_core.libmath as lm
import modular_core.libfiler as lf
import modular_core.libsettings as lset

import itertools as it
import types
import fnmatch
import random
import os
import sys
import time
import math
import numpy as np
from copy import deepcopy as copy
from scipy.integrate import simps as integrate

import traceback

import pdb
                                         
if __name__ == 'modular_core.libdatacontrol':
    if lfu.gui_pack is None: lfu.find_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'

class scalars(object):

    def __init__(self, label = 'some scalar', scalars = None, **kwargs):
        self.label = label
        self.tag = 'scalar'
        if not scalars is None:
            if type(scalars) is types.ListType:
                scalars = np.array(scalars)

            self.scalars = scalars

        else: self.scalars = []
        for key in kwargs.keys(): self.__dict__[key] = kwargs[key]

    def as_string_list(self):
        return [str(val) for val in self.scalars]

    def as_string(self):
        return ', '.join([str(val) for val in self.scalars])

class batch_scalars(object):

    def __init__(self, targets, label = 'batch of scalars'):
        self.batch_pool = []
        self.pool_names = targets
        self.override_targets = False
        self.current = 0

    def __iter__(self):
        return [self._get_trajectory_(dex) for 
            dex in range(len(self.batch_pool))].__iter__()

    def __len__(self):
        return len(self.batch_pool)

    def next(self):
        if self.current > self.high:
            raise StopIteration

        else:
            self.current += 1
            return self.current - 1

    def __getitem__(self, key):
        if type(key) is types.IntType:
            try: return self._get_trajectory_(key)
            except IndexError: raise IndexError
        else: raise TypeError

    def get_batch(self):
        return [self._get_trajectory_(dex) for 
            dex in range(len(self.batch_pool))]

    def _get_trajectory_(self, traj_dex):

        def _wrap_(values, dex):
            if hasattr(values, 'scalars'):
                values = values.scalars
                sca = scalars(label = self.pool_names[dex])
                sca.scalars = values
                return sca               
            else:
                sca = scalars(label = self.pool_names[dex])
                sca.scalars = values
                return sca

        def _wrap_surf_(values, dex):
            surfv = surface_vector(values, 
                label = self.pool_names[dex])
            #   ['populations'], ['x','y'], [x_, y_], 
            #       label = 'population surfaces')
            return surfv
        
        def _wrap_voxels_(values, dex):
            voxelv = voxel_vector(values, 
                label = self.pool_names[dex])
            return voxelv

        relevant = self.batch_pool[traj_dex]    #this will be system.data
        if type(relevant) is types.TupleType:   #numpy arrays or a tuple thereof
            batch = []
            if len(relevant[0].shape) == 2:
                #non_surf_cnt = relevant[0].shape[0]
                has_lines = True
                lcnt = relevant[0].shape[0]
            else:
                has_lines = False#non_surf_cnt = 0
                lcnt = 0
            if len(relevant) > 1:
                if len(relevant[1].shape) == 4:
                    has_surfs = True
                    scnt = relevant[1].shape[0]
                elif len(relevant[1].shape) == 5:
                    has_surfs = False
                    has_voxels = True
                    scnt = 0
                    vcnt = relevant[1].shape[0]
                else:
                    print 'unknown data object type!!'
                    pdb.set_trace()
                if len(relevant) > 2:
                    if len(relevant[2].shape) == 5:
                        has_voxels = True
                        vcnt = relevant[2].shape[0]
                else:
                    has_voxels = False
                    vcnt = 0
            else:
                has_surfs = False
                has_voxels = False
            for subdataobj in relevant:
                if len(subdataobj.shape) == 2:
                    subbatch = [_wrap_(rele,dex) for 
                        dex,rele in zip(xrange(lcnt), subdataobj)]
                elif len(subdataobj.shape) == 4:
                    subbatch = [_wrap_surf_(rele,dex) for 
                        dex,rele in zip(xrange(lcnt,lcnt+scnt), subdataobj)]
                elif len(subdataobj.shape) == 5:
                    subbatch = [_wrap_voxels_(rele,dex) for 
                        dex,rele in zip(xrange(lcnt+scnt,lcnt+scnt+vcnt), subdataobj)]
                batch.extend(subbatch)
        else:#if there is no tuple - the given numpy array should represent 1-1 targets
            batch = [_wrap_(rele,dex) for 
                dex,rele in enumerate(relevant)]
        return batch

class batch_data_pool(object):
    def __init__(self, *args, **kwargs):
        self.targets = args[0]
        self.trajectory = args[1].trajectory
        self.override_targets = None

        self._id = time.time()
        self.data_pool_ids = ['.'.join(['batch_child', 
            str(self._id), str(dex), 'pkl']) for dex 
                    in range(len(self.trajectory))]
        self.data_pools = [None]*len(self.data_pool_ids)

        self.live_pool = None
        self.current = 0

    def get_batch(self):
        pdb.set_trace()

    def _prep_pool_(self, dex):
        self._rid_pool_(self.current)
        self.current = dex
        self.live_pool = []

    def __len__(self):
        return len(self.live_pool)

    def __getitem__(self, key):
        if type(key) is types.IntType:
            try: return self._get_pool_(key)
            except IndexError: raise IndexError
        else: raise TypeError

    def _flatten_(self, pool):
        batch = []
        [batch.extend(self._get_trajectory_(dex)) 
            for dex in range(len(self.live_pool))]
        return batch

    def _get_pool_(self, dex):
        self.current = dex
        try:
            base = lfu.get_data_pool_path()
            sub_pool_id = os.path.join(base, self.data_pool_ids[dex])
            self.live_pool = lf.load_pkl_object(sub_pool_id)

        except IndexError: raise IndexError
        batch = [self._get_trajectory_(dex) for 
            dex in range(len(self.live_pool))]
        return batch

    def _get_trajectory_(self, traj_dex):

        def _wrap_(values, dex):
            sca = scalars(label = self.targets[dex])
            sca.scalars = values
            return sca

        relevant = self.live_pool[traj_dex]
        batch = [_wrap_(rele, dex) for dex, rele 
                        in enumerate(relevant)]
        return batch

    def _rid_pool_(self, dex):
        if not self.live_pool is None:
            if len(self.live_pool) > 0:
                print 'saving sub pool', dex
                lf.save_pkl_object(self.live_pool, os.path.join(
                    lfu.get_data_pool_path(), self.data_pool_ids[dex]))
                print 'saved sub pool', dex
                self.live_pool = []

class bin_vectors(object):
#Note: inheriting from lfu.modular_object here makes things SLOW!

    def __init__(self, label = 'another bin vector'):
        self.counts = [] #updated with a vector 1-1 with self.bins
        self.time = [] #updated once per capture
        self.bins = [] #set once
        self.tag = 'bin_vector'
        self.label = label

class voxel_vector(object):

    def __init__(self, cubes, label = 'another voxel vector'):
        self.tag = 'voxel_vector'
        self.label = label

        rng = np.arange(cubes.shape[0], dtype = float)
        self.axis_labels = ['cube_index']
        self.axis_values = [
            scalars(label = 'cube_index', scalars = rng)]
        self.axis_defaults = [da.scalars[0] for da in self.axis_values]

        self.data = cubes

    def make_cube(self, *args, **kwargs):
        pdb.set_trace()
        xleng = self.data.shape[1]
        yleng = self.data.shape[2]
        x = np.arange(xleng)
        y = np.arange(yleng)
        s_dex = self.axis_defaults[0]
        surf = self.data[s_dex]
        return (x, y, surf)

class surface_vector(object):

    def __init__(self, surfs, 
    #def __init__(self, surfs, surf_labels, axis_labels, axis_values, 
            label = 'another surface vector'):
        self.tag = 'surface_vector'
        self.label = label

        rng = np.arange(surfs.shape[0], dtype = float)
        self.axis_labels = ['surface_index']
        self.axis_values = [
            scalars(label = 'surface_index', scalars = rng)]
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

class surface_vector_reducing(object):

    def __init__(self, data = [], axes = [], surfs = [], 
            label = 'another reducing surface vector'):
        self.tag = 'surface_reducing'
        self.label = label
        self.data_scalars = [data for data in data if not data is self]
        self.axis_labels = axes
        self.axis_values = [scalars(label = dat.label, 
            scalars = lfu.uniqfy(dat.scalars)) for dat in 
            self.data_scalars if dat.label in self.axis_labels]
        self.axis_defaults = [da.scalars[0] for da in self.axis_values]
        self.surf_targets = surfs
        self.reduced = None

    def make_surface(self, x_ax = '', y_ax = '', surf_target = ''):
        data = self.data_scalars
        daters = [dater.label for dater in data]
        are_ax = [label in self.axis_labels for label in daters]
        axes = [copy(dater) for dater, is_ax in 
            zip(data, are_ax) if is_ax]
        ax_labs = [ax.label for ax in axes]
        if not (x_ax in ax_labs and y_ax in ax_labs and 
                not x_ax == y_ax and surf_target in self.surf_targets):
            print 'chosen axes do not correspond to surface'
            print 'axes:\n', ax_labs, '\nsurfaces:\n', self.surf_targets
            return False

        surf = lfu.grab_mobj_by_name(surf_target, data)
        x_ax_dex = ax_labs.index(x_ax)
        y_ax_dex = ax_labs.index(y_ax)
        ax_slices = copy(self.axis_defaults)
        ax_slices[x_ax_dex] = None
        ax_slices[y_ax_dex] = None

        reduced = (axes, surf)
        in_slices = []
        for ax_dex, ax in enumerate(axes):
            if ax_slices[ax_dex] is None:
                in_slices.append([True for val in ax.scalars])
            else:
                in_slices.append([(val == ax_slices[ax_dex]) 
                    for val in ax.scalars])

        in_every_slice = [(False not in row) for row in zip(*in_slices)]
        sub_surf = scalars_from_labels([surf_target])[0]
        sub_surf.scalars = [sur for sur, in_ in 
            zip(surf.scalars, in_every_slice) if in_]
        sub_axes = scalars_from_labels(self.axis_labels)
        for sub_ax, ax in zip(sub_axes, axes):
            sub_ax.scalars = lfu.uniqfy([val for val, in_ 
                in zip(ax.scalars, in_every_slice) if in_])

        self.reduced = (sub_axes, sub_surf)
        x = np.array(self.axis_values[x_ax_dex].scalars, dtype = float)
        y = np.array(self.axis_values[y_ax_dex].scalars, dtype = float)
        try:
            sf = np.array(sub_surf.scalars, dtype = float)
            sf = sf.reshape(len(x), len(y))
        except ValueError:
            pdb.set_trace()
            return
        return x, y, sf

def scalars_from_labels(targeted):
    return [scalars(label = target) for target in targeted]

def bin_vectors_from_labels(targeted):
    return [bin_vectors(label = target) for target in targeted]

def sort_data_by_type(data, specifics = []):
    if not specifics: specifics = [dater.label for dater in data]
    sorted_data = {'scalars': {}, 'coords': {}}
    for dater in [dater for dater in data if dater.label in specifics]:
        if dater.tag == 'scalar':
            sorted_data['scalars'][dater.label] = dater.scalars

        elif dater.tag == 'coordinates':
            sorted_data['coords']['_'.join(dater.coords.keys())] = dater.coords

    return sorted_data

def array_to_string(arr):
    string = ' '
    string = string.join([str(value) for value in arr])
    string += ' '
    return string

def coords_to_string(x, y, z):
    #concat = x + y + z
    concat = np.concatenate((x, y, z))
    array = [[concat[k], concat[k + len(x)], concat[k + 2*len(x)]] \
                                        for k in range(len(x))]
    array = [item for sublist in array for item in sublist]
    return array_to_string(array)

def quality_coords_to_string(x, y, z, Q, dims):
    string = str()
    xdim = int(dims[0]) + 1
    ydim = int(dims[1]) + 1
    zdim = int(dims[2]) + 1
    npts = xdim*ydim*zdim
    flat = ['0']*npts
    for j in range(len(Q)):
        try:
            flat[int(z[j])*xdim*ydim + int(y[j])*xdim + int(x[j])]=str(Q[j])

        except IndexError:
            print 'Youve got an indexing problem'
            pdb.set_trace()

    string = array_to_string(flat)
    return string

def clean_data_pools():

    def pool_name(ensem):
        pa = os.path.join(os.getcwd(), ensem)
        en = lf.load_pkl_object(pa)
        return en.data_pool_pkl

    dp_path = lfu.get_data_pool_path()

    pool_matches = []
    ensem_matches = []
    for root, dirnames, filenames in os.walk(dp_path):
        [pool_matches.append(os.path.join(root, finame)) for 
            finame in fnmatch.filter(filenames, 'data_pool.*.pkl')]

    enpkldir = lset.get_setting('ensempkl_directory')
    for root, dirnames, filenames in os.walk(enpkldir):
        [ensem_matches.append(os.path.join(root, finame)) for 
            finame in fnmatch.filter(filenames, '*.ensempkl')]

    saved_pools = [pool_name(en) for en in ensem_matches]
    del_pools = [item for item in pool_matches if 
        os.path.join(os.getcwd(), item) not in saved_pools]
    for pool in del_pools:
        if pool.count('smart') > 0:
            try:
                sm_pool = lf.load_pkl_object(pool)
                for sub_pool in sm_pool.data.data_pool_ids:
                    os.remove(os.path.join(dp_path, sub_pool))
            except OSError,e:
                print 'error: ', e.filename, ' - ', e.strerror
                print 'probably an orphan pool from terminated process...'
        os.remove(pool)





