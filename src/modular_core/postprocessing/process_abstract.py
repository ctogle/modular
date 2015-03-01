import modular_core.fundamental as lfu
import modular_core.settings as lset

import modular_core.data.batch_target as dba
import modular_core.io.liboutput as lo

import pdb,types,time,math,os
import numpy as np
#np.seterr(divide = 'raise')

if __name__ == 'modular_core.postprocessing.process_abstract':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'process_abstract of modular_core'

process_types = {}

###############################################################################
'''#
def parse_postproc_line(*args):
    data = args[0]
    ensem = args[1]
    parser = args[2]
    procs = args[3]
    routs = args[4]
    split = [item.strip() for item in data.split(':')]
    for proc_type in valid_postproc_base_classes:
        if split: name = split[0]
        if len(split) > 1:
            if split[1].strip() == proc_type._tag:
                _always = ensem.postprocess_plan.always_sourceable
                proc = proc_type._class(label = name, 
                    parent = ensem.postprocess_plan, 
                    always_sourceable = _always)
                procs.append(proc)
                    elif proc_type._tag == 'one to one binary operation':
                        ops = ['/', '*', '+', '-']
                        li = split[3]
                        for op in ops:
                            if op in li: proc.operation = op

                        proc.domain = li[li.find('of') + 2:].strip()
                        inputs = [item.strip() for item in 
                            li[:li.rfind('of')].split(proc.operation)]
                        proc.input_1, proc.input_2 = inputs[0], inputs[1]
                        #print 'one to one binary operation parsing not done'

                    elif proc_type._tag == 'period finding':
                        print 'period finding parsing not done'

    ensem.postprocess_plan._add_process(new = proc)
    if lfu.using_gui(): proc._widget(0, ensem)
    else: proc._target_settables(0, ensem)
'''#
###############################################################################
###############################################################################
###############################################################################






###############################################################################
### post_process_abstract is the base class of general post processes
###   subclasses of post_process_abstract provide actual analysis
###############################################################################

class post_process_abstract(lfu.mobject):

    #ABSTRACT
    '''#
    #a post process can:
    #   operate on each trajectory individually, preserving structure
    #   operate on a collection of trajectories
    #       these collections can be organized in a meaningful way
    #           a collection for each location on parameter space
    #               can have its own, or inherit a parameter space for this
    #           should design some other partitioning mechanism, for arbitrary collections
    #       the collection of all trajectories - simplest default behavior
    #
    #   each post_process must specify which of these regimes it can and will obey
    #
    #in general:
    #   self.data contains the result for processing by an output_plan
    #           Note: this is not the current implementation but should be
    #           if necessary to support nontrivial post process hierarchies
    '''#

    def _string_inputs(self):
        inps = []
        valid_inputs = self._valid_inputs(None,self.parent.parent)
        if type(self.input_regime) is types.ListType:
            for input_ in self.input_regime:
                if input_.startswith(self.always_sourceable[0]): numb = 0
                else: numb = valid_inputs.index(input_) - 1
                inps.append(numb)
        else:
            input_ = self.input_regime
            if input_.startswith(self.always_sourceable[0]): numb = 0
            else: numb = valid_inputs.index(input_) - 1
            inps.append(numb)
        inps = ', '.join([str(inp) for inp in inps])
        return inps

    def _string(self):
        return '\t' + self.label + ' : abstract'

    def __init__(self,*args,**kwargs):
        self._default('name','a post process',**kwargs)
        self._default('always_sourceable',[],**kwargs)
        self._default('fitting_aware',True,**kwargs)
        self._default('single_input',False,**kwargs)
        self._default('valid_regimes',['all trajectories'],**kwargs)
        self._default('regime','all trajectories',**kwargs)
        always = self.always_sourceable[:]
        self._default('valid_inputs',always,**kwargs)
        ireg = always[0] if self.single_input else always[:]
        self._default('input_regime',ireg,**kwargs)
        self._default('capture_targets',[],**kwargs)
        oname = self.name + ' output'
        self.output = lo.output_plan(name = oname,parent = self)
        self.children = [self.output]
        lfu.mobject.__init__(self,*args,**kwargs)

    def __call__(self,*args,**kwargs):
        self._initialize(*args,**kwargs)
        self._process(*args,**kwargs)

    def _initialize(self,*args,**kwargs):pass

    # actually runs the process, setting the result at attribute data
    def _process_______(self,*args,**kwargs):
        method = self.method
        self._regime(args[0])
        pool = self._start_pool(*args,**kwargs)
        sources = self._source_reference(1,*args,**kwargs)

        def zip_list(target,new_list):
            if target.children:
                target_names = [targ.name for targ in target.children[0].data]

                pdb.set_trace()

                for k in range(len(target.children)):
                    valid = [dater for dater in new_list.children[k] 
                        if dater.name not in target_names]
                    target.children[k].extend(valid)
            else: target.children.extend(new_list.children)

        for src in sources:zip_list(pool,src.data)
        
        if 'p_space' in kwargs.keys():pspace = kwargs['p_space']
        else:pspace = args[0].cartographer_plan

        margs = (method,pool,pspace)
        if self.regime == 'per trajectory':self._per_trajectory(*margs)
        elif self.regime == 'all trajectories':self._all_trajectories(*margs)
        elif self.regime == 'by parameter space':self._by_parameter_space(*margs)

    # run the method on each trajectory by itself
    def _per_trajectory(self,method,pool,pspace = None):
        self.data = dba.batch_node(
            children = [method(trajectory) for trajectory in pool.children])

    # run the method on the batch of all trajectories
    def _all_trajectories(self,method,pool,pspace = None):
        self.data = dba.batch_node(children = [method(pool)])

    # run the method on each parameter space location batch
    def _by_parameter_space(self,method,pool,pspace):
        results = []
        for tdx in range(len(pspace.trajectory)):
            results.append(method(pool.children[tdx]))
        self.data = dba.batch_node(children = results)

    # determine how process is run based on ensemble settings
    def _regime(self,*args,**kwargs):
        self.output.flat_data = False
        mappspace = self.parent.parent.cartographer_plan.use_plan

        if 'per trajectory' in self.valid_regimes:
            self.regime = 'per trajectory'
        elif 'by parameter space' in self.valid_regimes and mappspace:
            self.regime = 'by parameter space'
        elif 'all trajectories' in self.valid_regimes:
            self.regime = 'all trajectories'

    # initialize a data structure based on chosen inputs
    def _start_pool(self,*args,**kwargs):
        if 'simulation' in self.input_regime:return args[1]
        else:return dba.batch_node()

    # return input sources found in sources based on input_regime
    def _handle_sources(self,sources):
        if type(self.input_regime) is types.ListType:
            inputs = [lfu.grab_mobj_by_name(inp,sources) for inp in 
                self.input_regime if not inp in self.always_sourceable]
        else:
            if not self.input_regime in self.always_sourceable:
                inputs = [lfu.grab_mobj_by_name(self.input_regime,sources)]
            else: inputs = []
        return inputs

    # aggregate sources with no fitting
    def _source_reference_nofit(self,*args,**kwargs):
        sources = self.parent.processes
        inputs = self._handle_sources(sources)
        return inputs

    # aggregate sources with fitting
    def _source_reference_fit(self,*args,**kwargs):
        procs = self.parent.processes
        routs = self.parent.parent.fitting_plan.routines
        sources = procs + routs
        inputs = self._handle_sources(sources)
        return inputs

    # return the proper list of input objects based on input_regime
    def _source_reference(self,*args,**kwargs):
        if self.fitting_aware:return self._source_reference_fit(*args,**kwargs)
        else:return self._source_reference_nofit(*args,**kwargs)

    # return the list of possible inputs with no fitting routine support
    def _valid_inputs_nofit(self,*args,**kwargs):
        post_procs = args[1].postprocess_plan.processes
        self_dex = lfu.grab_mobj_index_by_name(self.name,post_procs)
        processes = lfu.grab_mobj_names(post_procs)[:self_dex]
        if self.name in processes:processes.remove(self.name)
        return self.always_sourceable + processes

    # return the list of possible inputs with fitting routine support
    def _valid_inputs_fit(self,*args,**kwargs):
        post_procs = args[1].postprocess_plan.processes
        self_dex = lfu.grab_mobj_index_by_name(self.name,post_procs)
        processes = lfu.grab_mobj_names(post_procs)[:self_dex]
        routines = lfu.grab_mobj_names(args[1].fitting_plan.routines)
        if self.name in processes:processes.remove(self.name)
        return self.always_sourceable + processes + routines

    # return the list of possible inputs
    def _valid_inputs(self,*args,**kwargs):
        if self.fitting_aware:return self._valid_inputs_fit(*args,**kwargs)
        else:return self._valid_inputs_nofit(*args,**kwargs)       

    # return the list of possible inputs based on outputs of selected inputs
    def _targetables(self,*args,**kwargs):
        targets = []
        # this will work because self.input_regime would be 'simulation' if
        # self._single_input_
        if 'simulation' in self.input_regime:
            #ensem = self.parent.parent
            ensem = args[1]
            targets.extend(ensem.run_params['plot_targets'][:])
        for source in self._source_reference(*args,**kwargs):
            targets.extend(source.capture_targets[:])
        if 'always_sources' in kwargs.keys():
            for src in kwargs['always_sources']:
                targets.extend(src.capture_targets[:])
        return lfu.uniqfy(targets)

    def _target_settables(self,*args,**kwargs):pass

    def _widget(self,*args,**kwargs):
        window = args[0]
        self._sanitize(*args,**kwargs)

        if self.valid_inputs:
            if self.single_input:
                self.widg_templates.append(
                    lgm.interface_template_gui(
                        panel_position = (0, 2), 
                        widgets = ['radio'], 
                        tooltips = [['Requires GUI update (Ctrl+G)' 
                                for input_ in self.valid_inputs]], 
                        #append_instead = [True], 
                        initials = [[self.input_regime]], 
                        instances = [[self]], 
                        keys = [['input_regime']], 
                        labels = [self.valid_inputs], 
                        refresh = [[True]], 
                        window = [[window]], 
                        box_labels = ['Input Data']))
            else:
                self.widg_templates.append(
                    lgm.interface_template_gui(
                        panel_position = (0, 2), 
                        widgets = ['check_set'], 
                        tooltips = [['Requires GUI update (Ctrl+G)' 
                                for input_ in self.valid_inputs]], 
                        append_instead = [True], 
                        instances = [[self]], 
                        keys = [['input_regime']], 
                        refresh = [[True]], 
                        rewidget = [[True]], 
                        labels = [self.valid_inputs], 
                        box_labels = ['Input Data']))

        self.widg_templates.append(
            lgm.interface_template_gui(
                keys = [['name']], 
                read_only = [True],
                minimum_sizes = [[(150, 50)]], 
                instances = [[self]], 
                widgets = ['text'], 
                box_labels = ['Post Process Name']))
        lfu.mobject._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

###############################################################################
### utility functions
###############################################################################

# prompt user for post_process type if needed and create
def post_process(variety = None,**pargs):
    opts = process_types.keys()
    if variety is None:
        if lfu.using_gui:
            variety = lgd.create_dialog(
                title = 'Choose Post Process Type',
                options = opts,variety = 'radioinput')
        else:
            prequest = 'enter a post process type:\n\t'
            for op in opts:prequest += op + '\n\t'
            prequest += '\n'
            variety = raw_input(prequest)
    if not variety in opts:
        print 'unrecognized post process type:',variety
        return
    proc = process_types[variety][0](**pargs)
    return proc

# parse one mcfg line into a post_process and add to ensems plan
def parse_process_line(line,ensem,parser,procs,routs,targs):
    print 'parse process line:\n\t"',line,'"\n'
    proc_types = process_types.keys()
    spl = lfu.msplit(line)
    variety = spl[1]
    pargs = process_types[variety][1](spl,ensem,procs,routs)
    proc = post_process(**pargs)
    procs.append(proc)
    ensem.postprocess_plan._add_process(new = proc)
    if lfu.using_gui:proc._widget(0,ensem)
    else:proc._target_settables(0,ensem)

# turn the comma separated int list into an input_regime
def parse_process_line_inputs(inputs,procs,routs):
    ips = [int(v) for v in lfu.msplit(inputs,',')]
    reg = []
    for inp in ips:
        if inp == 0:reg.append('simulation')
        elif inp <= len(procs):reg.append(procs[inp - 1].name)
    return reg

###############################################################################
###############################################################################










