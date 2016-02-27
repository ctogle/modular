import numpy
import PyDSTool as dst

import matplotlib.pyplot as plt

import pdb



def convert_reactions(ss,rs,vs,fs,es):
    vns,vvs = zip(*vs) if vs else ([],[])
    fns,fvs = zip(*fs) if fs else ([],[])
    ens,evs = zip(*es) if es else ([],[])
    def rxr(r):
        if r in vns:return r
        elif r in fns:
            r = fvs[fns.index(r)]
            return '('+str(r)+')'
        else:
            print('reaction rate is neither a function nor a variable!')
            raise ValueError
    def rxustr(rr,ru):
        rxu = ' * '.join((u[1]+'**'+str(u[0]) if u[0] > 1 else u[1] for u in ru))
        rxs = rxr(rr)
        if rxu:rxs = rxu+' * '+rxs
        return rxs
    rhs,afs = {},{}
    for sn,sv in ss:
        if sn in ens:
            base = evs[ens.index(sn)]
            for fn in fns:
                base = base.replace(fn,rxr(fn))
        else:base = ''
        rhs[sn] = base
    for rr,ru,rp,rn in rs:
        term = rxustr(rr,ru)
        uvs,uns = zip(*ru) if ru else ([],[])
        pvs,pns = zip(*rp) if rp else ([],[])
        for sn,sv in ss:
            m = 0
            if sn in uns:m -= uvs[uns.index(sn)]
            if sn in pns:m += pvs[pns.index(sn)]
            if not m == 0:
                smv = str(abs(m))+' * ' if abs(m) > 1 else ''
                sms = ' - ' if m < 0 else ' + '
                rhs[sn] += sms+smv+term
    for sn,sv in ss:
        if rhs[sn].startswith(' + '):
            rhs[sn] = rhs[sn].replace(' + ','',1)
    return rhs,afs

def get_simulator(e):
    esp = e.simparameters
    etime = e.end
    ctime = e.capture
    axes = e.pspace.axes
    rhs,afs = convert_reactions(
        esp['species'],esp['reactions'],
        esp['variables'],esp['functions'],
        esp['equations'])
    dtargs = e.targets
    dtargs[0] = 't'
    dshape = (len(dtargs),int(etime/ctime)+1)

    print('\n'+'-'*50)
    print('converted rhs:')
    for r in rhs:print('\t'+r+': '+rhs[r])
    print('-'*50+'\n')

    algparams   =   {
        'atol': 1e-3,
        #'stiff': False,
        #'max_step': 0.0,  ## CVODE INTERNAL USE ONLY
        #'min_step': 0.0,  ## CVODE INTERNAL USE ONLY
        #'init_step': 0.01,  ## DICTATES DT FOR FIXED OUTPUT MESH
        'init_step':ctime*0.5,  ## DICTATES DT FOR FIXED OUTPUT MESH
            }

    def simf(*args):
        DSargs = dst.args(name = 'dstoolm_test')
        dspars,dsics,dsvarspecs,dsfnspecs = {},{},{},{}
        for vn,vv in esp['variables']:
            if vn in axes:vv = args[axes.index(vn)+1]
            dspars[vn] = vv
        for sn,si in esp['species']:
            if sn in axes:si = args[axes.index(sn)+1]
            dsics[sn] = si
            dsvarspecs[sn] = rhs[sn]
        for fn,ft in afs:dsfnspecs[fn] = ft
        DSargs.algparams = algparams
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





