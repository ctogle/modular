import modular_core.fundamental as lfu

import numpy as np
import pdb,math

###############################################################################
###
###############################################################################

class measurement(lfu.mobject):

    def __init__(self,*args,**kwargs):
        lfu.mobject.__init__(self,*args,**kwargs)

    # i,j are data nodes with the same shape?
    def _measure(self,i,j):
        return int(i == j)

class postprocess_measurement(measurement):

    def __init__(self,*args,**kwargs):
        self._default('process',None,**kwargs)
        self._default('direction','maximize',**kwargs)
        measurement.__init__(self,*args,**kwargs)

    # i is the information node of a fit routine
    def _measure(self,i):
        #me = self.process.method(i,None)
        me = self.process.__getattribute__(self.process.method)(i,None)

        ### HACK
        crunch = np.mean(me.data[1])
        ### HACK

        if self.direction == 'maximize':
            meas = 1.0/crunch
        else:meas = crunch
        return meas

class ptwise_measurement(measurement):

    def __init__(self,*args,**kwargs):
        self._default('weights','uniform',**kwargs)
        if self.weights == 'uniform':self._weights = self._unif_weights
        if self.weights == 'affine':self._weights = self._affi_weights
        if self.weights == 'parabolic':self._weights = self._para_weights
        if self.weights == 'exponential':self._weights = self._expo_weights
        measurement.__init__(self,*args,**kwargs)

    def _unif_weights(self,measurements):
        return np.ones((len(measurements),),dtype = np.float)

    def _affi_weights(self,measurements):
        leng = len(measurements)
        x = np.linspace(0,leng,leng)
        b = 5.0
        m = -4.0/x[-1]
        y = m*x + b
        return y

    def _expo_weights(self,measurements):
        maxweight = 9.0
        x = np.linspace(maxweight,0,len(measurements))
        y = np.exp(-1.0*x)
        y *= maxweight/max(y)
        y += 1.0
        return y

    def _para_weights(self,measurements):
        maxweight = 4.0
        x = np.linspace(maxweight,0,len(measurements))
        y = (x-(max(x)/2.0))**2
        y *= maxweight/max(y)
        y += 1.0
        return y

    # should allow exponential, parabolic, affine, etc...
    def _weight(self,measurements):
        weights = self._weights(measurements)
        zwm = zip(weights,measurements)
        return [w*m for w,m in zwm if not math.isnan(m)]

    # i,j are batch_nodes with the same dshape and targets
    # call measurement on i,j[1:] 1-1 for ptwise
    def _measure(self,i,j):
        bnds = (0,i.dshape[-1])
        tmeasures = []
        x = i.data[0]
        for t in range(1,i.dshape[-2]):
            idat = i.data[t]
            jdat = j.data[t]
            measures = self._weight(self.measurement(x,idat,jdat,bnds))
            tmeasures.append(np.mean(measures))
        meas = np.mean(tmeasures)
        return meas

###############################################################################

class difference(ptwise_measurement):

    def __init__(self,*args,**kwargs):
        self.measurement = self._difference
        ptwise_measurement.__init__(self,*args,**kwargs)

    # i,j are arrays of equal length, 1-1
    def _difference(self,x,i,j,bnds):
        diffs = [abs(i[k]-j[k]) for k in range(*bnds)]
        return diffs

###############################################################################

class derivative1(ptwise_measurement):

    def __init__(self,*args,**kwargs):
        self.measurement = self._slope
        ptwise_measurement.__init__(self,*args,**kwargs)

    def _point_derive(self,x,k,bnds,d):
        dydx = (k[d] - k[d - 1])/(x[d] - x[d - 1]) 
        return dydx

    def _derive(self,x,k,bnds):
        deriv = [self._point_derive(x,k,bnds,d) 
            for d in range(bnds[0]+1,bnds[1])]
        return deriv
        
    # x,i,j are arrays of equal length, 1-1
    def _slope(self,x,i,j,bnds):
        islope = self._derive(x,i,bnds)
        jslope = self._derive(x,j,bnds)
        slopes = [abs(islope[k]-jslope[k]) 
            for k in range(bnds[0],bnds[1]-1)]
        return slopes

###############################################################################

class derivative2(ptwise_measurement):

    def __init__(self,*args,**kwargs):
        self.measurement = self._concavity
        ptwise_measurement.__init__(self,*args,**kwargs)

    def _point_derive(self,x,k,bnds,d):
        delx = (x[d+1]-x[d-1])/2.0
        ddyddx = (k[d+1]-(2*k[d])+k[d-1])/((x[d]-delx)**2)
        return ddyddx

    def _derive(self,x,k,bnds):
        deriv = [self._point_derive(x,k,bnds,d) 
            for d in range(bnds[0]+1,bnds[1]-1)]
        return deriv
        
    # x,i,j are arrays of equal length, 1-1
    def _concavity(self,x,i,j,bnds):
        islope = self._derive(x,i,bnds)
        jslope = self._derive(x,j,bnds)
        slopes = [abs(islope[k]-jslope[k]) 
            for k in range(bnds[0]+1,bnds[1]-2)]
        return slopes

###############################################################################










