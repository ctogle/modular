import modular_core.libfundamental as lfu

import modular_core.data.libdatacontrol as ldc
import modular_core.postprocessing.libpostprocess as lpp
import modular_core.criteria.trajectory_criterion as ltc

import pdb,sys
import numpy as np

###############################################################################
### conditional finds the fraction of a batch of trajectories which passes
### some criterion
###############################################################################

class conditional(lpp.post_process_abstract):

    def _string(self):
        inps = self._string_inputs()
        strs = [self.name,'conditional',inps]
        return '\t' + ' : '.join(strs)

    def __init__(self,*args,**kwargs):
        self._default('name','conditional',**kwargs)
        regs = ['all trajectories','by parameter space']
        self._default('valid_regimes',regs,**kwargs)
        self._default('regime','all trajectories',**kwargs)
        self.method = self.conditional_bin
        self.criterion = ltc.threshold(parent = self)
        self.children = [self.criterion]
        lpp.post_process_abstract.__init__(self,*args,**kwargs)

    def conditional_bin(self,*args,**kwargs):
        pool = args[0]
        passes = 0.0
        for traj in pool:
            if self.criterion(traj):
                passes += 1.0
        data = ldc.scalars_from_labels(['fraction passing criterion'])
        data[0].scalars = [passes/len(pool)]
        return data

    def _target_settables(self,*args,**kwargs):
        self.valid_regimes = ['all trajectories','by parameter space']
        self.valid_inputs = self._valid_inputs(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        self.capture_targets = ['fraction passing criterion']
        lpp.post_process_abstract._target_settables(self,*args,**kwargs)

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        kwargs['capture_targetable'] = capture_targetable
        self.criterion._widget(*args,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['panel'], 
                templates = [self.criterion.widg_templates]))
        lpp.post_process_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

# return valid **kwargs for meanfields based on msplit(line)
def parse_line(split,ensem,procs,routs):
    targs = split[3].split(' of ')
    means_of = targs[0]
    function_of = targs[1]
    relevant = lfu.msplit(means_of,',')
    inputs = lpp.parse_process_line_inputs(split[2],procs,routs)
    pargs = {
        'name':split[0],
        'variety':split[1],
        'input_regime':inputs,
        'means_of':relevant,
        'function_of':function_of,
        'bin_count':int(split[4]),
        'ordered':split[5].count('unordered') < 1,
            }
    return pargs

###############################################################################

if __name__ == 'modular_core.postprocessing.conditional':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lpp.process_types['conditional'] = (conditional,parse_line)

###############################################################################










