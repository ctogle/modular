import modular_core.fundamental as lfu

import modular_core.data.datacontrol as ldc
import modular_core.data.single_target as dst
import modular_core.data.batch_target as dba
import modular_core.postprocessing.process_abstract as lpp

import pdb,sys,math
import numpy as np
import scipy.cluster.vq as vq

###############################################################################
### bistability characterizes the bistable qualities of a single trajectory
###############################################################################

class bistability(lpp.post_process_abstract):

    def _string(self):
        inps = self._string_inputs()
        strs = [self.name,'bistability',inps]
        return '\t' + ' : '.join(strs)

    def __init__(self,*args,**kwargs):
        self._default('name','bistable',**kwargs)
        #regs = ['all trajectories','by parameter space']
        #self._default('valid_regimes',regs,**kwargs)
        #self._default('regime','all trajectories',**kwargs)
        self._default('valid_regimes',['per trajectory'],**kwargs)
        self._default('regime','per trajectory',**kwargs)

        self._default('bin_count',100,**kwargs)
        #self._default('cluster_count',2,**kwargs)
        self._default('ordered',True,**kwargs)

        self._default('function_of',None,**kwargs)
        self._default('targets',[],**kwargs)

        self.method = 'bistable'
        lpp.post_process_abstract.__init__(self,*args,**kwargs)

    def bistable(self,*args,**kwargs):
        pool = args[0]

        # pool.data.dshape = (#targets,#bins of input distribution)
        # assuming there are two peaks in the distribution, measure several quantities
        # integrate over each peak and compare probs of being in each
        # measure the distance between the peaks in bin space

        # identify peak centers
        # identify peak bounds in bin space
        # sum the density function to get the integral over the peak

        def getmidpoint(bins):        
            mx = raw_input('give me the midpoint in bin space!')
            try:return int(mx)
            except ValueError:
                print 'damnit you idiot:',mx
                return

        def bistab(bins,data):        
          
            # use data to identify values in bins that correspond to features

            mx = getmidpoint(bins)
            peak1 = data[:mx]
            peak2 = data[mx:]
            prob1 = peak1.sum()
            prob2 = peak2.sum()

            pdb.set_trace()

            return meas

        tcount = len(self.target_list)
        dshape = (tcount-1,1)
        data = np.zeros(dshape,dtype = np.float)
        bins = pool.data[pool.targets.index(self.function_of)]

        for dtx in range(tcount-1):
            dt = self.targets[dtx]
            dtdat = pool.data[pool.targets.index(dt)]

            meas = bistab(bins,dtdat)
            data[self.targets.index(dt)] = meas

            pdb.set_trace()

        #data[0] = bins

        bnode = self._init_data(dshape,self.target_list)
        bnode._trajectory(data)
        return bnode

    def _target_settables(self,*args,**kwargs):
        self.valid_regimes = ['per trajectory']
        self.valid_inputs = self._valid_inputs(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        if self.targets is None and capture_targetable:
            self.targets = capture_targetable
        if self.function_of is None and capture_targetable:
            self.function_of = capture_targetable[0]

        diff_targets = [item+':max-min' for item in self.targets]
        self.target_list = [self.function_of]+diff_targets

        self.capture_targets = self.target_list
        self.output.targeted = lfu.intersect_lists(
            self.output.targeted,self.capture_targets)
        lpp.post_process_abstract._target_settables(self,*args,**kwargs)

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self._target_settables(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                keys = [['targets']], 
                instances = [[self]], 
                widgets = ['check_set'], 
                box_labels = ['Targets'], 
                append_instead = [True], 
                provide_master = [True], 
                labels = [capture_targetable]))
        lpp.post_process_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

# return valid **kwargs for bistability based on msplit(line)
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
        'targets':relevant,
        'function_of':function_of,
        #'bin_count':int(split[4]),
        #'ordered':split[5].count('unordered') < 1,
            }
    return pargs

###############################################################################

if __name__ == 'modular_core.postprocessing.bistability':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lpp.process_types['bistability'] = (bistability,parse_line)

###############################################################################









 
