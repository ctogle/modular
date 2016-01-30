import modular_core.fundamental as lfu

import modular_core.data.datacontrol as ldc
import modular_core.data.single_target as dst
import modular_core.data.batch_target as dba
import modular_core.postprocessing.process_abstract as lpp

import pdb,sys,math,traceback,random,time
import numpy as np

###############################################################################
### bistability_events characterizes the bistable qualities of a set of
###  trajectories by extracting events that represent state transitions
###############################################################################

import matplotlib.pyplot as plt



def measure_event(x,y,e,ilow,e0):
    dt = x[e[1]]-x[e[0]]
    mt = x[e[0]]+dt/2.0
    if ilow:
        hy = y[e[0]:e[1]].mean()
        lo = y[0:e0].mean()
    else:
        lo = y[e[0]:e[1]].mean()
        hy = y[0:e0].mean()
    return dt,mt,hy,lo

def measure_events(x,y,events,ilow):
    e0 = events[0][0]
    measurements = []
    for e in events:
        measurements.append(measure_event(x,y,e,ilow,e0))
    return measurements

def approximate_hylo(y):

    hy,lo = 20,10
    #pdb.set_trace()

    return hy,lo

def seek_events(x,y,h,ahy,alo):
    events,us,ds = [],[],[]
    if y[0] < y.mean():ilow,last = True,-1
    elif y[0] > y.mean():ilow,last = False,1
    else:return []

    for j in range(1,x.shape[0]):
        if y[j] < alo and last >= 0:
            ds.append(j)
            last = -1
        elif y[j] > ahy and last <= 0:
            us.append(j)
            last = 1

    if not us or not ds:return []
    ucnt,dcnt = len(us),len(ds)
    tcnt = min(ucnt,dcnt)
    if ilow:events = [(us[j],ds[j]) for j in range(tcnt)]
    else:events = [(ds[j],us[j]) for j in range(tcnt)]
    measurements = measure_events(x,y,events,ilow)

    #plt.plot(x,y)
    #for ex,e in enumerate(events):
    #    plt.plot([x[e[0]],x[e[1]]],[h+2.0*ex,h+2.0*ex])
    #plt.show()

    return measurements

class bistability_events(lpp.post_process_abstract):

    def _string(self):
        inps = self._string_inputs()
        strs = [self.name,'bistability_events',inps]
        return '\t' + ' : '.join(strs)

    def __init__(self,*args,**kwargs):
        self._default('name','bistable_events',**kwargs)
        regs = ['all trajectories','by parameter space']
        self._default('valid_regimes',regs,**kwargs)
        self._default('regime','all trajectories',**kwargs)

        self._default('transient_length',0.25,**kwargs)
        self._default('threshold',0.2,**kwargs)

        self._default('function_of',None,**kwargs)
        self._default('targets',[],**kwargs)

        self.method = 'bistable'
        lpp.post_process_abstract.__init__(self,*args,**kwargs)

    def bistable(self,*args,**kwargs):
        pool = args[0]

        tcount = len(self.targets)
        dshape = (len(self.target_list),1)
        data = np.zeros(dshape,dtype = np.float)

        transx = int(pool.dshape[2]*self.transient_length)
        domain = pool.data[0,pool.targets.index(self.function_of),transx:]
        for dtx in range(tcount):
            events = []
            dt = self.targets[dtx]
            pdx = pool.targets.index(dt)
            dtdat = pool.data[:,pdx,transx:]
            thresh = self.threshold*dtdat.max()
            ahy,alo = approximate_hylo(dtdat)
            for tjx in range(pool.dshape[0]):
                dtjdat = dtdat[tjx]
                events.extend(seek_events(domain,dtjdat,thresh,ahy,alo))

            meandt = np.mean([e[0] for e in events])
            meanhy = np.mean([e[2] for e in events])
            meanlo = np.mean([e[3] for e in events])
            probhy = meandt/(domain[-1]-domain[0])
            problo = 1.0 - probhy
            data[self.target_list.index(dt+':dt')] = meandt
            data[self.target_list.index(dt+':high')] = meanhy
            data[self.target_list.index(dt+':low')] = meanlo
            data[self.target_list.index(dt+':prob_high')] = probhy
            data[self.target_list.index(dt+':prob_low')] = problo

        dumx = np.zeros(1,dtype = np.float)
        data[0] = dumx
        bnode = self._init_data(dshape,self.target_list)
        bnode._trajectory(data)
        return bnode

    def _target_settables(self,*args,**kwargs):
        self.valid_regimes = ['all trajectories']
        self.valid_inputs = self._valid_inputs(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        if self.targets is None and capture_targetable:
            self.targets = capture_targetable
        if self.function_of is None and capture_targetable:
            self.function_of = capture_targetable[0]

        plo_targets = [item+':prob_low' for item in self.targets]
        phi_targets = [item+':prob_high' for item in self.targets]
        los_targets = [item+':low' for item in self.targets]
        his_targets = [item+':high' for item in self.targets]
        diff_targets = [item+':dt' for item in self.targets]
        self.target_list = ['minimaldomain']+\
            diff_targets+los_targets+his_targets+plo_targets+phi_targets

        self.capture_targets = self.target_list
        self.output.targeted = lfu.intersect_lists(
            self.output.targeted,self.capture_targets)
        lpp.post_process_abstract._target_settables(self,*args,**kwargs)

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self._target_settables(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                keys = [['targets']], 
                instances = [[self]], 
                widgets = ['check_set'], 
                box_labels = ['Targets'], 
                append_instead = [True], 
                provide_master = [True], 
                labels = [capture_targetable]))
        lpp.post_process_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

# return valid **kwargs for bistability based on msplit(line)
def parse_line(split,ensem,procs,routs):
    inputs = lpp.parse_process_line_inputs(split[2],procs,routs)
    targs = split[3].split(' of ')
    means_of = targs[0]
    function_of = targs[1]
    relevant = lfu.msplit(means_of,',')
    pargs = {
        'name':split[0],
        'variety':split[1],
        'input_regime':inputs,
        'dater_ids':relevant+[function_of],
        'targets':relevant,
        'function_of':function_of,
        #'bin_count':int(split[4]),
        #'ordered':split[5].count('unordered') < 1,
            }
    return pargs

###############################################################################

if __name__ == 'modular_core.postprocessing.bistability_events':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lpp.process_types['bistability_events'] = (bistability_events,parse_line)

###############################################################################









 
