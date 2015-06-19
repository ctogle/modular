import modular_core.fundamental as lfu

import modular_core.data.datacontrol as ldc
import modular_core.data.single_target as dst
import modular_core.data.batch_target as dba
import modular_core.postprocessing.process_abstract as lpp

import pdb,sys,time
import numpy as np

###############################################################################
### extract creates a dataset that is a subset of trajectories in its input data
###############################################################################

class extract(lpp.post_process_abstract):

    def _string(self):
        raise NotImplemented

        inps = self._string_inputs()
        phrase = ','.join(self.means_of) + ' of ' + self.function_of
        ordered = 'ordered' if self.ordered else 'unordered'
        strs = [self.name,'meanfields',inps,phrase,str(self.bin_count),ordered]
        return '\t' + ' : '.join(strs)

    def __init__(self,*args,**kwargs):
        self._default('name','extraction',**kwargs)
        regs = ['all trajectories','by parameter space']
        self._default('valid_regimes',regs,**kwargs)
        self._default('regime','all trajectories',**kwargs)

        self._default('extracts',[],**kwargs)
        self._default('extractions',1,**kwargs)
        self.method = 'extr'
        lpp.post_process_abstract.__init__(self,*args,**kwargs)

    def extr(self,*args,**kwargs):
        pool = args[0]
        mapping = self.parent.parent.cartographer_plan.use_plan
        if mapping:xcnt = 1
        else:
            if self.extractions == 'all':xcnt = pool.data.shape[0]
            else:xcnt = int(self.extractions)
        tcount = len(self.extracts)
        dshape = (tcount,pool.data.shape[-1])
        for x in range(xcnt):
            data = np.zeros(dshape,dtype = np.float)
            for px in range(tcount):
                pt = self.extracts[px]
                data[px,:] = pool.data[x,pool.targets.index(pt),:]
            bnode = self._init_data(dshape,self.extracts)
            bnode._trajectory(data)
            self.data._add_child(bnode)
            self.data._stow_child(-1,v = False)

    def _target_settables(self,*args,**kwargs):
        self.valid_regimes = ['all trajectories','by parameter space']
        self.valid_inputs = self._valid_inputs(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        if self.extracts is None or self.extracts == ['all']:
            self.extracts = capture_targetable
        self.capture_targets = self.extracts
        lpp.post_process_abstract._target_settables(self,*args,**kwargs)

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self._target_settables(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['check_set'], 
                append_instead = [True], 
                provide_master = [True], 
                labels = [capture_targetable], 
                initials = [[self.extracts]], 
                instances = [[self]], 
                keys = [['extracts']], 
                box_labels = ['Targets']))
        lpp.post_process_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

# return valid **kwargs for extraction based on msplit(line)
def parse_line(split,ensem,procs,routs):
    extracts = lfu.msplit(split[3],',')
    extractions = split[4]
    inputs = lpp.parse_process_line_inputs(split[2],procs,routs)
    pargs = {
        'name':split[0],
        'variety':split[1],
        'input_regime':inputs,
        'extracts':extracts,
        'extractions':extractions,
            }
    return pargs

###############################################################################

if __name__ == 'modular_core.postprocessing.extraction':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lpp.process_types['extract'] = (extract,parse_line)

###############################################################################










