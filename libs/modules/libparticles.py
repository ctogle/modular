import libs.modular_core.libfundamental as lfu
from libs.modular_core.libfundamental import modular_object_qt as modular_object
import libs.modular_core.libmodcomponents as lmc
import libs.modular_core.libsimcomponents as lsc
import libs.modular_core.libgeometry as lgeo

import libs.modules.particles_support.generic_wrap as wrapper

import traceback
import sys

import pdb

module_name = 'particles'
run_param_keys = lmc.run_param_keys + ['Variables', 'Vectors']

if __name__ == 'libs.modules.libparticles':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is the', module_name, 'module!'

class sim_system(lsc.sim_system_external):

	def encode(self):
		'''
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
		'''
		C=5
		A=18,18,18,18,18,18,235,235,239,18,18,235,18,239,18,18,235,235,235,18,18,18,18,18,18
		G=10
		L=10.0
		S=0
		E=0.001
		F=120000
		'''
		sub_var = [var.to_string().replace(' ','').replace('\t','') 
				for key, var in self.params['variables'].items()]
		variable_string = '<variables>' + ','.join(sub_var)
		sub_vec = [vec.to_string().replace(' ','').replace('\t','')
				for key, vec in self.params['vectors'].items()]
		vector_string = '<vectors>' + ','.join(sub_vec)
		self.system_string = variable_string + vector_string
		print 'encoded', self.system_string

	def iterate(self):
		try:
			self.data = self.finalize_data(
				*wrapper.simulate(self.system_string))
			#self.data = [['DATA!']]

		except:
			traceback.print_exc(file=sys.stdout)
			print 'simulation failed; aborting'
			self.bAbort = True

	def finalize_data(self, data, targets, toss = None):
		if data is False:
			self.bAbort = True
			return data

		pdb.set_trace()
		data = [dater for dater in data if len(dater) > 1]
		reorder = []
		for name in self.params['plot_targets']:
			dex = targets.index(name)
			reorder.append(np.array(data[dex][:toss], dtype = np.float))

		return np.array(reorder, dtype = np.float)

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
		modular_object.set_settables(self, *args, from_sub = True)

class vector(modular_object):

	def _set_label_(self, value):
		before = self._label
		if modular_object._set_label_(self, value):
			del self.parent.run_params['vectors'][before]
			self.parent.run_params['vectors'][self._label] = self

	def __init__(self, *args, **kwargs):
		if 'label' not in kwargs.keys(): kwargs['label'] = 'vector'
		self.impose_default('values', [1.0], **kwargs)
		self.brand_new = True
		parameter_space_templates = []
		#parameter_space_templates =\
		#	[lgeo.interface_template_p_space_axis(instance = self, 
		#						p_sp_bounds = ['-10e64', '10e64'], 
		#							parent = self, key = 'value')]
		modular_object.__init__(self, *args, 
			parameter_space_templates =\
				parameter_space_templates, **kwargs)

	def to_string(self):
		self.ensem = None
		return '\t' + self.label + ' : ' + ','.join(self.values)

	def set_settables(self, *args, **kwargs):
		ensem = args[1]
		self.parent = ensem
		window = args[0]
		'''
		if self.brand_new:
			ensem.run_params['plot_targets'].append(self.label)
			plan = ensem.run_params['output_plans']['Simulation']
			plan.targeted.append(self.label)
			plan.rewidget(True)
			for subtargeted in plan.outputs:
				subtargeted.append(self.label)

			self.brand_new = not self.brand_new
		'''

		#dictionary_support = lgm.dictionary_support_mason(window)
		#where_reference = ensem.run_params['vectors']
		#cartographer_support = lgm.cartographer_mason(window)
		self.handle_widget_inheritance(*args, **kwargs)
		#self.parameter_space_templates =\
		#	[lgeo.interface_template_p_space_axis(parent = self, 
		#					p_sp_bounds = self._p_sp_bounds_[0], 
		#						instance = self, key = 'value')]
		#self.parameter_space_templates[0].set_settables(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				keys = [['values']], 
				instances = [[self]], 
				widgets = ['text'], 
				box_labels = ['Vector Components']))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['text'], 
				keys = [['label']], 
				instances = [[self]], 
				initials = [[self.label]], 
				box_labels = ['Vector Name']))
		modular_object.set_settables(self, *args, from_sub = True)

def parse_variable_line(*args):
	data = args[0]
	ensem = args[1]
	split = [item.strip() for item in data.split(':')]
	name, value = split[0], split[1]
	varib = variable(label = name, value = value)
	return name, varib

def parse_vector_line(*args):
	data = args[0]
	ensem = args[1]
	split = [item.strip() for item in data.split(':')]
	name, value = split[0], split[1]
	values = value.split(',')
	vect = vector(label = name, values = values)
	return name, vect

def set_parameters(ensem):
	if 'variables' in ensem.run_params.keys():
		for key, val in ensem.run_params['variables'].items():
			ensem.run_params['variables'][key]._destroy_()

	if 'vectors' in ensem.run_params.keys():
		for key, val in ensem.run_params['vectors'].items():
			ensem.run_params['vector'][key]._destroy_()

	ensem.run_params['variables'] = {}
	ensem.run_params['vectors'] = {}
	lmc.set_parameters(ensem)
	ensem.run_params.create_partition('system', 
		[	'variables', 'vectors', 
			'end_criteria', 'capture_criteria', 'plot_targets'	])

def generate_gui_templates_qt(window, ensemble):
	set_module_memory_(ensemble)
	panel_template_lookup =\
		lmc.generate_panel_template_lookup_standard(window, ensemble)
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
	panel_template_lookup.append(('vectors', 
		lgm.generate_add_remove_select_inspect_box_template(
			window = window, key = 'vectors', 
			labels = ['Add Vector', 'Remove Vector'], 
			wheres = [ensemble._children_, 
				ensemble.run_params['vectors']], 
			parent = ensemble, 
			selector_handle = (ensemble._module_memory_[0], 
									'vector_selector'), 
			memory_handle = (ensemble._module_memory_[0], 
							'vector_selected_memory'), 
			base_class = vector)))
	return lmc.generate_gui_templates_qt(window, ensemble, 
						lookup = panel_template_lookup)

def set_module_memory_(ensem):
	ensem._module_memory_ = [lfu.data_container(
		output_plan_selected_memory = 'Simulation', 
				variable_selected_memory = 'None', 
				vector_selected_memory = 'None')]

def parse_mcfg(lines, *args):
	support = [['variables', 'vectors'], 
				[parse_variable_line, 
				parse_vector_line]]
	lmc.parse_mcfg(lines, args[0], args[1], support)

def write_mcfg(*args):
	run_params = args[0]
	ensem = args[1]
	lines = ['']
	lmc.params_to_lines(run_params, 'variables', lines)
	lmc.params_to_lines(run_params, 'vectors', lines)
	return lmc.write_mcfg(args[0], args[1], lines)




