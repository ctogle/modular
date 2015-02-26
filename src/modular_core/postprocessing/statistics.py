import modular_core.fundamental as lfu

import modular_core.data.datacontrol as ldc
import modular_core.postprocessing.process_abstract as lpp

import pdb,sys
import numpy as np

###############################################################################
### meanfields calculates means for a set of targets as a function of one target
###############################################################################

class statistics(lpp.post_process_abstract):

    def _string(self):
        inps = self._string_inputs()
        phrase = self.mean_of + ' of ' + self.function_of
        bins = str(self.bin_count)
        ordered = 'ordered' if self.ordered else 'unordered'
        strs = [self.name,'standard statistics',inps,phrase,bins,ordered]
        return '\t' + ' : '.join(strs)

    def __init__(self,*args,**kwargs):
        self._default('name','statistics',**kwargs)
        regs = ['all trajectories','by parameter space']
        self._default('valid_regimes',regs,**kwargs)
        self._default('regime','all trajectories',**kwargs)

        self._default('function_of',None,**kwargs)
        self._default('mean_of',None,**kwargs)
        self._default('bin_count',100,**kwargs)
        self._default('ordered',True,**kwargs)
        self.method = self.statistics
        lpp.post_process_abstract.__init__(self,*args,**kwargs)

    def statistics(self,*args,**kwargs):
        fof,mof = self.function_of,self.mean_of
        bct,orr,pool = self.bin_count,self.ordered,args[0]

        bin_axes,mean_axes = select_for_binning(pool,fof,mof)
        bins,vals = bin_scalars(bin_axes,mean_axes,bct,orr)

        means = [np.mean(val) for val in vals]
        medians = [np.median(val) for val in vals]
        stddevs = [np.stddev(val) for val in vals]
        coeff_variations = [stddev_/mean_ if not mean == 0.0 else None 
                            for stddev_,mean_ in zip(stddevs,means)]
        variances = [variance(val) for val in vals]
        ddexes = range(len(means))

        data = ldc.scalars_from_labels(self.target_list)
        data[0].scalars = bins
        data[1].scalars = means
        data[2].scalars = medians
        data[3].scalars = variances
        data[4].scalars = stddevs
        data[5].scalars = [means[k] + stddevs[k] for k in ddexes]
        data[6].scalars = [means[k] - stddevs[k] for k in ddexes]
        data[7].scalars = coeff_variations
        return data

    def _target_settables(self, *args, **kwargs):
        self.valid_regimes = ['all trajectories','by parameter space']
        self.valid_inputs = self._valid_inputs(*args, **kwargs)
        capture_targetable = self._targetables(*args, **kwargs)
        if self.mean_of is None and capture_targetable:
            self.mean_of = capture_targetable[0]
        if self.function_of is None and capture_targetable:
            self.function_of = capture_targetable[0]
        self.target_list = [self.function_of, 
            self.mean_of + ' mean', self.mean_of + ' median', 
            self.mean_of + ' variance', '1 stddev of ' + self.mean_of, 
            self.mean_of + ' +1 stddev', self.mean_of + ' -1 stddev', 
            self.mean_of + ' coefficient of variation']
        self.capture_targets = self.target_list
        post_process._target_settables(self, *args, **kwargs)

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
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
                widgets = ['radio'], 
                labels = [capture_targetable], 
                initials = [[self.mean_of]], 
                instances = [[self]], 
                keys = [['mean_of']], 
                box_labels = ['Statistics of']))
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

if __name__ == 'modular_core.postprocessing.statistics':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lpp.process_types['statistics'] = (statistics,parse_line)

###############################################################################










