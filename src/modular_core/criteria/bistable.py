import modular_core.libfundamental as lfu

import modular_core.criteria.trajectory_abstract as tab

import pdb,types,sys
import numpy as np

###############################################################################
### a bistable criterion tests if a given trajectory exhibits bistability...
###############################################################################

class bistable(tab.trajectory_abstract):

    def __init__(self,*args,**kwargs):
        self._default('name','threshold criterion',**kwargs)
        #self._default('threshold',0,**kwargs)
        self._default('threshold',10.0,**kwargs)
        #self._default('target',None,**kwargs)
        self._default('target','T',**kwargs)
        self._default('targets',['T','A'],**kwargs)
        #self._default('targets',[],**kwargs)
        tab.trajectory_abstract.__init__(self,*args,**kwargs)

    def _sim_string(self):
        return ''

    def _string(self):
        return ''

    def _verify_pass(self,*args):
        traj = args[0]
        which = lfu.grab_mobj_by_name(self.target,traj)
        bistable = max(which.data) >= self.threshold*np.mean(which.data)
        return bistable

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,from_sub = False)
        self.widg_templates.append(
            lgm.interface_template_gui(
                panel_position = (1,1), 
                widgets = ['radio'], 
                labels = [self.targets], 
                initials = [[self.target]], 
                instances = [[self]], 
                keys = [['target']], 
                box_labels = ['Target to Check']))
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin'], 
                doubles = [[True]], 
                initials = [[float(self.threshold)]], 
                #minimum_values = [[0]], 
                #maximum_values = [[sys.maxint]], 
                instances = [[self]], 
                keys = [['threshold']], 
                box_labels = ['Threshold Value']))
        tab.trajectory_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

if __name__ == 'modular_core.criteria.bistable':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'bistable criterion of modular_core'










