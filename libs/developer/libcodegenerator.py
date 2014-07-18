import libs.modular_core.libfundamental as lfu

import pdb

########################################################################
### code samples
########################################################################

ex_modular_object = '''\
class <name>(lfu.modular_object_qt):

	def __init__(self, *args, **kwargs):
<inits>
		lfu.modular_object_qt.__init__(self, *args, **kwargs)

<methods>
	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
<attributes>
		lfu.modular_object_qt.set_settables(
			self, *args, from_sub = True)
'''

ex_modular_attribute_init = '''\
		self.impose_default('<key>', <default>, **kwargs)
'''

ex_modular_object_method = '''\
	def <method_name>(self, <method_args>, <method_kwargs>):
		print 'method <method_name> of', self
'''

ex_modular_gui_template_bool = '''\
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['check_set'], 
				verbosities = [<verbosity>], 
				instances = [[<instance>]], 
				append_instead = [<append>], 
				keys = [['<key>']], 
				labels = [['<label>']]))
'''

ex_modular_gui_template_string = '''\
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['text'], 
				verbosities = [<verbosity>], 
				read_only = [<read_only>], 
				multiline = [<multiline>], 
				initials = [[<initial>]], 
				alignments = [['<alignment>']], 
				instances = [[<instance>]], 
				keys = [['<key>']], 
				box_labels = ['<box_label>']))
'''

ex_program_module = '''\
import libs.modular_core.libfundamental as lfu


import pdb

<classes>

if __name__ == '<full_module_path>':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'

'''

ex_simulation_module = '''\
import libs.modular_core.libfundamental as lfu
from libs.modular_core.libfundamental import modular_object_qt as modular_object
import libs.modular_core.libmodcomponents as lmc
import libs.modular_core.libsimcomponents as lsc
import libs.modular_core.libgeometry as lgeo

import libs.modules.particles_support.generic_wrap as wrapper

import traceback
import sys

import pdb

module_name = <module_name>
run_param_keys = lmc.run_param_keys + ['Variables', 'Vectors']

if __name__ == '<full_module_path>':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is the', module_name, 'module!'

class sim_system(lsc.sim_system_external):

	def encode(self):
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
		self.handle_widget_inheritance(*args, **kwargs)
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

'''

ex_program = '''\
import libs.modular_core.libfundamental as lfu
import libs.gui.libqtgui as lqg
lgm = lqg.lgm
lgd = lqg.lgd
lgb = lqg.lgb
import libs.<program_name>.lib<base_class_module> as lprog

import os

class application_<program_name>(lqg.application):
	_content_ = [lprog.<base_class>()]
	gear_icon = os.path.join(os.getcwd(), 'resources', 'gear.png')

	def __init__(self, *args, **kwargs):
		lqg.application.__init__(self, *args, **kwargs)
		x, y = lfu.convert_pixel_space(1024, 256)
		x_size, y_size = lfu.convert_pixel_space(512, 512)
		self._standards_ = {
			'title' : '<program_name>', 
			'geometry' : (x, y, x_size, y_size), 
			'window_icon' : self.gear_icon}
		lqg._window_.apply_standards(self._standards_)
		#lqg.application.setStyle(lgb.create_style('windows'))
		#lqg.application.setStyle(lgb.create_style('xp'))
		#lqg.application.setStyle(lgb.create_style('vista'))
		#lqg.application.setStyle(lgb.create_style('motif'))
		#lqg.application.setStyle(lgb.create_style('cde'))
		lqg.application.setStyle(lgb.create_style('plastique'))
		#lqg.application.setStyle(lgb.create_style('clean'))

_application_ = application_<program_name>
_application_locked_ = False
'''

ex__init_ = '''\
#!/usr/bin/python2.7
'''

ex_setting_file = '''\

<interface>
interface_verbosity = 2

'''

bell_setting_manager = '''\
		self.settings_manager = lset.settings_manager(parent = self, 
							filename = "<program_name>_settings.txt")
		self.settings = self.settings_manager.read_settings()
'''

########################################################################
### end code samples
########################################################################

class code_writer(lfu.modular_object_qt):
	#	create modular objects
	#	add/remove widgets and methods
	#	test these by running them locally as a program
	def __init__(self, *args, **kwargs):
		lfu.modular_object_qt.__init__(self, *args, **kwargs)

	# _get_bells_ returns a list of strings associated with kwargs
	def _get_bells_(self, **kwargs):
		bells = []
		if 'setting_manager' in kwargs.keys():
			if kwargs['setting_manager']:
				bells.append(bell_setting_manager)
		return bells

	def make_mobject(self, name = '_new_mobject_', 
			attributes = [], methods = [], **kwargs):
		new = ex_modular_object[:]
		new = new.replace('<name>', name)
		attr_lines = [attr.write_template() for attr in attributes]
		new = new.replace('<attributes>', ''.join(attr_lines))
		meth_lines = [meth.write_method() for meth in methods]
		new = new.replace('<methods>', '\n'.join(meth_lines))
		inits = self._get_bells_(**kwargs)
		init_lines = [attr.write_init() for attr in attributes] + inits
		new = new.replace('<inits>', ''.join(init_lines))
		return new

	def make_program(self, base_class, base_class_module, 
							program = '_new_program_'):
		new = ex_program[:]
		new = new.replace('<base_class_module>', base_class_module)
		new = new.replace('<base_class>', base_class)
		new = new.replace('<program_name>', program)
		return new

	def make_prog_module(self, program = 'modular_core', 
				module = '_new_module_', classes = []):
		new = ex_program_module[:]
		path = '.'.join(['libs', program, 'lib' + module])
		new = new.replace('<full_module_path>', path)
		class_lines = '\n'.join(classes)
		new = new.replace('<classes>', class_lines)
		new = new.replace('<program_name>', program)
		return new

	def make_sim_module(self, 
			module = '_new_simulation_module_', motif = 'cython'):
		new = ex_simulation_module[:]
		path = '.'.join(['libs', 'modules', 'lib' + module])
		new = new.replace('<full_module_path>', path)
		new = new.replace('<module_name>', "'" + module + "'", 1)
		return new

	def make__init_(self):
		new = ex__init_[:]
		return new

if __name__ == 'libs.developer.libcodegenerator':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'


