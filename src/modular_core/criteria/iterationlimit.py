import modular_core.libfundamental as lfu

import modular_core.data.libdatacontrol as ldc
import modular_core.data.single_target as dst
import modular_core.data.batch_target as dba

import modular_core.criteria.abstract as ab

import pdb,sys
import numpy as np

###############################################################################
### iteration will verify if a mobjects iteration attribute exceeds some limit
###############################################################################

class iteration(ab.criterion_abstract):

    def __init__(self,*args,**kwargs):
        self._default('name','iteration criterion',**kwargs)
        self._default('max_iterations',1000,**kwargs)
        ab.criterion_abstract.__init__(self,*args,**kwargs)

    def _sim_string(self):
        return 'iteration>=' + str(self.max_iterations)

    def _string(self):
        return '\titeration limit : ' + str(self.max_iterations)

    def _initialize(self,*args,**kwargs):
        self.max_iterations = float(self.max_iterations)

    def _verify_pass(self,*args):
        mobji = args[0].iteration
        verif = mobji >= self.max_iterations
        return verif

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,from_sub = False)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin'], 
                doubles = [[False]], 
                initials = [[int(self.max_iterations)]], 
                minimum_values = [[0]], 
                maximum_values = [[sys.maxint]], 
                instances = [[self]], 
                keys = [['max_iterations']], 
                box_labels = ['Iteration Limit']))
        ab.criterion_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

# return valid **kwargs for iteration based on msplit(line)
def parse_line(spl,ensem,procs,routs):
    max_iterations = spl[1]
    cargs = {
        'variety':spl[0],
        'max_iterations':max_iterations,
            }
    return cargs

###############################################################################

if __name__ == 'modular_core.criteria.iterationlimit':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    ab.criterion_types['iteration limit'] = (iteration,parse_line)

###############################################################################










