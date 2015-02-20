import modular_core.libfundamental as lfu
import modular_core.simulationmodule as smd

module_name = 'gillespiem'

class simulation_module(smd.simulation_module):

    def __init__(self,*args,**kwargs):
        self.simulation = simulate
        smd.simulation_module.__init__(self,*args,**kwargs)

# this must be a single argument function because of map_async
def simulate(args):
    print 'gillespiem simulate!',args
    return np.array(dtype = np.float)


