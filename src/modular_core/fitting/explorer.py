import modular_core.fundamental as lfu
import modular_core.fitting.routine_abstract as fab

import pdb

###############################################################################
###
###############################################################################

class explorer(fab.routine_abstract):

    # consider a measurement, undo or keep step?
    def _accept_step(self,information,ran):
        if not ran:return False
        pdb.set_trace()
        return True

    def __init__(self,*args,**kwargs):
        self._default('name','an explorer',**kwargs)
        fab.routine_abstract.__init__(self,*args,**kwargs)

    def _target_settables(self,*args,**kwargs):
        capture_targetable = self._targetables(*args,**kwargs)
        self.target_list = capture_targetable[:]
        self.capture_targets = self.target_list 
        fab.routine_abstract._target_settables(self,*args,**kwargs)

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self._target_settables(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        fab.routine_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

# return valid **kwargs for explorer based on msplit(line)
def parse_line(split,ensem,procs,routs):
    eargs = {
        'name':split[0],
        'variety':split[1],
            }
    return eargs

###############################################################################

if __name__ == 'modular_core.fitting.explorer':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    fab.routine_types['explorer'] = (explorer,parse_line)

###############################################################################










