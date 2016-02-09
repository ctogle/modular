import modular4.base as mb
import math,numpy
from scipy.stats import pearsonr as correl

import pdb





class measurement(mb.mobject):

    def _targets(self,inputs):
        '''return the names of the outputs based on the names of the inputs'''
        for tx in range(len(self.targets)):self.targets.pop(0)
        for t in inputs:self.targets.append(t)
        return self.targets

    def __call__(self,*ags,**kws):
        return self.measure(*ags,**kws)

    def __init__(self,*ags,**kws):
        self._def('name','ameasurement',**kws)
        self._def('targets',[],**kws)
        self._def('input_scheme','0;trajectory',**kws)
        isch = self.input_scheme
        ishps = isch[isch.rfind(';')+1:].split(',')
        isrcs = isch[:isch.rfind(';')].split(',')
        self.input_sources = tuple(int(x) for x in isrcs)
        self.input_shapes = tuple(x.strip() for x in ishps)

    def bin_data(self,data,targs,x,ys,bcnt):
        xshape = (data.shape[0],data.shape[2])
        ysshape = (data.shape[0],len(ys),data.shape[2])
        xs = numpy.zeros(shape = xshape,dtype = numpy.float)
        yss = numpy.zeros(shape = ysshape,dtype = numpy.float)
        for trajdx in range(data.shape[0]):
            for targdx in range(data.shape[1]):
                targ = targs[targdx]
                if targ == x:xs[trajdx][:] = data[trajdx][targdx]
                if targ in ys:
                    yss[trajdx][ys.index(targ)][:] = data[trajdx][targdx]

        if not x == 'time':
            print('must bin by time')
            raise ValueError
        bins = xs[0].copy()
        if bins.size < bcnt:
            print('\nfewer data entries than bins; reduce bin count!\n')
            raise ValueError

        vals = yss.transpose((2,1,0))
        cx = len(bins)/bcnt
        b = bins[::cx]
        b = numpy.array([(b[x-1]+b[x])/2.0 for x in range(1,b.size)])
        newvlen = cx*vals.shape[2]
        v = numpy.zeros((bcnt,yss.shape[1],newvlen),dtype = numpy.float)
        for bx in range(bcnt):
            for tx in range(yss.shape[1]):
                v[bx][tx] = vals[bx*cx:(bx+1)*cx,tx].reshape((1,newvlen))
        return b,v

    def measure(self,data,targs,psp,**kws):
        return data,targs,psp

    def seek_targets(self,inputs):
        '''return the names of the input targets'''
        ts = []
        for i in self.input_sources:
            ts.extend(inputs[i-1].targets)
        return ts

    def set_targets(self,inputs,pspace):
        return self._targets(inputs)

def parse_correlation(p,l):
    ls = tuple(x.strip() for x in l.split(':'))
    u,v = ls[2].split(' of ')
    kws = {
        'input_scheme' : ls[1],
        'transient' : ls[-1],
        'bincount' : int(ls[3]),
        'bindomain' : v,
        'correldomain' : u.split(' and '),
            }
    return measurement_correlation(**kws)

class measurement_correlation(measurement):

    def __init__(self,*ags,**kws):
        measurement.__init__(self,*ags,**kws)
        self._def('name','correlation_measurement',**kws)
        self._def('transient',0.0,**kws)
        self._def('fillvalue',-100.0,**kws)
        self._def('bincount',1,**kws)
        self._def('bindomain',None,**kws)
        self._def('correldomain',None,**kws)

    def set_targets(self,inputs,pspace):
        cinputs = []
        for i in inputs:
            cinputs.append(i+'-correlation')
        if not self.bindomain in inputs:x = inputs[0]
        else:x = self.bindomain
        y,z = self.correldomain
        if not y in inputs or not z in inputs:
            print 'correlation targets are not found in input targets'
            raise ValueError
        cinputs = [x,y+','+z+'-correlation',y+','+z+'-pvalue']
        return measurement.set_targets(self,cinputs,pspace)

    def measure(self,data,targs,psploc,**kws):
        verify = lambda v : self.fillvalue if math.isnan(v) else v
        y,z = self.correldomain
        b,v = self.bin_data(data,targs,self.bindomain,[y,z],self.bincount)
        cpvs = numpy.array([correl(v[k,0,:],v[k,1,:]) for k in range(b.size)])
        data = numpy.array([b,
            [verify(val) for val in cpvs[:,0]],
            [verify(val) for val in cpvs[:,1]]],dtype = numpy.float)
        return data,self.targets,{'header':str(psploc)}





def parse_bypspace(p,l):
    ls = tuple(x.strip() for x in l.split(':'))
    kws = {
        'input_scheme' : ls[1],
        'targets' : [x.strip() for x in ls[2].split(',')],
            }
    return measurement_bypspace(**kws)

class measurement_bypspace(measurement):

    def __init__(self,*ags,**kws):
        measurement.__init__(self,*ags,**kws)
        self._def('name','bypspace_measurement',**kws)
        self._def('bins',None,**kws)
        self._def('domain',None,**kws)
        self._def('targets',None,**kws)

    def set_targets(self,inputs,pspace):
        cinputs = []
        if self.targets == ['all']:self.dtargets = inputs[:]
        else:self.dtargets = [t for t in self.dtargets if t in inputs]
        #cinputs = ['pspace location index']+list(pspace.axes)+cinputs+['reducer']
        cinputs = ['pspace location index']+list(pspace.axes)+self.dtargets
        return measurement.set_targets(self,cinputs,pspace)

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
        #self.surf_targets = ['parameter space location index'] + self.dater_ids
        #bnode = self._init_data(dshape,self.capture_targets,
        #    pspace_axes = self.axis_labels,surface_targets = self.surf_targets)
        return odata,self.targets,{'header':'pypspace'}




parsers = {
    'correlation' : parse_correlation,
    'reorganize' : parse_bypspace,
        }





