import modular_core.fundamental as lfu

import modular_core.data.datacontrol as ldc
import modular_core.data.single_target as dst
import modular_core.data.batch_target as dba
import modular_core.postprocessing.process_abstract as lpp

import pdb,sys,math
import numpy as np
import scipy.ndimage.morphology as morph

#import matplotlib.pyplot as plt

###############################################################################
### period_finder measures the period of a signal as a function of time
###############################################################################

class period_finder(lpp.post_process_abstract):

    def _string(self):
        #periods : find periods : 0 : all : -1
        raise NotImplemented

        inps = self._string_inputs()
        phrase = 'all'
        slice_dex = str(self.slice_dex)
        strs = [self.name,'trajectory slice',inps,phrase,slice_dex]
        return '\t' + ' : '.join(strs)

    def __init__(self,*args,**kwargs):
        self._default('name','periodfinder',**kwargs)
        self._default('valid_regimes',['per trajectory'],**kwargs)
        self._default('regime','per trajectory',**kwargs)
        self._default('dater_ids',[],**kwargs)
        self._default('window',5,**kwargs)
        self.method = 'find_period'
        lpp.post_process_abstract.__init__(self,*args,**kwargs)

    def find_period(self,*args,**kwargs):
        pool = args[0]
        tcount = len(self.targetlist)
        dshape = (tcount,pool.data[0].shape[0])
        data = np.zeros(dshape,dtype = np.float)

        trajectory = pool.data
        timevs = trajectory[0]
        tnames = pool.targets
        for px,pt in enumerate(tnames):
            if px == 0:data[px] = timevs
            targvs = trajectory[self.dater_ids.index(pt)]
            newtime,periods,amplitudes = self.find_period_in_window(timevs,targvs)
            if not newtime is None and not newtime.shape[0] == 0:
                tailoff = np.where(timevs == newtime[0])[0][0]
                tipoff = np.where(timevs == newtime[-1])[0][0]
                perdex = self.targetlist.index(pt+'-period')
                ampdex = self.targetlist.index(pt+'-amplitude')
                data[perdex,tailoff:tipoff+1] = periods
                data[ampdex,tailoff:tipoff+1] = amplitudes
                #data[perdex,:tailoff] = periods[0]
                #data[perdex,tipoff+1:] = periods[-1]
                #data[ampdex,:tailoff] = amplitudes[0]
                #data[ampdex,tipoff+1:] = amplitudes[-1]

        bnode = self._init_data(dshape,self.targetlist)
        bnode._trajectory(data)
        return bnode

    def hone(self,inds,y):
        ninds = []
        block = []
        for ind in inds:
            if y[ind] == 0.0:continue
            if not block:block.append(ind)
            else:
                if block[-1] == ind-1 and y[ind] == y[ind-1]:
                    block.append(ind)
                else:
                    ninds.append(int(np.median(block)))
                    block = [ind]
        if block:ninds.append(int(np.median(block)))
        return ninds

    def find_period_in_window(self,t,x):
        w = int(self.window)
        y = morph.grey_dilation(x,size = w)
        inds = np.argwhere(x == y)
        inds = self.hone(inds,x)

        plt.plot(t,x)
        plt.plot(t,y)
        plt.plot([t[i] for i in inds],[x[j] for j in inds])
        plt.show()

        if not inds:return None,None,None
        time = np.zeros((inds[-1]-inds[0],))
        period = np.zeros((inds[-1]-inds[0],))
        amp = np.zeros((inds[-1]-inds[0],))
        time[0:inds[-1]] = t[inds[0]:inds[-1]]
        for idx in range(1,len(inds)):
            icnt = inds[idx]-inds[idx-1]
            xs = x[inds[idx-1]:inds[idx]]
            a = 0.5 * (xs[0] + xs[-1] - 2 * np.min(xs))
            p = t[inds[idx]] - t[inds[idx-1]]
            dslice = slice(inds[idx-1]-inds[0],inds[idx]-inds[0])
            amp[dslice] = [a for ix in range(icnt)]
            period[dslice] = [p for ix in range(icnt)]
        return time,period,amp

    def _target_settables(self,*args,**kwargs):
        self.valid_regimes = ['per trajectory']
        self.valid_inputs = self._valid_inputs(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        if self.dater_ids is None or self.dater_ids == ['all']:
            self.dater_ids = capture_targetable

        targetlist = ['time'] 
        for d in self.dater_ids:
            if d == 'time':continue
            targetlist.append(d+'-period')
            targetlist.append(d+'-amplitude')
        self.targetlist = targetlist
        self.capture_targets = targetlist[:]

        #self.capture_targets = self.dater_ids
        self.output.targeted = lfu.intersect_lists(
            self.output.targeted,self.capture_targets)
        lpp.post_process_abstract._target_settables(self,*args,**kwargs)

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self._target_settables(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        #use a spin widget to select a location in the domain
        #   or a text box to support true slicing
        self.widg_templates.append(
            lgm.interface_template_gui(
                keys = [['window']], 
                instances = [[self]], 
                widgets = ['text'], 
                box_labels = ['Window'], 
                initials = [[self.window]]))
        self.widg_templates.append(
            lgm.interface_template_gui(
                keys = [['dater_ids']], 
                instances = [[self]], 
                widgets = ['check_set'], 
                box_labels = ['To Measure'], 
                append_instead = [True], 
                provide_master = [True], 
                labels = [capture_targetable]))
        lpp.post_process_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

# return valid **kwargs for periodfinder based on msplit(line)
def parse_line(split,ensem,procs,routs):
    # MUST SUPPORT 'all'....
    #if 'all' in relevant:proc.dater_ids = proc._targetables(0, ensem)
    #else: proc.dater_ids = relevant

    targets = lfu.msplit(split[3],',')
    window = split[4]
    inputs = lpp.parse_process_line_inputs(split[2],procs,routs)
    pargs = {
        'name':split[0],
        'variety':split[1],
        'input_regime':inputs,
        'dater_ids':targets,
        'window':window,
            }
    return pargs

###############################################################################

if __name__ == 'modular_core.postprocessing.periodfinding':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lpp.process_types['period finder'] = (period_finder,parse_line)

###############################################################################










