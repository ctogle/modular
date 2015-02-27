import modular_core.fundamental as lfu

import modular_core.data.datacontrol as ldc
import modular_core.data.single_target as dst
import modular_core.data.batch_target as dba
import modular_core.postprocessing.process_abstract as lpp

import pdb,sys,math
import numpy as np
from scipy.stats import pearsonr as correl

###############################################################################
### correlate measures the pearson correlation coefficient of two targets as
### a function of a third target
###############################################################################

class correlate(lpp.post_process_abstract):

    def _string(self):
        #x, y correlation : correlation : 0 : x and y of time : 10 : ordered
        inps = self.string_inputs()
        phrase = self.target_1+' and '+self.target_2+' of '+self.function_of
        bins = str(self.bin_count)
        ordered = 'ordered' if self.ordered else 'unordered'
        strs = [self.name,'correlation',inps,phrase,bins,ordered]
        return '\t' + ' : '.join(strs)

    def __init__(self,*args,**kwargs):
        self._default('name','correlation',**kwargs)
        regs = ['all trajectories','by parameter space']
        self._default('valid_regimes',regs,**kwargs)
        self._default('regime','all trajectories',**kwargs)

        self._default('target_1',None,**kwargs)
        self._default('target_2',None,**kwargs)
        self._default('function_of',None,**kwargs)
        self._default('bin_count',100,**kwargs)
        self._default('ordered',True,**kwargs)
        self._default('fill_value',-100.0,**kwargs)
        self.method = self.correlate
        lpp.post_process_abstract.__init__(self,*args,**kwargs)

    def correlate(self,*args,**kwargs):
        def verify(val):
            if math.isnan(val): return self.fill_value
            else: return val
        bcnt,orr = self.bin_count,self.ordered

        bins,vs1 = args[0]._bin_data(self.function_of,self.target_1,bcnt,orr)
        bins,vs2 = args[0]._bin_data(self.function_of,self.target_2,bcnt,orr)

        correlations,p_values = zip(
            *[correl(v1,v2) for v1,v2 in zip(vs1,vs2)])
        data = dst.scalars_from_labels([self.function_of, 
            'correlation coefficients','correlation p-value'])
        data[0].data = np.array(bins)
        data[1].data = np.array([verify(val) for val in correlations])
        data[2].data = np.array([verify(val) for val in p_values])
        return dba.batch_node(data = data)

    def _target_settables(self, *args, **kwargs):
        self.valid_regimes = ['all trajectories','by parameter space']
        self.valid_inputs = self._valid_inputs(*args, **kwargs)
        capture_targetable = self._targetables(*args, **kwargs)
        if self.target_1 is None and capture_targetable:
                self.target_1 = capture_targetable[0]
        if self.target_2 is None and capture_targetable:
                self.target_2 = capture_targetable[0]
        if self.function_of is None and capture_targetable:
                self.function_of = capture_targetable[0]
        self.capture_targets = [self.function_of, 
            'correlation coefficients','correlation p-value']
        lpp.post_process_abstract._target_settables(self,*args,**kwargs)

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self._target_settables(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                panel_position = (1, 3), 
                instances = [[self]], 
                keys = [['ordered']], 
                labels = [['Domain is Ordered']], 
                append_instead = [False], 
                widgets = ['check_set'], 
                box_labels = ['Ordered Domain']))
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin'], 
                instances = [[self]], 
                keys = [['bin_count']], 
                initials = [[self.bin_count]], 
                minimum_values = [[1]], 
                maximum_values = [[100000]], 
                box_labels = ['Number of Bins']))
        self.widg_templates.append(
            lgm.interface_template_gui(
                keys = [['function_of']], 
                instances = [[self]], 
                widgets = ['radio'], 
                panel_label = 'As a Function of', 
                initials = [[self.function_of]], 
                labels = [capture_targetable]))
        self.widg_templates.append(
            lgm.interface_template_gui(
                layout = 'horizontal', 
                keys = [['target_1'],['target_2']], 
                instances = [[self],[self]], 
                widgets = ['radio','radio'], 
                panel_label = 'Correlation of', 
                initials = [[self.target_1],[self.target_2]], 
                labels = [capture_targetable,capture_targetable], 
                box_labels = ['Target 1','Target 2']))
        lpp.post_process_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

# return valid **kwargs for correlation based on msplit(line)
def parse_line(split,ensem,procs,routs):
    targs = split[3].replace(' and ', '||').replace(' of ', '||')
    targs = targs.split('||')
    target_1,target_2,func_of = targs
    bcnt = int(split[4])
    ordr = True if 'ordered' == split[5] else False
    inputs = lpp.parse_process_line_inputs(split[2],procs,routs)
    pargs = {
        'name':split[0],
        'variety':split[1],
        'input_regime':inputs,
        'target_1':target_1,
        'target_2':target_2,
        'function_of':func_of,
        'bin_count':bcnt,
        'ordered':ordr,
            }
    return pargs

###############################################################################

if __name__ == 'modular_core.postprocessing.correlation':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lpp.process_types['correlation'] = (correlate,parse_line)

###############################################################################










