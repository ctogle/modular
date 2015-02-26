import modular_core.fundamental as lfu

import modular_core.data.datacontrol as ldc
import modular_core.data.single_target as dst
import modular_core.data.batch_target as dba

import modular_core.criteria.abstract as ab

import pdb,sys
import numpy as np

###############################################################################
### sim_time will verify if a mobjects iteration attribute exceeds some limit
###############################################################################

class sim_time(ab.criterion_abstract):

    def __init__(self,*args,**kwargs):
        self._default('name','simulation time criterion',**kwargs)
        self._default('max_time',100.0,**kwargs)
        ab.criterion_abstract.__init__(self,*args,**kwargs)

    def _sim_string(self):
        return 'time>=' + str(self.max_time)

    def _string(self):
        return '\ttime limit : ' + str(self.max_time)

    def _initialize(self,*args,**kwargs):
        self.max_time = float(self.max_time)

    def _verify_pass(self,*args):
        mobjt = args[0].time[-1]
        return self.max_time <= mobjt

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,from_sub = False)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin'], 
                doubles = [[True]], 
                initials = [[float(self.max_time)]], 
                minimum_values = [[0.0]], 
                maximum_values = [[sys.float_info.max]], 
                instances = [[self]], 
                keys = [['max_time']], 
                box_labels = ['Max Simulation Time']))
        ab.criterion_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

# return valid **kwargs for iteration based on msplit(line)
def parse_line(spl,ensem,procs,routs):
    max_time = spl[1]
    cargs = {
        'variety':spl[0],
        'max_time':max_time,
            }
    return cargs

###############################################################################

if __name__ == 'modular_core.criteria.timelimit':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    ab.criterion_types['time limit'] = (sim_time,parse_line)

###############################################################################










