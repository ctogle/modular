import modular_core.libfundamental as lfu

import modular_core.criteria.libcriterion as lc

import pdb,types,sys

if __name__ == 'modular_core.criteria.trajectory_criterion':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'trajectory_criterion of modular_core'

###############################################################################
### a trajectory criterion tests a condition given one trajectory of data
###############################################################################

class trajectory_criterion_abstract(lc.criterion_abstract):

    def __init__(self,*args,**kwargs):
        self._default('name','trajectory criterion',**kwargs)
        lc.criterion_abstract.__init__(self,*args,**kwargs)

    def _sim_string(self):
        return ''

    def _string(self):
        return ''

    def _initialize(self,*args,**kwargs):
        pass

    def _verify_pass(self,*args):
        pdb.set_trace()

        mobji = args[0].iteration
        verif = mobji >= self.max_iterations
        return verif

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        lc.criterion_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

###############################################################################
### threshold tests if some data target is measured to be both above and below
### a given threshold value, indicating that it crossed that threshold
###############################################################################

class threshold(trajectory_criterion_abstract):

    def __init__(self,*args,**kwargs):
        self._default('name','threshold criterion',**kwargs)
        self._default('below',False,**kwargs)
        self._default('above',False,**kwargs)
        #self._default('threshold',0,**kwargs)
        self._default('threshold',15,**kwargs)
        #self._default('target',None,**kwargs)
        self._default('target','T',**kwargs)
        self._default('targets',['T','A'],**kwargs)
        #self._default('targets',[],**kwargs)
        trajectory_criterion_abstract.__init__(self,*args,**kwargs)

    def _sim_string(self):
        return ''

    def _string(self):
        return ''

    def _initialize(self,*args,**kwargs):
        self.below = False
        self.above = False

    def _verify_pass(self,*args):
        traj = args[0]
        which = lfu.grab_mobj_by_name(self.target,traj)
        if min(which.scalars) <= self.threshold:self.below = True
        if max(which.scalars) >= self.threshold:self.above = True
        return self.below and self.above

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
        trajectory_criterion_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

if __name__ == 'modular_core.criteria.trajectory_criterion':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
    #process_types['conditional'] = (conditional,parse_line)
if __name__ == '__main__':print 'trajectory_criterion of modular_core'










