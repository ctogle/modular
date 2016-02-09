import modular4.measurement as mme
import math,numpy





class measurement_bypspace(mme.measurement):

    tag = 'bypspace'

    @staticmethod
    def parse(p,l):
        ls = tuple(x.strip() for x in l.split(':'))
        kws = {
            'input_scheme' : ls[1],
            'targets' : [x.strip() for x in ls[2].split(',')],
                }
        return measurement_bypspace(**kws)

    def __init__(self,*ags,**kws):
        mme.measurement.__init__(self,*ags,**kws)
        self._def('name','bypspace_measurement',**kws)
        self._def('bins',None,**kws)
        self._def('domain',None,**kws)
        self._def('targets',None,**kws)

    def set_targets(self,inputs,pspace):
        cinputs = []
        if self.targets == ['all']:self.dtargets = inputs[:]
        else:self.dtargets = [t for t in self.dtargets if t in inputs]
        cinputs = ['pspace location index']+list(pspace.axes)+self.dtargets
        return mme.measurement.set_targets(self,cinputs,pspace)

    def measure(self,zdata,axes,traj,**kws):
        ptrajaxvals = zip(*traj)
        dvals = [[] for x in range(len(self.dtargets))]
        for isrc in self.input_sources:
            for tx in range(len(traj)):
                mtdat = zdata[isrc-1][1][tx]
                if len(mtdat) != 1:
                    print 'unknown situation'
                    raise ValueError
                else:
                    mdat,mtgs,mloc = mtdat[0]
                    for dx in range(len(mtgs)):
                        if mtgs[dx] in self.targets:
                            dvals[dx].append(mdat[dx,-1])
        dshape = (len(self.targets),len(traj))
        odata = numpy.zeros(dshape,dtype = numpy.float)
        odata[0] = numpy.array([x for x in range(len(traj))])
        for x in range(len(axes)):odata[x+1] = numpy.array(ptrajaxvals[x])
        for x in range(len(self.dtargets)):
            odata[x+len(axes)+1] = numpy.array(dvals[x])
        return odata,self.targets,{'header':'pypspace'}





