import modular_core.fundamental as lfu
import modular_core.fitting.routine_abstract as fab
import modular_core.fitting.metrics as mts
import modular_core.data.batch_target as dba

import pdb,os
import scipy.interpolate as sp
import numpy as np

###############################################################################
###
###############################################################################

def interpolate(wrongx,wrongy,rightx,kind = 'linear'):
    interpolation = sp.interp1d(wrongx,wrongy,bounds_error = False,kind = kind)
    righty = interpolation(rightx)
    return righty

class annealing(fab.routine_abstract):

    def _capture_measurements(self,mes):
        bestflags = []
        for mx in range(self.metric_count):
            me = mes[mx]
            metme = self.metric_measurements[mx]
            metme.append(me)
            if not mx == 0:continue
            if me <= min(metme):metbest = True
            else:metbest = False
            bestflags.append(metbest)
        #mthrsh = self.metric_threshold
        mthrsh = 0
        if bestflags.count(True) > mthrsh:
            self.best = True

    def _fitter(self,measures,noisey = 0.2):
        if not self.metric_measurements[0]:fitter = True
        else:
            last = [m[-1] for m in self.metric_measurements]
            better = [(l-m) > (-1.0*noisey*m) for l,m in zip(last,measures)]
            mthrsh = self.metric_threshold
            if better.count(True) >= mthrsh:fitter = True
            else:fitter = False
        if fitter:self._capture_measurements(measures)
        return fitter

    # consider a measurement, undo or keep step?
    def _accept_step(self,information,ran):
        if self.iteration == 0:
            self.best = True
            return True
        else:self.best = False
        if not ran:return False
        runintp = dba.batch_node(
            dshape = self.input_data.dshape,
            targets = self.input_data.targets)
        rundata = information.data[0]
        inpdata = self.input_data.data
        runintp.data[0] = inpdata[0]
        for dx in range(1,rundata.shape[0]):
            rdat = rundata[dx]
            runintp.data[dx] = interpolate(rundata[0],rdat,inpdata[0])

        temp_measurements = []
        for mdx in range(self.metric_count):
            met = self.metrics[mdx]
            m = met._measure(self.input_data,runintp)
            temp_measurements.append(m)

        runintp._stow(v = False)
        fitter = self._fitter(temp_measurements)
        return fitter

    def __init__(self,*args,**kwargs):
        self._default('name','an annealer',**kwargs)
        self._default('max_iteration',100000.0,**kwargs)
        self._default('max_undos',100000,**kwargs)
        self._default('max_runtime',300.0,**kwargs)
        self._default('max_last_best',100000,**kwargs)
        self._default('max_temperature',1000.0,**kwargs)
        self._default('input_data_path',None,**kwargs)
        self._default('weight_scheme','uniform',**kwargs)

        if not hasattr(self,'metrics'):
            wrgs = {'weights':self.weight_scheme}
            self.metrics = [
                mts.difference(**wrgs),
                mts.derivative1(**wrgs),
                mts.derivative2(**wrgs)]
        self.metric_count = len(self.metrics)
        self.metric_threshold = int((self.metric_count/2.1) + 1.0)
        fab.routine_abstract.__init__(self,*args,**kwargs)

    def _initialize(self,*args,**kwargs):
        self.metric_measurements = [[] for m in self.metrics]

        finali = int(self.max_iteration)
        mtemp = self.max_temperature
        lam = -1.0 * np.log(mtemp)/finali
        cooling_domain = np.array(range(finali))
        self.cooling = np.exp(lam*cooling_domain)

        fab.routine_abstract._initialize(self,*args,**kwargs)
        self.max_temperature = mtemp

    def _movement_factor(self):
        self.temperature = self.cooling[self.iteration]
        return self.temperature/self.max_temperature

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

# return valid **kwargs for annealing based on msplit(line)
def parse_line(split,ensem,procs,routs):
    mi,mr,mu,ml,si = split[3:8]
    dpath = lfu.resolve_filepath(split[8])
    eargs = {
        'name':split[0],
        'variety':split[1],
        'max_iteration':int(mi),
        'max_runtime':int(mr),
        'max_undos':int(mu),
        'max_last_best':int(ml),
        'simulations_per_iteration':int(si),
        'pspace_source':split[2],
        'input_data_path':dpath, 
        'metamapfile':split[9],
            }
    return eargs

###############################################################################

if __name__ == 'modular_core.fitting.annealing':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    fab.routine_types['annealing'] = (annealing,parse_line)

###############################################################################










