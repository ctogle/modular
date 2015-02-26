import modular_core.fundamental as lfu
import modular_core.parameterspaces as lpsp

import modular_core.fitting.routine as lfr
import modular_core.postprocessing.process_abstract as lpp
import modular_core.criteria.abstract as cab
import modular_core.io.liboutput as lo
import modular_core.io.libfiler as lf

import pdb,types
from cStringIO import StringIO

if __name__ == 'modular_core.simulationmodule':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'simulationmodule of modular_core'

###############################################################################
### a simulation module has hooks for working with an ensemble
###############################################################################

# this must be a single argument function because of map_async
def simulate(sim_args):
    print 'dummy simulate function'
    return np.array([])

class simulation_module(lfu.mobject):
    run_parameter_keys = [  
        'End Criteria','Capture Criteria','Plot Targets','Fit Routines',
        'Post Processes','Parameter Space Map','Multiprocessing','Output Plans']

    def _parse_mcfg_plot_targets(li,ensem,parser,procs,routs,targs):
        if not li in targs:targs.append(li)

    def _parse_mcfg_multiprocessing(li,ensem,parser,procs,routs,targs):
        key,val = li.split(':')
        if key.strip() == 'workers':
            ensem.multiprocess_plan.worker_count = int(val)

    def _parse_mcfg_ensemble(li,ensem,parser,procs,routs,targs):
        spl = [l.strip() for l in li.split(':')]
        which,value = spl
        if which.startswith('multiprocessing'):
            ensem.multiprocess_plan.use_plan = lfu.coerce_string_bool(value)
        elif spl[0].startswith('mapparameterspace'):
            ensem.cartographer_plan.use_plan = lfu.coerce_string_bool(value)
        elif spl[0].startswith('fitting'):
            ensem.fitting_plan.use_plan = lfu.coerce_string_bool(value)
        elif spl[0].startswith('postprocessing'):
            ensem.postprocess_plan.use_plan = lfu.coerce_string_bool(value)
        elif spl[0].startswith('trajectory_count'):
            ensem.num_trajectories = int(value)
        ensem._rewidget(True)

    parse_types = [
        'end_criteria',
        'capture_criteria',
        'post_processes',
        'fit_routines', 
        'output_plans',
        'parameter_space',
        'plot_targets',
        'multiprocessing',
        'ensemble']
    parse_funcs = [
        cab.parse_criterion_line,
        cab.parse_criterion_line,
        lpp.parse_process_line, 
        lfr.parse_fitting_line,
        lo.parse_output_plan_line,
        None,
        _parse_mcfg_plot_targets,
        _parse_mcfg_multiprocessing,
        _parse_mcfg_ensemble]

    def __init__(self,*args,**kwargs):
        self._default('timeout',0.0,**kwargs)
        # simulation is a single argument function that returns
        # finalized data - single argument will be self.sim_args
        self._default('simulation',simulate,**kwargs)
        lfu.mobject.__init__(self,*args,**kwargs)
        self.treebook_memory = [0,[],[]]
        self.module_memory = []
        self.parsers = {}
        for pt,pf in zip(self.parse_types,self.parse_funcs):
            self.parsers[pt] = pf

    # add one parsed run_parameter mobject to run_params
    def _add_parsed(self,new,parser,params):
        if type(new) is types.TupleType:
            label, item = new[0], new[1]
            params[parser][new[0]] = new[1]
        elif type(new) is types.ListType:
            params[parser].extend(new)
        elif not new is None:params[parser].append(new)

    # parse an mcfg and set the ensemble to reflect it
    def _parse_mcfg(self,mcfg,ensem):
        params = ensem.run_params
        with open(mcfg,'r') as handle:mlines = handle.readlines()

        plot_flag = False;targs = params['plot_targets']
        pspace_flag = False;pspace_parsed_flag = False;p_sub_sps = []
        procs = [];routs = []
        ensem.capture_targets = targs

        parser = ''
        parsers = self.parsers
        pkeys = parsers.keys()
                
        def parse_pspace():
            if len(p_sub_sps) > 1:print 'only parsing first p-scan space'
            if pspace_flag and not pspace_parsed_flag:
                lpsp.parse_pspace(p_sub_sps[0],ensem)

        def parse_pspace_line(li):
            if li.startswith('<product_space>'):
                cnt_per_loc = int(li[li.find('>') + 1:])
                p_sub_sps.append([('<product_space>', cnt_per_loc)])
            elif li.startswith('<zip_space>'):
                cnt_per_loc = int(li[li.find('>') + 1:])
                p_sub_sps.append([('<zip_space>', cnt_per_loc)])
            elif li.startswith('<fitting_space>'):
                p_sub_sps.append([('<fitting_space>', None)])
            else:p_sub_sps[-1].append([item.strip() for item in li.split(':')])

        lcnt = 0        
        max_lcnt = len(mlines) - 1
        while lcnt < max_lcnt:
            lcnt += 1
            li = mlines[lcnt].strip()
            iscomment = li.startswith('#')
            isparser = li.startswith('<') and li.endswith('>')
            if iscomment or not li: continue
            elif isparser:
                parser = li[1:-1]
                if parser == 'plot_targets':plot_flag = True
                elif parser == 'parameter_space':pspace_flag = True
                elif parser == 'post_processes' or parser == 'fit_routines':
                    parse_pspace()
                    pspace_parsed_flag = True
            else:
                if parser == 'parameter_space':parse_pspace_line(li)
                elif parser in pkeys:
                    new = parsers[parser](li,ensem,parser,procs,routs,targs)
                    if not new is None:self._add_parsed(new,parser,params)
                else:print 'parsing error', parser, li
        parse_pspace()

    # prepend a header to generated mcfgs
    #  mcfg is a stringIO object
    def _write_mcfg_header(self,mcfg):
        mcfg.write('# modular mcfg for ensemble "' + ensem.name)
        mcfg.write('" using module "' + ensem.module_name + '"\n\n')
    
    # write all of one sort of run_parameter, identified with key
    #  mcfg is a stringIO object
    def _write_mcfg_run_param_key(params,key,mcfg):
        def _write_param(param):
            if hasattr(param,'_string'):mcfg.write('\t'+param._string()+'\n')
            else:mcfg.write('\t'+str(param)+'\n')
        mcfg.write('<' + key + '>\n')
        if type(params[key]) is types.ListType:
            for subparam in params[key]:
                _write_param(subparam)
        elif type(params[key]) is types.DictionaryType:
            for subkey in params[key].keys():
                _write_param(params[key][subkey])
        mcfg.write('\n')

    # write the current ensemble to an mcfg file 
    def _write_mcfg(self,mcfg_path,ensem,mcfg = None):
        rparams = ensem.run_params
        if mcfg is None:mcfg = StringIO()
        self._write_mcfg_header(mcfg)
        self._write_mcfg_run_param_key(rparams,'end_criteria',mcfg)
        self._write_mcfg_run_param_key(rparams,'capture_criteria',mcfg)
        self._write_mcfg_run_param_key(rparams,'plot_targets',mcfg)
        if ensem.cartographer_plan.parameter_space:
            pspace = ensem.cartographer_plan._string()
            mcfg.write('<parameter_space>\n'+pspace+'\n')
        mpplan = ensem.multiprocess_plan._string()
        mcfg.write('<multiprocessing>\n'+mpplan+'\n')
        if ensem.postprocess_plan.post_processes:
            self._write_mcfg_run_param_key(rparams,'post_processes',mcfg)
        if ensem.fitting_plan.routines:
            self._write_mcfg_run_param_key(rparams,'fit_routines',mcfg)
        self._write_mcfg_run_param_key(rparams,'output_plans',mcfg)
        mcfg = mcfg.getvalue()
        lf.write_text(mcfg_path,mcfg)

    # set state that is changed at most once per pspace location
    # called outside of Pool processes and before self._set_parameters
    def _set_parameters_prepoolinit(self):
        print 'run params prepoolinit...'

    # set state that is changed at most once per pspace location
    def _set_parameters(self):
        print 'run params to location'
        self.sim_args = ()

    # initialize run parameters of an ensemble
    def _reset_parameters(self):
        ensem = self.parent
        ensem.simulation_plan._reset_criteria_lists()
        ensem.postprocess_plan._reset_process_list()
        ensem.run_params['plot_targets'] = ['iteration','time']
        ensem.capture_targets = ensem.run_params['plot_targets']
        output_plan = ensem.run_params['output_plans']['Simulation']
        def_targeted = ['iteration','time']
        output_plan.targeted = def_targeted[:]
        for w in output_plan.writers:w.targeted = def_targeted[:]

    # perform one simulation and return the data in the proper format
    def _simulate(self,*args,**kwargs):
        print 'simulation'

    # set state associated with gui
    def _gui_memory(self):
        self.module_memory = [lfu.data_container(
            selected_output_plan = 'Simulation')]

    def _sanitize(self,*args,**kwargs):
        self.module_memory = []
        lfu.mobject._sanitize(self,*args,**kwargs)

    def _panel_templates(self,window,ensem,target_labels = None):
        panel_template_lookup = []
        if target_labels:plot_target_labels = target_labels
        else:plot_target_labels = ['iteration','time']
        ensem.simulation_plan.plot_targets = plot_target_labels
        ensem.capture_targets = plot_target_labels
        sim_plan = ensem.simulation_plan
        sim_plan._widget(window,ensem)
        
        panel_template_lookup.append(('end_criteria', 
            lgm.interface_template_gui(widgets = ['panel'], 
                templates = [sim_plan.widg_templates_end_criteria]))), 
        panel_template_lookup.append(('capture_criteria', 
            lgm.interface_template_gui(widgets = ['panel'], 
                templates = [sim_plan.widg_templates_capture_criteria])))
        panel_template_lookup.append(('plot_targets', 
            lgm.interface_template_gui(widgets = ['panel'], 
                templates = [sim_plan.widg_templates_plot_targets])))
        ensem.fitting_plan._widget(window,ensem)
        panel_template_lookup.append(('fit_routines', 
            lgm.interface_template_gui(widgets = ['panel'], 
                templates = [ensem.fitting_plan.widg_templates])))
        ensem.postprocess_plan._widget(window,ensem)
        panel_template_lookup.append(('post_processes', 
            lgm.interface_template_gui(widgets = ['panel'], 
                templates = [ensem.postprocess_plan.widg_templates])))
        ensem.cartographer_plan._widget(window,ensem)
        panel_template_lookup.append(('p_space_map', 
            lgm.interface_template_gui(widgets = ['panel'], 
                templates = [ensem.cartographer_plan.widg_templates])))
        ensem.multiprocess_plan._widget(window,ensem)
        panel_template_lookup.append(('multiprocessing', 
            lgm.interface_template_gui(widgets = ['panel'], 
                templates = [ensem.multiprocess_plan.widg_templates])))
        panel_template_lookup.append(('output_plans', 
            lgm.interface_template_gui(
                widgets = ['mobj_catalog'], 
                verbosities = [1], 
                instances = [[
                    ensem.run_params['output_plans'],self.module_memory[0]]], 
                keys = [[None,'selected_output_plan']], 
                initials = [[self.module_memory[0].selected_output_plan]])))
        return panel_template_lookup

    def _widget(self,*args,**kwargs):
        window = args[0]
        ensem = self.parent
        self._sanitize(*args,**kwargs)
        self._gui_memory()
        panel_template_lookup = self._panel_templates(window,ensem,**kwargs)
        main_templates,sub_templates,sub_labels =\
            lgb.tree_book_panels_from_lookup(panel_template_lookup,window,ensem)
        run_param_keys = self.run_parameter_keys
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['tree_book'], 
                verbosities = [1], 
                handles = [(self,'tree_reference')], 
                initials = [[self.treebook_memory]], 
                instances = [[self]], 
                keys = [['treebook_memory']], 
                pages = [[(page_template,template_list,param_key,sub_labels) 
                    for page_template,template_list,param_key,sub_labels in 
                        zip(main_templates,sub_templates, 
                            run_param_keys,sub_labels)]], 
                headers = [['Ensemble Run Parameters']]))
        lfu.mobject._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################










