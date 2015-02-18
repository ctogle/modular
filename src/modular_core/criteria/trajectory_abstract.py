import modular_core.libfundamental as lfu

import modular_core.criteria.abstract as ab

import pdb,types,sys

if __name__ == 'modular_core.criteria.trajectory_abstract':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'trajectory_abstract of modular_core'

###############################################################################
### a trajectory criterion tests a condition given one trajectory of data
###############################################################################

class trajectory_abstract(ab.criterion_abstract):

    def __init__(self,*args,**kwargs):
        self._default('name','trajectory criterion',**kwargs)
        ab.criterion_abstract.__init__(self,*args,**kwargs)

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
        ab.criterion_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################











