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

        ##########
        #runintp = dba.batch_node(
        #    dshape = self.input_data.dshape,
        #    targets = self.input_data.targets)
        #rundata = information.data[0]
        #inpdata = self.input_data.data
        #runintp.data[0] = inpdata[0]
        #for dx in range(1,rundata.shape[0]):
        #    rdat = rundata[dx]
        #    runintp.data[dx] = interpolate(rundata[0],rdat,inpdata[0])
        ##########
        
        print ' must measure the run data in information ' 
        pdb.set_trace()

        temp_measurements = []
        for mdx in range(self.metric_count):
            met = self.metrics[mdx]
            ##########
            #m = met._measure(self.input_data,runintp)
            ##########       
            pdb.set_trace()
            m = met._measure()
            temp_measurements.append(m)

        ##########
        #runintp._stow(v = False)
        ##########


        fitter = self._fitter(temp_measurements)
        return fitter

    def __init__(self,*args,**kwargs):
        self._default('name','a measure',**kwargs)
        self._default('simulations_per_iteration',1,**kwargs)
        #self._default('max_iteration',100000.0,**kwargs)
        #self._default('max_undos',100000,**kwargs)
        #self._default('max_runtime',300.0,**kwargs)
        #self._default('max_last_best',100000,**kwargs)
        #self._default('max_temperature',1000.0,**kwargs)

        #self._default('weight_scheme','uniform',**kwargs)
        wrgs = {'processtype':'k-means'}
        self.metrics = [mts.postprocess_measurement(**wrgs)]

        self.metric_count = len(self.metrics)
        self.metric_threshold = int((self.metric_count/2.1) + 1.0)
        fan.annealing.__init__(self,*args,**kwargs)

###############################################################################
###############################################################################

# return valid **kwargs for measure based on msplit(line)
def parse_line(split,ensem,procs,routs):
    dpath = lfu.resolve_filepath(split[3])
    #pdb.set_trace()
    eargs = {
        'name':split[0],
        'variety':split[1],
        'pspace_source':split[2],
        #'input_data_path':dpath, 
        'metamapfile':split[4], 
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









 
