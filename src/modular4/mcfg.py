import modular4.base as mb
import sim_anneal.pspace as psp

import numpy as np
import itertools as it

import pdb





def parse_missing(parser,lines):
    mb.log(5,'no parser method supplied for parser',parser)
    for l in lines:mb.log(5,'>>>> :\t'+l)
    return lines

def parse_end(parser,lines):
    i = float(lines[0].split(':')[1])
    return i

def parse_capture(parser,lines):
    i = float(lines[0].split(':')[1])
    return i

def parse_targets(parser,lines):
    return lines

def parse_measurements(parser,lines):
    parsed = []
    for l in lines:
        ml = l[:l.find(':')].strip()
        if ml in measurement_parsers:
            parsed.append(measurement_parsers[ml](ml,l))
    return parsed

def parse_outputs(parser,lines):
    parsed = [tuple(x.strip() for x in l.split(':')) for l in lines]
    return parsed

#def parse_ensemble(parser,lines):
#    print 'need real parser...',parser,lines
#    return lines

def parse_pspace(parser,lines):
    def parse_axis(a):
        ax,b,i,d = tuple(x.strip() for x in a.split(':'))
        b = tuple(float(x) for x in b.split(','))
        i = float(i)
        d = tuple(np.linspace(b[0],b[1],d))
        return ax,b,i,d
    if lines and '<' in lines[0] and '>' in lines[0]:
        intent = lines.pop(0).split(':')
        intent,trajcount = intent[0].strip(),int(intent[1])
    else:intent,trajcount = None,1
    axes,bnds,init,disc = zip(*tuple(parse_axis(l) for l in lines))
    sp = psp.pspace(bnds,init,disc,axes)
    if intent == '<map>':traj = list(it.product(*sp.discrete))
    elif intent == '<fit>':traj = [sp.initial[:]]
    else:traj = None
    return sp,traj,trajcount

def parse(mcfg,extra_parsers = {},**einput):
    with open(mcfg,'r') as h:lines = h.readlines()
    p = None
    for line in lines:
        l = line.strip()
        if not l or l.startswith('#'):continue
        elif l.startswith('<') and l.endswith('>'):
            p = l[1:-1]
            if not p in einput:einput[p] = []
        else:
            if p is None:continue
            einput[p].append(l)
    for i in einput:
        if i in extra_parsers:iparser = extra_parsers[i]
        elif i in parsers:iparser = parsers[i]
        else:iparser = parsers['!']
        einput[i] = iparser(i,einput[i])
    return einput

measurement_parsers = {}

parsers = {
    '!' : parse_missing,
    'end' : parse_end,
    'capture' : parse_capture,
    'targets' : parse_targets,
    'measurements' : parse_measurements,
    'outputs' : parse_outputs,
    #'ensemble' : parse_ensemble,
    'parameterspace' : parse_pspace,
        }





