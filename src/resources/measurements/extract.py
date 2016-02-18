import modular4.measurement as mme
import math,numpy

import pdb





class extract(mme.measurement):

    tag = 'extract'

    @staticmethod
    def parse(p,l):
        #extract : 0;location : t,a,r,g,e,t,s : bins : trajectories : transient
        #extract : 0;location : all : all : all : 0.0
        ls = tuple(x.strip() for x in l.split(':'))
        kws = {
            'input_scheme' : ls[1],
            'transient' : ls[-1],
            'bincount' : ls[3],
            'trajcount' : ls[4],
            'codomain' : [y.strip() for y in ls[2].split(',')],
                }
        return extract(**kws)

    def __init__(self,*ags,**kws):
        mme.measurement.__init__(self,*ags,**kws)
        self._def('name','extraction_measurement',**kws)
        self._def('transient',0.0,**kws)
        self._def('bincount',None,**kws)
        self._def('trajcount',None,**kws)
        self._def('codomain',[],**kws)

    def set_targets(self,inputs,pspace):
        if self.codomain == ['all']:
            self.codomain = [x for x in inputs]
        cinputs = []
        for i in inputs:
            if i in self.codomain:
                cinputs.append(i+'-extract')
        return mme.measurement.set_targets(self,cinputs,pspace)

    def measure(self,data,targs,psploc,**kws):
        if self.bincount is None or self.bincount == 'all':
            self.bincount = data.shape[2]
        else:self.bincount = int(self.bincount)
        if self.trajcount is None or self.trajcount == 'all':
            self.trajcount = data.shape[0]
        else:self.trajcount = int(self.trajcount)
        dshape = (int(self.trajcount),len(self.targets),int(self.bincount))
        odata = numpy.zeros(dshape,dtype = numpy.float)
        for x in range(len(self.codomain)):
            codom = self.codomain[x]
            tv = [t[:t.find('-extract')] for t in self.targets]
            odata[:,tv.index(codom),:] = data[:self.trajcount,x,:]
        return odata,self.targets,{'header':str(psploc)}





