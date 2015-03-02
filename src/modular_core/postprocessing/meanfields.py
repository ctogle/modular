import modular_core.fundamental as lfu

import modular_core.data.datacontrol as ldc
import modular_core.data.single_target as dst
import modular_core.data.batch_target as dba
import modular_core.postprocessing.process_abstract as lpp

import pdb,sys,time
import numpy as np

###############################################################################
### meanfields calculates means for a set of targets as a function of one target
###############################################################################

class meanfields(lpp.post_process_abstract):

    def _string(self):
        inps = self._string_inputs()
        phrase = ','.join(self.means_of) + ' of ' + self.function_of
        ordered = 'ordered' if self.ordered else 'unordered'
        strs = [self.name,'meanfields',inps,phrase,str(self.bin_count),ordered]
        return '\t' + ' : '.join(strs)

    def __init__(self,*args,**kwargs):
        self._default('name','meanfields',**kwargs)
        regs = ['all trajectories','by parameter space']
        self._default('valid_regimes',regs,**kwargs)
        self._default('regime','all trajectories',**kwargs)

        self._default('function_of', None, **kwargs)
        self._default('means_of', None, **kwargs)
        self._default('bin_count', 100, **kwargs)
        self._default('ordered', True, **kwargs)
        self.method = self.meanfields
        lpp.post_process_abstract.__init__(self,*args,**kwargs)

    def meanfields(self,*args,**kwargs):
        pool = args[0]

        tcount = len(self.target_list)
        dshape = (tcount,self.bin_count)
        data = np.zeros(dshape,dtype = np.float)
        bins,valss = pool._bin_data(
            self.function_of,self.means_of,
            self.bin_count,self.ordered)
        for dex in range(valss.shape[1]):
            vals = valss[:,dex,:]
            means = np.array([np.mean(v) for v in vals])
            data[dex + 1] = means
        data[0] = bins

        bnode = dba.batch_node(dshape = dshape,targets = self.target_list)
        bnode._trajectory(data)
        return bnode

    def _target_settables(self,*args,**kwargs):
        self.valid_regimes = ['all trajectories','by parameter space']
        self.valid_inputs = self._valid_inputs(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        if self.means_of is None and capture_targetable:
            self.means_of = capture_targetable
        if self.function_of is None and capture_targetable:
            self.function_of = capture_targetable[0]

        mean_targets = [item+' mean' for item in self.means_of]
        self.target_list = [self.function_of] + mean_targets
        self.capture_targets = self.target_list
        lpp.post_process_abstract._target_settables(self,*args,**kwargs)

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self._target_settables(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                panel_position = (1, 3), 
                widgets = ['check_set'], 
                append_instead = [False], 
                instances = [[self]], 
                keys = [['ordered']], 
                labels = [['Domain is Ordered']], 
                box_labels = ['Ordered Domain']))
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin'], 
                initials = [[self.bin_count]], 
                minimum_values = [[1]], 
                maximum_values = [[100000]], 
                instances = [[self]], 
                keys = [['bin_count']], 
                box_labels = ['Number of Bins']))
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['radio'], 
                labels = [capture_targetable], 
                initials = [[self.function_of]], 
                instances = [[self]], 
                keys = [['function_of']], 
                box_labels = ['As a Function of']))
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['check_set'], 
                append_instead = [True], 
                provide_master = [True], 
                labels = [capture_targetable], 
                initials = [[self.means_of]], 
                instances = [[self]], 
                keys = [['means_of']], 
                box_labels = ['Means of']))
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

if __name__ == 'modular_core.postprocessing.meanfields':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lpp.process_types['meanfields'] = (meanfields,parse_line)

###############################################################################










