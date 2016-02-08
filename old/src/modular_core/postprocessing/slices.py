import modular_core.fundamental as lfu

import modular_core.data.datacontrol as ldc
import modular_core.data.single_target as dst
import modular_core.data.batch_target as dba
import modular_core.postprocessing.process_abstract as lpp

import pdb,sys,math
import numpy as np

###############################################################################
### trajectory_slice extracts a slice of data from any input
###############################################################################

class trajectory_slice(lpp.post_process_abstract):

    def _string(self):
        #slices : slice from trajectory : 1 : all : -1
        inps = self._string_inputs()
        phrase = 'all'
        slice_dex = str(self.slice_dex)
        strs = [self.name,'trajectory slice',inps,phrase,slice_dex]
        return '\t' + ' : '.join(strs)

    def __init__(self,*args,**kwargs):
        self._default('name','slices',**kwargs)
        self._default('valid_regimes',['per trajectory'],**kwargs)
        self._default('regime','per trajectory',**kwargs)

        self._default('dater_ids',None,**kwargs)
        self._default('slice_dex',-1,**kwargs)
        self.method = 'slice_from_trajectory'
        #self.method = self.slice_from_trajectory
        lpp.post_process_abstract.__init__(self,*args,**kwargs)

    def _slice(self):
        try:
            slic = int(self.slice_dex)
            scnt = 1
        except ValueError:
            col_dex = self.slice_dex.index(':')
            slice_1 = int(self.slice_dex[:col_dex])
            slice_2 = int(self.slice_dex[col_dex:])
            slic = slice(slice_1,slice_2)
            scnt = slice_2 - slice_1
        return slic,scnt

    def slice_from_trajectory(self,*args,**kwargs):
        pool = args[0]

        slic,scnt = self._slice()
        tcount = len(self.dater_ids)
        dshape = (tcount,scnt)
        data = np.zeros(dshape,dtype = np.float)

        trajectory = pool.data
        tnames = pool.targets
        for px,pt in enumerate(tnames):
            data[self.dater_ids.index(pt)] = trajectory[px][slic]

        #bnode = dba.batch_node(dshape = dshape,targets = self.dater_ids)
        bnode = self._init_data(dshape,self.dater_ids)
        bnode._trajectory(data)
        return bnode

    def _target_settables(self,*args,**kwargs):
        self.valid_regimes = ['per trajectory']
        self.valid_inputs = self._valid_inputs(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        if self.dater_ids is None or self.dater_ids == ['all']:
            self.dater_ids = capture_targetable

        #is this why output plans require one more update all the time it seems?
        self.capture_targets = self.dater_ids
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
                keys = [['slice_dex']], 
                instances = [[self]], 
                widgets = ['text'], 
                box_labels = ['Slice Index'], 
                initials = [[self.slice_dex]]))
        self.widg_templates.append(
            lgm.interface_template_gui(
                keys = [['dater_ids']], 
                instances = [[self]], 
                widgets = ['check_set'], 
                box_labels = ['To Slice'], 
                append_instead = [True], 
                provide_master = [True], 
                labels = [capture_targetable]))
        lpp.post_process_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

# return valid **kwargs for slices based on msplit(line)
def parse_line(split,ensem,procs,routs):
    # MUST SUPPORT 'all'....
    #if 'all' in relevant:proc.dater_ids = proc._targetables(0, ensem)
    #else: proc.dater_ids = relevant

    targets = lfu.msplit(split[3],',')
    slice_dex = split[4]
    inputs = lpp.parse_process_line_inputs(split[2],procs,routs)
    pargs = {
        'name':split[0],
        'variety':split[1],
        'input_regime':inputs,
        'dater_ids':targets,
        'slice_dex':slice_dex,
            }
    return pargs

###############################################################################

if __name__ == 'modular_core.postprocessing.slices':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lpp.process_types['trajectory slice'] = (trajectory_slice,parse_line)

###############################################################################










