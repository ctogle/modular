import modular4.measurement as mme
import math,numpy
from scipy.stats import pearsonr as correl

import matplotlib.pyplot as plt

import pdb





# all measurements inherit from mme.measurement and override 3 or 4 methods
class bistability(mme.measurement):

    # tag to point to this class when found in an mcfg
    tag = 'bistability'

    # this defines how this object will 
    # be parsed from a string found in an mcfg
    @staticmethod
    def parse(p,l):
        ls = tuple(x.strip() for x in l.split(':'))
        u,v = ls[2].split(' of ')
        kws = {
            'input_scheme' : ls[1],
            'domain' : v.strip(),
            'codomain' : tuple(x.strip() for x in u.split(',')),
            'min_x_dt' : int(ls[3].strip()),
            'transient' : float(ls[4].strip()),
                }
        return bistability(**kws)

    def __init__(self,*ags,**kws):
        mme.measurement.__init__(self,*ags,**kws)
        self._def('name','bistability_measurement',**kws)
        # target in input data corresponding to the domain
        self._def('domain',None,**kws)
        # list of targets in input data corresponding to targets for measurement
        self._def('codomain',None,**kws)
        # fraction of trajectory to chop off, assuming it represents a transient period
        self._def('transient',0.2,**kws)
        # number of points required to represent a "stable" state
        self._def('min_x_dt',5,**kws)

    # based on the names of the input targets
    # set the names of the output targets
    def set_targets(self,inputs,pspace):
        if not self.domain in inputs:self.domain = inputs[0]
        bitgs = self.codomain
        plo = [x+':prob_low' for x in self.codomain]
        phi = [x+':prob_high' for x in self.codomain]
        los = [x+':prob_leak' for x in self.codomain]
        his = [x+':mean_high_value' for x in self.codomain]
        dfs = [x+':mean_high_del_t' for x in self.codomain]
        pco = [x+':mean_event_correlation' for x in self.codomain]
        ppv = [x+':mean_event_p-value' for x in self.codomain]
        cinputs = ['minimaldomain']+dfs+his+plo+phi+los+pco+ppv
        return mme.measurement.set_targets(self,cinputs,pspace)

    # this function will be called for each pspace location 
    # data is a numpy array ( trajectory , target , counts )
    # targs is a list of strings corresponding to each input data target
    def measure(self,data,targs,psploc,**kws):
        # create the outgoing data set
        tcount = len(self.codomain)
        dshape = (len(self.targets),data.shape[0])
        odata = numpy.zeros(dshape,dtype = numpy.float)

        # create a domain which disregards a specified transient period
        transx = int(data.shape[2]*self.transient)
        domain = data[0,targs.index(self.domain),transx:]

        # iterate over each trajectory, providing a measurement of its events
        for tjx in range(data.shape[0]):

            # aggregate the events from each target in the trajectory
            alltjevents = []
            for dtx in range(tcount):
                dt = self.codomain[dtx]
                dtdat = data[:,targs.index(dt),transx:]

                threshz,thwidth = dtdat.max()/5.0,dtdat.max()/8.0
                alo = max(1,threshz - thwidth)
                ahy = min(dtdat.max()-1,threshz + thwidth)
                tjevents = seek(domain,dtdat[tjx,:],ahy,alo,self.min_x_dt)

                #if tjx % 20 == 0:
                if False:
                    ax = plot_events(domain,dtdat[tjx,:],tjevents,threshz)
                    ax.plot([domain[0],domain[-1]],[threshz,threshz],linestyle = '--',color = 'red')
                    ax.plot([domain[0],domain[-1]],[alo,alo],linestyle = '--',color = 'black')
                    ax.plot([domain[0],domain[-1]],[ahy,ahy],linestyle = '--',color = 'black')
                    plt.show()

                alltjevents.append(tjevents)

            # apply a measurement to the events of each target in the trajectory
            for dtx in range(tcount):
                ed = alltjevents[dtx]
                dt = self.codomain[dtx]
                dtdat = data[tjx,targs.index(dt),transx:]
                if tcount > 1:
                    odt = self.codomain[1 if dtx == 0 else 0]
                    otdat = data[tjx,targs.index(odt),transx:]
                else:otdat = None
                if ed:
                    meas = measure_trajectory(domain,dtdat,alo,ahy,ed,alltjevents,otdat)
                    mdt,mhy,phy,plo,plk,evc,epv = meas
                else:mdt,mhy,phy,plo,plk,evc,epv = -1,-1,-1,-1,-1,-100,1

                # insert the measurement for this trajectory into the output data array
                dt = self.codomain[dtx]
                getodtx = lambda dt,s : self.targets.index(dt+s)
                odata[getodtx(dt,':mean_high_del_t'),tjx] = mdt
                odata[getodtx(dt,':mean_high_value'),tjx] = mhy
                odata[getodtx(dt,':prob_high'),tjx] = phy
                odata[getodtx(dt,':prob_low'),tjx] = plo
                odata[getodtx(dt,':prob_leak'),tjx] = plk
                odata[getodtx(dt,':mean_event_correlation'),tjx] = evc
                odata[getodtx(dt,':mean_event_p-value'),tjx] = epv

                # this is a dummy axis for plotting...
                odata[0,tjx] = numpy.zeros(1,dtype = numpy.float)

        # return the output array, list of targets in the array, auxillary info for plotting
        return odata,self.targets,{'header':str(psploc)}

# es is a list of events from a single trajectory
# aes are the events of all targets
def measure_trajectory(x,y,alo,ahy,es,aes,o = None):
    highcnt = numpy.count_nonzero(y > ahy)
    lowcnt = numpy.count_nonzero(y < alo)
    phy = float(highcnt)/y.size
    plo = float(lowcnt)/y.size
    plk = 1.0 - phy - plo
    if not es:return -1,-1,phy,plo,plk,-100,1
    dts = []
    hys = []
    crs = []
    pvs = []
    for e in es:
        dt = x[e[1]]-x[e[0]]
        hy = y[e[0]:e[1]].mean()
        if o is None:cr,pv = -100,1
        else:cr,pv = correl(y[e[0]:e[1]],o[e[0]:e[1]])
        dts.append(dt)
        hys.append(hy)
        crs.append(cr)
        pvs.append(pv)
    mdt = numpy.mean(dts)
    mhy = numpy.mean(hys)
    evc = numpy.mean(crs)
    epv = numpy.mean(pvs)
    return mdt,mhy,phy,plo,plk,evc,epv

# return measurements of events in a trajectory (x,y)
# an event identifies a "high count state" entry/exit for a species
# when y passes from below th to above th, a low->high transition may occur
# when y passes from above tl to below tl, a high->low transition may occur
# an event is always defined as a pair of transitions (low->high,high->low)
def seek(x,y,th,tl,min_x_dt):
    if y.min() > tl:return []
    elif y.max() < th:return []
    es,ms = [None],[]
    if y[0] > th:st = 1
    elif y[0] < tl:st = -1
    else:st = 0
    for j in range(1,y.size-1-min_x_dt):
        dy = y[j]-y[j-1]
        if st == 0:
            if dy >= th-y[j-1] and y[j+1:j+1+min_x_dt].max() > tl:st = 1
            elif dy <= tl-y[j-1] and y[j+1:j+1+min_x_dt].max() < th:st = -1
        elif st > 0:
            if dy <= tl-y[j-1]:
                st = -1
                if es[-1]:
                    es[-1] = (es[-1],j)
                    ms.append(es[-1])
                    es.append(None)
        elif st < 0:
            if dy >= th-y[j-1]:
                st = 1
                lastcross = j-1
                while not y[lastcross] < tl:lastcross -= 1
                es[-1] = lastcross
    if not ms:return ms
    else:return filter_events(x,y,th,tl,min_x_dt,ms)

# filtered events have the following properties:
#   1) at least one point is above th (sufficiently tall)
#   2) the end points are below tl (system is low before/after event)
#   3) the event contains at least min_x_dt points 
#         (sufficiently long compared to resolution)
#   4) there are at least min_x_dt points between any two events
#         (system stabilizes between events)
#   5) before and after any event there are at least min_x_dt points 
#         whose maximum value is below th (pre/post low state is stable)
#
# * the word "stable" means no transition happened for min_x_dt consecutive points
#
def filter_events(x,y,th,tl,min_x_dt,es):
    f = []
    for j in range(len(es)):
        if f:
            if es[j][0]-f[-1][1] < min_x_dt:
                f[-1] = (f[-1][0],es[j][1])
            elif y[f[-1][1]+1:es[j][0]-1].mean() > th:
                f[-1] = (f[-1][0],es[j][1])
            elif es[j][1]-es[j][0] > min_x_dt:
                f.append(es[j])
        elif es[j][1]-es[j][0] > min_x_dt:
            f.append(es[j])
    if f:
        j = f[0][0]
        if j < min_x_dt+1:f.pop(0)
        elif y[j-1-min_x_dt:j].max() >= th:f.pop(0)
    if f:
        j = f[-1][1]
        if j > x.size-min_x_dt-1:f.pop(-1)
        elif y[j+1:j+1+min_x_dt].max() >= th:f.pop(-1)
    return f

def plot_events(x,y,es,z):
    ax = plt.gca()
    ax.plot(x,y)
    for e in es:
        ax.plot((x[e[0]],x[e[1]]),(z,z),linewidth = 2.0,marker = 's',color = 'g')
    return ax





