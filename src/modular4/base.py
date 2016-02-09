import appdirs,os,sys,inspect

import pdb



class mobject(object):

    def _def(self,k,v,**kws):
        if not hasattr(self,k):
            if k in kws:dv = kws[k]
            else:dv = v
            self.__setattr__(k,dv)

def config_path(f = None):
    cp = os.path.join(appdirs.user_config_dir(),'modular4_resources')
    if not f is None:
        fp = os.path.join(cp,f)
        if os.path.isfile(fp):return fp
    return cp

def load_measurements(parsers,base_measurement_class):
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
                            print('overriding measurement parser: %s' % mtag)
                        parsers[mtag] = mparser
    print('loaded measurements:')
    for p in parsers:print('>>> :\t%s' % p)

    



