import anneal
import modular_core.ensemble as mce

class annealer(anneal.annealer):

    def __init__(self,
            initial = None,bounds = None,
            iterations = 10000,tolerance = 0.001):
        f = self.f

        # get x and y from the data file

        pdb.set_trace()

        anneal.annealer.__init__(self,f,x,y,
            initial,bounds,iterations,tolerance)

        self.mcfg = os.path.join(os.getcwd(),'MM_kinetics_means.mcfg')
        self.emng = mce.ensemble_manager()
        self.ensm = emng._add_ensemble('gillespiem')
        self.ensm.mcfg_path = mcfg
        self.ensm._parse_mcfg()
        #self.ensm._run_mcfg(mcfg)

