import modular_core.fundamental as lfu
import modular_core.io.pkl as pk
import modular_core.data.batch_target as dba

from cStringIO import StringIO
import pdb,os,sys,traceback

if __name__ == 'modular_core.parameterspace.metamap':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
if __name__ == '__main__':print 'metamap of modular_core'

###############################################################################
### a metamap helps maintain persistent mapping info for a model
###############################################################################

class metalocation(object):

    def _save(self,metas):
        # stow all data pools;output self in a readable format
        metas.write('\n'+'-'*100+'\nmetalocation : \n'+self.location_string)
        for dchild in self.simulation_pool.children:
            dchild._stow(v = True)
        #metas.write('\nsimulation_pool at : ')
        #pdb.set_trace()
        #metas.write('\n'+'='*100+'\n')

    def __init__(self,location_string,**kwargs):
        self.location_string = location_string
        self.simulation_pool = dba.batch_node(metapool = True)
    
    def _log_simulation_data(self,loc_pool):
        # if the shape of this loc_pool matches the shape of any previously
        # logged data pools, merge loc_pool with the existing pool
        # otherwise, add loc_pool as a new base pool for later sims
        for sp in self.simulation_pool.children:
            if not sp.dshape[1:] == loc_pool.dshape[1:]:continue
            if not sp.targets == loc_pool.targets:continue
            sp._merge_data(loc_pool)
            print 'merged some data'
            return
        self.simulation_pool._add_child(loc_pool)

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
        self._load()

    def _load(self):
        if os.path.isfile(self.mappath):
            proxy = pk.load_pkl_object(self.mappath)
            assert proxy.uniqueness == self.uniqueness,\
                'existing metamap file\'s uniqueness does not match!'
            self.entries = proxy.entries
            self.location_strings = proxy.location_strings
        else:
            self.entries = {}
            self.location_strings = []

    # output self in a recoverable, human readable format
    def _save(self):
        metastring = StringIO()
        for mloc in self.location_strings:
            self.entries[mloc]._save(metastring)
        self.metastring = metastring.getvalue()
        parent = self.parent
        self.parent = None
        self._sanitize()
        pk.save_pkl_object(self,self.mappath)
        self.parent = parent

    def _log(self,loc_str,loc_pool):
        if not loc_str in self.location_strings:
            metaloc = metalocation(loc_str)
            self.entries[loc_str] = metaloc
            self.location_strings.append(loc_str)
        else:metaloc = self.entries[loc_str]
        metaloc._log_simulation_data(loc_pool)

    def _recover_location(self,loc_str):
        mloc = self.entries[loc_str]
        if not len(mloc.simulation_pool.children) == 1:
            print 'metamap incomplete... defaulting to something...'
        loc_pool = mloc.simulation_pool.children[0]
        return loc_pool

    def _trajectory_count(self,loc_str,dshape):
        if loc_str in self.location_strings:
            mloc = self.entries[loc_str]
            for sp in mloc.simulation_pool.children:
                if dshape[1:] == sp.dshape[1:]:
                    return sp.dshape[0]
            return 0
        else:return 0

###############################################################################
###############################################################################










