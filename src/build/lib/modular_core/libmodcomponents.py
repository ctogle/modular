import modular_core.libfundamental as lfu
import modular_core.libfitroutine as lfr
import modular_core.libpostprocess as lpp
import modular_core.libgeometry as lgeo
import modular_core.libcriterion as lc
import modular_core.liboutput as lo

'''
import libs.modular_core.libfundamental as lfu
import libs.modular_core.libfitroutine as lfr
import libs.modular_core.libpostprocess as lpp
import libs.modular_core.libgeometry as lgeo
import libs.modular_core.libcriterion as lc
import libs.modular_core.liboutput as lo
'''

import types

import pdb

run_param_keys = [	'End Criteria', 
					'Capture Criteria', 
					'Plot Targets', 
					'Fit Routines', 
					'Post Processes', 
					'Parameter Space Map', 
					'Multiprocessing', 
					'Output Plans'	]

def set_parameters(ensem):
	if ensem.run_params['end_criteria']:
		ensem.simulation_plan.end_criteria = []

	if ensem.run_params['capture_criteria']:
		ensem.simulation_plan.capture_criteria = []

	ensem.simulation_plan.reset_criteria_lists()
	ensem.postprocess_plan.reset_process_list()
	ensem.run_params['plot_targets'] = ['iteration', 'time']
	output_plan = ensem.run_params['output_plans']['Simulation']
	output_plan.targeted = ['iteration', 'time']
	for dex in range(len(output_plan.outputs)):
		output_plan.outputs[dex] = ['iteration', 'time']


	#ensem.run_params.create_partition('system', 
	#	[	'variables', 'species', 'reactions', 'functions', 
	#		'end_criteria', 'capture_criteria', 'plot_targets'	])
	#ensem.cartographer_plan.parameter_space_mobjs =\
	#			ensem.run_params.partition['system']
	#ensem.run_params.create_partition('template owners', 
	#	['variables', 'functions', 'reactions', 'species'])


	ensem.run_params.create_partition('system', 
		[	'end_criteria', 'capture_criteria', 'plot_targets'	])
	ensem.cartographer_plan.parameter_space_mobjs =\
				ensem.run_params.partition['system']
	ensem.run_params.create_partition('template owners', [])

def generate_panel_template_lookup_standard(
		window, ensemble, target_labels = None):
	panel_template_lookup = []
	if target_labels: plot_target_labels = target_labels
	else: plot_target_labels = ['iteration', 'time']
	ensemble.simulation_plan.plot_targets = plot_target_labels
	ensemble.simulation_plan.set_settables(window, ensemble)
	sim_plan = ensemble.simulation_plan
	panel_template_lookup.append(('end_criteria', 
		lgm.interface_template_gui(
			widgets = ['panel'], 
			templates = [sim_plan.widg_templates_end_criteria]))), 
	panel_template_lookup.append(('capture_criteria', 
		lgm.interface_template_gui(
			widgets = ['panel'], 
			templates = [sim_plan.widg_templates_capture_criteria])))
	panel_template_lookup.append(('plot_targets', 
		lgm.interface_template_gui(
			widgets = ['panel'], 
			templates = [sim_plan.widg_templates_plot_targets])))
	ensemble.fitting_plan.set_settables(window, ensemble)
	panel_template_lookup.append(('fit_routines', 
		lgm.interface_template_gui(
			widgets = ['panel'], 
			templates = [ensemble.fitting_plan.widg_templates])))
	ensemble.postprocess_plan.set_settables(window, ensemble)
	panel_template_lookup.append(('post_processes', 
		lgm.interface_template_gui(
			widgets = ['panel'], 
			templates = [ensemble.postprocess_plan.widg_templates])))
	ensemble.cartographer_plan.set_settables(window, ensemble)
	panel_template_lookup.append(('p_space_map', 
		lgm.interface_template_gui(
			widgets = ['panel'], 
			templates = [ensemble.cartographer_plan.widg_templates])))
	ensemble.multiprocess_plan.set_settables(window, ensemble)
	panel_template_lookup.append(('multiprocessing', 
		lgm.interface_template_gui(
			widgets = ['panel'], 
			templates = [ensemble.multiprocess_plan.widg_templates])))
	panel_template_lookup.append(('output_plans', 
		lgm.interface_template_gui(
			widgets = ['mobj_catalog'], 
			instances = [[ensemble.run_params['output_plans'], 
								ensemble._module_memory_[0]]], 
			keys = [[None, 'output_plan_selected_memory']], 
			initials = [[ensemble._module_memory_[\
				0].output_plan_selected_memory]])))
	return panel_template_lookup

def generate_gui_templates_qt(window, ensemble, lookup = None):
	if lookup: panel_template_lookup = lookup
	else:
		set_module_memory_(ensemble)
		panel_template_lookup =\
			generate_panel_template_lookup_standard(window, ensemble)

	#should return a list of main templates, 
	# and a list of lists of sub templates
	#tree_book_panels_from_lookup looks at 
	# ensemble.run_params to find templates for mobjects
	return lgb.tree_book_panels_from_lookup(
		panel_template_lookup, window, ensemble)

def set_module_memory_(ensem):
	ensem._module_memory_ = [lfu.data_container(
		output_plan_selected_memory = 'Simulation')]

universal_support = [['end_criteria', 
					'capture_criteria', 
					'post_processes', 
					'fit_routines', 
					'output_plans', 
					'parameter_space', 
					'plot_targets', 
					'multiprocessing', 
					'ensemble'], 
					[lc.parse_criterion_line, 
					lc.parse_criterion_line, 
					lpp.parse_postproc_line, 
					lfr.parse_fitting_line, 
					lo.parse_output_plan_line, 
					None, None, None, None]]

def parse_mcfg(lines, *args):
	params = args[0]
	ensem = args[1]
	module_support = args[2]

	plot_flag = False
	post_proc_flag = False
	fitting_flag = False
	p_space_flag = False
	p_space_parsed_flag = False
	targs = []
	procs = []
	routs = []
	parser = ''
	parsers = {}

	for dex in range(len(module_support[0])):
		parsers[module_support[0][dex]] = module_support[1][dex]

	for dex in range(len(universal_support[0])):
		if not universal_support[0][dex] in parsers.keys():
			parsers[universal_support[0][dex]] =\
						universal_support[1][dex]

	l_cnt = 0
	while l_cnt < len(lines):
		li = lines[l_cnt].strip()
		l_cnt += 1
		if li.startswith('#') or not li: continue
		elif li.startswith("'''"): pdb.set_trace()
		elif li.startswith('<') and li.endswith('>') and\
								li[1:-1] in parsers.keys():
			parser = li[1:-1]
			if parser == 'plot_targets': plot_flag = True
			elif parser == 'parameter_space':
				p_sub_sps = []
				p_space_flag = True

			elif parser == 'post_processes':
				post_proc_flag = True
				if p_space_flag:
					if len(p_sub_sps) > 1:
						print 'only parsing first p-scan space'

					if not p_space_parsed_flag:
						lgeo.parse_p_space(p_sub_sps[0], ensem)
						p_space_parsed_flag = True

			elif parser == 'fit_routines':
				fitting_flag = True
				if p_space_flag:
					if len(p_sub_sps) > 1:
						print 'only parsing first p-scan space'

					if not p_space_parsed_flag:
						lgeo.parse_p_space(p_sub_sps[0], ensem)
						p_space_parsed_flag = True

			elif parser == 'ensemble': pass

		else:
			if parser == 'plot_targets': targs.append(li)

			elif parser == 'parameter_space':
				if li.startswith('<product_space>'):
					cnt_per_loc = int(li[li.find('>') + 1:])
					p_sub_sps.append([('<product_space>', cnt_per_loc)])

				elif li.startswith('<zip_space>'):
					cnt_per_loc = int(li[li.find('>') + 1:])
					p_sub_sps.append([('<zip_space>', cnt_per_loc)])

				elif li.startswith('<fitting_space>'):
					p_sub_sps.append([('<fitting_space>', None)])

				else:
					p_sub_sps[-1].append([item.strip() 
							for item in li.split(':')])

			elif parser == 'multiprocessing':
				spl = li.split(':')
				if len(spl) >= 2:
					if spl[0].strip() == 'workers':
						w_count = int(spl[1])
						ensem.multiprocess_plan.worker_count = w_count

			elif parser == 'ensemble':
				spl = [l.strip() for l in li.split(':')]
				if spl[0].startswith('multiprocessing'):
					ensem.multiprocess_plan.use_plan =\
						lfu.coerce_string_bool(spl[1])
				elif spl[0].startswith('mapparameterspace'):
					ensem.cartographer_plan.use_plan =\
						lfu.coerce_string_bool(spl[1])
				elif spl[0].startswith('fitting'):
					ensem.fitting_plan.use_plan =\
						lfu.coerce_string_bool(spl[1])
				elif spl[0].startswith('postprocessing'):
					ensem.postprocess_plan.use_plan =\
						lfu.coerce_string_bool(spl[1])
				elif spl[0].startswith('trajectory_count'):
					ensem.num_trajectories = int(spl[1])
				ensem.rewidget(True)

			elif parser in parsers.keys():
				new = parsers[parser](li, ensem, parser, procs, routs)
				if not new is None:
					if type(new) is types.TupleType:
						label, item = new[0], new[1]
						params[parser][new[0]] = new[1]

					elif type(new) is types.ListType:
						params[parser].extend(new)

					else: params[parser].append(new)

			else:
				print 'parsing error', parser, li
				pdb.set_trace()

	if p_space_flag and not p_space_parsed_flag:
		lgeo.parse_p_space(p_sub_sps[0], ensem)

	if plot_flag:
		params['plot_targets'] = targs[:]
		#const_targs = ensem.simulation_plan._always_targetable_
		#all_targets = list(set(targs) | set(const_targs))
		#ensem.simulation_plan.plot_targets = all_targets
		targetables = []
		for param in module_support[0]:
			group = params[param]
			if type(group) is types.ListType: targetables.extend(group)
			elif type(group) is types.DictionaryType:
				targetables.extend(group.values())
			else: targetables.append(group)

		for targable in targetables:
			if hasattr(targable, 'brand_new') and\
						hasattr(targable, 'label'):
				if not targable.label in targs:
					targable.brand_new = False

	#if p_space_flag and not p_space_parsed_flag:
	#	lgeo.parse_p_space(p_sub_sps[0], ensem)

def params_to_lines(run_params, key, lines):
	lines.append('<' + key + '>')
	if type(run_params[key]) is types.ListType:
		params = run_params[key]

	elif type(run_params[key]) is types.DictionaryType:
		params = run_params[key].values()

	if params:
		if issubclass(params[0].__class__, lfu.modular_object_qt):
			lines.extend([param.to_string() for param in params])

		else: lines.extend(['\t' + str(param) for param in params])

	lines.append('')

def write_mcfg(run_params, ensem, lines):

	def p_space_to_lines():
		lines.append('<parameter_space>')
		lines.extend(ensem.cartographer_plan.to_string())
		lines.append('')

	def mp_plan_to_lines():
		lines.append('<multiprocessing>')
		lines.extend(ensem.multiprocess_plan.to_string())
		lines.append('')

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
	return lines

if __name__ == 'modular_core.libmodcomponents':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'




