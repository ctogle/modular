import dstoolm4.writer as dw

import pdb



class simmodule(object):

    name = 'dstoolm'
    
    def parse_species(p,r):
        ss = []
        for l in r:
            s,i = l.split(':')
            ss.append((s.strip(),int(i)))
        return ss

    def parse_reactions(p,r):
        reg = lambda x : (int(x[:x.find(' ')]),x[x.rfind(' '):].strip())
        rs = []
        for l in r:
            rx,rn = l.split(':')
            left,right = rx.split('->')
            left = left.strip().split('+')
            right = right.strip().split('+')
            lleft = left[-1]
            rate = lleft[lleft.rfind(' ')+1:]
            left[-1] = left[-1].replace(rate,'')
            null = ('','nothing','null')              
            used = tuple(reg(x.strip()) for x in left if not x.strip() in null)
            prod = tuple(reg(x.strip()) for x in right if not x.strip() in null)
            rs.append((rate,used,prod,rn.strip()))
        return rs

    def parse_variables(p,r):
        vs = []
        for l in r:
            v,f = l.split(':')
            vs.append((v.strip(),float(f)))
        return vs

    def parse_functions(p,r):
        fs = []
        for l in r:
            fn,fu = l.split(':')
            fs.append((fn.strip(),fu.strip()))
        return fs

    parsers = {
        'species' : parse_species, 
        'reactions' : parse_reactions, 
        'variables' : parse_variables, 
        'functions' : parse_functions, 
            }

    def prepare(e):
        simfunc = dw.get_simulator(e)
        simmodule.overrides['simulate'] = simfunc
        return simfunc

    overrides = {
        'prepare' : prepare, 
        'simulate' : None, 
            }





