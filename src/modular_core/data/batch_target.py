import modular_core.fundamental as lfu
import modular_core.data.datacontrol as ldc
import modular_core.data.single_target as dst
import modular_core.io.libfiler as lf
#import modular_core.io.hdf5 as hdf
import h5py

import pdb,os,time,types
import numpy as np

if __name__ == 'modular_core.data.batch_target':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'batch_target of modular_core'

###############################################################################
### utility functions
###############################################################################

pool_ids = [0]
def pool_id():
    newid = int(time.time()) + pool_ids[-1] + 1
    pool_ids.append(newid)
    #return 'data_pool.node.' + str(newid) + '.pkl'
    return 'data_pool.node.' + str(newid) + '.hdf5'

###############################################################################
###############################################################################

###############################################################################
### batch_node is the base class for data hierarchy nodes
### modular uses a hierarchy of data nodes ending in single target objects
###############################################################################

class batch_node(ldc.data_mobject):

    def _pkl_data(self,v = False):
        if v:print 'saving batch node',self.data_pool_id,'...'
        pa = os.path.join(lfu.get_data_pool_path(),self.data_pool_id)
        data = lfu.data_container(top = self.data,children = self.children)
        lf.save_mobject(data,pa)
        if v:print 'saved batch node',self.data_pool_id
        self.data = pa
        self.children = None

    def _unpkl_data(self,v = False):
        if v:print 'loading batch node',self.data_pool_id,'...'
        datapath = self.data
        data = lf.load_mobject(datapath)
        self.data = data.top
        self.children = data.children
        if v:print 'loaded batch node',self.data_pool_id

    def _hdf5_data(self,v = False):
        pa = self.hdffile.filename
        self.hdffile.close()
        self.data = pa
        if self.children:pdb.set_trace()
        self.children = None

    def _unhdf5_data(self,v = False):
        if v:print 'loading batch node',self.data_pool_id,'...'
        dpath = self.data

        self.hdffile = h5py.File(dpath,'r',libver = 'latest')
        self.data = self.hdffile['data']

        #data = lf.load_mobject(datapath)
        #self.data = data.top
        #self.children = data.children
        self.children = None
        print 'DID I HAVE CHILDREN?!'

        if v:print 'loaded batch node',self.data_pool_id

    def _stowed(self):
        if type(self.data) is types.StringType:return True
        elif type(self.data) is types.UnicodeType:return True
        else:return False
        
    # compress data and store as pkl file in safe data_pool directory
    def _stow(self,v = True): 
        if v:print 'stowing batch node',self.data_pool_id,'...'
        #if not type(self.data) is types.StringType:self._pkl_data()
        if not type(self.data) is types.StringType:self._hdf5_data()
        if v:print 'stowed batch node',self.data_pool_id,'...'

    # uncompress data and store as data attribute
    def _recover(self,v = True):
        if v:print 'recovering batch node',self.data_pool_id,'...'
        #if type(self.data) is types.StringType:self._unpkl_data()
        recover = type(self.data) is types.StringType or\
                  type(self.data) is types.UnicodeType
        if recover:self._unhdf5_data()
        if v:print 'recovered batch node',self.data_pool_id,'...'

    def _stow_child(self,dex):
        which = self.children[dex]
        which._stow(v = True)
        self.data_pool_ids.append(which.data_pool_id)

    def _recover_child(self,dex):
        which = self.children[dex]
        self.data_pool_ids.remove(which.data_pool_id)
        which._recover(v = True)
        return which

    def _add_child(self,node = None):
        if node is None:node = batch_node(parent = self)
        self.children.append(node)
        return node

    def _sanitize(self):
        dpath = os.path.join(lfu.get_data_pool_path(),self.data_pool_id)
        self.hdffile = None
        self.data = dpath
        self.dims = None

    def __getstate__(self):
        self._sanitize()
        return self.__dict__

    def __init__(self,*args,**kwargs):
        self._default('dshape',None,**kwargs)
        self._default('dims',None,**kwargs)
        self._default('parent',None,**kwargs)
        self._default('children',[],**kwargs)
        self._default('data',None,**kwargs)
        self._default('trajectoryindex',0,**kwargs)
        self._default('pspace_axes',None,**kwargs)
        self._default('targets',None,**kwargs)
        self._default('surface_targets',None,**kwargs)
        self.data_pool_id = pool_id()
        self.data_pool_ids = []
        if not self.dshape is None:self._init_data()
        ldc.data_mobject.__init__(self,*args,**kwargs)

    def _open(self):
        self._init_data(fop = 'r')

    def _init_data(self,fop = 'w'):
        dpath = os.path.join(lfu.get_data_pool_path(),self.data_pool_id)
        self.hdffile = h5py.File(dpath,fop,libver = 'latest')
        if fop == 'w':
            zeros = np.zeros(self.dshape,dtype = np.float)
            self.dims = len(self.dshape)
            self.data = self.hdffile.create_dataset('data',
                shape = self.dshape,dtype = np.float,data = zeros)
        elif fop == 'r':
            self.data = self.hdffile['data']

    # x and y are strings for bins,vals resp.
    # bcnt is the number of bins; if x in monotonic, ordered is True
    def _bin_data(self,x,y,bcnt,ordered):
        xs,ys = self._bin_select(x,y)
        if ordered and x == 'time':
            bins = xs[0].copy()
            vals = ys.transpose()
            #vals = ys.copy().transpose()
            if len(bins) < bcnt:
                print '\nfewer data entries than bins; reduce bin count!\n'
                raise ValueError
            elif len(bins) > bcnt:
                c = len(bins)/bcnt
                newbins = bins[::c]
                newbins = [(newbins[k-1]+newbins[k])/2.0 
                        for k in range(1,len(newbins))]
                newvlen = c*vals.shape[1]
                newvals = np.zeros((bcnt,newvlen),dtype = np.float)
                for b in range(bcnt):
                    newvals[b] = vals[b*c:(b+1)*c].reshape((1,newvlen))
                bins = newbins
                vals = newvals
        else:
            pdb.set_trace()
        return bins,vals

    # return the single_target data_mobjects held by children
    # associated with both x and y
    def _bin_select(self,x,y):
        dshape = self.data.shape
        xs = np.zeros(shape = (dshape[0],dshape[2]),dtype = np.float)
        ys = np.zeros(shape = (dshape[0],dshape[2]),dtype = np.float)
        for trajdx in range(dshape[0]):
            for targdx in range(dshape[1]):
                targ = self.targets[targdx]
                if targ == x:xs[trajdx] = self.data[trajdx][targdx]
                if targ == y:ys[trajdx] = self.data[trajdx][targdx]
        return xs,ys

    # data is a numpy array;axis 0 is 1-1 with targets
    # add a batch_node to children containing new data
    def _trajectory(self,data):#,targets = None):
        if self.dims == 2:self.data[:] = data
        elif self.dims == 3:
            self.data[self.trajectoryindex] = data
            self.trajectoryindex += 1

    def _spruce(self,friendly):
        if self.pspace_axes and self.surface_targets:
            red = dst.reducer(name = 'reducer',data = friendly[:],
                surfs = self.surface_targets,axes = self.pspace_axes)
            friendly.append(red)

    def _friendly(self):
        if type(self.data) is types.ListType:return True
        else:return False
        
    # return suitable data structures for plotting
    def _plot_friendly(self):
        if self._friendly():
            friendly = self.data[:]
            self._spruce(friendly)
            return friendly
        else:
            self._open()
            data = self.data
            targets = self.targets
            friendly = []
            if len(data.shape) == 2:datamobj = dst.scalars
            else:return friendly
            #else:pdb.set_trace()
            for dx in range(data.shape[0]):
                std = datamobj(name = targets[dx],data = data[dx],marker = 'x')
                friendly.append(std)
            self._spruce(friendly)
            return friendly
                                                                     
###############################################################################
###############################################################################










 
