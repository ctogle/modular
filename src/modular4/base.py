import modular4.mpi as mmpi

import appdirs,os,sys,inspect,logging,time,numpy
import scipy.interpolate as sp

import pdb



class mobject(object):
    '''
    base class for all modular4 classes
    '''

    def _def(self,k,v,**kws):
        '''convenient function for imposing default attributes'''
        if not hasattr(self,k):
            if k in kws:dv = kws[k]
            else:dv = v
            self.__setattr__(k,dv)

def config_path(f = None):
    '''
    return the configuration path associated with modular4
    if a file is provided, return this file concatenated onto the configuration path
    '''
    cp = os.path.join(appdirs.user_config_dir(),'modular4_resources')
    if not f is None:
        fp = os.path.join(cp,f)
        if os.path.isfile(fp):return fp
    return cp

def load_measurements(parsers,base_measurement_class):
    '''look for measurement classes to import'''
    sys.path.append(config_path())
    for rf in os.listdir(config_path()):
        if rf.endswith('.py'):
            rm = __import__(rf.replace('.py',''))
            for mo in dir(rm):
                c = rm.__dict__[mo]
                if inspect.isclass(c):
                    if issubclass(c,base_measurement_class):
                        mtag,mparser = c.tag,c.parse
                        if mtag in parsers:
                            log(5,'overriding measurement parser',mtag)
                        parsers[mtag] = mparser
    if mmpi.root():
        log(5,'loaded measurements')
        for p in parsers:log(5,'>>>',p)

def linterp(oldx,oldy,newx,k = 0):
    interpolation = sp.interp1d(oldx,oldy,bounds_error = True,kind = k)
    if newx.min() < oldx.min():
        tx = 0
        for v in newx:
            if v > oldx.min():break
            else:tx += 1
        newx = newx[tx:]
    if newx.max() > oldx.max():
        tx = 0
        for v in newx:
            if v > oldx.max():break
            else:tx += 1
        newx = newx[:tx]
    newy = interpolation(newx)
    return newx,newy

def uniq(u):
    '''return an ordered subsequence of a sequence without duplicates'''
    r = []
    for ud in u:
        if not ud in r:
            r.append(ud)
    return r

loglevels = {0:10,1:20,2:30,3:40,4:50,5:60}
logstring = '>>log<<|%'+str(len(str(mmpi.size())))+'i|>>'
logging.addLevelName(60,logstring % mmpi.rank())
def log(level,msg,*args):
    '''logging utility function'''
    frame = inspect.stack()[1]
    f = frame[3]
    m = frame[1][frame[1].rfind(os.path.sep)+1:].replace('.py','')
    s = ' %s.%s()-> %s'+' : %s'*len(args)
    sargs = (m,f,msg)+tuple(str(x) for x in args)
    logging.log(loglevels[level],s,*sargs)

def clock(t = None):
    '''return the current date and time in a formatted string'''
    if t is None:t = time.time()
    s = '%Y-%m-%d %H:%M:%S'
    d = time.strftime(s,time.localtime(t))
    return d





