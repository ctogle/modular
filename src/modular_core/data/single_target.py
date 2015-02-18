import modular_core.libfundamental as lfu
import modular_core.data.libdatacontrol as ldc

import pdb
import numpy as np

###############################################################################
### utility functions
###############################################################################

# return list of scalars objects with appropriate names
def scalars_from_labels(targeted):
    return [scalars(name = target) for target in targeted]

# return list of bin_vector objects with appropriate names
def bin_vectors_from_labels(targeted):
    return [bin_vectors(name = target) for target in targeted]

###############################################################################
###############################################################################

###############################################################################
### base_target is the base class for single target data_mobjects
###############################################################################

class base_target(ldc.data_mobject):

    def __init__(self,*args,**kwargs):
        self._default('data',None,**kwargs)
        ldc.data_mobject.__init__(self,*args,**kwargs)

###############################################################################
###############################################################################

###############################################################################
### scalars is the simplest single target data structure
### it is essentially a 1-D array of float values
###############################################################################

class scalars(base_target):

    def _string_list(self):
        return [str(val) for val in self.data]

    def __init__(self,*args,**kwargs):
        self._default('name','a scalar',**kwargs)
        self._default('tag','scalar',**kwargs)
        base_target.__init__(self,*args,**kwargs)

###############################################################################
### reducer takes any dimensional data and produces lines, surfaces, and cubes
### by fixing axes as needed
###############################################################################

class reducer(base_target):

    def __init__(self,*args,**kwargs):
        self._default('name','a reducer',**kwargs)
        self._default('tag','surface_reducing',**kwargs)
        self._default('data',[],**kwargs)
        self._default('axes',[],**kwargs)
        self._default('surfs',[],**kwargs)
        base_target.__init__(self,*args,**kwargs)

        #self.data_scalars = [data for data in data if not data is self]
        self.data_scalars = self.data[:]
        self.axis_values = [
            scalars(name = dat.name,data = lfu.uniqfy(dat.data)) 
            for dat in self.data_scalars if dat.name in self.axes]
        self.axis_defaults = [da.data[0] for da in self.axis_values]
        self.reduced = None

    def _surface(self,x_ax = '',y_ax = '',surf_target = ''):
        data = self.data_scalars
        daters = [dater.name for dater in data]
        are_ax = [label in self.axes for label in daters]
        axes = [dater for dater,is_ax in zip(data,are_ax) if is_ax]
        ax_labs = [ax.name for ax in axes]
        if not (x_ax in ax_labs and y_ax in ax_labs and 
                not x_ax == y_ax and surf_target in self.surfs):
            print 'chosen axes do not correspond to surface'
            print 'axes:\n',ax_labs,'\nsurfaces:\n',self.surfs
            return False

        surf = lfu.grab_mobj_by_name(surf_target,data)
        x_ax_dex = ax_labs.index(x_ax)
        y_ax_dex = ax_labs.index(y_ax)
        ax_slices = self.axis_defaults[:]
        ax_slices[x_ax_dex] = None
        ax_slices[y_ax_dex] = None

        reduced = (axes,surf)
        in_slices = []
        for ax_dex,ax in enumerate(axes):
            if ax_slices[ax_dex] is None:
                in_slices.append([True for val in ax.data])
            else:
                in_slices.append(
                    [(val == ax_slices[ax_dex]) for val in ax.data])

        in_every_slice = [(False not in row) for row in zip(*in_slices)]
        sub_surf = scalars_from_labels([surf_target])[0]
        sub_surf.data = [sur for sur,ie in zip(surf.data,in_every_slice) if ie]
        sub_axes = scalars_from_labels(self.axes)
        for sub_ax,ax in zip(sub_axes,axes):
            vals = [val for val,ie in zip(ax.data,in_every_slice) if ie]
            sub_ax.data = lfu.uniqfy(vals)

        self.reduced = (sub_axes,sub_surf)
        x = np.array(self.axis_values[x_ax_dex].data,dtype = float)
        y = np.array(self.axis_values[y_ax_dex].data,dtype = float)
        sf = np.array(sub_surf.data,dtype = float)
        sf = sf.reshape(len(x),len(y))
        return x,y,sf

###############################################################################

class bin_vector(object):

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

###############################################################################

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

###############################################################################
###############################################################################
                                         
if __name__ == 'modular_core.data.single_target':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'single_target of modular_core'










