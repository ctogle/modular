import modular_core.fundamental as lfu

import modular_core.data.datacontrol as ldc
import modular_core.data.single_target as dst
import modular_core.data.batch_target as dba
import modular_core.postprocessing.process_abstract as lpp
import modular_core.criteria.bistable as bitest

import pdb,sys
import numpy as np

###############################################################################
### binmeasure measures each trajectory with a measurement and bins them to make
### histograms and the like
###############################################################################

class binmeasure(lpp.post_process_abstract):

    def _string(self):
        inps = self._string_inputs()
        strs = [self.name,'measurement',inps]
        return '\t' + ' : '.join(strs)

    def __init__(self,*args,**kwargs):
        self._default('name','measurement',**kwargs)
        regs = ['all trajectories','by parameter space']
        self._default('valid_regimes',regs,**kwargs)
        self._default('regime','all trajectories',**kwargs)
        #self._default('target',None,**kwargs)
        self._default('targets',None,**kwargs)
        self._default('bin_count',10,**kwargs)
        self.method = self.measurement_bin

        self.measure = measurement_steady_state_count(parent = self)
        self.children = [self.measure]
        lpp.post_process_abstract.__init__(self,*args,**kwargs)

    def measurement_bin(self,*args,**kwargs):
        pool = args[0]
        stowed = pool._stowed()
        if stowed:pool._recover()

        measurements = [[] for t in self.targets]
        for traj in pool.data:
            for tdx,t in enumerate(self.targets):
                meas = self.measure(traj,pool.targets,t)
                measurements[tdx].append(meas)

        #now ignoring self.bin_counts....
        binlimits = [int(min(measurements[0])),int(max(measurements[0]))]
        if len(measurements) > 1:
            for tmeas in measurements[1:]:
                tmin = min(tmeas)
                tmax = max(tmeas)
                if tmin < binlimits[0]:binlimits[0] = int(tmin)
                if tmax > binlimits[1]:binlimits[1] = int(tmax)
        bins = [x for x in range(*binlimits)]
        tcount = len(self.target_list)
        dshape = (tcount,len(bins))
        data = np.zeros(dshape,dtype = np.float)
        bins = [b-0.5 for b in bins]
        bins.append(max(bins)+bins[-1]-bins[-2])
        bins = np.array(bins)

        for subdx,submeas in enumerate(measurements):
            bincounts,bins = np.histogram(submeas,bins = bins)
            data[subdx+1] = bincounts

        avg = lambda x:(bins[x-1]+bins[x])/2.0
        bins = [avg(k) for k in range(1,len(bins))]
        data[0] = bins

        if stowed:pool._stow()
        #bnode = dba.batch_node(dshape = dshape,targets = self.target_list)
        bnode = self._init_data(dshape,self.target_list)
        bnode._trajectory(data)
        return bnode

    def _target_settables(self,*args,**kwargs):
        self.valid_regimes = ['all trajectories','by parameter space']
        self.valid_inputs = self._valid_inputs(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        self.target_list = ['bins']+[t+' counts' for t in self.targets]
        self.capture_targets = self.target_list
        lpp.post_process_abstract._target_settables(self,*args,**kwargs)

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self._target_settables(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        kwargs['capture_targetable'] = capture_targetable
        self.measure._widget(*args,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['panel'], 
                templates = [self.measure.widg_templates]))
        lpp.post_process_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

class measurement_steady_state_count(lfu.mobject):

    def __init__(self,*args,**kwargs):
        self._default('window',0.2,**kwargs)
        lfu.mobject.__init__(self,*args,**kwargs)

    def __call__(self,*args,**kwargs):
        data,targets,target = args
        tdata = data[targets.index(target)]
        dlen = len(tdata)
        wdata = tdata[dlen-self.window*dlen:dlen]
        value = np.median(wdata)
        #value = np.mean(wdata)
        return value

###############################################################################
###############################################################################

# return valid **kwargs for meanfields based on msplit(line)
def parse_line(split,ensem,procs,routs):
    targets = lfu.msplit(split[3],',')
    inputs = lpp.parse_process_line_inputs(split[2],procs,routs)
    pargs = {
        'name':split[0],
        'variety':split[1],
        'input_regime':inputs,
        'targets':targets,
        'bin_count':int(split[4]),
            }
    return pargs

###############################################################################

if __name__ == 'modular_core.postprocessing.measurebin':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lpp.process_types['bin measurement'] = (binmeasure,parse_line)

###############################################################################











