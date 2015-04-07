import modular_core.fundamental as lfu
import modular_core.fitting.routine_abstract as fab
import modular_core.fitting.annealing as fan
import modular_core.fitting.metrics as mts
import modular_core.data.batch_target as dba

import pdb,os
import scipy.interpolate as sp
import matplotlib.pyplot as plt
import numpy as np

###############################################################################
### measure will run some number of trajectories, run some post processing
### consider some measurements upon some final targets
### move through pspace minimizing measurements, annealing as fan.annealing does
###############################################################################

class measure(fan.annealing):

    # consider a measurement, undo or keep step?
    def _accept_step(self,information,ran):
        if self.iteration == 0:
            self.best = True
            return True
        else:self.best = False
        if not ran:return False

        temp_measurements = []
        for mdx in range(self.metric_count):
            met = self.metrics[mdx]
            m = met._measure(information)
            temp_measurements.append(m)

        fitter = self._fitter(temp_measurements)
        return fitter

    def __init__(self,*args,**kwargs):
        self._default('name','a measure',**kwargs)
        self._default('simulations_per_iteration',100,**kwargs)
        self._default('measurement',None,**kwargs)
        self._default('max_iteration',100000.0,**kwargs)
        self._default('max_undos',100000,**kwargs)
        self._default('max_runtime',600.0,**kwargs)
        self._default('max_last_best',100000,**kwargs)

        wrgs = {'process':self.measurement}
        self.metrics = [mts.postprocess_measurement(**wrgs)]
        fan.annealing.__init__(self,*args,**kwargs)

###############################################################################
###############################################################################

# return valid **kwargs for measure based on msplit(line)
def parse_line(split,ensem,procs,routs):

    # create a k-means post process to use later...
    ###
    pvar = 'k-means'
    spl = split[8]
    spl = lfu.msplit(spl[spl.find('<')+1:spl.find('>')],'%')

    import modular_core.postprocessing.process_abstract as lpp
    ptypes = lpp.process_types
    pargs = ptypes[pvar][1](spl,None,[],[])
    pproc = ptypes[pvar][0](**pargs)
    pproc._target_settables(0,ensem)
    ###

    mi,mr,mu,ml,si = split[3:8]
    eargs = {
        'name':split[0],
        'variety':split[1],
        'max_iteration':int(mi),
        'max_runtime':int(mr),
        'max_undos':int(mu),
        'max_last_best':int(ml),
        'simulations_per_iteration':int(si),
        'pspace_source':split[2],
        'measurement':pproc, 
        'metamapfile':split[9], 
            }
    return eargs

###############################################################################

if __name__ == 'modular_core.fitting.measurement':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    fab.routine_types['measure'] = (measure,parse_line)

###############################################################################









 
