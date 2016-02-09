import modular4.measurement as mme
import math,numpy

import pdb





class means(mme.measurement):

    tag = 'means'

    @staticmethod
    def parse(p,l):
        ls = tuple(x.strip() for x in l.split(':'))
        u,v = ls[2].split(' of ')
        kws = {
            'input_scheme' : ls[1],
            'transient' : ls[-1],
            'bincount' : int(ls[3]),
            'bindomain' : v,
            'meandomain' : u.split(' and '),
                }
        return means(**kws)

    def __init__(self,*ags,**kws):
        mme.measurement.__init__(self,*ags,**kws)
        self._def('name','means_measurement',**kws)
        self._def('transient',0.0,**kws)
        self._def('fillvalue',-100.0,**kws)
        self._def('bincount',1,**kws)
        self._def('bindomain',None,**kws)
        self._def('meandomain',None,**kws)

    def set_targets(self,inputs,pspace):
        cinputs = []
        for i in inputs:cinputs.append(i+'-mean')
        if not self.bindomain in inputs:x = inputs[0]
        else:x = self.bindomain

        pdb.set_trace()

        y,z = self.correldomain
        if not y in inputs or not z in inputs:
            print 'correlation targets are not found in input targets'
            raise ValueError
        cinputs = [x,y+','+z+'-correlation',y+','+z+'-pvalue']

        return mme.measurement.set_targets(self,cinputs,pspace)

    def measure(self,data,targs,psploc,**kws):
        verify = lambda v : self.fillvalue if math.isnan(v) else v

        y,z = self.correldomain

        b,v = self.bin_data(data,targs,self.bindomain,[y,z],self.bincount)

        cpvs = numpy.array([correl(v[k,0,:],v[k,1,:]) for k in range(b.size)])

        data = numpy.array([b,
            [verify(val) for val in cpvs[:,0]],
            [verify(val) for val in cpvs[:,1]]],dtype = numpy.float)

        return data,self.targets,{'header':str(psploc)}






