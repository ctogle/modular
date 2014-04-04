import libs.modular_core.libfundamental as lfu
from libs.modular_core.libfundamental import modular_object_qt as modular_object
import libs.modular_core.libsimcomponents as lsc
import libs.modular_core.libmath as lm
import libs.modular_core.libgeometry as lgeo
import libs.modular_core.libfitroutine as lfr
import libs.modular_core.libpostprocess as lpp
import libs.modular_core.libcriterion as lc
import libs.modular_core.libmodcomponents as lmc

import libs.modules.chemicallite_support.stringchemical as chemfast
#import libs.modules.libchemicalstring_3 as chemfast

import sys
import types
import random
import numpy as np
from math import log as log
import traceback

import pdb

if __name__ == 'libs.modules.libchemicallite':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__':
	print 'this is the chemical lite module library!'

module_name = 'chemicallite'

'''
run_param_keys = [	'End Criteria', 
					'Capture Criteria', 
					'Plot Targets', 
					'Fit Routines', 
					'Post Processes', 
					'Parameter Space Map', 
					'Multiprocessing', 
					'Output Plans'	] +\
'''
run_param_keys = lmc.run_param_keys +\
	['Variables', 'Functions', 'Reactions', 'Species']

def generate_gui_templates_qt(window, ensemble):
	set_module_memory_(ensemble)
	plot_target_labels = ['iteration', 'time'] +\
		ensemble.run_params['species'].keys() +\
		ensemble.run_params['variables'].keys() +\
		ensemble.run_params['functions'].keys()
	panel_template_lookup =\
		lmc.generate_panel_template_lookup_standard(
				window, ensemble, plot_target_labels)
	'''
	panel_template_lookup = []
	plot_target_labels = ['iteration', 'time'] +\
		ensemble.run_params['species'].keys() +\
		ensemble.run_params['variables'].keys() +\
		ensemble.run_params['functions'].keys()
	ensemble.simulation_plan.plot_targets = plot_target_labels
	ensemble.simulation_plan.set_settables(window, ensemble) #this may not need to be here
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
	set_module_memory_(ensemble)
	panel_template_lookup.append(('output_plans', 
		lgm.interface_template_gui(
			widgets = ['mobj_catalog'], 
			instances = [[ensemble.run_params['output_plans'], 
								ensemble._module_memory_[0]]], 
			keys = [[None, 'output_plan_selected_memory']], 
			initials = [[ensemble._module_memory_[\
				0].output_plan_selected_memory]])))
	'''
	panel_template_lookup.append(('variables', 
		lgm.generate_add_remove_select_inspect_box_template(
			window = window, key = 'variables', 
			labels = ['Add Variable', 'Remove Variable'], 
			wheres = [ensemble._children_, 
				ensemble.run_params['variables']], 
			parent = ensemble, 
			selector_handle = (ensemble._module_memory_[0], 
									'variable_selector'), 
			memory_handle = (ensemble._module_memory_[0], 
							'variable_selected_memory'), 
			base_class = variable)))
	panel_template_lookup.append(('functions', 
		lgm.generate_add_remove_select_inspect_box_template(
			window = window, key = 'functions', 
			labels = ['Add Function', 'Remove Function'], 
			wheres = [ensemble._children_, 
				ensemble.run_params['functions']], 
			parent = ensemble, 
			selector_handle = (ensemble._module_memory_[0], 
									'function_selector'), 
			memory_handle = (ensemble._module_memory_[0], 
							'function_selected_memory'), 
			base_class = function_cont)))
	panel_template_lookup.append(('reactions', 
		lgm.generate_add_remove_select_inspect_box_template(
			window = window, key = 'reactions', 
			labels = ['Add Reaction', 'Remove Reaction'], 
			wheres = [ensemble._children_, 
				ensemble.run_params['reactions']], 
			parent = ensemble, 
			selector_handle = (ensemble._module_memory_[0], 
									'reaction_selector'), 
			memory_handle = (ensemble._module_memory_[0], 
							'reaction_selected_memory'), 
			base_class = reaction, 
			function_handles = [[(ensemble, '_make_rxn_')], 
											None, None])))
	panel_template_lookup.append(('species', 
		lgm.generate_add_remove_select_inspect_box_template(
			window = window, key = 'species', 
			labels = ['Add Species', 'Remove Species'], 
			wheres = [ensemble._children_, 
				ensemble.run_params['species']], 
			parent = ensemble, 
			selector_handle = (ensemble._module_memory_[0], 
									'species_selector'), 
			memory_handle = (ensemble._module_memory_[0], 
							'species_selected_memory'), 
			base_class = species, 
			function_handles = [[(ensemble, '_make_spec_')], 
											None, None])))
	#should return a list of main templates, 
	# and a list of lists of sub templates
	#tree_book_panels_from_lookup looks at 
	# ensemble.run_params to find templates for mobjects

	#return lgb.tree_book_panels_from_lookup(
	#	panel_template_lookup, window, ensemble)
	return lmc.generate_gui_templates_qt(window, 
		ensemble, lookup = panel_template_lookup)

def set_module_memory_(ensem):
	ensem._module_memory_ = [lfu.data_container(
		output_plan_selected_memory = 'Simulation', 
				variable_selected_memory = 'None', 
				function_selected_memory = 'None', 
				reaction_selected_memory = 'None', 
				species_selected_memory = 'None')]

def set_parameters(ensem):
	set_module_memory_(ensem)

	if 'end_criteria' in ensem.run_params.keys():
		for crit in ensem.run_params['end_criteria']:
			crit._destroy_()

	if 'capture_criteria' in ensem.run_params.keys():
		for crit in ensem.run_params['capture_criteria']:
			crit._destroy_()

	if 'variables' in ensem.run_params.keys():
		for key, val in ensem.run_params['variables'].items():
			ensem.run_params['variables'][key]._destroy_()

	if 'species' in ensem.run_params.keys():
		for key, val in ensem.run_params['species'].items():
			ensem.run_params['species'][key]._destroy_()

	if 'reactions' in ensem.run_params.keys():
		for val in ensem.run_params['reactions']: val._destroy_()

	if 'functions' in ensem.run_params.keys():
		for key, val in ensem.run_params['functions'].items():
			ensem.run_params['functions'][key]._destroy_()

	if ensem.postprocess_plan.post_processes:
		for proc in ensem.postprocess_plan.post_processes:
			proc._destroy_()

	ensem.simulation_plan.reset_criteria_lists()
	ensem.run_params['variables'] = {}
	ensem.run_params['species'] = {}
	ensem.run_params['reactions'] = []
	ensem.run_params['functions'] = {}
	ensem.run_params['plot_targets'] = ['iteration', 'time']
	ensem.postprocess_plan.reset_process_list()
	output_plan = ensem.run_params['output_plans']['Simulation']
	output_plan.targeted = ['iteration', 'time']
	for dex in range(len(output_plan.outputs)):
		output_plan.outputs[dex] = ['iteration', 'time']

	ensem.run_params.create_partition('system', 
		[	'variables', 'species', 'reactions', 'functions', 
			'end_criteria', 'capture_criteria', 'plot_targets'	])
	ensem.cartographer_plan.parameter_space_mobjs =\
				ensem.run_params.partition['system']
	ensem.run_params.create_partition('template owners', 
		['variables', 'functions', 'reactions', 'species'])

def parse_variable_line(data, ensem):
	split = [item.strip() for item in data.split(':')]
	name, value = split[0], split[1]
	varib = variable(label = name, value = value)
	return name, varib

def parse_function_line(data, ensem):
	split = [item.strip() for item in data.split(':')]
	name, value = split[0], split[1]
	func = function_cont(label = name, func_statement = value)
	return name, func

def parse_reaction_line(data, ensem):

	def left_right_process(left, right):
		left = [(left[k + 1], int(left[k])) for k in 
				[num*2 for num in range(len(left)/2)]]
		right = [(right[k + 1], int(right[k])) for k in 
				[num*2 for num in range(len(right)/2)]]
		return left, right

	data = data.split(' ')
	try: label = ' '.join(data[data.index(':') + 1:])
	except ValueError: label = 'a reaction'
	try: divider = [item.find('-') for item in data].index(0)
	except:
		try: divider = [item.find('-') for item in data].index(1)
		except:
			print 'cant interpret divider in reaction'
			return []

	if data[divider] == '<->':
		rates = [data[divider - 1], data[divider + 1]]
		left = [item for item in data[:divider - 1] if item != '+']
		try: right = [item for item in data[divider + 2:data.index(':')] if item != '+']
		except ValueError: right = [item for item in data[divider + 2:] if item != '+']
		left, right = left_right_process(left, right)
		rxn1 = reaction(label, rates[0], 
				propensity_scheme = 'classic', used = left, 
						produced = right, parent = ensem)
		rxn2 = reaction(label, rates[1], 
				propensity_scheme = 'classic', used = right, 
						produced = left, parent = ensem)
		ensem._children_.extend([rxn1, rxn2])
		return [rxn1, rxn2]

	elif data[divider] == '->':
		rates = [data[divider - 1]]
		left = [item for item in data[:divider - 1] if item != '+']
		try:
			right = [item for item in 
					data[divider + 1:data.index(':')] 
									if item != '+']

		except ValueError:
			right = [item for item in data[divider + 1:] if item != '+']

		left, right = left_right_process(left, right)
		rxn = reaction(label, rates[0], propensity_scheme = 'classic', 
						used = left, produced = right, parent = ensem)
		ensem._children_.append(rxn)
		return [rxn]

	elif data[divider] == '<-':
		rates = [data[divider + 1]]
		left = [item for item in data[:divider] if item != '+']
		try: right = [item for item in data[divider + 2:data.index(':')] if item != '+']
		except ValueError:
			right = [item for item in data[divider + 2:] if item != '+']

		left, right = left_right_process(left, right)
		rxn = reaction(label, rates[0], propensity_scheme = 'classic', 
						used = right, produced = left, parent = ensem)
		ensem._children_.append(rxn)
		return [rxn]

	if data != ['']:
		print 'unable to parse reaction: ' + str(data)
		pdb.set_trace()

	return []

def parse_species_line(data, ensem):
	data = [dat.strip() for dat in data.split(':')]
	spec, value = data[0], int(data[1])
	new = species(spec, parent = ensem, 
				initial_count = value, 
				current_count = value)
	return spec, new

def parse_mcfg(lines, *args):
	support = [['variables', 'functions', 'reactions', 'species'], 
						[parse_variable_line, parse_function_line, 
						parse_reaction_line, parse_species_line]]
	lmc.parse_mcfg(lines, args[0], args[1], support)

'''
	params = args[0]
	ensem = args[1]

	def parse_criterion_line(data):
		split = [item.strip() for item in data.split(':')]
		for crit_type in lc.valid_criterion_base_classes:
			if split[0] == crit_type._tag:
				crit = crit_type._class()
				if len(split) > 1:
					if crit_type._tag == 'time limit':
						crit.max_time = split[1]

					elif crit_type._tag == 'iteration limit':
						crit.max_iterations = split[1]

					elif crit_type._tag == 'capture limit':
						crit.max_captures = split[1]

					elif crit_type._tag == 'species scaler increment':
						crit.increment = split[1]
						if len(split) > 2: crit.key = split[2]

					elif crit_type._tag == 'species count':
						crit.spec_count_target = split[1]
						if len(split) > 2: crit.key = split[2]

					else: pdb.set_trace()

		return [crit]

	def parse_variable_line(data):
		split = [item.strip() for item in data.split(':')]
		name, value = split[0], split[1]
		varib = variable(label = name, value = value)
		return name, [varib]

	def parse_function_line(data):
		split = [item.strip() for item in data.split(':')]
		name, value = split[0], split[1]
		func = function_cont(label = name, func_statement = value)
		return name, [func]

	def parse_reaction_line(data):

		def left_right_process(left, right):
			left = [(left[k + 1], int(left[k])) for k in 
					[num*2 for num in range(len(left)/2)]]
			right = [(right[k + 1], int(right[k])) for k in 
					[num*2 for num in range(len(right)/2)]]
			return left, right

		data = data.split(' ')
		try:
			label = ' '.join(data[data.index(':') + 1:])

		except ValueError:
			label = 'a reaction'

		try:
			divider = [item.find('-') for item in data].index(0)
				
		except:
			try:
				divider = [item.find('-') for item in data].index(1)

			except:
				print 'cant interpret divider in reaction'
				return []

		if data[divider] == '<->':
			rates = [data[divider - 1], data[divider + 1]]
			left = [item for item in data[:divider - 1] if item != '+']
			try:
				right = [item for item in data[divider + 2:data.index(':')] if item != '+']

			except ValueError:
				right = [item for item in data[divider + 2:] if item != '+']

			left, right = left_right_process(left, right)
			rxn1 = reaction(label, rates[0], 
					propensity_scheme = 'classic', used = left, 
							produced = right, parent = ensem)
			rxn2 = reaction(label, rates[1], 
					propensity_scheme = 'classic', used = right, 
							produced = left, parent = ensem)
			ensem._children_.extend([rxn1, rxn2])
			return [rxn1, rxn2]

		elif data[divider] == '->':
			rates = [data[divider - 1]]
			left = [item for item in data[:divider - 1] if item != '+']
			try:
				right = [item for item in 
						data[divider + 1:data.index(':')] 
										if item != '+']

			except ValueError:
				right = [item for item in data[divider + 1:] if item != '+']

			left, right = left_right_process(left, right)
			rxn = reaction(label, rates[0], propensity_scheme = 'classic', 
							used = left, produced = right, parent = ensem)
			ensem._children_.append(rxn)
			return [rxn]

		elif data[divider] == '<-':
			rates = [data[divider + 1]]
			left = [item for item in data[:divider] if item != '+']
			try:
				right = [item for item in data[divider + 2:data.index(':')] if item != '+']

			except ValueError:
				right = [item for item in data[divider + 2:] if item != '+']

			left, right = left_right_process(left, right)
			rxn = reaction(label, rates[0], propensity_scheme = 'classic', 
							used = right, produced = left, parent = ensem)
			ensem._children_.append(rxn)
			return [rxn]

		#except:
		if data != ['']:
			print 'unable to parse reaction: ' + str(data)
			pdb.set_trace()

		return []

	def parse_species_line(data):
		try:
			data = [dat.strip() for dat in data.split(':')]
			return data[0], int(data[1])

		except: print 'unable to parse species: ' + str(data)

	def fix_species_list(rxns, specs):
		agents = {}
		for rxn in rxns:
			for agent in rxn.used + rxn.produced:
				agents[agent[0]] = species(parent = ensem, 
									label = agent[0], 
									initial_count = 0, 
									current_count = 0)

		for key in specs.keys():
			try:
				agents.keys().index(key)
				agents[key] = specs[key]

			except ValueError:
				print 'agent: ' + key + ' does not react - neglecting'

		specs = agents
		return rxns, specs

	def parse_postproc_line(data, ensem):
		split = [item.strip() for item in data.split(':')]
		for proc_type in lpp.valid_postproc_base_classes:
			if split: name = split[0]
			if len(split) > 1:
				if split[1].strip() == proc_type._tag:
					proc = proc_type._class(label = name, 
						parent = ensem.postprocess_plan)
					procs.append(proc)
					if len(split) > 2:
						inputs = [int(item.strip()) for 
							item in split[2].split(',')]
						input_regime = []
						for inp in inputs:
							if inp == 0: input_regime.append('simulation')
							elif inp < len(procs):
								input_regime.append(procs[inp].label)

							else:
								print ' '.join(['process', 'couldnt', 
											'reach', 'input', 'from', 
												'hierarchy']), proc

						proc.input_regime = input_regime
						if proc_type._tag == 'standard statistics':
							try:
								targs = split[3].split(' of ')
								proc.mean_of = targs[0]
								proc.function_of = targs[1]

							except IndexError: pass
							try: proc.bin_count = int(split[4].strip())
							except IndexError: pass
							try:
								if split[5].strip().count('ordered') > 0:
									proc.ordered = True

							except IndexError: pass

						elif proc_type._tag == 'counts to concentrations':
							print 'counts to concentrations parsing not done'

						elif proc_type._tag == 'correlation':
							try:
								targs = split[3].replace(
									' and ', '||').replace(' of ', '||')
								targs = targs.split('||')
								proc.target_1 = targs[0]
								proc.target_2 = targs[1]
								proc.function_of = targs[2]

							except IndexError: pass
							try: proc.bin_count = int(split[4].strip())
							except IndexError: pass
							try:
								if split[5].strip().count('ordered') > 0:
									proc.ordered = True

							except IndexError: pass

						elif proc_type._tag == 'slice from trajectory':
							try:
								relevant = [item.strip() for item 
										in split[3].split(',')]
								proc.slice_dex = split[4].strip()

							except IndexError: pass
							if 'all' in relevant:
								proc.dater_ids =\
									proc.get_targetables(0, ensem)

							else: proc.dater_ids = relevant

						elif proc_type._tag == 'reorganize data':
							try:
								relevant = [item.strip() for item 
										in split[3].split(',')]

							except IndexError: pass
							if 'all' in relevant:
								proc.dater_ids =\
									proc.get_targetables(0, ensem)

							else: proc.dater_ids = relevant

						elif proc_type._tag == 'one to one binary operation':
							print 'one to one binary operation parsing not done'

						elif proc_type._tag == 'probability':
							print 'probability parsing not done'

						elif proc_type._tag == 'period finding':
							print 'period finding parsing not done'

						else: pdb.set_trace()

		ensem.postprocess_plan.add_process(new = proc)
		proc.set_settables(0, ensem)
		return [proc]

	def parse_fitting_line(data, ensem):
		split = [item.strip() for item in data.split(':')]
		for fit_type in lfr.valid_fit_routine_base_classes:
			if split: name = split[0]
			if len(split) > 1:
				if split[1].strip() == fit_type._tag:
					rout = fit_type._class(label = name, 
						parent = ensem.fitting_plan)
					routs.append(rout)

				if len(split) > 2: rout.regime = split[2].strip()

		ensem.fitting_plan.add_routine(new = rout)
		rout.set_settables(0, ensem)
		return [rout]

	def parse_output_plan_line(line, ensem):
		spl = [item.strip() for item in line.split(' : ')]
		dex = int(spl[0])
		if dex == 0: output = ensem.output_plan
		#else: output = procs[dex - 1].output
		elif dex <= len(procs): output = procs[dex - 1].output
		else: output = routs[dex - len(procs) - 1].output
		output.save_directory = spl[1]
		output.save_filename = spl[2]
		if 'plt' in spl[3]: output.output_plt = True
		else: output.output_plt = False
		if 'vtk' in spl[3]: output.output_vtk = True
		else: output.output_vtk = False
		if 'pkl' in spl[3]: output.output_pkl = True
		else: output.output_pkl = False
		if 'txt' in spl[3]: output.output_txt = True
		else: output.output_txt = False
		relevant = [item.strip() for item in spl[4].split(',')]
		if 'all' in relevant:
			output.set_settables(0, ensem)
			output.targeted = output.get_target_labels()

		else: output.targeted = relevant

	#this parse function is limiting to one p-sp axis per mobj
	def parse_p_space(p_sub, ensem):

		def validate(rng):
			valid = []
			for val in rng.split(','):
				try: valid.append(float(val))
				except: pass

			return valid

		def turn_on_mobjs_first_p_space_axis(mobj):
			dex = axes.index(mobj.label)
			mobj_attr = variants[dex]
			mobj.set_settables(0, ensem)
			for p_temp in mobj.parameter_space_templates:
				if mobj_attr == p_temp.key:
					p_temp.contribute_to_p_sp = True
					p_temp.p_sp_bounds = rng_bounds[dex]
					p_temp.p_sp_perma_bounds = rng_bounds[dex]
					p_temp.p_sp_increment = increments[dex]

		def read_increment(rng):
			if rng.count(';') > 0: read = float(rng[rng.rfind(';')+1:])
			else: read = 10
			return read

		if p_sub[0][0].count('<product_space>'):
			comp_meth = 'Product Space'

		elif p_sub[0][0].count('<zip_space>'): comp_meth = '1 - 1 Zip'
		elif p_sub[0][0].count('<fitting_space>'): comp_meth = 'Fitting'

		if comp_meth == 'Product Space' or comp_meth == '1 - 1 Zip':
			ax_lines = p_sub[1:]

		elif comp_meth == 'Fitting':
			pdb.set_trace()

		def parse_axes(lines):
			axes = [ax[0] for ax in lines]
			variants = [ax[1] for ax in lines]
			ax_rngs = [ax[2] for ax in lines]
			return axes, variants, ax_rngs

		axes, variants, ax_rngs = parse_axes(ax_lines)
		increments = [read_increment(rng) for rng in ax_rngs]
		ranges = [lm.make_range(rng)[0] for rng in ax_rngs]
		rng_bounds = [[validate(rng)[0], validate(rng)[-1]] 
										for rng in ranges]

		poss_contribs = ['species', 'variables', 'reactions']
		p_mobjs = ensem.cartographer_plan.parameter_space_mobjs
		for key in p_mobjs.keys():
			if key in poss_contribs:
				if type(p_mobjs[key]) is types.DictionaryType:
					for sub_key in p_mobjs[key].keys():
						mobj = p_mobjs[key][sub_key]
						if mobj.label in axes:
							turn_on_mobjs_first_p_space_axis(mobj)

				if type(p_mobjs[key]) is types.ListType:
					for mobj in p_mobjs[key]:
						if mobj.label in axes:
							turn_on_mobjs_first_p_space_axis(mobj)

		ensem.cartographer_plan.generate_parameter_space()
		selected = [ensem.cartographer_plan.\
			parameter_space.get_start_position()]
		#if p_sub[0][0].count('<product_space>'):
		#	comp_meth = 'Product Space'
		#elif p_sub[0][0].count('<zip>'): comp_meth = '1 - 1 Zip'


		if comp_meth == 'Product Space' or comp_meth == '1 - 1 Zip':
			traj_dlg = lgd.trajectory_dialog(parent = None, 
				base_object = selected, composition_method = comp_meth, 
				p_space = ensem.cartographer_plan.parameter_space)

			for ax, vari, rng in zip(axes, variants, ranges):
				trj_dlg_dex = traj_dlg.axis_labels.index(
								' : '.join([ax, vari]))
				traj_dlg.variations[trj_dlg_dex] = validate(rng)

			traj_dlg.on_make()
			if traj_dlg.made:
				ensem.cartographer_plan.trajectory_string =\
									traj_dlg.result_string
				ensem.cartographer_plan.on_delete_selected_pts(
											preselected = None)
				ensem.cartographer_plan.on_reset_trajectory_parameterization()
				ensem.cartographer_plan.on_append_trajectory(traj_dlg.result)

			ensem.cartographer_plan.traj_count = p_sub[0][1]
			ensem.cartographer_plan.on_assert_trajectory_count(all_ = True)

		elif comp_meth == 'Fitting':
			pdb.set_trace()

	plot_flag = False
	post_proc_flag = False
	fitting_flag = False
	p_space_flag = False
	targs = []
	procs = []
	routs = []
	parser = ''
	for line in lines:
		if line.strip().startswith('#') == True or line.strip() == '':
			continue

		elif line.startswith('<end_criteria>'):
			parser = 'end_criteria'
			continue

		elif line.startswith('<capture_criteria>'):
			parser = 'capture_criteria'
			continue

		elif line.startswith('<variables>'):
			parser = 'variable'
			continue

		elif line.startswith('<functions>'):
			parser = 'function'
			continue

		elif line.startswith('<reactions>'):
			parser = 'reaction'
			continue

		elif line.startswith('<species>'):
			parser = 'species'
			continue

		elif line.startswith('<plot_targets>'):
			plot_flag = True
			parser = 'plot_targets'
			continue

		elif line.startswith('<post_processes>'):
			post_proc_flag = True
			if p_space_flag:
				if len(p_sub_sps) > 1:
					print 'only parsing first p-scan space'

				parse_p_space(p_sub_sps[0], ensem)

			parser = 'post_processes'
			continue

		elif line.startswith('<fit_routines>'):
			fitting_flag = True
			if p_space_flag:
				if len(p_sub_sps) > 1:
					print 'only parsing first p-scan space'

				parse_p_space(p_sub_sps[0], ensem)

			parser = 'fit_routines'
			continue

		elif line.startswith('<parameter_space>'):
			p_sub_sps = []
			p_space_flag = True
			parser = 'parameter_space'
			continue

		elif line.startswith('<multiprocessing>'):
			parser = 'multiprocessing'
			continue

		elif line.startswith('<output_plans>'):
			parser = 'output_plans'
			continue

		else:
			if parser == 'end_criteria':
				crit = parse_criterion_line(line[:-1])[0]
				ensem.simulation_plan.add_end_criteria(crit = crit)

			if parser == 'capture_criteria':
				crit = parse_criterion_line(line[:-1])[0]
				ensem.simulation_plan.add_capture_criteria(crit = crit)

			elif parser == 'variable':
				vari, vari_inst = parse_variable_line(line[:-1])
				params['variables'][vari] = vari_inst[0]

			elif parser == 'function':
				func, func_inst = parse_function_line(line[:-1])
				params['functions'][func] = func_inst[0]

			elif parser == 'reaction':
				params['reactions'].extend(
					parse_reaction_line(line[:-1]))

			elif parser == 'species':
				spec, value = parse_species_line(line[:-1])
				params['species'][spec] = species(
											spec, parent = ensem, 
											initial_count = value, 
											current_count = value)

			elif parser == 'plot_targets':
				target = line.strip()
				targs.append(target)

			elif parser == 'post_processes':
				parse_postproc_line(line[:-1], ensem)[0]

			elif parser == 'fit_routines':
				parse_fitting_line(line[:-1], ensem)[0]

			elif parser == 'parameter_space':
				if line.strip().startswith('<product_space>'):
					cnt_per_loc = int(line[line.find('>') + 1:].strip())
					p_sub_sps.append([('<product_space>', cnt_per_loc)])

				elif line.strip().startswith('<zip_space>'):
					cnt_per_loc = int(line[line.find('>') + 1:].strip())
					p_sub_sps.append([('<zip_space>', cnt_per_loc)])

				elif line.strip().startswith('<fitting_space>'):
					p_sub_sps.append([('<fitting_space>', None)])

				else:
					p_sub_sps[-1].append([item.strip() for item in 
									line[:-1].strip().split(':')])

			elif parser == 'multiprocessing':
				spl = line.split(':')
				if len(spl) >= 2:
					if spl[0].strip() == 'workers':
						ensem.multiprocess_plan.worker_count = int(spl[1])

			elif parser == 'output_plans':
				parse_output_plan_line(line[:-1], ensem)

	params['reactions'], params['species'] = \
		fix_species_list(params['reactions'], params['species'])

	if plot_flag:
		params['plot_targets'] = targs
		targetables = params['species'].values() +\
					params['variables'].values() +\
					params['functions'].values()
		for targable in targetables:
			if not targable.label in targs:
				targable.brand_new = False

	if p_space_flag and (not post_proc_flag or not fitting_flag):
		parse_p_space(p_sub_sps[0], ensem)
	'''

def write_mcfg(*args):
	run_params = args[0]
	ensem = args[1]
	'''
	def p_space_to_lines():
		lines.append('<parameter_space>')
		lines.extend(ensem.cartographer_plan.to_string())
		lines.append('')

	def mp_plan_to_lines():
		lines.append('<multiprocessing>')
		lines.extend(ensem.multiprocess_plan.to_string())
		lines.append('')

	def params_to_lines(key):
		lines.append('<' + key + '>')
		if type(run_params[key]) is types.ListType:
			params = run_params[key]

		elif type(run_params[key]) is types.DictionaryType:
			params = run_params[key].values()

		if params:
			if issubclass(params[0].__class__, modular_object):
				lines.extend([param.to_string() for param in params])

			else: lines.extend(['\t' + str(param) for param in params])

		lines.append('')
	'''
	lines = ['']
	#params_to_lines('end_criteria')
	#params_to_lines('capture_criteria')
	lmc.params_to_lines(run_params, 'variables', lines)
	lmc.params_to_lines(run_params, 'functions', lines)
	lmc.params_to_lines(run_params, 'reactions', lines)
	lmc.params_to_lines(run_params, 'species', lines)
	#params_to_lines('plot_targets')
	#p_space_to_lines()
	#params_to_lines('post_processes')
	#mp_plan_to_lines()
	#params_to_lines('output_plans')
	return lmc.write_mcfg(args[0], args[1], lines)

#class scalers(object):
#
#	def __init__(self, label = 'some scaler', scalers = []):
#		self.label = label
#		self.scalers = scalers
#		self.tag = 'scaler'

class sim_system(lsc.sim_system_external):

	def encode(self):

		def make_rxn_string(rxn):
			used = '+'.join([''.join(['(', str(agent[1]), ')', 
							agent[0]]) for agent in rxn.used])
			prod = '+'.join([''.join(['(', str(agent[1]), ')', 
						agent[0]]) for agent in rxn.produced])
			return '->'.join([used, str(rxn.rate), prod])

		def int_fix(cnt):
			if float(cnt) < 1: return 0
			else: return cnt

		sub_spec = [':'.join([spec.label, 
			str(int_fix(spec.initial_count))]) 
			for spec in self.params['species'].values()]
		spec_string = '<species>' + ','.join(sub_spec)
		sub_var = [':'.join([key, str(var.value)]) for key, var in 
								self.params['variables'].items()]
		variable_string = '<variables>' + ','.join(sub_var)
		sub_func = ['='.join([key, fu.func_statement.replace(',', '&')]) 
					for key, fu in self.params['functions'].items()]
		function_string = '<functions>' + ','.join(sub_func)
		sub_rxn = ','.join([make_rxn_string(rxn) for rxn in 
								self.params['reactions']])
		reaction_string = '<reactions>' + sub_rxn
		sub_end = self.read_criteria(
			self.params['end_criteria'], '')
		end_string = '<end>' + sub_end
		sub_capt = self.read_criteria(
			self.params['capture_criteria'], '')
		capture_string = '<capture>' + sub_capt
		targs = self.params['plot_targets']
		sub_targ = ','.join(targs[3:] + targs[:3])
		target_string = '<targets>' + sub_targ + '||'
		self.system_string = spec_string + variable_string +\
			function_string + reaction_string + end_string +\
			capture_string + target_string

	'''
	def __init__(self, ensem = None, params = {}):
		self.ensemble = ensem
		self.params = params
		#lsc.sim_system.__init__(self, ensem, params)

	def read_criteria(self, crits, start_string):
		for crit in crits:
			if issubclass(crit.__class__, lc.criterion_iteration):
				value = crit.max_iterations
				start_string += 'iteration>=' + str(value)

			elif issubclass(crit.__class__, lc.criterion_sim_time):
				value = crit.max_time
				start_string += 'time>=' + str(value)

			elif issubclass(crit.__class__, 
					#criterion_spec_included_scaler_increment):
					lc.criterion_scaler_increment):
				target = crit.key
				value = str(crit.increment)
				start_string += ':'.join(['increment', target, value])

		return start_string

	def initialize(self):

		def make_rxn_string(rxn):
			used = '+'.join([''.join(['(', str(agent[1]), ')', 
							agent[0]]) for agent in rxn.used])
			prod = '+'.join([''.join(['(', str(agent[1]), ')', 
						agent[0]]) for agent in rxn.produced])
			return '->'.join([used, str(rxn.rate), prod])

		def int_fix(cnt):
			if float(cnt) < 1: return 0
			else: return cnt

		self.iteration = 0
		sub_spec = [':'.join([spec.label, 
			str(int_fix(spec.initial_count))]) 
			for spec in self.params['species'].values()]
		spec_string = '<species>' + ','.join(sub_spec)
		sub_var = [':'.join([key, str(var.value)]) for key, var in 
								self.params['variables'].items()]
		variable_string = '<variables>' + ','.join(sub_var)
		sub_func = ['='.join([key, fu.func_statement.replace(',', '&')]) 
					for key, fu in self.params['functions'].items()]
		function_string = '<functions>' + ','.join(sub_func)
		sub_rxn = ','.join([make_rxn_string(rxn) for rxn in 
								self.params['reactions']])
		reaction_string = '<reactions>' + sub_rxn
		sub_end = self.read_criteria(
			self.params['end_criteria'], '')
		end_string = '<end>' + sub_end
		sub_capt = self.read_criteria(
			self.params['capture_criteria'], '')
		capture_string = '<capture>' + sub_capt
		targs = self.params['plot_targets']
		sub_targ = ','.join(targs[3:] + targs[:3])
		target_string = '<targets>' + sub_targ + '||'
		self.system_string = spec_string + variable_string +\
			function_string + reaction_string + end_string +\
			capture_string + target_string
	'''

	def iterate(self):
		try:
			self.data = self.finalize_data(
				*chemfast.simulate(self.system_string))

		except:
			traceback.print_exc(file=sys.stdout)
			print 'simulation failed; aborting'
			self.bAbort = True

class variable(modular_object):

	def _set_label_(self, value):
		before = self._label
		if modular_object._set_label_(self, value):
			del self.parent.run_params['variables'][before]
			self.parent.run_params['variables'][self._label] = self

	def __init__(self, *args, **kwargs):
		if 'label' not in kwargs.keys(): kwargs['label'] = 'variable'
		self.impose_default('value', 1.0, **kwargs)
		self.brand_new = True
		parameter_space_templates =\
			[lgeo.interface_template_p_space_axis(instance = self, 
								p_sp_bounds = ['-10e64', '10e64'], 
									parent = self, key = 'value')]
		modular_object.__init__(self, *args, 
			parameter_space_templates =\
				parameter_space_templates, **kwargs)

	def to_string(self):
		self.ensem = None
		return '\t' + self.label + ' : ' + str(self.value)

	def set_settables(self, *args, **kwargs):
		ensem = args[1]
		self.parent = ensem
		window = args[0]
		if self.brand_new:
			ensem.run_params['plot_targets'].append(self.label)
			plan = ensem.run_params['output_plans']['Simulation']
			plan.targeted.append(self.label)
			plan.rewidget(True)
			for subtargeted in plan.outputs:
				subtargeted.append(self.label)

			self.brand_new = not self.brand_new

		#dictionary_support = lgm.dictionary_support_mason(window)
		where_reference = ensem.run_params['variables']
		cartographer_support = lgm.cartographer_mason(window)
		self.handle_widget_inheritance(*args, **kwargs)
		self.parameter_space_templates =\
			[lgeo.interface_template_p_space_axis(parent = self, 
							p_sp_bounds = self._p_sp_bounds_[0], 
								instance = self, key = 'value')]
		self.parameter_space_templates[0].set_settables(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['spin'], 
				doubles = [[True]], 
				initials = [[float(self.value)]], 
				instances = [[self]], 
				keys = [['value']], 
				box_labels = ['Variable Value'], 
				mason = cartographer_support, 
				parameter_space_templates =\
					[self.parameter_space_templates[0]]))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['text'], 
				#mason = dictionary_support, 
				#wheres = [[where_reference]], 
				keys = [['label']], 
				instances = [[self]], 
				initials = [[self.label]], 
				box_labels = ['Variable Name']))
		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)

class function_cont(modular_object):

	def __init__(self, *args, **kwargs):
		if 'label' not in kwargs.keys(): kwargs['label'] = 'function'
		self.impose_default('func_statement', '', **kwargs)
		self.brand_new = True
		modular_object.__init__(self, *args, **kwargs)

	def to_string(self):
		return '\t' + self.label + ' : ' + self.func_statement

	def set_settables(self, *args, **kwargs):
		ensem = args[1]
		frame = args[0]
		if self.brand_new:
			ensem.run_params['plot_targets'].append(self.label)
			plan = ensem.run_params['output_plans']['Simulation']
			plan.targeted.append(self.label)
			plan.rewidget(True)
			for subtargeted in plan.outputs:
				subtargeted.append(self.label)

			self.brand_new = not self.brand_new

		self.handle_widget_inheritance(*args, **kwargs)
		where_reference = ensem.run_params['functions']
		#dictionary_support = lgm.dictionary_support_mason(frame)
		self.handle_widget_inheritance(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				keys = [['func_statement']], 
				instances = [[self]], 
				widgets = ['text'], 
				minimum_sizes = [[(200, 75)]], 
				box_labels = ['Function Statement'], 
				initials = [[self.func_statement]]))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['text'], 
				#mason = dictionary_support, 
				wheres = [[where_reference]], 
				keys = [['label']], 
				instances = [[self]], 
				initials = [[self.label]], 
				box_labels = ['Function Name']))
		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)

class reaction(modular_object):

	def __init__(self, label = 'another reaction', 
			rate = float(10.0), propensity_scheme = 'classic', 
			propensity_function_maker = None, parent = None, 
			occurrences = [], used = None, produced = None, 
			visible_attributes = ['label', 'propensity_scheme', 
								'rate', 'used', 'produced']):
		self.system = None
		self.rate = rate
		if occurrences is None: self.occurrences = []
		else: self.occurrences = occurrences
		#instances of these are somehow coupled unless a 
		#	used and produced list is passed to init, 
		#	EVEN an empty list will do (used = [] does not!)
		if used is None: self.used = []
		else: self.used = used
		if produced is None: self.produced = []
		else: self.produced = produced
		self.propensity = 1.0
		self.propensity_minimum = 1e-30
		self.propensity_scheme = propensity_scheme
		parameter_space_templates =\
			[lgeo.interface_template_p_space_axis(parent = self, 
							p_sp_bounds = [0.0000001, 1000.0], 
							instance = self, key = 'rate')]
		modular_object.__init__(self, label = label, parent = parent, 
							visible_attributes = visible_attributes, 
			parameter_space_templates = parameter_space_templates)

	def to_string(self):

		def agents_to_line(agents):
			if agents:
				_line = [str(pair[1]) + ' ' + pair[0] for pair in agents]
				_line = ' '.join(_line)

			else: _line = 'nothing'
			return _line

		used_line = agents_to_line(self.used)
		produced_line = agents_to_line(self.produced)
		rxn_string = ' '.join([used_line, str(self.rate), 
									'->', produced_line])
		rxn_string = '\t' + rxn_string + ' : ' + self.label
		return rxn_string

	def react(self, system):
		enough_agent = [system.species[agent[0]].current_count >=\
								agent[1] for agent in self.used]
		try:
			enough_agent.index(False)
			return False

		except ValueError:
			for agent in self.used:
				system.species[agent[0]].current_count -= int(agent[1])

			for agent in self.produced:
				system.species[agent[0]].current_count += int(agent[1])

			try:
				self.occurrences.append((system.iteration, system.time[-1]))

			except IndexError:
				self.occurrences.append((0, 0))

			return True

		return False

	def determine_propensity(self, system):
		try:
			return self.propensity_scheme(system)

		except TypeError:
			if self.propensity_scheme == 'classic':
				self.propensity_scheme =\
					self.classic_propensity
				return self.determine_propensity(system)

			elif self.propensity_scheme == '':
				self.revert_to_classic_propensity()

	def revert_to_classic_propensity(self):
		print '\nreaction propensity function failed'
		print 'reverting to classic propensity scheme for:'
		print '\t', self.label, '\n'
		self.propensity_scheme = self.classic_propensity

	def classic_propensity(self, system):
		population = 1.0
		for agent in self.used:
			for k in range(int(agent[1])):
				population *= float(system.species[
									agent[0]].current_count - k)

		self.propensity = population * self.rate
		if self.propensity > self.propensity_minimum:
			return self.propensity

		else:
			return 0.0

	def verify_agents(self, spec_list):

		def clean_list(agents):
			agents = [agent for agent in agents if agent[0] in spec_list]
			return agents

		self.used = clean_list(self.used)
		self.produced = clean_list(self.produced)

	def set_settables(self, *args, **kwargs):
		ensem = args[1]
		window = args[0]
		spec_list = ensem.run_params['species'].keys()
		cartographer_support = lgm.cartographer_mason(window)
		self.handle_widget_inheritance(*args, **kwargs)
		self.parameter_space_templates =\
			[lgeo.interface_template_p_space_axis(parent = self, 
							p_sp_bounds = self._p_sp_bounds_[0], 
								instance = self, key = 'rate')]
		self.parameter_space_templates[0].set_settables(*args, **kwargs)
		left_template = lgm.interface_template_gui(
				panel_position = (0, 2), 
				mason = cartographer_support, 
				layout = 'vertical', 
				keys = [['label'], ['rate']], 
				instances = [[self], [self]], 
				widgets = ['text', 'text'], 
				minimum_sizes = [[(400, 100)], [(100, 100)]], 
				box_labels = ['Reaction Name', 'Reaction Rate'], 
				initials = [[self.label], [self.rate]], 
				parameter_space_templates = [None, 
					self.parameter_space_templates[0]])
		self.verify_agents(spec_list)
		agents_template = lgm.interface_template_gui(
				panel_position = (0, 0), 
				layout = 'horizontal', 
				widgets = ['check_spin_list', 'check_spin_list'], 
				keys = [['used'], ['produced']], 
				instances = [[self], [self]], 
				labels = [spec_list, spec_list],
				box_labels = ['Reagents', 'Products'])
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['splitter'], 
				orientations = [['horizontal']], 
				templates = [[left_template, agents_template]]))
		modular_object.set_settables(self, *args, from_sub = True)

class species(modular_object):

	def _set_label_(self, value):
		before = self._label
		if modular_object._set_label_(self, value):
			del self.parent.run_params['species'][before]
			self.parent.run_params['species'][self._label] = self

	def __init__(self, label = 'another species', initial_count = 0, 
						current_count = None, visible_attributes = \
						['label', 'initial_count'], parent = None):
		self.system = None
		self.initial_count = initial_count
		if current_count == None: self.current_count = initial_count
		else: self.current_count = current_count
		self.brand_new = True
		parameter_space_templates =\
			[lgeo.interface_template_p_space_axis(instance = self, 
				key = 'initial_count', p_sp_bounds = [0, 1000000], 
					p_sp_increment = 1, p_sp_continuous = False, 
									parent = self)]
		modular_object.__init__(self, label = label, 
						visible_attributes = visible_attributes, 
			parameter_space_templates = parameter_space_templates)

	def to_string(self):
		self.ensem = None
		return '\t' + self.label + ' : ' + str(self.initial_count)

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.parent = args[1]
		ensem = self.parent
		cartographer_support = lgm.cartographer_mason(window)
		self.handle_widget_inheritance(*args, **kwargs)
		if self.brand_new:
			ensem.run_params['plot_targets'].append(self.label)
			plan = ensem.run_params['output_plans']['Simulation']
			plan.targeted.append(self.label)
			plan.rewidget(True)
			for subtargeted in plan.outputs:
				subtargeted.append(self.label)

			self.brand_new = not self.brand_new

		label_data_links = [lfu.interface_template_dependance(
								(self, 'label', self.label), 
								linkages = [(ensem.run_params, 
										'plot_targets', True, 
											'append_list')])]
		#this will cause a bug if a propensity_function_maker class
		# with a .key attribute which should not be linked to the
		# species name exists - so do not use one with this module
		#on the other hand, a subclass which uses .key exploits this
		#	this bug can be fixed with name mangling on the base class!!

		label_data_links.extend([lfu.interface_template_dependance(
			(self, 'label', self.label), linkages =\
				[(ensem.run_params['output_plans']['Simulation'], 
							'targeted', True, 'append_list')])])
		[label_data_links.extend([lfu.interface_template_dependance(
			(self, 'label', self.label), linkages =\
				[(ensem.run_params['output_plans']['Simulation'], 
					'outputs', True, 'append_list_nested', dex)])]) 
											for dex in range(4)]
		label_data_links.extend(
			[lfu.interface_template_dependance(
				(self, 'label', self.label), 
				linkages = [(rxn, 'used', True, 
					'append_tuples_list', 0, 0)]) 
					for rxn in ensem.run_params['reactions']])
		label_data_links.extend(
			[lfu.interface_template_dependance(
				(self, 'label', self.label), 
				linkages = [(rxn, 'produced', True, 
					'append_tuples_list', 0, 0)]) 
					for rxn in ensem.run_params['reactions']])		
		window = args[1]
		self.handle_widget_inheritance(*args, **kwargs)
		self.parameter_space_templates =\
			[lgeo.interface_template_p_space_axis(instance = self, 
							key = 'initial_count', parent = self, 
							p_sp_bounds = self._p_sp_bounds_[0], 
							p_sp_increment = self._p_sp_increments_[0], 
											p_sp_continuous = False)]
		self.parameter_space_templates[0].set_settables(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				mason = cartographer_support, 
				widgets = ['spin'], 
				instances = [[self]], 
				keys = [['initial_count']], 
				minimum_values = [[0]], 
				maximum_values = [[sys.maxint]], 
				initials = [[self.initial_count]], 
				box_labels = ['Initial Count'], 
				parameter_space_templates =\
					[self.parameter_space_templates[0]]))
		self.widg_templates.append(
			lgm.interface_template_gui(
				keys = [['label']], 
				minimum_sizes = [[(150, 50)]], 
				instances = [[self]], 
				widgets = ['text'], 
				box_labels = ['Species Name']))
		modular_object.set_settables(self, *args, from_sub = True)

'''
class criterion_spec_included_scaler_increment(
				lc.criterion_scaler_increment):

	def __init__(self, increment = 10.0, key = 'time', 
			base_class = lfu.interface_template_class(
					object, 'species scaler increment'), 
			label = 'scaler increment criterion', visible_attributes =\
			['label', 'base_class', 'bRelevant', 'key', 'increment']):
		lc.criterion_scaler_increment.__init__(self, label = label, 
			base_class = base_class, increment = increment, key = key)

	def find_last_value(self, system):
		try:
			last_value = system.species[self.key].current_count

		except:
			try:
				#this works for lists
				last_value = system.__dict__[self.key][-1]

			except TypeError:
				#if its just a value instead of a list
				last_value = system.__dict__[self.key]

		return last_value

	def set_settables(self, *args, **kwargs):
		ensem = args[1]
		self.keys = ['iteration', 'time'] +\
			ensem.run_params['species'].keys()
		self.handle_widget_inheritance(*args, from_sub = False)
		super(criterion_spec_included_scaler_increment, 
				self).set_settables(*args, from_sub = True)

class criterion_species_count(lc.criterion):

	def __init__(self, *args, **kwargs):
		if not 'base_class' in kwargs.keys():
			kwargs['base_class'] = lfu.interface_template_class(
										object, 'species count')

		if not 'label' in kwargs.keys():
			kwargs['label'] = 'species count criterion'

		if not 'visible_attributes' in kwargs.keys():
			kwargs['visible_attributes'] = ['label', 'base_class', 
								'bRelevant', 'spec_count_target']

		self.impose_default('key', None, **kwargs)
		self.impose_default('keys', [], **kwargs)
		self.impose_default('spec_count_target', 100, **kwargs)
		lc.criterion.__init__(self, *args, **kwargs)

	def to_string(self):
		return '\tspecies count : ' + str(self.spec_count_target) +\
												' : ' + self.key

	def initialize(self, *args, **kwargs):
		self.spec_count_target = float(self.spec_count_target)

	def verify_pass(self, system):
		for spec in system.species.keys():
			if self.key == spec:
				if sorted([	self.spec_count_target, 
							system.species[spec].current_count, 
							system.species[spec].initial_count	])[1]\
											== self.spec_count_target:
					#print 'criterion: reached target species count'
					return True

		return False

	def set_uninheritable_settables(self, *args, **kwargs):
		self.visible_attributes = ['label', 'base_class', 
			'bRelevant', 'spec_count_target', 'key', 'keys']
		#this has to be overridden even if this class lacks
		# its own uninheritable settables
		pass

	def set_settables(self, *args, **kwargs):
		ensem = args[1]
		self.keys = ensem.run_params['species'].keys()
		if not self.keys:
			self.keys = ['no available species!']
			self.key = 'no available species!'

		self.handle_widget_inheritance(*args, from_sub = False)
		self.widg_templates.append(
			lgm.interface_template_gui(
				panel_position = (1, 1), 
				widgets = ['radio'], 
				labels = [self.keys], 
				initials = [[self.key]], 
				instances = [[self]], 
				keys = [['key']], 
				box_labels = ['Species']))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['spin'], 
				doubles = [[False]], 
				initials = [[int(self.spec_count_target)]], 
				instances = [[self]], 
				keys = [['spec_count_target']], 
				box_labels = ['Target Species Count']))
		super(criterion_species_count, self).set_settables(
									*args, from_sub = True)
'''

'''
lc.valid_criterion_base_classes = [
	lfu.interface_template_class(
		lc.criterion_sim_time, 'time limit'), 
	lfu.interface_template_class(
		lc.criterion_iteration, 'iteration limit'), 
	lfu.interface_template_class(
		lc.criterion_capture_count, 'capture limit'), 
	lfu.interface_template_class(
		criterion_spec_included_scaler_increment, 
					'species scaler increment'), 
	lfu.interface_template_class(
		criterion_species_count, 'species count')]
'''


