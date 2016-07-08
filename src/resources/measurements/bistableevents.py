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
            'debug' : bool(ls[5].strip()),
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
        self._def('z_factor',0.2,**kws)
        self._def('w_factor',0.125,**kws)
        # fill value for NaN calculations from numpy..
        self._def('fillvalue',-100.0,**kws)
        self._def('debug',False,**kws)
        self._def('debug_plot',False,**kws)

    # based on the names of the input targets
    # set the names of the output targets
    def set_targets(self,inputs,pspace):
        if not self.domain in inputs:self.domain = inputs[0]

        ect = [x+':mean_event_count' for x in self.codomain]

        mdt = [x+':mean_mean_high_del_t' for x in self.codomain]
        sdt = [x+':mean_stddev_high_del_t' for x in self.codomain]
        vdt = [x+':mean_variance_high_del_t' for x in self.codomain]
        cdt = [x+':mean_covariance_high_del_t' for x in self.codomain]
        mndt = [x+':mean_min_high_del_t' for x in self.codomain]
        mxdt = [x+':mean_max_high_del_t' for x in self.codomain]

        mhy = [x+':mean_mean_high_value' for x in self.codomain]
        shy = [x+':mean_stddev_high_value' for x in self.codomain]
        vhy = [x+':mean_variance_high_value' for x in self.codomain]
        chy = [x+':mean_covariance_high_value' for x in self.codomain]
        mnhy = [x+':mean_min_high_value' for x in self.codomain]
        mxhy = [x+':mean_max_high_value' for x in self.codomain]

        plo = [x+':mean_prob_low' for x in self.codomain]
        phy = [x+':mean_prob_high' for x in self.codomain]
        peb = [x+':mean_prob_both' for x in self.codomain]
        pcn = [x+':mean_prob_cond' for x in self.codomain]

        eco = [x+':mean_event_correlation' for x in self.codomain]
        #epv = [x+':mean_event_pvalue' for x in self.codomain]

        cinputs = ect+\
            mdt+sdt+vdt+cdt+mndt+mxdt+\
            mhy+shy+vhy+chy+mnhy+mxhy+\
            plo+phy+peb+pcn+eco
            #plo+phy+eco+epv
        return mme.measurement.set_targets(self,cinputs,pspace)

    # this function will be called for each pspace location 
    # data is a numpy array ( trajectory , target , counts )
    # targs is a list of strings corresponding to each input data target
    def measure(self,data,targs,psploc,**kws):
        aux = {'header':str(psploc)}

        # the list of input targets
        tcount = len(self.codomain)

        # proxy data to average over trajectories
        tdata = [[] for t in self.targets]

        # actual output data (one value per output target)
        dshape = (len(self.targets),1)
        odata = numpy.zeros(dshape,dtype = numpy.float)

        # immediately ignore a transient period before steady state
        transx = int(data.shape[2]*self.transient)
        domain = data[0,targs.index(self.domain),transx:]

        # iterate over trajectories
        for tjx in range(data.shape[0]):
            alltjevents = []
            if tjx == 0:aux['extra_trajectory'] = []

            # iterate over targets in a trajectory
            for dtx in range(tcount):
                dt = self.codomain[dtx]
                dtdat = data[:,targs.index(dt),transx:]


                '''#
                n = 50
                b = numpy.linspace(5,dtdat.max(),n+1)
                hy,bs = numpy.histogram(dtdat,bins = b,density = False)
                fm = lambda u,v : (u+v)/2.0
                bx = numpy.array([fm(bs[y-1],bs[y]) for y in range(1,bs.size)])
                plt.plot(bx,hy)
                plt.gca().set_yscale('log')
                plt.show()
                '''#


                #dteffmax = dtdat.max()
                dteffmax = numpy.percentile(dtdat,99.9)
                print('maxvperc:',dtdat.max(),dteffmax)

                # magic numbers for event detection
                threshz = dteffmax*self.z_factor
                thwidth = dteffmax*self.w_factor
                alo = max(1,threshz - thwidth)
                ahy = min(dteffmax-1,threshz + thwidth)

                # seek all events in this trajectory for this target
                tjevents = seek(domain,dtdat[tjx,:],ahy,alo,self.min_x_dt)
                alltjevents.append(tjevents)



                #if self.debug and (tjx == 0 and (dtx == 0 or dtx == 1)):
                if self.debug and tjx == 0:
                    if dtx == 0:tcol = 'blue'
                    elif dtx == 1:tcol = 'green'
                    elif dtx == 2:tcol = 'red'
                    if dtx in (0,1):
                        aux['extra_trajectory'].append(((domain,dtdat[tjx,:]),
                            {'linewidth':2,'color':tcol,'label':dt}))
                        if dtx == 0:
                            etx = [domain[0],domain[-1]]
                            etkws = {'linewidth':2,'linestyle':'--','color':'black'}
                            aux['extra_trajectory'].append(((etx,[alo,alo]),etkws))
                            aux['extra_trajectory'].append(((etx,[ahy,ahy]),etkws))
                            etkws = {'linewidth':3,'marker':'s','color':'red'}
                            ety = [threshz,threshz]
                            for tje in tjevents:
                                etx = [domain[tje[0]],domain[tje[1]]]
                                aux['extra_trajectory'].append(((etx,ety),etkws))

                if self.debug_plot:
                    ax = plot_events(domain,dtdat[tjx,:],tjevents,threshz)
                    etx = [domain[0],domain[-1]]
                    ax.plot(etx,[threshz,threshz],linestyle = '--',color = 'red')
                    ax.plot(etx,[alo,alo],linestyle = '--',color = 'black')
                    ax.plot(etx,[ahy,ahy],linestyle = '--',color = 'black')
                    plt.show()



            # iterate over targets again
            for dtx in range(tcount):
                ed = alltjevents[dtx]
                dt = self.codomain[dtx]
                dtdat = data[tjx,targs.index(dt),transx:]

                # get other data for correlation measurements (if more than one target)
                if tcount > 1:
                    odt = self.codomain[1 if dtx == 0 else 0]
                    otdat = data[tjx,targs.index(odt),transx:]
                    oed = alltjevents[1 if dtx == 0 else 0]
                else:otdat,oed = None,None

                mb.log(5,'events found',len(ed))
                if ed:
                    # measure statistics of the events of the trajectory
                    meas,x,h = measure_trajectory(domain,dtdat,ed,otdat,oed)

                    if self.debug_plot and len(ed) > 1000:
                        plt.plot(x,h)
                        plt.show()

                    #def defoval(tx):odata[tx].append(numpy.mean(tdata[tx]))

                else:
                    # mercilessly kill the entire run if ANY trajectory has no events
                    mb.log(5,'NOEVENTSFOUND!',len(ed))
                    #raise ValueError
                    meas = (-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,0,1,-100,-1,-1)

                # add measurements to the proxy container
                getodtx = lambda s : self.targets.index(dt+s)
                tdata[getodtx(':mean_event_count')].append(len(ed))
                tdata[getodtx(':mean_mean_high_del_t')].append(meas[0])
                tdata[getodtx(':mean_stddev_high_del_t')].append(meas[1])
                tdata[getodtx(':mean_min_high_del_t')].append(meas[2])
                tdata[getodtx(':mean_max_high_del_t')].append(meas[3])
                tdata[getodtx(':mean_variance_high_del_t')].append(meas[4])
                tdata[getodtx(':mean_covariance_high_del_t')].append(meas[5])
                tdata[getodtx(':mean_mean_high_value')].append(meas[6])
                tdata[getodtx(':mean_stddev_high_value')].append(meas[7])
                tdata[getodtx(':mean_min_high_value')].append(meas[8])
                tdata[getodtx(':mean_max_high_value')].append(meas[9])
                tdata[getodtx(':mean_variance_high_value')].append(meas[10])
                tdata[getodtx(':mean_covariance_high_value')].append(meas[11])
                tdata[getodtx(':mean_prob_high')].append(meas[12])
                tdata[getodtx(':mean_prob_low')].append(meas[13])
                tdata[getodtx(':mean_prob_both')].append(meas[15])
                tdata[getodtx(':mean_prob_cond')].append(meas[16])
                if math.isnan(meas[14]):
                    mb.log(5,'INVALIDCORRELATIONMEASUREMENT!')
                    tdata[getodtx(':mean_event_correlation')].append(self.fillvalue)
                    #tdata[getodtx(':mean_event_pvalue')].append(self.fillvalue)
                else:
                    tdata[getodtx(':mean_event_correlation')].append(meas[14])
                    #tdata[getodtx(':mean_event_pvalue')].append(meas[15])

        # iterate over the targets, averaging over the proxy container (trajectories)
        for dtx in range(tcount):
            dt = self.codomain[dtx]

            getodtx = lambda s : self.targets.index(dt+s)
            def defoval(tx):odata[tx,0] = numpy.mean(tdata[tx])

            defoval(getodtx(':mean_event_count'))

            defoval(getodtx(':mean_mean_high_del_t'))
            defoval(getodtx(':mean_stddev_high_del_t'))
            defoval(getodtx(':mean_min_high_del_t'))
            defoval(getodtx(':mean_max_high_del_t'))
            defoval(getodtx(':mean_variance_high_del_t'))
            defoval(getodtx(':mean_covariance_high_del_t'))

            defoval(getodtx(':mean_mean_high_value'))
            defoval(getodtx(':mean_stddev_high_value'))
            defoval(getodtx(':mean_min_high_value'))
            defoval(getodtx(':mean_max_high_value'))
            defoval(getodtx(':mean_variance_high_value'))
            defoval(getodtx(':mean_covariance_high_value'))

            defoval(getodtx(':mean_prob_high'))
            defoval(getodtx(':mean_prob_low'))
            defoval(getodtx(':mean_prob_both'))
            defoval(getodtx(':mean_prob_cond'))
            defoval(getodtx(':mean_event_correlation'))
            #defoval(getodtx(':mean_event_pvalue'))

        return odata,self.targets,aux



# es is a list of events from a single trajectory
def measure_trajectory(x,y,es,o = None,oes = None):
    dts,pile,opile = [],[],[]
    for e in es:
        dt = x[e[1]]-x[e[0]]
        dts.append(dt)
        pile.extend(y[e[0]:e[1]])
        if not o is None:opile.extend(o[e[0]:e[1]])

    if o is None:bes = []
    else:bes = conditional_events(x,es,oes)


    n = 10
    b = numpy.linspace(5,numpy.max(dts),n+1)
    hy,bs = numpy.histogram(dts,bins = b,density = False)
    fm = lambda u,v : (u+v)/2.0
    bx = numpy.array([fm(bs[y-1],bs[y]) for y in range(1,bs.size)])


    # mean, stddev, min, max, and variance of event widths
    mdt = numpy.mean(dts)
    sdt = numpy.std(dts)
    mndt = numpy.min(dts)
    mxdt = numpy.max(dts)
    vdt = numpy.var(dts)

    # mean, stddev, min, max, variance of points during events
    mhy = numpy.mean(pile)
    shy = numpy.std(pile)
    mnhy = numpy.min(pile)
    mxhy = numpy.max(pile)
    vhy = numpy.var(pile)

    # correlation of points during events with points of another target
    if o is None:ecr,epv,cdt,chy = -100,-100,-100,-100
    else:
        ecr,epv = correl(pile,opile)
        chy,cdt = numpy.cov(pile,opile),-100

    # probability of being in the high toxin state at any given time
    phy = sum(dts)/float(x[-1]-x[0])
    plo = 1.0 - phy

    
    bdts = [x[t[1]]-x[t[0]] for t in bes]
    pboth = sum(bdts)/float(x[-1]-x[0])
    pcond = pboth/phy if phy > 0.0 else 0.0
    #pdb.set_trace()


    # report 10 distinct measurements of the events in this trajectory
    res = (
        mdt,sdt,mndt,mxdt,vdt,cdt,
        mhy,shy,mnhy,mxhy,vhy,chy,
        #phy,plo,ecr,epv)
        phy,plo,ecr,pboth,pcond)
    return res,bx,hy



# determine the probability that BOTH modules would be in the toxic state
def conditional_events(x,es,oes):
    bes = []
    for ej in range(len(es)):
        e1,e2 = es[ej]
        # there are either 0, 1, or 2 events which may overlap this event
        # determine the subrange of events within event during which both are toxic
        for oj in range(len(oes)):
            o1,o2 = oes[oj]
            if e2 <= o1 or o2 <= e1:continue
            else:
                b1,b2 = max(e1,o1),min(e2,o2)
                bes.append((b1,b2))

            #elif e1 <= o1 and o1 <= e2:bes.append((o1,e2))
            #elif e1 <= o2 and o2 <= e2:bes.append((e1,o2))
            #elif o1 <= e2 and e2 <= o2 and o1 <= e2 and e2 <= o2:
            #    bes.append((e1,e2))

    '''#
    z = 10
    ax = plot_events(x,y,es,z)
    for e in oes:
        ax.plot((x[e[0]],x[e[1]]),(z+5,z+5),linewidth = 2.0,marker = 's',color = 'b')
    for e in bes:
        ax.plot((x[e[0]],x[e[1]]),(z+10,z+10),linewidth = 2.0,marker = 's',color = 'r')
    plt.show()
    '''#

    return bes



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



def plot_events(x,y,es,z,ax = None):
    if ax is None:ax = plt.gca()
    ax.plot(x,y)
    for e in es:
        ax.plot((x[e[0]],x[e[1]]),(z,z),linewidth = 2.0,marker = 's',color = 'g')
    return ax





