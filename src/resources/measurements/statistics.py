import modular4.measurement as mme
import math,numpy

import pdb





class stats(mme.measurement):

    tag = 'statistics'

    @staticmethod
    def parse(p,l):
        ls = tuple(x.strip() for x in l.split(':'))
        u,v = ls[2].split(' of ')
        kws = {
            'input_scheme' : ls[1],
            'transient' : ls[-1],
            'bincount' : int(ls[3]),
            'domain' : v,
            'codomain' : [y.strip() for y in u.split(',')],
                }
        return stats(**kws)

    def __init__(self,*ags,**kws):
        mme.measurement.__init__(self,*ags,**kws)
        self._def('name','statistics_measurement',**kws)
        self._def('transient',0.0,**kws)
        self._def('fillvalue',-100.0,**kws)
        self._def('bincount',1,**kws)
        self._def('domain',None,**kws)
        self._def('codomain',[],**kws)

    def set_targets(self,inputs,pspace):
        if not self.domain in inputs:x = inputs[0]
        else:x = self.domain
        cinputs = [x]
        for i in inputs:
            if i in self.codomain:
                cinputs.append(i+'_mean')
                cinputs.append(i+'_median')
                cinputs.append(i+'_stddev')
                cinputs.append(i+'_+1stddev')
                cinputs.append(i+'_-1stddev')
                cinputs.append(i+'_variance')
                cinputs.append(i+'_coefficient_of_variation')
        return mme.measurement.set_targets(self,cinputs,pspace)

    def measure(self,data,targs,psploc,**kws):
        #verify = lambda v : self.fillvalue if math.isnan(v) else v
        b,v = self.bin_data(data,targs,self.domain,self.codomain,self.bincount)
        odata = numpy.zeros((len(self.targets),self.bincount),dtype = numpy.float)
        for x in range(len(self.codomain)):
            tx = self.targets.index(self.codomain[x]+'_mean')
            tv = v[:,x,:]
            mn = numpy.mean(tv,axis = 1)
            md = numpy.median(tv,axis = 1)
            sd = numpy.std(tv,axis = 1)
            mnpsd = mn+sd
            mnmsd = mn-sd
            cv = sd/mn
            odata[tx] = mn
            odata[tx+1] = md
            odata[tx+2] = sd
            odata[tx+3] = mnpsd
            odata[tx+4] = mnmsd
            odata[tx+5] = cv
        odata[0] = b
        return odata,self.targets,{'header':str(psploc)}





