import numpy
import PyDSTool as dst

import matplotlib.pyplot as plt

import pdb



def convert_reactions(ss,rs,vs,fs):
    vns,vvs = zip(*vs)
    fns,fvs = zip(*fs)
    def rxr(r):
        if r in vns:return r
        elif r in fns:
            r = fvs[fns.index(r)]
            return '('+str(r)+')'
        else:
            print('reaction rate is neither a function nor a variable!')
            raise ValueError
    def rxustr(rr,ru):
        rxu = '*'.join((u[1] for u in ru))
        rxs = rxr(rr)
        if rxu:rxs = rxu+'*'+rxs
        return rxs
    rhs,afs = {},{}
    for sn,sv in ss:rhs[sn] = ''
    for rr,ru,rp,rn in rs:
        term = rxustr(rr,ru)
        for uv,un in ru:rhs[un] += '-'+(str(uv) if uv > 1 else '')+term
        for pv,pn in rp:rhs[pn] += '+'+(str(pv) if pv > 1 else '')+term
    for sn,sv in ss:
        if rhs[sn].startswith('+'):
            rhs[sn] = rhs[sn].replace('+','',1)
    return rhs,afs

def get_simulator(e):
    esp = e.simparameters
    etime = e.end
    ctime = e.capture
    axes = e.pspace.axes
    rhs,afs = convert_reactions(
        esp['species'],esp['reactions'],
        esp['variables'],esp['functions'])
    dtargs = e.targets
    dtargs[0] = 't'
    dshape = (len(dtargs),int(etime/ctime)+1)

    print('\n'+'-'*50)
    print('converted rhs:')
    for r in rhs:print('\t'+r+': '+rhs[r])
    print('-'*50+'\n')

    def simf(*args):
        DSargs = dst.args(name='dstoolm_test')
        dspars,dsics,dsvarspecs,dsfnspecs = {},{},{},{}
        for vn,vv in esp['variables']:
            if vn in axes:vv = args[axes.index(vn)+1]
            dspars[vn] = vv
        for sn,si in esp['species']:
            if sn in axes:si = args[axes.index(sn)+1]
            dsics[sn] = si
            dsvarspecs[sn] = rhs[sn]
        for fn,ft in afs:dsfnspecs[fn] = ft
        DSargs.pars = dspars
        DSargs.fnspecs = dsfnspecs
        DSargs.varspecs = dsvarspecs
        DSargs.ics = dsics
        DSargs.tdomain = [0,etime]
        ode  = dst.Generator.Vode_ODEsystem(DSargs)
        traj = ode.compute('trajectory')
        pts  = traj.sample(dt = ctime)
        data = numpy.zeros(dshape,dtype = numpy.float)
        for dtx in range(len(dtargs)):
            data[dtx] = pts[dtargs[dtx]]
        return data
    return simf





