import modular_core.fundamental as lfu
import modular_core.fitting.routine_abstract as fab

###############################################################################
###
###############################################################################

class explorer(fab.routine_abstract):

    def __init__(self,*args,**kwargs):
        self._default('name','an explorer',**kwargs)
        fab.routine_abstract.__init__(self,*args,**kwargs)

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










