import modular_core.fundamental as lfu

import modular_core.data.datacontrol as ldc
import modular_core.data.single_target as dst
import modular_core.data.batch_target as dba
import modular_core.postprocessing.process_abstract as lpp

import pdb,sys,math,traceback,random,time
import numpy as np
import scipy.cluster.vq as vq

###############################################################################
### bistability characterizes the bistable qualities of a single trajectory
###############################################################################

import matplotlib.pyplot as plt

def bell_pair(x,m1,m2,s1,s2,a1,a2):
    g1 = a1*np.exp(-0.5*((x-m1)/s1)**2)
    g2 = a2*np.exp(-0.5*((x-m2)/s2)**2)
    penalty = 0.0
    penalty += (g1.sum() + g2.sum() - 1.0)**8
    penalty += (1.0/(0.00001 + (abs(m1-m2)/math.sqrt(s1*s2))))**8
    return g1 + g2 + penalty




def measure(f,x,y,guess):
    fofy = f(x,*guess)
    m = (fofy - y)**2
    return m
        
def reflect(p,a,b):
    if p < a:p = a + (a - p)
    if p > b:p = b - (p - b)
    return p
        
def wraparound(p,a,b):
    if p < a:p = b - (a - p)
    if p > b:p = a + (p - b)
    return p

def step(x,guess,minmaxes,temp,delta = None):
    def move(p,d = None,mm = None):
        if mm is None:xmin,xmax = x.min(),x.max()
        else:xmin,xmax = mm
        maxstepsize = temp*(xmax-xmin)/3.0
        stepsize = random.random()*maxstepsize
        if d is None:delp = random.choice((-1,1))*stepsize
        else:delp = np.sign(d)*stepsize
        newp = newp = p + delp
        #newp = reflect(newp,xmin,xmax)
        newp = wraparound(newp,xmin,xmax)
        return newp
    roll = lambda : random.random() > 0.5
    if delta is None:delta = tuple(None for x in guess)
    newguess = tuple(move(p,d,mm) if roll() else p for p,d,mm in zip(guess,delta,minmaxes))
    return newguess

def simanneal(f,x,y,guess,minmaxes):
    deltaguess = tuple(0 for x in guess)
    attempt = 0;attempts = 100000;lastplot = 0;tolerance = 0.0001;mdist = 1.0

    heatdomain = np.linspace(0,attempts,attempts)
    heatcurve = np.exp(-3.0*heatdomain/heatdomain.max())
    temp = heatcurve[attempt]

    metric = measure(f,x,y,guess)  
    steppedguess = step(x,guess,minmaxes,temp)
    while attempt < attempts and metric.sum() > tolerance:
        temp = heatcurve[attempt]
        attempt += 1
        lastplot += 1
        steppedmetric = measure(f,x,y,steppedguess)
        mdist = metric.sum()-steppedmetric.sum()
        if mdist > 0.0:
            deltaguess = tuple(g1-g2 for g1,g2 in zip(steppedguess,guess))


            '''
            print 'better?',attempt,steppedmetric.sum(),metric.sum()
            if lastplot > 20000:
                plt.plot(x,y,color = 'black')
                plt.plot(x,f(x,*steppedguess),color = 'green')
                plt.plot(x,f(x,*guess),color = 'red')
                plt.show()
                lastplot = 0
            '''


            guess = steppedguess
            metric = steppedmetric
            steppedguess = step(x,guess,minmaxes,temp,deltaguess)
        else:steppedguess = step(x,guess,minmaxes,temp)


    print 'better?!!!',attempt,guess,metric.sum()


    return guess

def trimspace(f,x,y,guess,minmaxes):
    def trim(p,m):
        r = (m[1]-m[0])/3
        m0 = m[0] if p-m[0] < r else p - r
        m1 = m[1] if m[1]-p < r else p + r
        return m0,m1
    newminmaxes = tuple(trim(g,m) for g,m in zip(guess,minmaxes))
    return newminmaxes




def simanneal_iter(f,x,y,n,g,m):

    for dn in range(n):
        g = simanneal(f,x,y,g,m)
        if dn < n - 1:
            print 'pretrim',m
            m = trimspace(f,x,y,g,m)
            print 'posttrim',m

    print 'sim anneal'
    plt.plot(x,y,color = 'black')
    plt.plot(x,f(x,*g),color = 'red')
    plt.show()

    return g




def findmidx(x,y,g):
    def nearest(x,a):
        dels = [abs(v - a) for v in x]
        return dels.index(min(dels))
    x1,x2 = g[0],g[1]
    i1 = nearest(x,x1)
    i2 = nearest(x,x2)
    if i1 < i2:mx = nearest(y[i1:i2],y[i1:i2].min())+i1
    elif i2 < i1:mx = nearest(y[i2:i1],y[i2:i1].min())+i2
    else:mx = i1
    return mx

    #if g[0] < g[1]:mx = nearest(x,g[0]+g[2]*5)
    #else:mx = nearest(x,g[1]+g[3]*5)
    #return mx

    #x1,x2 = g[0],g[1]
    #i1 = nearest(x,x1)
    #i2 = nearest(x,x2)
    #mx = int((i1+i2)/2.0)
    #return mx






class bistability(lpp.post_process_abstract):

    def _string(self):
        inps = self._string_inputs()
        strs = [self.name,'bistability',inps]
        return '\t' + ' : '.join(strs)

    def __init__(self,*args,**kwargs):
        self._default('name','bistable',**kwargs)
        #regs = ['all trajectories','by parameter space']
        #self._default('valid_regimes',regs,**kwargs)
        #self._default('regime','all trajectories',**kwargs)
        self._default('valid_regimes',['per trajectory'],**kwargs)
        self._default('regime','per trajectory',**kwargs)

        self._default('bin_count',100,**kwargs)
        #self._default('cluster_count',2,**kwargs)
        self._default('ordered',True,**kwargs)

        self._default('function_of',None,**kwargs)
        self._default('targets',[],**kwargs)

        self.method = 'bistable'
        lpp.post_process_abstract.__init__(self,*args,**kwargs)

    def bistable(self,*args,**kwargs):
        pool = args[0]

        def bistab(bins,data):        

            stime = time.time()
            minmaxes = (
                (0,bins.max()),(0,bins.max()),
                (0,bins.max()/5.0),(0,bins.max()/5.0),
                (0.0001,1.0),(0.0001,1.0))

            guess = tuple((a+b)/2.0 for a,b in minmaxes)

            fits = simanneal_iter(bell_pair,bins,data,1,guess,minmaxes)

            #plt.show()
            
            md,m1,m2,s1,s2 = abs(fits[0]-fits[1]),fits[0],fits[1],fits[2],fits[3]

            penalty = abs(m1-m2)/math.sqrt(s1*s2)
            if penalty > 10.0:
                print 'FLAG ON THE PLAY!'
                return -1,-1,-1

            else:
                mx = findmidx(bins,data,fits)
                peak1 = data[:mx]
                peak2 = data[mx:]
                prob1 = peak1.sum()
                prob2 = peak2.sum()

                print 'fits',fits,time.time()-stime,prob1,prob2

            return md,prob1,prob2

        tcount = len(self.targets)
        dshape = (len(self.target_list),1)
        data = np.zeros(dshape,dtype = np.float)
        bins = pool.data[pool.targets.index(self.function_of)]

        for dtx in range(tcount-1):
            dt = self.targets[dtx]
            dtdat = pool.data[pool.targets.index(dt)]
            diff,low,high = bistab(bins,dtdat)
            data[self.target_list.index(dt+':distance')] = diff
            data[self.target_list.index(dt+':low')] = low
            data[self.target_list.index(dt+':high')] = high


        #plt.show()


        dumx = np.zeros(1,dtype = np.float)
        data[0] = dumx
        bnode = self._init_data(dshape,self.target_list)
        bnode._trajectory(data)
        return bnode

    def _target_settables(self,*args,**kwargs):
        self.valid_regimes = ['per trajectory']
        self.valid_inputs = self._valid_inputs(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        if self.targets is None and capture_targetable:
            self.targets = capture_targetable
        if self.function_of is None and capture_targetable:
            self.function_of = capture_targetable[0]

        los_targets = [item+':low' for item in self.targets]
        his_targets = [item+':high' for item in self.targets]
        diff_targets = [item+':distance' for item in self.targets]
        self.target_list = [self.function_of]+diff_targets+los_targets+his_targets

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

if __name__ == 'modular_core.postprocessing.bistability':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lpp.process_types['bistability'] = (bistability,parse_line)

###############################################################################









 
