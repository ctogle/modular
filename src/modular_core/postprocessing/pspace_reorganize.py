import modular_core.fundamental as lfu

import modular_core.data.datacontrol as ldc
import modular_core.data.single_target as dst
import modular_core.data.batch_target as dba
import modular_core.postprocessing.process_abstract as lpp

import pdb,sys
import numpy as np

###############################################################################
### reorganize arranges data based on the parameter space
### this allows plotting of a post process versus run_parameter values
###############################################################################

class reorganize(lpp.post_process_abstract):

    def _string(self):
        #reorg : reorganize data : 2 : all
        inps = self._string_inputs()
        strs = [self.name,'reorganize data',inps,'all']
        return '\t' + ' : '.join(strs)

    def _post_init(self,*args,**kwargs):
        print 'daters from reorg', self.dater_ids
        if self.dater_ids == ['all']:
            self.dater_ids = self._targetables(*args,**kwargs)

    #the purpose of this process is to reorganize data
    #so that measurements are taken as a function of p-space index
    #within the p-space trajectory, to be resolved into color plots
    #representing 2-d subspaces of the p-space
    #thus any process which can use p-space, can be reorganized
    #if not using p-space, data won't be in the proper structure - 
    # this process then cannot be used and must be ignored
    def __init__(self,*args,**kwargs):
        self._default('name','reorganize',**kwargs)
        regs = ['all trajectories','by parameter space']
        self._default('valid_regimes',regs,**kwargs)
        self._default('regime','all trajectories',**kwargs)
        self._default('dater_ids',None,**kwargs)
        self.method = self.data_by_trajectory
        lpp.post_process_abstract.__init__(self,*args,**kwargs)

    def _process(self,*args,**kwargs):
        cplan = args[0].cartographer_plan
        fplan = args[0].fitting_plan

        #this is a hack to fix an undiagnosed bug ### IS THIS STILL NECESSARY?
        #self.valid_regimes = ['all trajectories']

        if not cplan.use_plan and not fplan.use_plan:
            self.data = dba.batch_node()
            print 'not mapping p-space\n\treorganize ignored...'
        else:lpp.post_process_abstract._process(self,*args,**kwargs)

    # overloaded to pass pspace into method
    def _all_trajectories(self,method,pool,pspace):
        self.data = dba.batch_node(children = [method(pool,pspace)])
        self.output.flat_data = False

    # overloaded to pass pspace into method
    def _by_parameter_space(self,method,pool,pspace):
        self._all_trajectories(method,pool,pspace)

    #take a collection of trajectories in 1 - 1 with p_space trajectory
    #create a dater of indices for that trajectory
    #create new daters in 1 - 1 with that dater, 
    #one for each dater in each trajectory of the original collection, 
    #which aggregates the original collection of trajectories
    def data_by_trajectory(self,*args,**kwargs):
        pool = args[0]
        trajectory = pool.children
        pspace_trajectory = args[1]
        if pspace_trajectory is None:
            print 'not mapping p-space\n\treorganize ignored...'
            bnode = dba.batch_node(dshape = ())
            return bnode

        axcnt = len(self.axis_labels)
        t0lnames = trajectory[0].targets
        ptrajdexes = []
        ptrajaxvals = [[] for x in range(axcnt)]
        datervals = [[] for x in range(len(self.dater_ids))]
        for dex,locale in enumerate(trajectory):
            locale._recover()
            locale_data = locale.data
            ptrajdexes.append(dex)
            pspace_locale_values = pspace_trajectory[dex].location
            for tdx in range(axcnt):
                ptrajaxvals[tdx].append(float(pspace_locale_values[tdx]))

            for ddx in range(len(self.dater_ids)):
                dname = self.dater_ids[ddx]
                value = locale_data[ddx][-1]
                datervals[ddx].append(value)
            locale._stow()

        tcount = len(self.capture_targets)
        dshape = (tcount,len(trajectory))
        data = np.zeros(dshape,dtype = np.float)
        data[0] = np.array(ptrajdexes)
        for tdx in range(axcnt):
            data[tdx+1] = np.array(ptrajaxvals[tdx])
        for ddx in range(len(self.dater_ids)):
            data[ddx+axcnt+1] = np.array(datervals[ddx])
        self.surf_targets = ['parameter space location index'] + self.dater_ids

        bnode = self._init_data(dshape,self.capture_targets,
            pspace_axes = self.axis_labels,surface_targets = self.surf_targets)
        #bnode = dba.batch_node(
        #    dshape = dshape,targets = self.capture_targets,
        #    pspace_axes = self.axis_labels,surface_targets = self.surf_targets)
        bnode._trajectory(data)
        return bnode

    def _target_settables(self,*args,**kwargs):
        self.valid_inputs = self._valid_inputs(*args,**kwargs)
        if self.dater_ids is None or self.dater_ids == ['all']:
            self.dater_ids = self._targetables(*args,**kwargs)

        cplan = args[1].cartographer_plan
        self.axis_labels = []
        if cplan.parameter_space:
            [self.axis_labels.append(ax.name) for 
                ax in cplan.parameter_space.axes]

        self.capture_targets = ['parameter space location index'] +\
            self.axis_labels + self.dater_ids[:] + ['reducer']
        self.output.targeted = lfu.intersect_lists(
            self.output.targeted,self.capture_targets)
        lpp.post_process_abstract._target_settables(self,*args,**kwargs)

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self._target_settables(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                keys = [['dater_ids']], 
                instances = [[self]], 
                widgets = ['check_set'], 
                box_labels = ['Relevant Data'], 
                append_instead = [True], 
                provide_master = [True], 
                labels = [capture_targetable]))
        lpp.post_process_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

# return valid **kwargs for reorganize based on msplit(line)
def parse_line(split,ensem,procs,routs):
    #reorg : reorganize data : 2 : all
    targets = lfu.msplit(split[3],',')
    inputs = lpp.parse_process_line_inputs(split[2],procs,routs)
    pargs = {
        'name':split[0],
        'variety':split[1],
        'input_regime':inputs,
        'dater_ids':targets,
            }
    return pargs

###############################################################################

if __name__ == 'modular_core.postprocessing.pspace_reorganize':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lpp.process_types['reorganize'] = (reorganize,parse_line)

###############################################################################










