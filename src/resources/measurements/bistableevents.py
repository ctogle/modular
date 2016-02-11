import modular4.measurement as mme
import math,numpy

import matplotlib.pyplot as plt

import pdb





class bistability(mme.measurement):

    tag = 'bistability'

    @staticmethod
    def parse(p,l):
        ls = tuple(x.strip() for x in l.split(':'))
        u,v = ls[2].split(' of ')
        kws = {
            'input_scheme' : ls[1],
            'domain' : v.strip(),
            'codomain' : tuple(x.strip() for x in u.split(',')),
                }
        return bistability(**kws)

    def __init__(self,*ags,**kws):
        mme.measurement.__init__(self,*ags,**kws)
        self._def('name','bistability_measurement',**kws)
        self._def('domain',None,**kws)
        self._def('codomain',None,**kws)
        self._def('transient',0.1,**kws)

    def set_targets(self,inputs,pspace):
        if not self.domain in inputs:self.domain = inputs[0]
        bitgs = self.codomain
        plo = [x+':prob_low' for x in self.codomain]
        phi = [x+':prob_high' for x in self.codomain]
        los = [x+':prob_leak' for x in self.codomain]
        his = [x+':mean_high_value' for x in self.codomain]
        dfs = [x+':mean_high_del_t' for x in self.codomain]
        cinputs = ['minimaldomain']+dfs+his+plo+phi+los
        return mme.measurement.set_targets(self,cinputs,pspace)

    # this function will be called for each pspace location 
    # data is a numpy array ( trajectory , target , counts )
    # targs is a list of strings corresponding to each input data target
    def measure(self,data,targs,psploc,**kws):
        # create the outgoing data set
        tcount = len(self.codomain)
        dshape = (len(self.targets),1)
        odata = numpy.zeros(dshape,dtype = numpy.float)

        # create a domain which disregards a specified transient period
        transx = int(data.shape[2]*self.transient)
        domain = data[0,targs.index(self.domain),transx:]

        # for each target (species to perform the measurement over) ... 
        for dtx in range(tcount):
            dt = self.codomain[dtx]
            pdx = targs.index(dt)
            dtdat = data[:,pdx,transx:]



            # START SUBJECT TO CHANGE

            # hard coded transition threshold values!
            # could use a better way to automate this calculation
            threshz,thwidth = 20,10
            ahy,alo = threshz + thwidth,threshz - thwidth

            # aggregate all events from each trajectory
            events = []

            # for each trajectory at this pspace location
            for tjx in range(data.shape[0]):

                # seek_events takes a 
                # domain,comain,threshold for high transition,threshold for low transition
                # it returns measurements of events it detects in this trajectory
                #events.extend(seek_events(dtjdom,dtjdat,ahy,alo))
                tjevents = seek(domain,dtdat[tjx,:],ahy,alo)
                events.extend(tjevents)

                #if tjx % 50 == 0:
                #    plot_events(domain,dtdat[tjx,:],tjevents)

            # measure quantities for this target based on all events from all
            # trajectories of the pspace location
            print('BISTABILITY MEASUREMENT FOUND %i EVENTS!' % len(events))
            if events:
                meandt = numpy.mean([e[1] for e in events])
                meanhy = numpy.mean([e[2] for e in events])
            else:
                meandt = -1.0
                meanhy = -1.0

            highcnt = numpy.count_nonzero(dtdat > ahy)
            lowcnt = numpy.count_nonzero(dtdat < alo)
            #atcnt = numpy.count_nonzero(dtdat == threshz)
            probhy = float(highcnt)/dtdat.size
            problo = float(lowcnt)/dtdat.size
            problk = 1.0 - probhy - problo

            # END SUBJECT TO CHANGE



            # read the measurements for this target at this pspace location into the outgoing data array
            odata[self.targets.index(dt+':mean_high_del_t')] = meandt
            odata[self.targets.index(dt+':mean_high_value')] = meanhy
            odata[self.targets.index(dt+':prob_high')] = probhy
            odata[self.targets.index(dt+':prob_low')] = problo
            odata[self.targets.index(dt+':prob_leak')] = problk

        # insert a dummy array so that this data can be easily viewed in isolation
        odata[0] = numpy.zeros(1,dtype = numpy.float)

        # return a tuple containing the 
        # outgoing data,the names of the targets in that data,and supplemental information
        return odata,self.targets,{'header':str(psploc)}

# return measurements of events in a trajectory (x,y)
# when y passes from below th to above th, a low->high transition may occur
# when y passes from above tl to below tl, a high->low transition may occur
# an event is always defined as a pair of transitions (low->high,high->low)
def seek(x,y,th,tl):
    if y.min() > tl:return []
    elif y.max() < th:return []
    es,ms = [None],[]
    if y[0] > th:st = 1
    elif y[0] < tl:st = -1
    else:st = 0
    for j in range(1,y.size):
        dy = y[j]-y[j-1]
        if st == 0:
            if dy > th-y[j-1]:
                print('trans ambig->high')
                st = 1
            elif dy < tl-y[j-1]:
                print('trans ambig->low')
                st = -1
        elif st > 0:
            if dy < tl-y[j-1]:
                print('trans high->low')
                st = -1
                if es[-1]:
                    es[-1] = (es[-1],j)

                    # events which are within 5 units of one another should be
                    # merged... (because events shorter than this are ignored)
                    # THIS IS NOT CURRENTLY THE CASE

                    ms.append(measure_event(x,y,es[-1]))
                    es.append(None)
        elif st < 0:
            if dy > th-y[j-1]:
                print('trans low->high')
                st = 1
                es[-1] = j
    return [m for m in ms if not m is None]

# e is a tuple (low->high transition index in x,high->low transition index in x)
def measure_event(x,y,e):
    if e[1]-e[0] < 5:
        print('event was too short!')
        return
    dt = x[e[1]]-x[e[0]]
    hy = y[e[0]:e[1]].mean()
    return e,dt,hy

def plot_events(x,y,es):
    plt.plot(x,y)
    for e,dt,hy in es:
        plt.plot((x[e[0]],x[e[1]]),(hy,hy),linewidth = 5.0,marker = 'o')
    plt.show()





