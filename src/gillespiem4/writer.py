from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext
from cStringIO import StringIO
import numpy,os,sys,re

import pdb



def gibson_lookup(rxns,funcs):
    fnames = tuple(f[0] for f in funcs)
    rcnt = len(rxns)
    alwayses = [d for d in range(rcnt) if rxns[d][0] in fnames]
    lookups = [[] for r in rxns]
    for rdx in range(rcnt):
        # enumerate the species affected by rxns[rdx]
        r = rxns[rdx]
        affected_species = []
        for p in r[2]:
            found = False
            for u in r[1]:
                if u[1] == p[1]:
                    found = True
                    if not u[0] == p[0] and not p[1] in affected_species:
                        affected_species.append(p[1])
            if not found and not p[1] in affected_species:
                affected_species.append(p[1])
        for u in r[1]:
            found = False
            for p in r[2]:
                if p[1] == u[1]:
                    found = True
                    if not p[0] == u[0] and not u[1] in affected_species:
                        affected_species.append(u[1])
            if not found and not u[1] in affected_species:
                affected_species.append(u[1])
        #print 'rxn',r[3],affected_species
        for alw in alwayses:
            fratex = fnames.index(rxns[alw][0])
            func,fuu = funcs[fratex]
            if depends_on(func,fuu,funcs,'time'):
                lookups[rdx].append(alw)
                continue
            for affs in affected_species:
                if depends_on(func,fuu,funcs,affs):
                    lookups[rdx].append(alw)
                    break
        for rdx2 in range(rcnt):
            r2 = rxns[rdx2]
            for u2 in r2[1]:
                if u2[1] in affected_species:
                    if not rdx2 in lookups[rdx]:
                        lookups[rdx].append(rdx2)
    return lookups

def depends_on(fn,fu,fs,d):
    if fu.count(fn) > 0:
        print 'cannot support recursive functions in simulation!'
        raise ValueError
    for othfn,othfu in fs:
        if fu.count(othfn) > 0:
            if depends_on(othfn,othfu,fs,d):
                return True
    return fu.count(d) > 0

def write_nparray(src,name,shape,dtype = 'numpy.double',spacer = '\n\t'):
    predtype = dtype[dtype.find('.')+1:]
    src.write(spacer+'cdef '+predtype+' [')
    src.write(','.join([':']*len(shape))+'] '+name+' = ')
    src.write('numpy.zeros('+str(shape)+',dtype = '+dtype+')')

def write_carray(src,name,shape,dtype = 'double',spacer = '\n\t'):
    src.write(spacer+'cdef '+dtype+' '+name+'[')
    src.write(','.join([str(s) for s in shape])+']')

def write_rxnpropensity(rxn,stargets,funcs):
    uchecks = []
    for u in rxn[1]:
        ucnt,uspec = u
        udex = stargets.index(uspec)
        uline = ['(state['+str(udex)+']-'+str(x)+')' for x in range(ucnt)]
        uline[0] = uline[0].replace('-0','')
        if ucnt > 1:uline.append(str(1.0/ucnt))
        uchecks.append('*'.join(uline))
    try: ratestring = str(float(rxn[0]))
    except ValueError:
        found = False
        for f in funcs:
            if rxn[0] in f[0]:
                ratestring = rxn[0]+'(state)'
                found = True
                break
        if not found:
            ratestring = 'state['+str(stargets.index(rxn[0]))+']'
    uchecks.append(ratestring)
    rxnpropexprsn = '*'.join(uchecks)
    return rxnpropexprsn

def write_extfunc(src,fname,fpath,dom,targets,etime,backsrc):
    if not os.path.exists(fpath):
        print 'missing external signal file: \'%s\'' % fpath
        raise ValueError
    x,y = [],[]
    with open(fpath,'r') as fh:
        extsig = fh.readlines()
        for esl in extsig:
            esl = esl.strip().split(',')
            if esl and esl[0]:
                nx,ny = esl
                x.append(nx)
                y.append(ny)

    dshape = (len(x),)
    write_nparray(src,fname+'_domain',dshape,spacer = '\n')
    write_nparray(src,fname+'_codomain',dshape,spacer = '\n')
    src.write('\n')
    for j in range(len(x)):
        src.write(fname+'_domain['+str(j)+'] = '+x[j]+';')
        if j % 25 == 0 and j > 0:src.write('\n')
        if float(x[j]) > etime:break
    src.write('\n')
    for j in range(len(y)):
        src.write(fname+'_codomain['+str(j)+'] = '+y[j]+';')
        if j % 25 == 0 and j > 0:src.write('\n')
        if float(x[j]) > etime:break
    argstring = 'double['+str(len(targets))+'] state'
    src.write('\ncdef int '+fname+'_lastindex = 0')
    backsrc.write('\n\tglobal '+fname+'_lastindex')
    backsrc.write('\n\t'+fname+'_lastindex = 0')
    src.write('\ncdef inline double '+fname+'('+argstring+'):')

    src.write('\n\tglobal '+fname+'_domain')
    src.write('\n\tglobal '+fname+'_codomain')
    src.write('\n\tglobal '+fname+'_lastindex')
    sdx = targets.index(dom)
    src.write('\n\tcdef double xcurrent = state['+str(sdx)+']')
    src.write('\n\tcdef double domvalue = '+fname+'_domain')
    src.write('['+fname+'_lastindex]')
    src.write('\n\tcdef double codomvalue')
    src.write('\n\twhile xcurrent > domvalue:')
    src.write('\n\t\t'+fname+'_lastindex'+' += 1')
    src.write('\n\t\tdomvalue = '+fname+'_domain')
    src.write('['+fname+'_lastindex]')
    src.write('\n\tcodomvalue = '+fname+'_codomain')
    src.write('['+fname+'_lastindex-1]')
    src.write('\n\treturn codomvalue\n')

def install_cython(extdir,extname,fpaths):
    cwd = os.getcwd()
    os.chdir(extdir)
    exts = cythonize([Extension(extname,fpaths)])
    args = ['clean']
    setup(script_args = args,ext_modules = exts,
        include_dirs = [numpy.get_include()])
    os.makedirs(os.path.join(os.getcwd(),'build'))
    args = ['build_ext','--inplace']
    setup(script_args = args,ext_modules = exts,
        include_dirs = [numpy.get_include()])
    os.chdir(cwd)

def write_cython(src,fpath):
    if os.path.exists(fpath):
        with open(fpath,'r') as fh:
            existing = fh.read()
        if existing == src:
            print 'existing cython code is identical...'
            return
    with open(fpath,'w') as fh:fh.write(src)
      
def read(seq,sx,oc = '(',cc = ')'):
    score = 1
    sx += 1
    while score > 0:
        sx += 1
        if seq[sx] == oc:score += 1
        elif seq[sx] == cc:
            if score > 0:score -= 1
    return sx

def ext_func_name_gen(maxnum = 100):
    fnum = 0
    while fnum < maxnum:
        fnum += 1
        fname = 'extfunc_'+str(fnum)
        yield fname

def write_cython_functions(src,fs,sts,etime):
    def convert(substr):
        if substr in fns or substr in extfns.values():return substr+'(state)'
        #elif substr in self.variables:
        #    return 'state['+str(sts.index(substr))+']'
        elif substr in sts:return 'state['+str(sts.index(substr))+']'
        else:return substr
    backsrc = StringIO()
    fng = ext_func_name_gen()
    fns = tuple(f[0] for f in fs)
    scnt = len(sts)
    extfns = {}
    extstr = 'external_signal('
    for fn,fu in fs:
        escnt = fu.count('external_signal')
        if escnt == 1:
            nfn = next(fng)
            fid = fu.find(extstr)+len(extstr)
            espath,esdom = fu[fid:read(fu,fid,'(',')')].split(',')
            fline = extstr+espath+','+esdom+')'
            extfns[fline] = nfn
            fu = fu.replace(fline,nfn)
            write_extfunc(src,nfn,espath,esdom,sts,etime,backsrc)
        elif escnt > 1:
            print 'gillespiem must support two external signals in a function...'
            raise ValueError
        fsplit = re.split('(\W)',fu)
        fstrng = ''.join([convert(substr) for substr in fsplit])
        src.write('\ncdef inline double '+fn+'(double ['+str(scnt)+'] state):')
        src.write('\n\tcdef double val = '+fstrng)
        selfdex = sts.index(fn)
        src.write('\n\tstate['+str(selfdex)+'] = val')
        src.write('\n\treturn val\n')
    return backsrc

header =\
'''
# cython:profile=False,boundscheck=False,nonecheck=False,wraparound=False,initializedcheck=False,cdivision=True
###################################
# imports:
from libc.math cimport log
from libc.math cimport sin
from libc.math cimport cos
#from libc.stdlib cimport rand
#cdef extern from "limits.h":
#\tint INT_MAX
from numpy import cumprod as cumulative_product
cdef double pi = 3.14159265359
import random,numpy
import time as timemodule
from cython.view cimport array as cvarray

cdef inline double heaviside(double value):
\tif value >= 0.0:return 1.0
\telse:return 0.0

'''

def write_simulator(e,name):
    sps = e.simparameters
    ss,rs,vs,fs = [],[],[],[]
    if 'species' in sps:ss = sps['species']
    if 'reactions' in sps:rs = sps['reactions']
    if 'variables' in sps:vs = sps['variables']
    if 'functions' in sps:fs = sps['functions']
    scnt,rcnt,vcnt,fcnt = len(ss),len(rs),len(vs),len(fs)
    statetargets = ('time',) + tuple(s[0] for s in ss) +\
        tuple(v[0] for v in vs) + tuple(f[0] for f in fs)
    dshape = (len(e.pspacemap.targets),e.pspacemap.captcount)
    sshape = (1 + scnt + vcnt + fcnt,)
    cshape = (len(e.pspacemap.targets),)
    agstring = ','.join(('rseed',)+e.pspace.axes)

    src = StringIO()
    src.write(header)
    backsrc = write_cython_functions(src,fs,statetargets,e.end)
    src.write('\n'*10+'#'*80+'\n')
    src.write('\ncpdef gillespie_run('+agstring+'):')
    src.write('\n'+backsrc.getvalue()+'\n')
    write_nparray(src,'data',dshape)
    write_carray(src,'capture',cshape)
    write_carray(src,'state',sshape)
    src.write('\n\tstate[0] = 0.0')
    for sx in range(scnt):
        sp,si = ss[sx]
        sv = sp if sp in e.pspace.axes else str(si)
        src.write('\n\tstate['+str(sx+1)+'] = '+sv)
    for vx in range(vcnt):
        vn,vv = vs[vx]
        vv = vn if vn in e.pspace.axes else str(vv)
        src.write('\n\tstate['+str(scnt+vx+1)+'] = '+vv)
    for fx in range(fcnt):src.write('\n\t'+fs[fx][0]+'(state)')

    src.write('\n\tprint(\''+'-'*40+'\')')
    src.write('\n\tprint(\'rseed:\','+agstring+')')
    src.write('\n\tprint(\''+'-'*40+'\')')

    src.write('\n\trandom.seed(rseed)')
    src.write('\n\tcdef int totalcaptures = '+str(e.pspacemap.captcount))
    src.write('\n\tcdef int capturecount = 0')
    src.write('\n\tcdef int rtabledex')
    src.write('\n\tcdef int tdex')
    src.write('\n\tcdef int cdex')
    src.write('\n\tcdef double totalpropensity')
    src.write('\n\tcdef double tpinv')
    src.write('\n\tcdef double time = 0.0')
    src.write('\n\tcdef double lasttime = 0.0')
    src.write('\n\tcdef double realtime = 0.0')
    src.write('\n\tcdef double del_t = 0.0')
    src.write('\n\tcdef double randr')
    src.write('\n\tcdef int whichrxn = 0')
    src.write('\n\tcdef int rxncount = '+str(rcnt))
    write_carray(src,'reactiontable',(rcnt,))
    write_carray(src,'propensities',(rcnt,))
    for rdex in range(rcnt):
        rxnpropexprsn = write_rxnpropensity(rs[rdex],statetargets,fs)
        src.write('\n\tpropensities['+str(rdex)+'] = '+rxnpropexprsn)
    write_carray(src,'tdexes',cshape,dtype = 'int')
    for tdx in range(len(e.pspacemap.targets)):
        statedex = statetargets.index(e.pspacemap.targets[tdx])
        src.write('\n\ttdexes['+str(tdx)+'] = '+str(statedex))
    src.write('\n\n\twhile capturecount < totalcaptures:')
    src.write('\n\t\ttotalpropensity = 0.0')
    for x in range(rcnt):
        uchecks = []
        for u in rs[x][1]:
            udex = statetargets.index(u[1])
            uchecks.append('state['+str(udex)+'] >= '+str(u[0]))
        if uchecks:ucheckline = '\n\t\tif '+' and '.join(uchecks)+':'
        else:ucheckline = '\n\t\t'
        src.write(ucheckline)
        src.write('totalpropensity = totalpropensity + propensities['+str(x)+']')
        src.write('\n\t\treactiontable['+str(x)+'] = totalpropensity')
    src.write('\n\n\t\tif totalpropensity > 0.0:')
    src.write('\n\t\t\ttpinv = 1.0/totalpropensity')
    src.write('\n\t\t\tdel_t = -1.0*log(random.random())*tpinv')
    src.write('\n\t\t\trandr = random.random()*totalpropensity')
    src.write('\n\t\t\tfor rtabledex in range(rxncount):')
    src.write('\n\t\t\t\tif randr < reactiontable[rtabledex]:')
    src.write('\n\t\t\t\t\twhichrxn = rtabledex')
    src.write('\n\t\t\t\t\tbreak\n')
    src.write('\n\n\t\telse:')
    src.write('\n\t\t\tdel_t = '+str(e.capture))
    src.write('\n\t\t\twhichrxn = -1')
    src.write('\n\n\t\tstate[0] += del_t')
    src.write('\n\t\trealtime = state[0]')
    src.write('\n\t\twhile lasttime < realtime and capturecount < totalcaptures:')
    src.write('\n\t\t\tstate[0] = lasttime')
    src.write('\n\t\t\tlasttime += '+str(e.capture)+'\n')
    for fx in range(fcnt):src.write('\n\t\t\t'+fs[fx][0]+'(state)')
    src.write('\n\n\t\t\tfor cdex in range('+str(len(e.pspacemap.targets))+'):')
    src.write('\n\t\t\t\tdata[cdex,capturecount] = state[tdexes[cdex]]')
    src.write('\n\t\t\tcapturecount += 1')
    src.write('\n\t\tstate[0] = realtime')
    lookup = gibson_lookup(rs,fs)
    src.write('\n\n\t\tif whichrxn == -1:')
    for rdex in range(rcnt):
        rxnpropexprsn = write_rxnpropensity(rs[rdex],statetargets,fs)
        src.write('\n\t\t\tpropensities['+str(rdex)+'] = '+rxnpropexprsn)
    rwhichrxnmap = range(rcnt)
    for rdex in rwhichrxnmap:
        src.write('\n\t\telif whichrxn == '+str(rdex)+':')
        r = rs[rdex]
        for u in r[1]:
            ucnt,uspec = u
            udex = statetargets.index(uspec)
            src.write('\n\t\t\tstate['+str(udex)+'] -= '+str(ucnt))
        for p in r[2]:
            pcnt,pspec = p
            pdex = statetargets.index(pspec)
            src.write('\n\t\t\tstate['+str(pdex)+'] += '+str(pcnt))
        src.write('\n')
        for look in lookup[rdex]:
            rxnpropexprsn = write_rxnpropensity(rs[look],statetargets,fs)
            src.write('\n\t\t\tpropensities['+str(look)+'] = '+rxnpropexprsn)
    src.write('\n\n\treturn numpy.array(data,dtype = numpy.float)\n')
    src.write('\n'+'#'*80+'\n'*10)
    return src

def func_from_source(extdir,extname,src):
    filepath = os.path.join(extdir,extname+'.pyx')
    write_cython(src,filepath)
    install_cython(extdir,extname,[filepath])
    sys.path.append(extdir)
    ext = __import__(extname)
    return ext.gillespie_run

def get_simulator(e,name,install = True):
    if install:
        src = write_simulator(e,name)
        simfunc = func_from_source(e.home,name,src.getvalue())
    else:
        sys.path.append(e.home)
        ext = __import__(name)
        simfunc = ext.gillespie_run
    return simfunc





