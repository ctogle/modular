import modular_core.fundamental as lfu

import pdb,os

if __name__ == 'modular_core.parameterspace.metamap':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
if __name__ == '__main__':print 'metamap of modular_core'

###############################################################################
### a metamap helps maintain persistent mapping info for a model
###############################################################################


class metamap(lfu.mobject):
    # metamap needs to know every possible axis for this model

    # uniqueness should be an object to compare to to verify model identity
    # it should be provided by the simulation module
    # it should change if the model of a simulation changes
    # it should not change if the models run_parameters vary
    # it is a pspace location independent representation of the model
    def __init__(self,*args,**kwargs):
        self._default('uniqueness',None,**kwargs)
        self._default('mapfile','pspmap.mmap',**kwargs)
        self.mappath = os.path.join(lfu.get_mapdata_pool_path(),self.mapfile)
        lfu.mobject.__init__(self,*args,**kwargs)

    def _log(self,loc_str,zeroth,loc_pool):

        pdb.set_trace()

###############################################################################
###############################################################################










