import modular4.base as mb
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
        # fill value for NaN calculations from numpy..
        self._def('fillvalue',-100.0,**kws)

    # based on the names of the input targets
    # set the names of the output targets
    def set_targets(self,inputs,pspace):
        if not self.domain in inputs:self.domain = inputs[0]
        bitgs = self.codomain
        plo = [x+':mean_prob_low' for x in self.codomain]
        phi = [x+':mean_prob_high' for x in self.codomain]
        los = [x+':mean_prob_leak' for x in self.codomain]
        his = [x+':mean_high_value' for x in self.codomain]
        dfs = [x+':mean_high_del_t' for x in self.codomain]
        efs = [x+':mean_event_frequency' for x in self.codomain]
        pco = [x+':mean_event_correlation' for x in self.codomain]
        ppv = [x+':mean_event_pvalue' for x in self.codomain]
        cinputs = ['minimaldomain']+dfs+his+plo+phi+los+efs+pco+ppv
        return mme.measurement.set_targets(self,cinputs,pspace)

    # this function will be called for each pspace location 
    # data is a numpy array ( trajectory , target , counts )
    # targs is a list of strings corresponding to each input data target
    def measure(self,data,targs,psploc,**kws):
        aux = {'header':str(psploc)}
        verify = lambda v : self.fillvalue if math.isnan(v) else v
        tcount = len(self.codomain)
        dtshape = (len(self.targets),data.shape[0])
        tdata = [[] for t in self.targets]
        dshape = (len(self.targets),1)
        odata = numpy.zeros(dshape,dtype = numpy.float)
        transx = int(data.shape[2]*self.transient)
        domain = data[0,targs.index(self.domain),transx:]
        for tjx in range(data.shape[0]):
            alltjevents = []
            if tjx == 0:aux['extra_trajectory'] = []
            for dtx in range(tcount):
                dt = self.codomain[dtx]
                dtdat = data[:,targs.index(dt),transx:]
                threshz,thwidth = dtdat.max()/5.0,dtdat.max()/8.0
                alo = max(1,threshz - thwidth)
                ahy = min(dtdat.max()-1,threshz + thwidth)
                tjevents = seek(domain,dtdat[tjx,:],ahy,alo,self.min_x_dt)



                #if tjx % 20 == 0:
                if tjx == 0 and (dtx == 0 or dtx == 1):
                    tcol = 'blue' if dtx == 0 else 'green'
                    aux['extra_trajectory'].append(((domain,dtdat[tjx,:]),
                        {'linewidth':2,'color':tcol,'label':dt}))
                    etx = [domain[0],domain[-1]]
                    aux['extra_trajectory'].append(((etx,[alo,alo]),
                        {'linewidth':2,'linestyle':'--','color':'black'}))
                    aux['extra_trajectory'].append(((etx,[ahy,ahy]),
                        {'linewidth':2,'linestyle':'--','color':'black'}))
                    for tje in tjevents:
                        etx = [domain[tje[0]],domain[tje[1]]]
                        aux['extra_trajectory'].append(((etx,[threshz,threshz]),
                            {'linewidth':3,'marker':'s','color':'red'}))
                if False:
                    ax = plot_events(domain,dtdat[tjx,:],tjevents,threshz)
                    ax.plot([domain[0],domain[-1]],[threshz,threshz],linestyle = '--',color = 'red')
                    ax.plot([domain[0],domain[-1]],[alo,alo],linestyle = '--',color = 'black')
                    ax.plot([domain[0],domain[-1]],[ahy,ahy],linestyle = '--',color = 'black')
                    plt.show()



                alltjevents.append(tjevents)
            for dtx in range(tcount):
                ed = alltjevents[dtx]
                dt = self.codomain[dtx]
                getodtx = lambda dt,s : self.targets.index(dt+s)
                dtdat = data[tjx,targs.index(dt),transx:]
                if tcount > 1:
                    odt = self.codomain[1 if dtx == 0 else 0]
                    otdat = data[tjx,targs.index(odt),transx:]
                else:otdat = None
                mb.log(5,'events found',len(ed))
                tdata[0].append(len(ed))
                if ed:
                    meas = measure_trajectory(
                        domain,dtdat,alo,ahy,ed,alltjevents,otdat)
                    mdt,mhy,phy,plo,plk,mefreq,evc,epv = meas
                    tdata[getodtx(dt,':mean_high_del_t')].append(mdt)
                    tdata[getodtx(dt,':mean_high_value')].append(mhy)
                    tdata[getodtx(dt,':mean_prob_high')].append(phy)
                    tdata[getodtx(dt,':mean_prob_low')].append(plo)
                    tdata[getodtx(dt,':mean_prob_leak')].append(plk)
                    tdata[getodtx(dt,':mean_event_frequency')].append(mefreq)
                    if not math.isnan(evc):
                        tdata[getodtx(dt,':mean_event_correlation')].append(verify(evc))
                        tdata[getodtx(dt,':mean_event_pvalue')].append(verify(epv))
                else:
                    meas = measure_boring_trajectory(
                        domain,dtdat,alo,ahy,ed,alltjevents,otdat)
                    phy,plo,plk = meas
                    tdata[getodtx(dt,':mean_prob_high')].append(phy)
                    tdata[getodtx(dt,':mean_prob_low')].append(plo)
                    tdata[getodtx(dt,':mean_prob_leak')].append(plk)
                    tdata[getodtx(dt,':mean_event_frequency')].append(0.0)
                    
        for dtx in range(tcount):
            dt = self.codomain[dtx]
            getodtx = lambda s : self.targets.index(dt+s)
            def defoval(tx,dv):
                if tdata[tx]:odata[tx,0] = numpy.mean(tdata[tx])
                else:odata[tx,0] = dv
            defoval(getodtx(':mean_high_del_t'),-1.0)
            defoval(getodtx(':mean_high_value'),-1.0)
            defoval(getodtx(':mean_prob_high'),-1.0)
            defoval(getodtx(':mean_prob_low'),-1.0)
            defoval(getodtx(':mean_prob_leak'),-1.0)
            defoval(getodtx(':mean_event_frequency'),-1.0)
            defoval(getodtx(':mean_event_correlation'),-100.0)
            defoval(getodtx(':mean_event_pvalue'),1.0)
        mecnt = numpy.mean(tdata[0])
        odata[0,0] = mecnt
        return odata,self.targets,aux

# es is a list of events from a single trajectory
# aes are the events of all targets
def measure_trajectory(x,y,alo,ahy,es,aes,o = None):
    #highcnt = numpy.count_nonzero(y > ahy)
    #lowcnt = numpy.count_nonzero(y < alo)
    #phy = float(highcnt)/y.size
    #plo = float(lowcnt)/y.size
    #plk = 1.0 - phy - plo
    #if not es:return -1,-1,phy,plo,plk,0.0,-100,1

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
    efq = float(len(es))/float(x[-1]-x[0])
    evc = numpy.mean(crs)
    epv = numpy.mean(pvs)
    phy = sum(dts)/float(x[-1]-x[0])
    plo = 1.0 - phy
    plk = -1.0
    return mdt,mhy,phy,plo,plk,efq,evc,epv

def measure_boring_trajectory(x,y,alo,ahy,es,aes,o = None):
    highcnt = numpy.count_nonzero(y >= ahy)
    lowcnt = numpy.count_nonzero(y <= alo)
    #leakcnt = numpy.count_nonzero(y > alo and y < ahy)
    leakcnt = -1.0
    if highcnt > lowcnt:phy,plo = 1.0,0.0
    elif highcnt < lowcnt:phy,plo = 0.0,1.0
    else:phy,plo = 0.5,0.5
    return phy,plo,leakcnt/float(y.size)

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
                while lastcross > 0 and not y[lastcross] < tl:
                    lastcross -= 1
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

def calc_lines_callback(self,ax,d,t,x,ys):
    pass

def plot_events(x,y,es,z):
    ax = plt.gca()
    ax.plot(x,y)
    for e in es:
        ax.plot((x[e[0]],x[e[1]]),(z,z),linewidth = 2.0,marker = 's',color = 'g')
    return ax





