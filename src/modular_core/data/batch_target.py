import modular_core.fundamental as lfu
import modular_core.data.datacontrol as ldc
import modular_core.data.single_target as dst
import modular_core.io.libfiler as lf
#import modular_core.io.hdf5 as hdf
import h5py

import pdb,os,time,types,random
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
    return 'data_pool.'+str(random.random())+'.node.' + str(newid) + '.hdf5'

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

    # CHILDREN ARE LOST FOREVER
    def _hdf5_data(self,v = False):
        pa = self.hdffile.filename
        self.hdffile.close()
        self.data = pa
        if self.children:pdb.set_trace()
        #self.children = None
        self.children = []

    # CHILDREN ARE NEVER RECOVERED
    def _unhdf5_data(self,v = False):
        if v:print 'loading batch node',self.data_pool_id,'...'
        dpath = self.data
        self.hdffile = h5py.File(dpath,'r',libver = 'latest')
        self.data = self.hdffile['data']
        if v:print 'loaded batch node',self.data_pool_id

    # determine if _recover() is necessary
    def _stowed(self):
        isstr = type(self.data) is types.StringType
        isuni = type(self.data) is types.UnicodeType
        haschild = len(self.children) > 0
        stow = (isstr or isuni) and not haschild
        return stow
        
    # compress data and store as pkl file in safe data_pool directory
    def _stow(self,v = True): 
        if v:print 'stowing batch node',self.data_pool_id,'...'
        if not self._stowed():self._hdf5_data()
        if v:print 'stowed batch node',self.data_pool_id,'...'

    # uncompress data and store as data attribute
    def _recover(self,v = True):
        if v:print 'recovering batch node',self.data_pool_id,'...'
        if self._stowed():self._unhdf5_data()
        if v:print 'recovered batch node',self.data_pool_id,'...'

    def _stow_child(self,dex,v = True):
        which = self.children[dex]
        which._stow(v = v)
        self.data_pool_ids.append(which.data_pool_id)

    def _recover_child(self,dex,v = True):
        which = self.children[dex]
        self.data_pool_ids.remove(which.data_pool_id)
        which._recover(v = v)
        return which

    def _add_child(self,node = None):
        if node is None:node = batch_node(parent = self)
        self.children.append(node)
        return node

    def _add_children(self,nodes):
        for n in nodes:
            n.parent = self
            self.children.append(n)

    def _sanitize(self):
        dpath = os.path.join(lfu.get_data_pool_path(),self.data_pool_id)
        self.hdffile = None
        self.data = dpath
        self.dims = None

    def __getstate__(self):
        self._sanitize()
        return self.__dict__

    def __init__(self,*args,**kwargs):
        self._default('metapool',False,**kwargs)
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
        try:self._init_data(fop = 'r')
        except:pdb.set_trace()

    def _init_data(self,fop = 'w'):
        if self.metapool:prepath = lfu.get_mapdata_pool_path()
        else:prepath = lfu.get_data_pool_path()
        dpath = os.path.join(prepath,self.data_pool_id)
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
    def _bin_data(self,x,ys,bcnt,ordered):
        xs,yss = self._bin_select(x,ys)
        if ordered and x == 'time':
            #should probably mean xs
            bins = xs[0].copy()
            vals = yss.transpose((2,1,0))
            if len(bins) < bcnt:
                print '\nfewer data entries than bins; reduce bin count!\n'
                #return bins,vals
                raise ValueError
            elif len(bins) > bcnt:
                c = len(bins)/bcnt
                newbins = bins[::c]
                avg = lambda x:(newbins[x-1]+newbins[x])/2.0
                newbins = np.array([avg(k) for k in range(1,len(newbins))])
                newvlen = c*vals.shape[2]
                newvals = np.empty((bcnt,yss.shape[1],newvlen),dtype = np.float)
                for b in range(bcnt):
                    for t in range(yss.shape[1]):
                        newvals[b][t] = vals[b*c:(b+1)*c,t].reshape((1,newvlen))
                return newbins,newvals
        else:
            pdb.set_trace()
            return bins,vals

    # return the single_target data_mobjects held by children
    # associated with both x and y
    def _bin_select(self,x,ys):
        dshape = self.data.shape
        xs = np.empty(shape = (dshape[0],dshape[2]),dtype = np.float)
        yss = np.empty(shape = (dshape[0],len(ys),dshape[2]),dtype = np.float)
        for trajdx in range(dshape[0]):
            for targdx in range(dshape[1]):
                targ = self.targets[targdx]
                if targ == x:xs[trajdx][:] = self.data[trajdx][targdx]
                if targ in ys:
                    ydex = ys.index(targ)
                    yss[trajdx][ydex][:] = self.data[trajdx][targdx]
        return xs,yss

    # reshape the hierarchy so that children[0].data becomes a set
    # of nodes below the node returned
    # will this cause cyclic references preventing garbage collection?
    def _split_child(self):
        split = batch_node()
        child = self.children[0]
        targets = child.targets
        dshape = child.data.shape[1:]
        for traj in self.children[0].data:
            traj_pool = batch_node(
                dshape = dshape,targets = targets)
            traj_pool._trajectory(traj)
            split._add_child(traj_pool)
            split._stow_child(-1,v = False)
        return split

    # receive a batch of results, calling _trajectory on each
    def _trajectorize(self,datas):
        for dat in datas:self._trajectory(dat)

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
        
    def _stow_friendly(self):
        self._stow(v = False)
        self.friendly = self._plot_friendly()

    def _stow_friendly_child(self,dex):
        self.children[dex]._stow_friendly()

    # when zpdata comes from a distant node
    # the data will be stowed on that node
    # but the friendly copy of the zeroth 
    # level process data will be on the nodes
    def _unfriendly(self):
        self._init_data()
        friendly = self.friendly
        for fdx in range(self.dshape[0]):
            self.data[fdx,:] = friendly[fdx].data[:]
        self._stow(v = False)

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
            for dx in range(data.shape[0]):
                std = datamobj(name = targets[dx],data = data[dx],marker = 'x')
                friendly.append(std)
            self._spruce(friendly)
            return friendly
                                                                     
###############################################################################
###############################################################################










 
