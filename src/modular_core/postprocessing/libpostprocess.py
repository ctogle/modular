import modular_core.libfundamental as lfu
import modular_core.libsettings as lset

import modular_core.data.batch_target as dba
import modular_core.io.liboutput as lo

import pdb,types,time,math,os
import numpy as np
#np.seterr(divide = 'raise')

if __name__ == 'modular_core.postprocessing.libpostprocess':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'libpostprocess of modular_core'

process_types = {}

###############################################################################
### post_process_plan manages post_processes
###############################################################################

class post_process_plan(lfu.plan):

    def __init__(self,*args,**kwargs):
        self._default('name','post process plan',**kwargs)
        self._default('processes',[],**kwargs)
        use = lset.get_setting('postprocessing')
        self._default('use_plan',use,**kwargs)
        fit = lset.get_setting('fitting_aware')
        self._default('fitting_aware',fit,**kwargs)
        self._default('display_children',False,**kwargs)
        self._default('always_sourceable',[],**kwargs)
        self._default('selected_process',None,**kwargs)
        lfu.plan.__init__(self,*args,**kwargs)
        self.current_tab_index = 0

    # perform processes, measure time, return data pool
    def _enact(self,*args,**kwargs):
        for process in self.processes:
            stime = time.time()
            process(*args,**kwargs)
            dura = time.time() - stime
            print 'completed post process',process.name,'in',dura,'seconds'
        return args[1]

    # reset children and processes
    def _reset_process_list(self):
        del self.processes[:]
        del self.children[:]

    # add new post process; default to meanfields
    def _add_process(self,new = None):
        if new is None:
            #proc_class_def = process_types['meanfields'][0]
            #new = proc_class_def(parent = self)
            new = post_process(parent = self)
        new.fitting_aware = self.fitting_aware
        new.always_sourceable = self.always_sourceable
        new.parent = self

        if hasattr(self.parent,'run_params'):
            ops = self.parent.run_params['output_plans']
            ops[new.name+' output'] = new.output

        self.processes.append(new)
        self.children.append(new)
        self.parent.module._rewidget(True)
        self._rewidget(True)

    # remove selected post process
    def _del_process(self,selected = None):
        if selected is None:selected = self._selected()
        if selected:
            self.processes.remove(selected)
            self.children.remove(selected)

            if hasattr(self.parent,'run_params'):
                ops = self.parent.run_params['output_plans']
                del ops[select.name+' output']

        self._rewidget(True)

    # shift a process up in the post process hierarchy
    def _process_up(self):
        select = self._selected()
        if select:
            select_dex = lfu.grab_mobj_dex_by_name(
                select.name,self.processes)
            self.processes.pop(select_dex)
            self.processes.insert(select_dex - 1, select)
            self._rewidget_processes()

    # shift a process down in the post process hierarchy
    def _process_down(self):
        select = self._selected()
        if select:
            select_dex = lfu.grab_mobj_dex_by_name(
                select.name,self.processes)
            self.processes.pop(select_dex)
            self.processes.insert(select_dex + 1, select)
            self._rewidget_processes()

    # propagate rewidg to children processes
    def _rewidget_processes(self,rewidg = True):
        for p in self.processes:p._rewidget(rewidg)

    # return the currently selected post process if there is one
    def _selected(self):
        if not hasattr(self,'process_selector'):print 'no selector'; return
        selector = self.process_selector[0].layout().itemAt(0).widget()
        dex = selector.currentIndex()-1
        if dex in range(len(self.processes)):
            return self.processes[dex]

    # make sure children can see ensemble...
    def _rewidget_children(self,*args,**kwargs):
        infos = (kwargs['infos'],self.parent)
        for child in self.children:
            if child._rewidget(**kwargs):
                child._widget(*infos)

    def _tab_book_pages(self,*args,**kwargs):
        pages = []
        for proc in self.processes:
            proc._widget(*args,**kwargs)
            pp_page = lgm.interface_template_gui(
                widgets = ['panel'], 
                scrollable = [True], 
                templates = [proc.widg_templates])
            pages.append((proc.name,[pp_page]))
        return pages

    def _widget(self,*args,**kwargs):
        window = args[0]
        select_label = self.selected_process
        self._sanitize(*args,**kwargs)
        primary_template = lgm.interface_template_gui(
            layout = 'grid', 
            grid_spacing = 10, 
            widg_positions = [(0,0),(0,2),(1,2),(2,2),(3,2),(4,2)], 
            widg_spans = [(3,2)]+[None]*5, 
            widgets = ['mobj_catalog','button_set'], 
            verbosities = [1,1], 
            instances = [[self.processes,self],None], 
            keys = [[None,'selected_process'],None], 
            handles = [(self,'process_selector'),None], 
            labels = [None,
                ['Add Post Process','Remove Post Process', 
                'Move Up In Hierarchy','Move Down In Hierarchy']], 
            initials = [[select_label],None], 
            bindings = [None,
                [lgb.create_reset_widgets_wrapper(window,self._add_process),
                lgb.create_reset_widgets_wrapper(window,self._del_process), 
                lgb.create_reset_widgets_wrapper(window,self._process_up), 
                lgb.create_reset_widgets_wrapper(window,self._process_down)]])
        if self.display_children:
            childrens_template = lgm.interface_template_gui(
                widgets = ['tab_book'], 
                verbosities = [0], 
                pages = [self._tab_book_pages(*args,**kwargs)], 
                initials = [[self.current_tab_index]], 
                handles = [(self, 'tab_ref')], 
                instances = [[self]], 
                keys = [['current_tab_index']])
            split_template = lgm.interface_template_gui(
                widgets = ['splitter'], 
                orientations = [['horizontal']], 
                templates = [[primary_template,childrens_template]])
            self.widg_templates.append(split_template)
        else: self.widg_templates.append(primary_template)
        lfu.plan._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################





###############################################################################
###############################################################################
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
    def _process(self,*args,**kwargs):
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
            locale = pspace.trajectory[tdx]
            traj_count = locale.trajectory_count
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

        print 'type input regime',type(self.input_regime)

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





# BINNING SECTION NEEDS CLEANUP
# BINNING SECTION NEEDS CLEANUP
# BINNING SECTION NEEDS CLEANUP

def select_for_binning____(pool,be_binned,be_meaned):
    #print 'be meaned', be_meaned

    if hasattr(pool,'_bin_select'):
        return pool._bin_select(be_binned,be_meaned)




    if hasattr(pool,'_flatten_'):flat_pool = pool._flatten_(pool)

    elif hasattr(pool,'_flatten_children'):
        flat_pool = pool._flatten_children()

    else: flat_pool = lfu.flatten(pool)#[item for sublist in pool for item in sublist]
    bin_lookup  = [pool[k][j].name == be_binned for k in range(len(pool)) for j in range(len(pool[k]))]
    mean_lookup = [pool[k][j].name == be_meaned for k in range(len(pool)) for j in range(len(pool[k]))]

    if not bin_lookup or not mean_lookup:pdb.set_trace()

    bin_axes = [flat_pool[k] for k in range(len(flat_pool)) if bin_lookup[k] == True]
    mean_axes = [flat_pool[k] for k in range(len(flat_pool)) if mean_lookup[k] == True]
    return bin_axes,mean_axes

def bin_scalars_______(axes,ax_vals,bin_res,ordered = True,
        bin_basis_override = None,bin_max = None,bin_min = None):



    if bin_basis_override is None: baxes = axes
    else: baxes = bin_basis_override
    if bin_min is None:bin_min = min([min(ax.scalars) for ax in baxes])
    if bin_max is None:bin_max = max([max(ax.scalars) for ax in baxes])
    orders = 1000000000000000000.0
    bin_res = (bin_max - bin_min) / bin_res
    bins = [x / orders for x in range(int(bin_min*orders),int(bin_max*orders),int(bin_res*orders))]
    vals = [[] for k in range(len(bins))]
    bin_bump = bin_res/2.0

    if ordered: #for when ordering is monotonically increasing
        j_last = [0]*len(axes)
        for i in range(len(bins)):
            threshold_top = bins[i] + bin_bump
            for k in range(len(axes)):
                last_j = j_last[k]
                for j in range(last_j, len(axes[k].scalars)):
                    if axes[k].scalars[j] < threshold_top:
                        vals[i].append(ax_vals[k].scalars[j])
                    else:
                        j_last[k] = j
                        break

    else: #for when no ordering is assumed
        for i in range(len(bins)):
            try:threshold_bottom = threshold_top
            except:threshold_bottom = bins[i]
            threshold_top = bins[i] + bin_bump
            for k in range(len(axes)):
                for j in range(len(axes[k].scalars)):
                    if axes[k].scalars[j] < threshold_top and axes[k].scalars[j] > threshold_bottom:
                        vals[i].append(ax_vals[k].scalars[j])       

    return bins, vals

# BINNING SECTION NEEDS CLEANUP
# BINNING SECTION NEEDS CLEANUP
# BINNING SECTION NEEDS CLEANUP

###############################################################################
###############################################################################










