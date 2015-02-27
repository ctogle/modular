import modular_core.fundamental as lfu
import modular_core.data.datacontrol as ldc
import modular_core.data.single_target as dst
import modular_core.io.libfiler as lf

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
    return 'data_pool.node.' + str(newid) + '.pkl'

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
        lf.save_pkl_object(data,pa)
        if v:print 'saved batch node',self.data_pool_id
        self.data = pa
        self.children = None

    def _unpkl_data(self,v = False):
        if v:print 'loading batch node',self.data_pool_id,'...'
        datapath = self.data
        data = lf.load_pkl_object(datapath)
        self.data = data.top
        self.children = data.children
        if v:print 'loaded batch node',self.data_pool_id

    def _stowed(self):
        if type(self.data) is types.StringType:return True
        else:return False
        
    # compress data and store as pkl file in safe data_pool directory
    def _stow(self,v = True): 
        if v:print 'stowing batch node',self.data_pool_id,'...'
        if not type(self.data) is types.StringType:self._pkl_data()
        if v:print 'stowed batch node',self.data_pool_id,'...'

    # uncompress data and store as data attribute
    def _recover(self,v = True):
        if v:print 'recovering batch node',self.data_pool_id,'...'
        if type(self.data) is types.StringType:self._unpkl_data()
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

    def _add_child(self,node):
        self.children.append(node)

    def __init__(self,*args,**kwargs):
        self._default('parent',None,**kwargs)
        self._default('children',[],**kwargs)
        self._default('data',[],**kwargs)
        self.data_pool_id = pool_id()
        self.data_pool_ids = []
        ldc.data_mobject.__init__(self,*args,**kwargs)

    def __add__(self,other):
        new = batch_node()
        pdb.set_trace()
        return new

    def _bin_ordered(self,xs,ys,bins,vals):
        bin_res = bins[1] - bins[0]
        bin_hwid = bin_res/2.0
        j_last = [0]*len(xs)
        for i in range(len(bins)):
            threshold_top = bins[i] + bin_hwid
            for k in range(len(xs)):
                last_j = j_last[k]
                for j in range(last_j,len(xs[k].data)):
                    if xs[k].data[j] < threshold_top:
                        vals[i].append(ys[k].data[j])
                    else:
                        j_last[k] = j
                        break
        return bins,vals

    # CLEAN THIS UP
    def _bin_unordered(self,xs,ys,bins,vals):
        pdb.set_trace()
        for i in range(len(bins)):
            try:threshold_bottom = threshold_top
            except:threshold_bottom = bins[i]
            threshold_top = bins[i] + bin_bump
            for k in range(len(axes)):
                for j in range(len(axes[k].scalars)):
                    if bins[k].data[j] < threshold_top and\
                            bins[k].data[j] > threshold_bottom:
                        vals[i].append(vals[k].data[j])       
        return bins,vals

    # x and y are strings for bins,vals resp.
    # bcnt is the number of bins; if x in monotonic, ordered is True
    def _bin_data(self,x,y,bcnt,ordered):
        xs,ys = self._bin_select(x,y)
        bin_min = min([min(ax.data) for ax in xs])
        bin_max = max([max(ax.data) for ax in xs])
        bins = np.linspace(bin_min,bin_max,bcnt)
        vals = [[] for k in range(len(bins))]
        if ordered:bins,vals = self._bin_ordered(xs,ys,bins,vals)
        else:bins,vals = self._bin_unordered(xs,ys,bins,vals)
        return bins,vals

    # return the single_target data_mobjects held by children
    # associated with both x and y
    def _bin_select(self,x,y):
        singles = self._flatten_children()
        xs,ys = [],[]
        for sing in singles:
            if sing.name == x:xs.append(sing)
            if sing.name == y:ys.append(sing)
        return xs,ys

    # return an aggregate of all childrens' data
    def _flatten_children(self):
        flat = []
        stowed = self._stowed()
        if stowed:self._recover()
        for no in self.children:flat.extend(no.data)
        if stowed:self._stow()
        return flat

    # data is a numpy array;axis 0 is 1-1 with targets
    # add a batch_node to children containing new data
    def _trajectory(self,data,targets):
        node = batch_node(parent = self)

        if len(data.shape) == 2:datamobj = dst.scalars
        else:pdb.set_trace()

        for dx in range(data.shape[0]):
            std = datamobj(name = targets[dx],data = data[dx])
            node.data.append(std)
        self._add_child(node)
                                                                     
###############################################################################
###############################################################################










 
