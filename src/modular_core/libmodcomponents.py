import modular_core.libfundamental as lfu
import modular_core.libgeometry as lgeo

import modular_core.fitting.libfitroutine as lfr
import modular_core.postprocessing.libpostprocess as lpp
import modular_core.criteria.libcriterion as lc
import modular_core.io.liboutput as lo
import modular_core.io.libfiler as lf

import pdb,types
from cStringIO import StringIO

if __name__ == 'modular_core.libmodcomponents':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__': print 'this is a library!'

###############################################################################
### a simulation module has hooks for working with an ensemble
###############################################################################

class simulation_module(lfu.mobject):
    run_parameter_keys = [  
        'End Criteria','Capture Criteria','Plot Targets','Fit Routines',
        'Post Processes','Parameter Space Map','Multiprocessing','Output Plans']

    def _parse_mcfg_plot_targets(li,ensem,parser,procs,routs,targs):
        #targs.append(li)
        return li

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

    def passs(*args,**kwargs):
        return lfu.mobject()
    parse_types = ['end_criteria','capture_criteria','post_processes','fit_routines', 
        'output_plans','parameter_space','plot_targets','multiprocessing','ensemble']
    parse_funcs = [
        #passs,
        #passs,
        lc.parse_criterion_line,
        lc.parse_criterion_line,
        lpp.parse_postproc_line, 
        lfr.parse_fitting_line,
        lo.parse_output_plan_line,
        None,
        _parse_mcfg_plot_targets,
        _parse_mcfg_multiprocessing,
        _parse_mcfg_ensemble]

    def __init__(self,*args,**kwargs):
        lfu.mobject.__init__(self,*args,**kwargs)
        self.treebook_memory = [0,[],[]]
        self.module_memory = []
        self.parsers = {}
        for pt,pf in zip(self.parse_types,self.parse_funcs):
            self.parsers[pt] = pf

    def _add_parsed(self,new,parser,params):
        if type(new) is types.TupleType:
            label, item = new[0], new[1]
            params[parser][new[0]] = new[1]
        elif type(new) is types.ListType:
            params[parser].extend(new)
        else:params[parser].append(new)

    def _parse_mcfg(self,mcfg,ensem):
        params = ensem.run_params
        with open(mcfg,'r') as handle:mlines = handle.readlines()

        plot_flag = False,targs = params['plot_targets']
        p_space_flag = False;p_space_parsed_flag = False;p_sub_sps = []
        procs = [];routs = []

        parser = ''
        parsers = self.parsers
        pkeys = parsers.keys()
                
        def parse_p_space():
            if len(p_sub_sps) > 1:print 'only parsing first p-scan space'
            if p_space_flag and not p_space_parsed_flag:
                lgeo.parse_p_space(p_sub_sps[0],ensem)

        def parse_p_space_line(li):
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
                elif parser == 'parameter_space':p_space_flag = True
                elif parser == 'post_processes' or parser == 'fit_routines':
                    parse_p_space()
                    p_space_parsed_flag = True
            else:
                if parser == 'parameter_space':parse_p_space_line(li)
                elif parser in pkeys:
                    new = parsers[parser](li,ensem,parser,procs,routs,targs)
                    if not new is None:self._add_parsed(new,parser,params)
                else:print 'parsing error', parser, li

        parse_p_space()
        #if p_space_flag and not p_space_parsed_flag:
        #    lgeo.parse_p_space(p_sub_sps[0],ensem)

        '''#
        if plot_flag:
            #params['plot_targets'] = targs[:]
            targetables = []
            for param in module_support[0]:
                group = params[param]
                if type(group) is types.ListType:
                    targetables.extend(group)
                elif type(group) is types.DictionaryType:
                    targetables.extend(group.values())
                else: targetables.append(group)

            for targable in targetables:
                if hasattr(targable, 'brand_new') and\
                            hasattr(targable, 'label'):
                    if not targable.label in targs:
                        targable.brand_new = False
        '''#




    def _write_mcfg(self,mcfg_path,ensem):
        # this should use stringIO

        def params_to_lines(run_params, key, lines):
            lines.append('<' + key + '>')
            if type(run_params[key]) is types.ListType:params = run_params[key]
            elif type(run_params[key]) is types.DictionaryType:
                params = run_params[key].values()
            if params:
                if issubclass(params[0].__class__,lfu.mobject):
                    lines.extend([param._string() for param in params])
            else: lines.extend(['\t' + str(param) for param in params])
            lines.append('')

        def p_space_to_lines():
            lines.append('<parameter_space>')
            lines.extend(ensem.cartographer_plan._string())
            lines.append('')

        def mp_plan_to_lines():
            lines.append('<multiprocessing>')
            lines.extend(ensem.multiprocess_plan._string())
            lines.append('')

        lines = []
        run_params = ensem.run_params
        params_to_lines(run_params, 'end_criteria', lines)
        params_to_lines(run_params, 'capture_criteria', lines)
        params_to_lines(run_params, 'plot_targets', lines)
        if ensem.cartographer_plan.parameter_space: p_space_to_lines()
        if ensem.postprocess_plan.post_processes:
            params_to_lines(run_params, 'post_processes', lines)

        if ensem.fitting_plan.routines:
            params_to_lines(run_params, 'fit_routines', lines)

        mp_plan_to_lines()
        params_to_lines(run_params, 'output_plans', lines)
        mcfg = '\n'.join(lines)

        lf.write_text(mcfg_path,mcfg)




    def _set_parameters(self,ensem):
        print 'run params to location'

    def _reset_parameters(self,ensem):
        ensem.simulation_plan.reset_criteria_lists()
        ensem.postprocess_plan.reset_process_list()
        ensem.run_params['plot_targets'] = ['iteration','time']
        output_plan = ensem.run_params['output_plans']['Simulation']
        def_targeted = ['iteration','time']
        output_plan.targeted = def_targeted[:]
        for w in output_plan.writers:w.targeted = def_targeted[:]

    def _sanitize(self,*args,**kwargs):
        self.module_memory = []
        lfu.mobject._sanitize(self,*args,**kwargs)

    def _panel_templates(self,*args,**kwargs):
        window = args[0]
        ensem = args[1]
        panel_template_lookup = []
        #if target_labels: plot_target_labels = target_labels
        plot_target_labels = ['iteration','time']
        ensem.simulation_plan.plot_targets = plot_target_labels
        ensem.simulation_plan._widget(window,ensem)
        sim_plan = ensem.simulation_plan
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
                verbosities = [3], 
                instances = [[
                    ensem.run_params['output_plans'],self.module_memory[0]]], 
                keys = [[None,'selected_output_plan']], 
                initials = [[self.module_memory[0].selected_output_plan]])))
        return panel_template_lookup

    def _widget(self,*args,**kwargs):
        window = args[0]
        ensem = self.parent
        self._sanitize(*args,**kwargs)

        #if lookup: panel_template_lookup = lookup
        #else:
        #    set_module_memory_(ensem)
        #    panel_template_lookup = self._panel_templates(*args,**kwargs)
        def set_module_memory_():
            self.module_memory = [lfu.data_container(
                selected_output_plan = 'Simulation')]
        set_module_memory_()

        panel_template_lookup = self._panel_templates(window,ensem,**kwargs)

        #should return a list of main templates, 
        # and a list of lists of sub templates
        #tree_book_panels_from_lookup looks at 
        # ensem.run_params to find templates for mobjects
        main_templates,sub_templates,sub_labels =\
            lgb.tree_book_panels_from_lookup(
                panel_template_lookup,window,ensem)
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





















