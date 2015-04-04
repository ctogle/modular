import modular_core.fundamental as lfu

import modular_core.data.datacontrol as ldc
import modular_core.data.single_target as dst
import modular_core.data.batch_target as dba
import modular_core.postprocessing.process_abstract as lpp

import pdb,sys,math
import numpy as np
import scipy.cluster.vq as vq

###############################################################################
### k_means performs a k_means clustering method (from scipy) to characterize data
###############################################################################

class k_means(lpp.post_process_abstract):

    def _string(self):
        inps = self._string_inputs()
        strs = [self.name,'k_means',inps]
        return '\t' + ' : '.join(strs)

    def __init__(self,*args,**kwargs):
        self._default('name','k_means',**kwargs)
        regs = ['all trajectories','by parameter space']
        self._default('valid_regimes',regs,**kwargs)
        #self._default('valid_regimes',['per trajectory'],**kwargs)
        #self._default('regime','per trajectory',**kwargs)
        self._default('regime','all trajectories',**kwargs)

        self._default('bin_count',100,**kwargs)
        self._default('cluster_count',2,**kwargs)
        self._default('ordered',True,**kwargs)

        self._default('function_of',None,**kwargs)
        self._default('k_means_of',['gamma'],**kwargs)

        self.method = self.k_means_clusters
        lpp.post_process_abstract.__init__(self,*args,**kwargs)

    def k_means_clusters(self,*args,**kwargs):
        pool = args[0]

        tcount = len(self.target_list)
        dshape = (tcount,self.bin_count)
        data = np.zeros(dshape,dtype = np.float)
        bins,valss = pool._bin_data(
            self.function_of,self.k_means_of,
            self.bin_count,self.ordered)
        kcount = len(self.k_means_of)

        cc = self.cluster_count
        def kdist(bindvals):
            kmeans = vq.kmeans(bindvals,cc)
            cposs,distortion = kmeans
            return abs(cposs[1]-cposs[0]),distortion

        for dex in range(valss.shape[1]):
            vals = valss[:,dex,:]
            cdiff,cdist = zip(*[kdist(vals[x]) for x in range(vals.shape[0])])
            data[dex+1] = cdiff[:]
            data[dex+kcount+1] = cdist[:]
        data[0] = bins

        bnode = self._init_data(dshape,self.target_list)
        bnode._trajectory(data)
        return bnode

    def _target_settables(self,*args,**kwargs):
        #self.valid_regimes = ['per trajectory']
        self.valid_regimes = ['all trajectories','by parameter space']
        self.valid_inputs = self._valid_inputs(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        if self.k_means_of is None and capture_targetable:
            self.k_means_of = capture_targetable
        if self.function_of is None and capture_targetable:
            self.function_of = capture_targetable[0]

        diff_targets = [item+'-centroid-difference' for item in self.k_means_of]
        dist_targets = [item+'-centroid-distortion' for item in self.k_means_of]
        self.target_list = [self.function_of]+diff_targets+dist_targets

        self.capture_targets = self.target_list
        self.output.targeted = lfu.intersect_lists(
            self.output.targeted,self.capture_targets)
        lpp.post_process_abstract._target_settables(self,*args,**kwargs)

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self._target_settables(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)

###############################################################################
        #use a spin widget to select a location in the domain
        #   or a text box to support true slicing
        #self.widg_templates.append(
        #    lgm.interface_template_gui(
        #        keys = [['slice_dex']], 
        #        instances = [[self]], 
        #        widgets = ['text'], 
        #        box_labels = ['Slice Index'], 
        #        initials = [[self.slice_dex]]))
        self.widg_templates.append(
            lgm.interface_template_gui(
                keys = [['k_means_of']], 
                instances = [[self]], 
                widgets = ['check_set'], 
                box_labels = ['Targets'], 
                append_instead = [True], 
                provide_master = [True], 
                labels = [capture_targetable]))
###############################################################################

        lpp.post_process_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

# return valid **kwargs for k_means based on msplit(line)
def parse_line(split,ensem,procs,routs):
    inputs = lpp.parse_process_line_inputs(split[2],procs,routs)
    targs = split[3].split(' of ')
    means_of = targs[0]
    function_of = targs[1]
    relevant = lfu.msplit(means_of,',')
    pargs = {
        'name':split[0],
        'variety':split[1],
        'input_regime':inputs,
        'dater_ids':relevant+[function_of],
        'means_of':relevant,
        'function_of':function_of,
        'bin_count':int(split[4]),
        'ordered':split[5].count('unordered') < 1,
            }
    return pargs

###############################################################################

if __name__ == 'modular_core.postprocessing.k_means_clusters':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lpp.process_types['k-means'] = (k_means,parse_line)

###############################################################################










