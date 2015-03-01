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
        self._default('target',None,**kwargs)
        self._default('bin_count',10,**kwargs)
        self.method = self.measurement_bin

        self.measure = measurement_steady_state_count(parent = self)

        self.children = [self.measure]
        lpp.post_process_abstract.__init__(self,*args,**kwargs)

    def measurement_bin(self,*args,**kwargs):
        pool = args[0]
        stowed = pool._stowed()
        if stowed:pool._recover()

        tcount = len(self.target_list)
        dshape = (tcount,self.bin_count)
        data = np.zeros(dshape,dtype = np.float)

        measurements = []
        for traj in pool.data:
            meas = self.measure(traj,pool.targets)
            measurements.append(meas)

        bincounts,bins = np.histogram(measurements,bins = self.bin_count)
        # histogram returns bin_edges; ignore the last edge...
        data[0] = bins[:-1]
        data[1] = bincounts

        if stowed:pool._stow()
        bnode = dba.batch_node(dshape = dshape,targets = self.target_list)
        bnode._trajectory(data)
        return bnode

    def _target_settables(self,*args,**kwargs):
        self.valid_regimes = ['all trajectories','by parameter space']
        self.valid_inputs = self._valid_inputs(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        self.target_list = ['bins','counts']
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
        data,targets = args
        tdata = data[targets.index(self.parent.target)]
        dlen = len(tdata)
        wdata = tdata[dlen-self.window*dlen:dlen]
        value = np.mean(wdata)
        return value

###############################################################################
###############################################################################

# return valid **kwargs for meanfields based on msplit(line)
def parse_line(split,ensem,procs,routs):
    target = split[3]
    inputs = lpp.parse_process_line_inputs(split[2],procs,routs)
    pargs = {
        'name':split[0],
        'variety':split[1],
        'input_regime':inputs,
        'target':target,
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











