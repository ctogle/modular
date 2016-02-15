import modular4.base as mb
import math,numpy

import pdb





parsers = {}

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
            mb.log(5,'must bin by time')
            raise ValueError
        bins = xs[0].copy()
        if bins.size < bcnt:
            mb.log(5,'fewer data entries than bins; reduce bin count!')
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
        vpb = v.shape[0]/b.shape[0]
        if not int(vpb) == float(vpb):
            mb.log(5,'incompatible bin count for end/capture specification')
            raise ValueError
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





