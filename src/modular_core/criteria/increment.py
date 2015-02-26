import modular_core.fundamental as lfu

import modular_core.data.datacontrol as ldc
import modular_core.data.single_target as dst
import modular_core.data.batch_target as dba

import modular_core.criteria.abstract as ab

import pdb,sys
import numpy as np

###############################################################################
### increment will check if the current state of a target has changed by an 
### amount specified since the last capture
###############################################################################

class increment(ab.criterion_abstract):

    def __init__(self,*args,**kwargs):
        self._default('name','increment criterion',**kwargs)
        self._default('increment',10.0,**kwargs)
        self._default('target','time',**kwargs)
        self._default('targets',['iteration','time'],**kwargs)
        ab.criterion_abstract.__init__(self,*args,**kwargs)

    def _sim_string(self):
        return 'increment:' + self.target + ':' + str(self.increment)

    def _string(self):
        strr = '\t' + self.target + ' increment : ' + str(self.increment)
        return strr

    def _initialize(self,*args,**kwargs):
        self.increment = float(self.increment)
        if self.target == 'time':self._last_value = self._last_value_list
        if self.target == 'iteration':self._last_value = self._last_value_value
        self.targetdex = [dater.label == self.target 
                for dater in system.data].index(True)

    def _last_value_value(self,system):
        last_value = system.__dict__[self.key]
        return last_value

    def _last_value_list(self,system):
        last_value = system.__dict__[self.key][-1]
        return last_value

    def _verify_pass(self,*args):
        mobj = args[0]
        last_value = self.find_last_value(mobj)
        last_captured_value = mobj.data[self.targetdex].scalars[-1]
        return abs(last_value - last_captured_value) >= self.increment

    def _widget(self,*args,**kwargs):
        window = args[0]
        self._sanitize(*args,from_sub = False)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin'], 
                doubles = [[True]], 
                initials = [[float(self.increment)]], 
                minimum_values = [[0.0]], 
                maximum_values = [[sys.float_info.max]], 
                instances = [[self]], 
                keys = [['increment']], 
                box_labels = ['Increment']))
        self.widg_templates.append(
            lgm.interface_template_gui(
                panel_position = (1, 1), 
                widgets = ['radio'], 
                labels = [self.targets], 
                initials = [[self.target]], 
                instances = [[self]], 
                keys = [['target']], 
                box_labels = ['Target to Check']))
        ab.criterion_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

# return valid **kwargs for increment based on msplit(line)
def parse_line(spl,ensem,procs,routs):
    increment = spl[1]
    target = spl[2]
    cargs = {
        'variety':spl[0],
        'increment':increment,
        'target':target,
            }
    return cargs

###############################################################################

if __name__ == 'modular_core.criteria.increment':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    ab.criterion_types['increment'] = (increment,parse_line)

###############################################################################










