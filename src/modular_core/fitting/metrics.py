import modular_core.fundamental as lfu

import numpy as np
import pdb,math

import matplotlib.pyplot as plt

class measurement(lfu.mobject):

    def __init__(self,*args,**kwargs):
        lfu.mobject.__init__(self,*args,**kwargs)

    # i,j are data nodes with the same shape?
    def _measure(self,i,j):
        return int(i == j)

class ptwise_measurement(measurement):

    def __init__(self,*args,**kwargs):
        measurement.__init__(self,*args,**kwargs)

    def _unif_weights(self,measurements):
        return np.ones((len(measurements),),dtype = np.float)

    def _expo_weights(self,measurements):
        maxweight = 9.0
        x = np.linspace(maxweight,0,len(measurements))
        y = np.exp(-1.0*x)
        y *= maxweight/max(y)
        y += 1.0
        return y

    def _para_weights(self,measurements):
        maxweight = 9.0
        x = np.linspace(maxweight,0,len(measurements))
        y = (x-(max(x)/2.0))**2
        y *= maxweight/max(y)
        y += 1.0
        return y

    # should allow exponential, parabolic, affine, etc...
    def _weight(self,measurements):
        #weights = self._unif_weights(measurements)
        #weights = self._expo_weights(measurements)
        weights = self._para_weights(measurements)
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

class difference(ptwise_measurement):

    def __init__(self,*args,**kwargs):
        self.measurement = self._difference
        ptwise_measurement.__init__(self,*args,**kwargs)

    # i,j are arrays of equal length, 1-1
    def _difference(self,x,i,j,bnds):
        diffs = [abs(i[k]-j[k]) for k in range(*bnds)]
        return diffs

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







class metric(lfu.mobject):

    #ABSTRACT
    '''
    a metric takes two sets of data and runs some method which
    returns one scalar representing some sort of distance
    '''
    def __init__(self, *args, **kwargs):

        self.impose_default('best_measure', 0, **kwargs)
        self.impose_default('display_threshold', 0, **kwargs)
        self.impose_default('display_time', 1.0, **kwargs)
        self.impose_default('prints_for_best', False, **kwargs)
        self.impose_default('acceptance_weight', 1.0, **kwargs)
        self.impose_default('best_advantage', 2.0, **kwargs)
        self.impose_default('best_flag', False, **kwargs)
        self.impose_default('is_heaviest', False, **kwargs)
        lfu.mobject.__init__(self, *args, **kwargs)
        self._children_ = []

    def check_best(self, display = False):
        if self.best_flag:
            if not self.is_heaviest:
                self.acceptance_weight /= self.best_advantage

        self.best_flag = False
        if self.data[0].scalars[-1] == min(self.data[0].scalars):
            self.best_measure = len(self.data[0].scalars) - 1
            self.best_flag = True
            #self.best_flag = True and self.prints_for_best
            if not self.is_heaviest:
                self.acceptance_weight *= self.best_advantage

        if (self.best_flag or display) and self.is_heaviest:
            meas = self.data[0].scalars[-1]
            print ' '.join(['\nmetric', self.name, 'measured best', 
                    str(meas), str(len(self.data[0].scalars) - 1)])
            for pos in self.parent.parameter_space.get_current_position():
                print pos
            #lgd.quick_plot_display(to_fit_to[0], 
            #   to_fit_to[1:] + run_data_interped, 
            #           delay = self.display_time)
            print '\n'

    def measure(self, *args, **kwargs):
        to_fit_to = args[0]
        run_data = args[1]
        dom_weight_max = 5.0
        domain_weights = np.exp(np.linspace(dom_weight_max, 
                            0, len(to_fit_to[0].scalars)))
        #domain_weights = [1 for val in 
        #   np.linspace(0, 1, len(to_fit_to[0].scalars))]
        #domain_weights = np.linspace(dom_weight_max, 
        #               1, len(to_fit_to[0].scalars))
        if self.best_flag:
            self.best_flag = False
            self.acceptance_weight /= 2.0

        try: report_only = kwargs['report_only']
        except KeyError: report_only = False

        labels = [[do.name for do in de] for de in args]
        run_data_domain = run_data[labels[1].index(labels[0][0])]
        try:
            run_data_codomains = [run_data[labels[1].index(
                    labels[0][lab_dex+1])] for lab_dex 
                        in range(len(labels[0][1:]))]
        except ValueError: pdb.set_trace()
        run_data_interped = [scalars(
            label = 'interpolated result - ' + codomain.name, 
            scalars = lm.linear_interpolation(run_data_domain.scalars, 
                    codomain.scalars, to_fit_to[0].scalars, 'linear')) 
                                for codomain in run_data_codomains]
        x_meas_bnds = (0, len(to_fit_to[0].scalars))
        meas = [[diff for diff in kwargs['measurement'](
            fit_to.scalars, interped.scalars, x_meas_bnds, 
            to_fit_to[0].scalars, domain_weights) if not 
                math.isnan(diff)] for fit_to, interped in 
                    zip(to_fit_to[1:], run_data_interped)]
        meas = np.mean([np.mean(mea) for mea in meas])
        if not report_only:
            self.data[0].scalars.append(meas)
            if meas == min(self.data[0].scalars) and\
                    meas < self.data[0].scalars[self.best_measure]:
                self.best_measure = len(self.data[0].scalars) - 1
                #self.best_flag = self.best_measure > self.display_threshold
                #self.best_flag = True and self.prints_for_best
                self.best_flag = True

            if self.best_flag:
                if 'weight' in kwargs.keys():
                    self.acceptance_weight = kwargs['weight']

                else: self.acceptance_weight *= 2.0
            if (self.best_flag or kwargs['display']) and self.is_heaviest:
                print ' '.join(['metric', self.name, 'measured', 
                    str(meas), str(len(self.data[0].scalars))])
                print self.parent.parameter_space.get_current_position()
                lgd.quick_plot_display(to_fit_to[0], 
                    to_fit_to[1:] + run_data_interped, 
                            delay = self.display_time)

        else: return meas

class metric_slope_2nd_derivative(metric):

    def __init__(self, *args, **kwargs):
        if not 'name' in kwargs.keys():
            kwargs['name'] = '2nd derivative metric'
        metric.__init__(self, *args, **kwargs)

    def initialize(self, *args, **kwargs):
        #self.data = scalars_from_labels(['mean 2nd derivative'])
        self.data = ldc.scalars_from_labels(['mean 2nd derivative'])
        metric.initialize(self, *args, **kwargs)

    def measure(self, *args, **kwargs):
        kwargs['measurement'] = self.second_derivative_differences
        return metric.measure(self, *args, **kwargs)

    def second_derivative_differences(self, *args, **kwargs):

        def calc_2nd_deriv(x, y, dex):
            del_x_avg = (x[dex + 1] - x[dex - 1])/2.0
            return (y[dex + 1] - (2*y[dex]) + y[dex - 1])\
                                /((x[dex] - del_x_avg)**2)

        to_fit_to_y = args[0]
        runinterped = args[1]
        bounds = args[2]
        to_fit_to_x = args[3]
        dom_weights = args[4]
        runinterped_slope = [
            calc_2nd_deriv(to_fit_to_x, runinterped, k) 
                for k in range(1, len(to_fit_to_x) -1)]
        to_fit_to_y_slope = [
            calc_2nd_deriv(to_fit_to_x, to_fit_to_y, k) 
                for k in range(1, len(to_fit_to_x) -1)]
        return [weight*abs(to_fit_to_y_slope[k] - runinterped_slope[k]) 
                            for weight, k in zip(dom_weights, range(
                                    bounds[0] + 1, bounds[1] - 2))]

class metric_slope_3rd_derivative(metric):

    def __init__(self, *args, **kwargs):
        if not 'name' in kwargs.keys():
            kwargs['name'] = '3rd derivative metric'
        metric.__init__(self, *args, **kwargs)

    def initialize(self, *args, **kwargs):
        #self.data = scalars_from_labels(['mean 3rd derivative'])
        self.data = ldc.scalars_from_labels(['mean 3rd derivative'])
        metric.initialize(self, *args, **kwargs)

    def measure(self, *args, **kwargs):
        kwargs['measurement'] = self.third_derivative_differences
        return metric.measure(self, *args, **kwargs)

    def third_derivative_differences(self, *args, **kwargs):

        def calc_3rd_deriv(x, y, dex):
            top = (y[dex - 2] - (3*y[dex - 1]) +\
                        (3*y[dex]) + y[dex + 1])
            del_x_avg = ((x[dex + 1] - x[dex - 2]))/3.0
            return top/((x[dex] - del_x_avg)**3)

        to_fit_to_y = args[0]
        runinterped = args[1]
        bounds = args[2]
        to_fit_to_x = args[3]
        dom_weights = args[4]
        runinterped_slope = [
            calc_3rd_deriv(to_fit_to_x, runinterped, k) 
                for k in range(1, len(to_fit_to_x) -1)]
        to_fit_to_y_slope = [
            calc_3rd_deriv(to_fit_to_x, to_fit_to_y, k) 
                for k in range(1, len(to_fit_to_x) -1)]
        return [weight*abs(to_fit_to_y_slope[k] - runinterped_slope[k]) 
                for weight, k in zip(dom_weights, 
                range(bounds[0] + 2, bounds[1] - 2))]

