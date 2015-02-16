import modular_core.libfundamental as lfu

import modular_core.data.libdatacontrol as ldc
import modular_core.postprocessing.libpostprocess as lpp
import modular_core.criteria.trajectory_criterion as ltc

import pdb,sys
import numpy as np

###############################################################################
### reorganize arranges data based on the parameter space
### this allows plotting of a post process versus run_parameter values
###############################################################################

class reorganize(lpp.post_process_abstract):

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

    #def _initialize(self):
    #    self._target_settables(0,self.parent.parent)
    #
    #    if 'all' in self.dater_ids: pdb.set_trace()
    #
    #    lpp.post_process_abstract._initialize()

    def _string(self):
        #reorg : reorganize data : 2 : all
        inps = self._string_inputs()
        strs = [self.name,'reorganize data',inps,'all']
        return '\t' + ' : '.join(strs)

    def _process(self,*args,**kwargs):
        cplan = args[0].cartographer_plan
        fplan = args[0].fitting_plan

        #this is a hack to fix an undiagnosed bug
        #self.valid_regimes = ['all trajectories']

        if not cplan.use_plan and not fplan.use_plan:
            print 'not mapping p-space\n\treorganize ignored...'
        else:post_process._process(self,*args,**kwargs)

    def _all_trajectories(self,method,pool,pspace):
        self.data = [method(pool,pspace)]
        self.output.flat_data = False

    #take a collection of trajectories in 1 - 1 with p_space trajectory
    #create a dater of indices for that trajectory
    #create new daters in 1 - 1 with that dater, 
    #one for each dater in each trajectory of the original collection, 
    #which aggregates the original collection of trajectories
    def data_by_trajectory(self, *args, **kwargs):
        trajectory = args[0]
        pspace_map = args[1]

        data = ldc.scalars_from_labels(['parameter space location index']+\
                self.axis_labels + [label for label in self.dater_ids])
        for dex,locale in enumerate(trajectory):
            data[0].scalars.append(dex)
            pspace_locale_values = pspace_map.trajectory[dex].location
            [dater.scalars.append(float(loc)) for loc,dater in 
                zip(pspace_locale_values,data[1:len(self.axis_labels) + 1])]
            for dater in data[len(self.axis_labels) + 1:]:
                value = lfu.grab_mobj_by_name(dater.name,locale).scalars[-1]
                dater.scalars.append(value)

        surf_targets = ['parameter space location index'] + self.dater_ids
        data.append(ldc.surface_vector_reducing(data, 
            self.axis_labels,surf_targets,'reorg surface vector'))
        return data

    def _target_settables(self,*args,**kwargs):
        self.valid_inputs = self._valid_inputs(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        if self.dater_ids is None: self.dater_ids = []

        cplan = args[1].cartographer_plan
        self.axis_labels = []
        if cplan.parameter_space:
            [self.axis_labels.append(ax.name) for 
                ax in cplan.parameter_space.axes]

        self.capture_targets = ['parameter space location index'] +\
            self.axis_labels + [label for label in self.dater_ids] +\
            ['reorg surface vector']
        self.output.targeted = lfu.intersect_lists(
            self.output.targeted,self.capture_targets)
        lpp.post_process_abstract._target_settables(self,*args,**kwargs)

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
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










