import gillespiem4.writer as gw

import pdb



class simmodule(object):

    name = 'gillespiem'
    
    def parse_species(p,r):
        ss = []
        for l in r:
            s,i = l.split(':')
            ss.append((s.strip(),int(i)))
        return ss

    def parse_reactions(p,r):
        reg = lambda x : (int(x[:x.find(' ')]),x[x.find(' '):].strip())
        rs = []
        for l in r:
            rx,rn = l.split(':')
            left,right = rx.split('->')
            left = left.strip().split('+')
            right = right.strip().split('+')
            rate = left.pop(-1).strip()
            if ' ' in rate:
                wsp = rate.rfind(' ')
                left,rate = [rate[:wsp]],rate[wsp+1:]
            null = ('','nothing','null')              
            used = tuple(reg(x) for x in left if not x in null)
            prod = tuple(reg(x) for x in right if not x in null)
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
        dshape,extname = e.pspacemap.dshape[1:],'gillespiem4ext'
        simfunc = gw.get_simulator(e,extname,install = e.perform_installation)
        simmodule.overrides['simulate'] = simfunc
        return simfunc

    overrides = {
        'prepare' : prepare, 
        'simulate' : None, 
            }





