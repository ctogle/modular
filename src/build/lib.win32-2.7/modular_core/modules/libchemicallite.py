import modular_core.libfundamental as lfu
from modular_core.libfundamental import modular_object_qt as modular_object
import modular_core.libsimcomponents as lsc
import modular_core.libmath as lm
import modular_core.libgeometry as lgeo
import modular_core.libfitroutine as lfr
import modular_core.libpostprocess as lpp
#import libs.modular_core.libcriterion as lc
import modular_core.libmodcomponents as lmc

import stringchemical as chemfast
import stringchemical_timeout as chemfast_timeout

'''
import libs.modular_core.libfundamental as lfu
from libs.modular_core.libfundamental import modular_object_qt as modular_object
import libs.modular_core.libsimcomponents as lsc
import libs.modular_core.libmath as lm
import libs.modular_core.libgeometry as lgeo
import libs.modular_core.libfitroutine as lfr
import libs.modular_core.libpostprocess as lpp
#import libs.modular_core.libcriterion as lc
import libs.modular_core.libmodcomponents as lmc

import libs.modules.chemicallite_support.stringchemical as chemfast
import libs.modules.chemicallite_support.stringchemical_timeout as chemfast_timeout
'''

import sys, time, types, random, traceback
import numpy as np
from math import log as log

import pdb

if __name__ == 'modular_core.modules.libchemicallite':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__':
	print 'this is the chemical lite module library!'

module_name = 'chemicallite'
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

def parse_variable_line(*args):
	data = args[0]
	ensem = args[1]
	split = [item.strip() for item in data.split(':')]
	name, value = split[0], split[1]
	varib = variable(label = name, value = value)
	return name, varib

def parse_function_line(*args):
	data = args[0]
	ensem = args[1]
	split = [item.strip() for item in data.split(':')]
	name, value = split[0], split[1]
	func = function_cont(label = name, func_statement = value)
	return name, func

def parse_reaction_line(*args):
	data = args[0]
	ensem = args[1]

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

def parse_species_line(*args):
	data = args[0]
	ensem = args[1]
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

def write_mcfg(*args):
	run_params = args[0]
	ensem = args[1]
	lines = ['']
	lmc.params_to_lines(run_params, 'variables', lines)
	lmc.params_to_lines(run_params, 'functions', lines)
	lmc.params_to_lines(run_params, 'reactions', lines)
	lmc.params_to_lines(run_params, 'species', lines)
	return lmc.write_mcfg(args[0], args[1], lines)

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

	def iterate(self):
		try:
			#seed = int(time.time()) + self.identifier
			if self.timeout:
				self.data = self.finalize_data(
					*chemfast_timeout.simulate(
						self.system_string, self.timeout))
						#self.system_string, seed, self.timeout))

			else:
				self.data = self.finalize_data(
					*chemfast.simulate(self.system_string))
					#*chemfast.simulate(self.system_string, seed))

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
								#p_sp_bounds = ['-10e64', '10e64'], 
							p_sp_bounds = [0.0, sys.float_info.max], 
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




