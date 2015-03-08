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

class metalocation(lfu.mobject):

    def __init__(self,location_string,**kwargs):
        self.location_string = location_string
        lfu.mobject.__init__(self,**kwargs)
    
    def _log_zeroth(self,zeroth):
        pdb.set_trace()
    
    def _log_simulation_data(self,loc_pool):
        pdb.set_trace()

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
        lfu.mobject.__init__(self,**kwargs)
        self.entries = {}
        self.location_strings = []

    def _log(self,loc_str,zeroth,loc_pool):
        if not loc_str in self.location_strings:
            metaloc = metalocation(loc_str)
            self.entries[loc_str] = metaloc
            self.location_strings.append(loc_str)
        else:metaloc = self.entries[loc_str]
        metaloc._log_zeroth(zeroth)
        metaloc._log_simulation_data(loc_pool)

###############################################################################
###############################################################################










