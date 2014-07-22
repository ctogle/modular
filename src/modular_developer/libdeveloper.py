import modular_core.libfundamental as lfu
import modular_core.libsettings as lset
import modular_core.libfiler as lf

import modular_developer.libprogramdeveloper as lprogd
import modular_developer.libmoduledeveloper as lmodud
import modular_developer.libmobjectdeveloper as lmobjd

import importlib
from copy import deepcopy as copy
import inspect
import types
import sys
import os

import pdb

class modular_developer2(lfu.modular_object_qt):

	def __init__(self, *args, **kwargs):

		self.prog_mngr = lprogd.program_manager(parent = self)
		self.pmod_mngr = lmodud.module_manager(parent = self)
		self.smod_mngr = lmodud.simulation_module_manager(parent = self)
		self.mobj_mngr = lmobjd.modular_object_manager(parent = self)

		self.current_tab_index = 0
		self.settings_manager = lset.settings_manager(
			parent = self, filename = 'developer_settings.txt')
		self.settings = self.settings_manager.read_settings()
		lfu.modular_object_qt.__init__(self, *args, **kwargs)
		self._children_ = [
			self.prog_mngr, self.pmod_mngr, 
			self.smod_mngr, self.mobj_mngr]

	def change_settings(self):
		self.settings_manager.display()

	def make_tab_book_pages(self, *args, **kwargs):
		window = args[0]
		prog_templates = self.prog_mngr.widg_templates
		pmod_templates = self.pmod_mngr.widg_templates
		smod_templates = self.smod_mngr.widg_templates
		mobj_templates = self.mobj_mngr.widg_templates
		pages = [
			('Create/Edit Programs', prog_templates), 
			('Create/Edit Program Modules', pmod_templates), 
			('Create/Edit Simulation Modules', smod_templates), 
			('Create/Edit Modular Objects', mobj_templates)]
		return pages

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)

		wrench_icon_path = os.path.join(
			os.getcwd(), 'resources', 'wrench_icon.png')
		refresh_icon_path = os.path.join(
			os.getcwd(), 'resources', 'refresh.png')
		center_icon_path = os.path.join(
			os.getcwd(), 'resources', 'center.png')
		wrench_icon = lgb.create_icon(wrench_icon_path)
		refresh_icon = lgb.create_icon(refresh_icon_path)
		center_icon = lgb.create_icon(center_icon_path)

		settings_ = lgb.create_action(parent = window, label = 'Settings', 
					bindings = lgb.create_reset_widgets_wrapper(
					window, self.change_settings), icon = wrench_icon, 
					shortcut = 'Ctrl+Shift+S', statustip = 'Settings')
		self.refresh_ = lgb.create_reset_widgets_function(window)
		update_gui_ = lgb.create_action(parent = window, 
			label = 'Refresh GUI', icon = refresh_icon, 
			shortcut = 'Ctrl+G', bindings = self.refresh_, 
			statustip = 'Refresh the GUI (Ctrl+G)')
		center_ = lgb.create_action(parent = window, label = 'Center', 
					bindings = [window.on_resize, window.on_center], 
							icon = center_icon, shortcut = 'Ctrl+C', 
										statustip = 'Center Window')

		self.menu_templates.append(
			lgm.interface_template_gui(
				menu_labels = ['&File', '&File', '&File'], 
				menu_actions = [settings_, center_, update_gui_]))
		self.tool_templates.append(
			lgm.interface_template_gui(
				tool_labels = ['&Tools', '&Tools', '&Tools'], 
				tool_actions = [settings_, center_, update_gui_]))

		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['tab_book'], 
				verbosities = [0], 
				pages = [self.make_tab_book_pages(*args, **kwargs)], 
				initials = [[self.current_tab_index]], 
				handles = [(self, 'tab_ref')], 
				instances = [[self]], 
				keys = [['current_tab_index']]))
		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)

'''
the goal of the libdeveloper program is to procedurally generate
code which is useful in many contexts

it operates at several levels:
	program level
		create programs
		add/remove program modules (from anywhere)
	program module level
		create modules associated with any program or modular_core
		add/remove modular objects
	simulation module level
		create simulation modules for Modular Simulator
		there are many options for this - encapsulate
	modular object level
		create modular objects
		add/remove widgets and methods
		test these by running them locally as a program
'''

if __name__ == 'modular_developer.libdeveloper':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'








class code_examples(lfu.modular_object_qt):

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

	def make_mobject(self, name = '_new_mobject_', 
			attributes = [], methods = [], inits = []):
		new = copy(self.ex_modular_object)
		new = new.replace('<name>', name)
		attr_lines = [attr.write_template() for attr in attributes]
		new = new.replace('<attributes>', ''.join(attr_lines))
		meth_lines = [meth.write_method() for meth in methods]
		new = new.replace('<methods>', '\n'.join(meth_lines))
		init_lines = [attr.write_init() for attr in attributes] + inits
		new = new.replace('<inits>', ''.join(init_lines))
		return new

	def make_mobject_attribute_init(self, key = '_new_key_', 
								default = '_new_default_'):
		new = copy(self.ex_modular_attribute_init)
		new = new.replace('<key>', key)
		new = new.replace('<default>', default)
		return new

	def make_mobject_method(self, name = '_new_mobject_method_', 
							args = '*args', kwargs = '**kwargs'):
		new = copy(self.ex_modular_object_method)
		new = new.replace('<method_name>', name)
		new = new.replace('<method_args>', args)
		new = new.replace('<method_kwargs>', kwargs)
		return new

	def make_mobject_gui_template_bool(self, 
			verbosity = '1', instance = 'self', append = 'False', 
					key = '_modu_bool_', label = 'modular bool'):
		new = copy(self.ex_modular_gui_template_bool)
		new = new.replace('<verbosity>', verbosity)
		new = new.replace('<instance>', instance)
		new = new.replace('<append>', append)
		new = new.replace('<label>', label)
		new = new.replace('<key>', key)
		return new

	def make_mobject_gui_template_string(self, verbosity = '1', 
			multiline = 'False', initial = 'self._modu_str_', 
			key = '_modu_str_', align = 'center', instance = 'self', 
						read_only = 'False', label = '_modu_attr_'):
		new = copy(self.ex_modular_gui_template_string)
		new = new.replace('<verbosity>', verbosity)
		new = new.replace('<instance>', instance)
		new = new.replace('<read_only>', read_only)
		new = new.replace('<multiline>', multiline)
		new = new.replace('<alignment>', align)
		new = new.replace('<initial>', initial)
		new = new.replace('<key>', key)
		new = new.replace('<box_label>', label)
		return new

	def make_prog_module(self, program = 'modular_core', 
				module = '_new_module_', classes = []):
		new = copy(self.ex_program_module)
		path = '.'.join(['libs', program, 'lib' + module])
		new = new.replace('<full_module_path>', path)
		class_lines = '\n'.join(classes)
		new = new.replace('<classes>', class_lines)
		return new

	def make_sim_module(self, module = '_new_simulation_module_'):
		new = copy(self.ex_simulation_module)
		path = '.'.join(['libs', 'modules', 'lib' + module])
		new = new.replace('<full_module_path>', path)
		new = new.replace('<module_name>', "'" + module + "'", 1)
		return new

	def make_program(self, base_class, base_class_module, 
							program = '_new_program_'):
		new = copy(self.ex_program)
		new = new.replace('<base_class_module>', base_class_module)
		new = new.replace('<base_class>', base_class)
		new = new.replace('<program_name>', program)
		return new

	def make__init_(self):
		new = copy(self.ex__init_)
		return new

class mobject_attribute(lfu.modular_object_qt):

	def __init__(self, *args, **kwargs):
		if 'examples' in kwargs.keys():
			examples = kwargs['examples']

		else: examples = code_examples(parent = self)
		self.examples = examples
		self.impose_default('template_lines', [], **kwargs)
		self.impose_default('attr_type', 'bool', **kwargs)
		self.impose_default('attr_value', 'False', **kwargs)
		self.impose_default('attr_label', '_modu_attribute_', **kwargs)
		self.impose_default('attr_verbosity', '1', **kwargs)
		self.impose_default('attr_instance', 'self', **kwargs)
		self.impose_default('attr_key', '_modu_bool_', **kwargs)
		self.impose_default('attr_initial', '.'.join([
			self.attr_instance, self.attr_key]), **kwargs)
		lfu.modular_object_qt.__init__(self, *args, **kwargs)
		self.attr_key = lfu.unique_pool_item(
			self.parent.mobject_analysis_attr_labels, 
						self.attr_key, parent = self)
		if self.template_lines: self.read_template()

	def write_init(self):
		if self.attr_type == 'bool':
			key = '_modu_bool_'
			default = 'False'

		elif self.attr_type == 'string':
			key = '_modu_str_'
			default = "''"

		if self.attr_key.value: key = self.attr_key.value
		lines = self.examples.make_mobject_attribute_init(
							key = key, default = default)
		return lines

	def write_template_bool(self):
		if self.attr_label: label = self.attr_label
		else: label = 'modular attribute label'
		if self.attr_verbosity: verbosity = self.attr_verbosity
		else: verbosity = '1'
		if self.attr_instance: instance = self.attr_instance
		else: instance = 'self'
		if self.attr_key.value: key = self.attr_key.value
		else: key = '_modu_bool_'
		lines = self.examples.make_mobject_gui_template_bool(
			verbosity = verbosity, instance = instance, 
			key = key, label = label)
		return lines

	def write_template_string(self):
		if self.attr_verbosity: verbosity = self.attr_verbosity
		else: verbosity = '1'
		if self.attr_instance: instance = self.attr_instance
		else: instance = 'self'
		if self.attr_key.value: key = self.attr_key.value
		else: key = '_modu_str_'
		if self.attr_initial: initial = self.attr_initial
		else: initial = 'self._modu_str_'
		if self.attr_label: label = self.attr_label
		else: label = '_modu_attr_'
		lines = self.examples.make_mobject_gui_template_string(
				initial = initial, key = key, align = 'center', 
				verbosity = verbosity, multiline = 'False', 
				instance = instance, read_only = 'False', label = label)
		return lines

	def write_template(self):
		lines = []
		if self.attr_type == 'bool':
			lines = self.write_template_bool()

		elif self.attr_type == 'string':
			lines = self.write_template_string()

		else: print 'unwriteable widget type', self.attr_type
		return ''.join(lines)

	def read_template(self):

		def extract(line_dex, open_, _close):
			line = self.template_lines[line_dex]
			open_dex = line.find(open_) + len(open_)
			close_dex = line.find(_close)
			extracted = line[open_dex:close_dex]
			return extracted

		if self.template_lines:
			#print '#'*50
			#for li in self.template_lines: print li
			#print '#'*50
			type_line_dex = [li.startswith('widgets = ') for li 
							in self.template_lines].index(True)
			key_line_dex = [li.startswith('keys = ') for li 
							in self.template_lines].index(True)

		else: return

		#type_line = self.template_lines[type_line_dex]
		#types_open_dex = type_line.find('[') + 1
		#types_closed_dex = type_line.find(']')
		#widget = type_line[types_open_dex:types_closed_dex]
		widget = extract(type_line_dex, '[', ']')
		key = extract(key_line_dex, '[[\'', '\']')

		if widget == "'text'": self.attr_type = 'string'
		elif widget == "'check_set'": self.attr_type = 'bool'
		else: print 'unreadable widget type', widget
		if key: self.attr_key.value = key
		else: print 'unreadable widget key', key

	def generate_template(self):
		print 'not sure what generate template will do here'

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.read_template()
		attr_types = ['bool', 'string']
		self.handle_widget_inheritance(*args, **kwargs)
		templates = []
		templates.append(
			lgm.interface_template_gui(
				widgets = ['text'], 
				initials = [[self.attr_label]], 
				alignments = [['center']], 
				instances = [[self]], 
				keys = [['attr_label']], 
				box_labels = ['Label']))
		templates.append(
			lgm.interface_template_gui(
				widgets = ['text'], 
				initials = [[self.attr_key.value]], 
				alignments = [['center']], 
				instances = [[self.attr_key]], 
				keys = [['value']], 
				box_labels = ['Name']))
		templates.append(
			lgm.interface_template_gui(
				widgets = ['radio'], 
				labels = [attr_types], 
				initials = [[self.attr_type]], 
				instances = [[self]], 
				keys = [['attr_type']], 
				box_labels = ['Type']))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['panel'], 
				templates = [templates], 
				box_labels = ['Attribute ' + self.attr_label]))
		lfu.modular_object_qt.set_settables(
			self, *args, from_sub = True)

class mobject_method(lfu.modular_object_qt):

	def __init__(self, *args, **kwargs):
		if 'examples' in kwargs.keys():
			examples = kwargs['examples']

		else: examples = code_examples(parent = self)
		self.examples = examples
		self.impose_default('method_lines', [], **kwargs)
		if self.method_lines: self.read_method()
		self.impose_default('meth_name', 
			'_modular_method_name_', **kwargs)
		self.impose_default('meth_args', '*args', **kwargs)
		self.impose_default('meth_kwargs', '**kwargs', **kwargs)

		lfu.modular_object_qt.__init__(self, *args, **kwargs)

	def write_method(self):
		if self.meth_name: meth_name = self.meth_name
		else: meth_name = '_modular_method_name_'
		if self.meth_args: meth_args = self.meth_args
		else: meth_args = '*args'
		if self.meth_kwargs: meth_kwargs = self.meth_kwargs
		else: meth_kwargs = '**kwargs'
		lines = self.examples.make_mobject_method(name = meth_name, 
							args = meth_args, kwargs = meth_kwargs)
		return ''.join(lines)

	def read_method(self):
		#self.impose_default('meth_args', '*args', **kwargs)
		#self.impose_default('meth_kwargs', '**kwargs', **kwargs)
		if self.method_lines:
			name_line_dex = [li.startswith('def ') for li 
						in self.method_lines].index(True)

		else: return False
		name_line = self.method_lines[name_line_dex]
		name_open_dex = name_line.find('def ') + 4
		name_closed_dex = name_line.find('(')
		name = name_line[name_open_dex:name_closed_dex]
		self.meth_name = name
		return True

	def dummy(self): print 'method was not readable'

	def generate_template(self):
		if self.read_method():
			template = lgm.interface_template_gui(
				widgets = ['button_set'], 
				labels = [[self.meth_name]], 
				bindings = [[getattr(
						self.parent.temp_mobj, 
						self.meth_name)]])
			return template

		else:
			print 'could not read method'
			template = lgm.interface_template_gui(
				widgets = ['button_set'], 
				labels = [['dummy method']], 
				bindings = [[self.dummy]])
			return template

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.read_method()
		self.handle_widget_inheritance(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['text'], 
				#handles = [(self, 'method_name_box')], 
				initials = [[self.meth_name]], 
				instances = [[self]], 
				keys = [['meth_name']], 
				box_labels = ['Method Name']))
		lfu.modular_object_qt.set_settables(
			self, *args, from_sub = True)

class mobject_template_arrangement(lfu.modular_object_qt):

	#_inspector_is_mobj_panel_ = True

	def __init__(self, *args, **kwargs):
		if 'examples' in kwargs.keys():
			examples = kwargs['examples']

		else: examples = code_examples(parent = self)
		self.examples = examples
		self.impose_default('arrangement_lines', [], **kwargs)
		self.impose_default('arrange_type', 'Panel', **kwargs)

		if self.arrangement_lines: self.read_arrangement()
		lfu.modular_object_qt.__init__(self, *args, **kwargs)

	def write_arrangement(self):
		lines = self.examples.make_mobject_template_arrangment()
		return ''.join(lines)

	def read_arrangement(self):
		if self.arrangement_lines: pass
			#name_line_dex = [li.startswith('def ') for li 
			#			in self.method_lines].index(True)

		else: return False
		#name_line = self.method_lines[name_line_dex]
		#name_open_dex = name_line.find('def ') + 4
		#name_closed_dex = name_line.find('(')
		#name = name_line[name_open_dex:name_closed_dex]
		#self.meth_name = name
		return True

	def dummy(self): print 'arrangement was not readable'

	def generate_template(self):
		if self.read_arrangement():
			template = lgm.interface_template_gui(
				widgets = ['button_set'], 
				labels = [[self.meth_name]], 
				bindings = [[self.dummy]])
			return template

		else:
			print 'could not read arrangement'
			template = lgm.interface_template_gui(
				widgets = ['button_set'], 
				labels = [['dummy method']], 
				bindings = [[self.dummy]])
			return template

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.read_arrangement()
		self.handle_widget_inheritance(*args, **kwargs)
		arrange_types = ['Panel', 'Splitter']
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['radio'], 
				labels = [arrange_types], 
				initials = [[self.arrange_type]], 
				instances = [[self]], 
				keys = [['arrange_type']], 
				box_labels = ['Type']))
		#interface for member control
		lfu.modular_object_qt.set_settables(
			self, *args, from_sub = True)

class mobject_analyzer(lfu.modular_object_qt):

	def __init__(self, *args, **kwargs):
		self.temp_mobj_code_path = os.path.join(os.getcwd(), 'libs', 
						'developer', 'libdeveloper_temp_module.py')

		#self._panel_scroll_memory_ = [None, None]
		self._panel_scroll_memory_ = None

		self.mobject_subclasses = []
		self.mobject_names = []

		self.mobject_analysis_name = ''
		self.mobject_analysis_attributes = []
		self.mobject_analysis_attr_labels = []
		self.mobject_analysis_methods = []
		self.mobject_analysis_arrangements = []

		self.method_selector = None
		self.attribute_selector = None
		self.method_selected_memory = None
		self.attribute_selected_memory = None
		self.arrangement_selected_memory = None

		if 'examples' in kwargs.keys():
			self.examples = kwargs['examples']

		else: self.examples = code_examples(parent = self)
		lfu.modular_object_qt.__init__(self, *args, **kwargs)
		self._children_ = []

	def record_until_unindent(self, lines, start_dex):
		indent = lines[start_dex].count('\t')
		record = True

		relevant_lines = [lines[start_dex]]
		line_dex = start_dex + 1
		while line_dex < len(lines) and record:
			line = lines[line_dex]
			rec_indent = line.count('\t')
			if not rec_indent > indent and not line.strip() == '':
				record = False
				line_dex += 1
				continue

			relevant_lines.append(line)
			line_dex += 1

		return relevant_lines

	def analyze(self, text_ = None):

		def analyze_module(text):
			class_lines = []
			lines = text.split('\n')
			class_def_lines = [li.count('class ') > 0 for li in lines]
			dexes = [dex for dex in range(len(class_def_lines)) 
										if class_def_lines[dex]]
			for dex in dexes:
				class_lines.append(self.record_until_unindent(lines, dex))

			mod = self.parent.relevant_program_module
			dexes = [mod in item[1] for item in 
				self.parent.relevant_program_modules]
			pas = [item[0] for item in self.parent.relevant_program_modules]
			if dexes.count(True) == 1:
				pa = pas[dexes.index(True)]
				mod_pa = '.'.join(pa[len(os.getcwd()):].split(os.sep)[1:]+\
							['lib' + self.parent.relevant_program_module])
				mod_ = importlib.import_module(mod_pa)
				mobjs = []
				for name, obj in inspect.getmembers(mod_, inspect.isclass):
					if issubclass(obj, lfu.modular_object_qt):
						mobjs.append(obj)

				mobjs_in_mod_names = [repr(mobj).replace('"', '').\
					replace("'", '').replace('>', '').\
					replace('<', '').split('.')[-1] for mobj in mobjs]
				#this is a poor, error-prone implementation...
				class_lines = [lines_ for lines_ in class_lines if 
					self.read_mobject_name(lines_[0], super_ = '(') 
											in mobjs_in_mod_names]

			else:
				print 'module name conflict'
				pdb.set_trace()

			classes = [mobject_proxy(class_lines = class_lines, 
						examples = self.examples, parent = self) 
								for class_lines in class_lines]
			return classes
			#self.mobject_subclasses = classes
			#self.mobject_names = [self.read_mobject_name(sub.class_lines[0]) 
			#							for sub in self.mobject_subclasses]

		if text_: self.mobject_subclasses = analyze_module(text_)
		else:
			self.mobject_subclasses = []
			print 'load every module and scan for mobjects, making proxies'

		print 'analyze!'
		self.rewidget(True)

	def read_mobject_name(self, text, 
			super_ = '(lfu.modular_object_qt)'):
		class_dex = text.find('class ') + len('class ')
		class_name_end_dex = text[class_dex:].find(super_) + class_dex
		name = text[class_dex:class_name_end_dex]
		return name

	def read_mobject_attributes(self, text):
		attributes = []
		set_set_str = 'def set_settables(self, *args, **kwargs):'
		set_set_end_str = 'lfu.modular_object_qt.set_settables('
		interface_gui_str = 'lgm.interface_template_gui('
		set_set_dex = text.find(set_set_str) + len(set_set_str)
		set_set_end_dex = text[set_set_dex:].find(
					set_set_end_str) + set_set_dex
		set_lines = text[set_set_dex:set_set_end_dex]
		set_lines = set_lines.split('\n')
		templ_lines = [line.count(interface_gui_str) > 0 
								for line in set_lines]

		line_dex = 0
		indent = None
		record = False
		templates = []
		while line_dex < len(templ_lines):
			line = set_lines[line_dex]
			if templ_lines[line_dex]:
				front = line[:line.find(interface_gui_str)]
				indent = front.count('\t')
				record = True
				templates.append([])
				line_dex += 1
				continue

			if record:
				rec_indent = line.count('\t')
				if not rec_indent > indent:
					record = False
					line_dex += 1
					continue

				templates[-1].append(line.strip('\t'))

			line_dex += 1

		[attributes.append(mobject_attribute(template_lines =\
			template_lines, examples = self.examples, parent = self)) 
									for template_lines in templates]
		return attributes

	def read_mobject_methods(self, text):
		methods_objs = []
		meth_str = '(lfu.modular_object_qt):'
		meth_end_str = 'def set_settables('
		method_str = 'def '
		method_reserved = '__init__'
		meth_dex = text.find(meth_str) + len(meth_str)
		meth_end_dex = text[meth_dex:].find(meth_end_str) + meth_dex
		meth_lines = text[meth_dex:meth_end_dex]
		meth_lines = meth_lines.split('\n')
		method_lines = [line.count(method_str) > 0 
							for line in meth_lines]

		line_dex = 0
		indent = None
		record = False
		methods = []
		while line_dex < len(meth_lines):
			line = meth_lines[line_dex]
			if line and line.count(method_str) > 0 and\
						line.count(method_reserved) == 0:
				front = line[:line.find(method_str)]
				indent = front.count('\t')
				record = True
				methods.append([line.replace('\t', '', 1)])
				line_dex += 1
				continue

			if record:
				rec_indent = line.count('\t')
				if not rec_indent > indent:
					methods[-1].append(line.replace('\t', '', 1))
					record = False
					line_dex += 1
					continue

				methods[-1].append(line.replace('\t', '', 1))

			line_dex += 1

		[methods_objs.append(mobject_method(method_lines = method_lines, 
							examples = self.examples, parent = self)) 
										for method_lines in methods]
		return methods_objs

	def analyze_mobject_text(self, text):
		name = self.read_mobject_name(text)
		self.mobject_analysis_name = name
		self.mobject_analysis_name_box[0].children()[1].setText(name)
		self.mobject_analysis_attr_labels = []
		self.mobject_analysis_attributes =\
			self.read_mobject_attributes(text)
		self.mobject_analysis_methods =\
			self.read_mobject_methods(text)
		self.rewidget(True)

	def make_arrangement_templates(self, *args, **kwargs):
		templates = []
		for arra in self.mobject_analysis_arrangements:
			arra.set_settables(*args, **kwargs)
			templates.extend(arra.widg_templates)

		return templates		

	def make_connectivity_templates(self, *args, **kwargs):
		window = args[0]
		templates = [
			lgm.generate_add_remove_select_inspect_box_template(
				window = window, key = 'mobject_analysis_arrangements', 
				labels = ['Add Arrangement', 'Remove Arrangement'], 
				wheres = [self.mobject_analysis_arrangements, 
						self.mobject_analysis_arrangements], 
				parent = self, 
				selector_handle = (self, 'arrangement_selector'), 
				memory_handle = (self, 'arrangement_selected_memory'), 
				base_class = mobject_template_arrangement, 
				verbosities = [10, 1])]
		arrangement_templates =\
			self.make_arrangement_templates(*args, **kwargs)
		templates.append(lgm.interface_template_gui(
				widgets = ['panel'], 
				scrollable = [True], 
				layouts = ['vertical'], 
				box_labels = ['Arrangements'], 
				templates = [arrangement_templates]))
		#can i hijack the mobj_catalog instance with arrangement templates
		#interface for defining arrangements between attribute templates
		return templates

	def make_attribute_templates(self, *args, **kwargs):
		templates = []
		for attr in self.mobject_analysis_attributes:
			attr.set_settables(*args, **kwargs)
			templates.extend(attr.widg_templates)

		return templates

	def make_method_templates(self, *args, **kwargs):
		templates = []
		for meth in self.mobject_analysis_methods:
			meth.set_settables(*args, **kwargs)
			templates.extend(meth.widg_templates)

		return templates

	def mobject_analysis_set_settables(self, *args, **kwargs):
		window = args[0]
		mobj = kwargs['mobj']
		mobj_name = self.read_mobject_name(mobj)
		prog = 'developer'
		mod = 'developer_temp_module'
		module_path = '.'.join(['libs', prog, 'lib' + mod])
		temp_module = self.examples.make_prog_module(
			program = prog, module = mod, classes = [mobj])
		lf.output_lines([temp_module], self.temp_mobj_code_path)
		__import__(module_path)
		reload(sys.modules[module_path])
		self.temp_mobj = sys.modules[module_path].__dict__[mobj_name]()
		self.temp_mobj.set_settables(window)
		self.mobject_analysis_templates = self.temp_mobj.widg_templates
		try: os.remove(self.temp_mobj_code_path)
		except: print 'could not remove', self.temp_mobj_code_path
		try: os.remove(self.temp_mobj_code_path + 'c')
		except: print 'could not remove', self.temp_mobj_code_path + 'c'

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		split_one = lgm.interface_template_gui(
				widgets = ['text'], 
				handles = [(self, 'mobject_analysis_name_box')], 
				minimum_sizes = [[(150, 75)]], 
				panel_position = (0, 0), 
				panel_scrollable = True, 
				panel_scroll_memory = (self, '_panel_scroll_memory_'), 
				instances = [[self]], 
				keys = [['mobject_analysis_name']], 
				box_labels = ['Mobject Name'])
		connectivity_templates =\
			self.make_connectivity_templates(*args, **kwargs)
		split_two = lgm.interface_template_gui(
				widgets = ['panel'], 
				panel_position = (1, 0), 
				layouts = ['vertical'], 
				box_labels = ['Template Arrangements'], 
				templates = [connectivity_templates])
		attribute_templates =\
			self.make_attribute_templates(*args, **kwargs)
		method_templates =\
			self.make_method_templates(*args, **kwargs)
		mobj_attribute_templates = [
			lgm.generate_add_remove_select_inspect_box_template(
				window = window, key = 'mobject_analysis_attributes', 
				labels = ['Add Attribute', 'Remove Attribute'], 
				wheres = [self.mobject_analysis_attributes, 
						self.mobject_analysis_attributes], 
				parent = self, 
				selector_handle = (self, 'attribute_selector'), 
				memory_handle = (self, 'attribute_selected_memory'), 
				base_class = mobject_attribute)]
		mobj_method_templates = [
			lgm.generate_add_remove_select_inspect_box_template(
				window = window, key = 'mobject_analysis_methods', 
				labels = ['Add Method', 'Remove Method'], 
				wheres = [self.mobject_analysis_methods, 
						self.mobject_analysis_methods], 
				parent = self, 
				selector_handle = (self, 'method_selector'), 
				memory_handle = (self, 'method_selected_memory'), 
				base_class = mobject_method)]
		split_three = lgm.interface_template_gui(
				widgets = ['panel', 'panel', 'panel', 'panel'], 
				widg_positions = [(1, 0), (1, 1), (0, 0), (0, 1)], 
				layout = 'grid', 
				panel_position = (2, 0), 
				layouts = ['vertical', 'vertical', None, None], 
				scrollable = [True, True, False, False], 
				templates = [attribute_templates, method_templates, 
					mobj_attribute_templates, mobj_method_templates], 
				box_labels = ['Attributes', 'Methods', 
					'Mobjects Attributes', 'Mobjects Methods'])
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['splitter'], 
				scrollable = [True], 
				orientation = ['vertical'], 
				templates = [[split_one, split_three, split_two]]))
		lfu.modular_object_qt.set_settables(
			self, *args, from_sub = True)

class mobject_proxy(lfu.modular_object_qt):

	def __init__(self, *args, **kwargs):
		self.impose_default('examples', 
			code_examples(parent = self), **kwargs)
		self.impose_default('class_lines', [], **kwargs)
		self.impose_default('applied', False, **kwargs)

		self.impose_default('mobject_name', '', **kwargs)
		self.impose_default('mobject_attributes', [], **kwargs)
		self.impose_default('mobject_attr_labels', [], **kwargs)
		self.impose_default('mobject_methods', [], **kwargs)
		self.impose_default('mobject_arrangements', [], **kwargs)

		lfu.modular_object_qt.__init__(self, *args, **kwargs)
		self.analyze_mobject_text(''.join(self.class_lines))

	def read_mobject_name(self, text, 
			super_ = '(lfu.modular_object_qt)'):
		class_dex = text.find('class ') + len('class ')
		class_name_end_dex = text[class_dex:].find(super_) + class_dex
		name = text[class_dex:class_name_end_dex]
		return name

	def read_mobject_attributes(self, text):
		attributes = []
		print 'proxy read_mobject_attributes call?'
		return attributes
		set_set_str = 'def set_settables(self, *args, **kwargs):'
		set_set_end_str = 'lfu.modular_object_qt.set_settables('
		interface_gui_str = 'lgm.interface_template_gui('
		set_set_dex = text.find(set_set_str) + len(set_set_str)
		set_set_end_dex = text[set_set_dex:].find(
					set_set_end_str) + set_set_dex
		set_lines = text[set_set_dex:set_set_end_dex]
		set_lines = set_lines.split('\n')
		templ_lines = [line.count(interface_gui_str) > 0 
								for line in set_lines]

		line_dex = 0
		indent = None
		record = False
		templates = []
		while line_dex < len(templ_lines):
			line = set_lines[line_dex]
			if templ_lines[line_dex]:
				front = line[:line.find(interface_gui_str)]
				indent = front.count('\t')
				record = True
				templates.append([])
				line_dex += 1
				continue

			if record:
				rec_indent = line.count('\t')
				if not rec_indent > indent:
					record = False
					line_dex += 1
					continue

				templates[-1].append(line.strip('\t'))

			line_dex += 1

		[attributes.append(mobject_attribute(template_lines =\
			template_lines, examples = self.examples, parent = self)) 
									for template_lines in templates]
		return attributes

	def read_mobject_methods(self, text):
		methods_objs = []
		print 'proxy read_mobject_methods call?'
		return method_objs
		meth_str = '(lfu.modular_object_qt):'
		meth_end_str = 'def set_settables('
		method_str = 'def '
		method_reserved = '__init__'
		meth_dex = text.find(meth_str) + len(meth_str)
		meth_end_dex = text[meth_dex:].find(meth_end_str) + meth_dex
		meth_lines = text[meth_dex:meth_end_dex]
		meth_lines = meth_lines.split('\n')
		method_lines = [line.count(method_str) > 0 
							for line in meth_lines]

		line_dex = 0
		indent = None
		record = False
		methods = []
		while line_dex < len(meth_lines):
			line = meth_lines[line_dex]
			if line and line.count(method_str) > 0 and\
						line.count(method_reserved) == 0:
				front = line[:line.find(method_str)]
				indent = front.count('\t')
				record = True
				methods.append([line.replace('\t', '', 1)])
				line_dex += 1
				continue

			if record:
				rec_indent = line.count('\t')
				if not rec_indent > indent:
					methods[-1].append(line.replace('\t', '', 1))
					record = False
					line_dex += 1
					continue

				methods[-1].append(line.replace('\t', '', 1))

			line_dex += 1

		[methods_objs.append(mobject_method(method_lines = method_lines, 
							examples = self.examples, parent = self)) 
										for method_lines in methods]
		return methods_objs

	def analyze_mobject_text(self, text):
		self.mobject_name = self.read_mobject_name(text, super_ = '(')
		#self.mobject_name_box[0].children()[1].setText(name)
		#self.mobject_attr_labels = []
		#self.mobject_attributes = self.read_mobject_attributes(text)
		#self.mobject_methods = self.read_mobject_methods(text)
		self.rewidget(True)

	def set_settables(self, *args, **kwargs):
		window = args[0]
		#self.analyze_mobject_text()
		self.handle_widget_inheritance(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['check_set'], 
				append_instead = [False], 
				instances = [[self]], 
				keys = [['applied']], 
				labels = [['Mobject Applied']], 
				box_labels = [self.mobject_name]))
		lfu.modular_object_qt.set_settables(
			self, *args, from_sub = True)

class modular_developer(lfu.modular_object_qt):

	def __init__(self, *args, **kwargs):
		self.mason = lgm.standard_mason()
		self.examples = code_examples(parent = self)
		self.mobject_hierarchy = mobject_analyzer(
			parent = self, examples = self.examples)
		self.program_module_name = ''
		self.relevant_program = 'modular_core'
		self.relevant_program_module = None
		self.selected_program = 'modular_core'
		self.simulation_module_name = ''
		self.program_name = ''
		self.program_extension = ''
		self.current_text_prog_mod = ''
		self.current_text_sim_mod = ''
		self.current_text_mobj = ''
		self.current_text_prog = ''
		self.current_text_prog_baseclass = ''
		self.program_run_option = ''
		self.program_description = ''
		self.prog_mod_mobject_selected = None
		self.prog_mod_mobject_text = ''
		self.current_tab_index = 0
		self.prog_mobject_selected_memory = None
		self.settings_manager = lset.settings_manager(
			parent = self, filename = 'developer_settings.txt')
		self.settings = self.settings_manager.read_settings()
		lfu.modular_object_qt.__init__(self, *args, **kwargs)
		self._children_ = [self.mobject_hierarchy]

	def change_settings(self):
		self.settings_manager.display()

	def run_modular_object(self, window):
		self.mobject_hierarchy.mobject_analysis_set_settables(
						window, mobj = self.current_text_mobj)
		templates = self.mobject_hierarchy.mobject_analysis_templates
		attr_panel = lgm.interface_template_gui(
						widgets = ['panel'], 
						box_labels = ['Mobjects Interface'], 
						templates = [templates])
		methods = self.mobject_hierarchy.mobject_analysis_methods
		helpers = [meth.generate_template() for meth in methods]
		helper_panel = lgm.interface_template_gui(
						widgets = ['panel'], 
						layouts = ['vertical'], 
						box_labels = ['Additional Test Controls'], 
						templates = [helpers])
		splitter = lgm.interface_template_gui(
					widgets = ['splitter'], 
					orientations = [['horizontal']], 
					templates = [[attr_panel, helper_panel]])
		self.mobject_analysis_panel = lgb.create_scroll_area(
					lgb.create_panel([splitter], self.mason))
		panel_x = self.mobject_analysis_panel.sizeHint().width()*1.5
		panel_y = self.mobject_analysis_panel.sizeHint().height()*1.25
		panel_x, panel_y = min([panel_x, 1600]), min([panel_y, 900])
		self.mobject_analysis_panel.setGeometry(
					150, 120, panel_x, panel_y)
		self.mobject_analysis_panel.show()

	def new_modular_object(self, name = '_new_mobject_', 
			attributes = [], methods = [], imposed = False):
		if self.mobject_hierarchy.mobject_analysis_name and not imposed:
			name = self.mobject_hierarchy.mobject_analysis_name

		attrs = self.mobject_hierarchy.mobject_analysis_attributes
		if attrs and not imposed:
			attributes = attrs

		meths = self.mobject_hierarchy.mobject_analysis_methods
		if meths and not imposed:
			methods = meths

		self.current_text_mobj = self.examples.make_mobject(
			name = name, attributes = attributes, methods = methods)
		self.mobj_text_box[0].setText(self.current_text_mobj)
		self.mobject_hierarchy.analyze_mobject_text(
							self.current_text_mobj)
		self.rewidget(True)

	def analyze_modular_object(self):
		self.mobject_hierarchy.analyze_mobject_text(
							self.current_text_mobj)

	def impose_modular_object_from_analyzer(self, 
			name = '_new_mobject_', attrs = [], methods = []):
		if self.mobject_hierarchy.mobject_analysis_name:
			name = self.mobject_hierarchy.mobject_analysis_name

		if self.mobject_hierarchy.mobject_analysis_attributes:
			attrs = self.mobject_hierarchy.mobject_analysis_attributes

		if self.mobject_hierarchy.mobject_analysis_methods:
			methods = self.mobject_hierarchy.mobject_analysis_methods

		self.new_modular_object(name = name, attributes = attrs, 
							methods = methods, imposed = True)

	def add_mobject_to_module(self, module_text, mobject_text):
		def trim(text): return text[:-2]
		while module_text.endswith('\n') or module_text.endswith('\t'):
			module_text = trim(module_text)

		module_text += '\n\n' + mobject_text
		return module_text

	def read_module_name_from_text(self, text):
		name_dex = text.find('__name__ ==')
		name_end_dex = text[name_dex:].find(':')
		name_in = text[name_dex:name_dex + name_end_dex]
		name = name_in[name_in.rfind('lib') + 3:-1]
		return name

	def new_program_module(self, program = 'modular_core', 
				module = '_new_module_', make_file = False):
		if self.program_module_name: module = self.program_module_name
		if self.relevant_program: program = self.relevant_program
		else: print 'defaulting to modular_core'
		self.current_text_prog_mod = self.examples.make_prog_module(
								program = program, module = module)
		self.mobject_hierarchy.analyze(self.current_text_prog_mod)
		self.prog_mod_text_box[0].setText(self.current_text_prog_mod)
		if make_file:
			self.output_program_module(
				program = program, module = module)

	def output_program_module(self, program = 'modular_core', 
				module = '_new_module_', module_text = None):
		if not module_text:
			if self.program_module_name: module = self.program_module_name
			if self.relevant_program: program = self.relevant_program
			else: print 'defaulting to modular_core'

		module_filename = ''.join(['lib', module, '.py'])
		module_path = os.path.join(os.getcwd(), 
			'libs', program, module_filename)
		if module_text: out_text = module_text
		else: module_text = self.current_text_prog_mod
		if lf.output_lines([module_text], 
				module_path, overwrite = True):
			print 'generated new module:', module_filename

	def load_program_module(self):
		mod = self.relevant_program_module
		dexes = [mod in item[1] for item in 
			self.relevant_program_modules]
		pas = [item[0] for item in self.relevant_program_modules]
		if dexes.count(True) == 1:
			path = os.path.join(pas[dexes.index(True)], 
								'lib' + mod + '.py')

		else:
			print 'module name conflict'
			pdb.set_trace()

		with open(path, 'r') as handle: lines = handle.readlines()
		text = ''.join(lines)
		self.current_text_prog_mod = text
		if not self.mobject_hierarchy.mobject_subclasses:
			self.mobject_hierarchy.analyze(self.current_text_prog_mod)

		self.prog_mod_text_box[0].setText(self.current_text_prog_mod)
		self.prog_mod_name_box[0].children()[1].setText(
				self.read_module_name_from_text(text))

	def make_proxy_templates(self, *args, **kwargs):
		templates = []
		for proxy in self.mobject_hierarchy.mobject_subclasses:
			proxy.set_settables(*args, **kwargs)
			templates.extend(proxy.widg_templates)

		return templates

	def new_simulation_module(self, 
			module = '_new_simulation_module_', make_file = False):
		if self.simulation_module_name:
			module = self.simulation_module_name

		self.current_text_sim_mod =\
			self.examples.make_sim_module(module = module)
		self.sim_mod_text_box[0].setText(self.current_text_sim_mod)
		if make_file: self.output_simulation_module(module = module)

	def output_simulation_module(self, 
			module = '_new_simulation_module_'):
		if self.simulation_module_name:
			module = self.simulation_module_name

		module_filename = ''.join(['lib', module, '.py'])
		module_path = os.path.join(os.getcwd(), 
			'libs', 'modules', module_filename)
		if lf.output_lines([self.current_text_sim_mod], 
						module_path, overwrite = False):
			print 'generated new module:', module_filename

	def new_program(self, program_name = '_new_program_', 
				new_base_class = True, make_file = False):
		if self.program_name: program_name = self.program_name
		if new_base_class:
			self.new_base_class_module_text =\
				self.examples.make_prog_module(
					program = program_name, 
					module = program_name)
			#inits should contain lines for added setting manager instance!
			inits = [
				'\n\t\tself.settings_manager = lset.settings_manager(\n', 
				'\t\t\tparent = self, filename = "<program_name>_settings.txt")\n'
				'\t\tself.settings = self.settings_manager.read_settings()\n']
			self.new_base_class_module_text =\
				self.add_mobject_to_module(
				self.new_base_class_module_text, 
				self.examples.make_mobject(
						name = program_name, 
							inits = inits))
			self.current_text_prog_baseclass =\
				self.new_base_class_module_text
			self.prog_baseclass_text_box[0].children()[1].setText(
								self.current_text_prog_baseclass)
			base_class = program_name
			base_class_module = program_name

		self.current_text_prog = self.examples.make_program(
			base_class, base_class_module, program = base_class)
		self.prog_text_box[0].children()[1].setText(self.current_text_prog)
		if make_file: self.output_program()

	def output_program(self, program_name = '_new_program_', 
				program_run_option = 'newprog', 
				program_description = 'run _new_program_'):
		if self.program_name: program_name = self.program_name
		if self.program_run_option:
			program_run_option = self.program_run_option

		if self.program_description:
			program_description = self.program_description

		program_path = os.path.join(os.getcwd(), 'libs', 
			'gui', 'libqtgui_' + program_name + '.py')
		if lf.output_lines([self.current_text_prog], 
					program_path, overwrite = False):
			program_directory = os.path.join(
				os.getcwd(), 'libs', program_name)
			if not os.path.exists(program_directory):
				os.makedirs(program_directory)

			init_file_path = os.path.join(os.getcwd(), 
				'libs', program_name, '__init__.py')
			lf.output_lines([self.examples.make__init_()], 
						init_file_path, overwrite = False)

			new_base_module_class_name =\
				self.read_module_name_from_text(
					self.new_base_class_module_text)
			self.output_program_module(program = program_name, 
				module = new_base_module_class_name, 
				module_text = self.new_base_class_module_text)

			if self.program_run_option:
				program_run_option = self.program_run_option

			if self.program_description:
				program_description = self.program_description

			lfu.add_program_to_registry(program_name, 
				program_run_option, program_description)
			print 'generated program:', program_name

	def remove_program(self):
		if self.selected_program == 'modular_core':
			print 'cannot remove modular_core!'
			return

		prog_guilib_filename = 'libqtgui_' + self.selected_program
		prog_guilib = 'libs.gui.' + prog_guilib_filename
		guilib = importlib.import_module(prog_guilib)
		try: lock = guilib._application_locked_
		except AttributeError:
			print 'program lock state is ambiguous; will not remove!'
			return

		if lock: print 'program is locked; will not remove!'
		else:
			guilib_path = os.path.join(os.getcwd(), 
				'libs', 'gui', prog_guilib_filename + '.py')
			try: os.remove(guilib_path)
			except: print prog_guilib, 'is already missing...'
			try: os.remove(guilib_path + 'c')
			except: print prog_guilib + 'c', 'is already missing...'
			program_lib_path = os.path.join(os.getcwd(), 
						'libs', self.selected_program)
			for fi in os.listdir(program_lib_path):
				try: os.remove(os.path.join(program_lib_path, fi))
				except: print fi, 'is already missing...'

			os.removedirs(program_lib_path)
			lfu.remove_program_from_registry(self.selected_program)
			print 'removed program:', self.selected_program
			self.selected_program = 'modular_core'
			self.rewidget(True)

	def make_tab_book_pages(self, *args, **kwargs):
		window = args[0]
		programs = ['modular_core'] + lfu.get_modular_program_list()
		self.relevant_program_modules =\
			lfu.list_program_modules(self.relevant_program)
		relevant_program_modules = lfu.flatten([item[1] for item 
							in self.relevant_program_modules])
		if not self.relevant_program_module or\
				not self.relevant_program_module\
					in relevant_program_modules:
			try:
				self.relevant_program_module =\
					relevant_program_modules[0]

			except IndexError: pass

		programs_templates = []
		prog_modules_templates = []
		sim_modules_templates = []
		mobjects_templates = []

		programs_templates_top = [lgm.interface_template_gui(
				widgets = ['button_set', 'text', 
						'text', 'text', 'radio'], 
				layout = 'grid', 
				widg_positions = [(0, 0), (1, 0), (2, 0), 
						(0, 2), (1, 2), (2, 2), (0, 1)], 
				widg_spans = [None, None, None, 
					None, None, None, (3, 1)], 
				instances = [None, [self], [self], [self], [self]], 
				keys = [None, ['program_name'], ['program_run_option'], 
						['program_description'], ['selected_program']], 
				labels = [['Write Program', 'Generate Program', 
					'Remove Program'], None, None, None, programs], 
				initials = [None, [self.program_name], 
							[self.program_run_option], 
							[self.program_description], 
							[self.selected_program]], 
				bindings = [[self.new_program, self.output_program, 
					self.remove_program], None, None, None, None], 
				box_labels = [None, 'Program Name', 
							'Program Run Extension', 
							'Program Description', 'Select Program'])]
		programs_templates_bottom_inner = [lgm.interface_template_gui(
				widgets = ['text', 'text'], 
				layout = 'horizontal', 
				multiline = [True, True], 
				for_code = [True, True], 
				handles = [(self, 'prog_text_box'), 
					(self, 'prog_baseclass_text_box')], 
				initials = [[self.current_text_prog], 
					[self.current_text_prog_baseclass]], 
				alignments = [['left'], ['left']], 
				minimum_sizes = [[(786, 384)], [(786, 384)]], 
				instances = [[self], [self]], 
				keys = [['current_text_prog'], 
					['current_text_prog_baseclass']], 
				box_labels = ['GUI Entry Point', 
					'New Base Class Module'])]
		programs_templates_bottom = [lgm.interface_template_gui(
				widgets = ['panel'], 
				box_labels = ['New Program Essential Files'], 
				#scrollable = [True], 
				templates = [programs_templates_bottom_inner])]
		programs_templates.append(
			lgm.interface_template_gui(
				widgets = ['splitter'], 
				orientations = [['vertical']], 
				templates = [[programs_templates_top[0], 
						programs_templates_bottom[0]]]))

		proxy_templates = self.make_proxy_templates(*args, **kwargs)
		prog_modules_templates_top_left = [
			lgm.interface_template_gui(
				widgets = ['button_set', 'text', 'radio', 'selector'], 
				layout = 'grid', 
				layouts = ['vertical', 'vertical', 
							'vertical', 'vertical'], 
				widg_positions = [(0, 0), (0, 2), (0, 1), (1, 2)], 
				widg_spans = [None, None, (2, 1), None], 
				handles = [None, 
					(self, 'prog_mod_name_box'), None, None], 
				refresh = [None, None, [True], None], 
				window = [None, None, [window], None], 
				instances = [None, [self], [self], [self]], 
				keys = [None, ['program_module_name'], 
					['relevant_program'], ['relevant_program_module']], 
				labels = [['Write Program Module', 
					'Generate Program Module', 
					'Load Program Module'], None, programs, 
								relevant_program_modules], 
				initials = [None, [self.program_module_name], 
									[self.relevant_program], 
							[self.relevant_program_module]], 
				bindings = [[self.new_program_module, 
					self.output_program_module, 
					lgb.create_reset_widgets_wrapper(window, 
						self.load_program_module)], None, None, None], 
				box_labels = [None, 'Module Name', 
					'Relevant Program', 'Relevant Module'])]
		prog_modules_templates_bottom_left = [
			lgm.interface_template_gui(
				widgets = ['text'], 
				multiline = [True], 
				for_code = [True], 
				handles = [(self, 'prog_mod_text_box')], 
				initials = [[self.current_text_prog_mod]], 
				alignments = [['left']], 
				minimum_sizes = [[(786, 256)]], 
				instances = [[self]], 
				keys = [['current_text_prog_mod']])]
		prog_modules_templates_top_right = [
			lgm.interface_template_gui(
				widgets = ['button_set', 'selector', 'text'], 
				box_labels = [None, None, 'Selected Mobject'], 
				labels = [['Catalog All Mobjects', 'Run Mobject'], 
					[proxy.mobject_name for proxy in self.\
						mobject_hierarchy.mobject_subclasses], None], 
					#self.mobject_hierarchy.mobject_names, None], 
				multiline = [None, None, True], 
				read_only = [None, None, True], 
				bindings = [[lgb.create_reset_widgets_wrapper(window, 
									self.mobject_hierarchy.analyze)], 
						#self.mobject_hierarchy.analyze, func_args =\
						#		(self.prog_mod_mobject_text, ))], 
										None, None], 
				instances = [None, [self], [self]], 
				keys = [None, ['prog_mod_mobject_selected'], 
								['prog_mod_mobject_text']], 
				initials = [None, [self.prog_mod_mobject_selected], 
								[self.prog_mod_mobject_text]], 
				handles = [None, None, 
					(self, 'prog_mod_mobject_box')])]
		prog_modules_templates_bottom_right = [
			lgm.generate_add_remove_select_inspect_box_template(
				window = window, key = 'prog_module_mobject_proxies', 
				labels = ['Add Mobject', 'Remove Mobject'], 
				wheres = [self.mobject_hierarchy.mobject_subclasses, 
						self.mobject_hierarchy.mobject_subclasses], 
				parent = self, 
				selector_handle = (self, 'prog_mobject_proxy_selector'), 
				memory_handle = (self, 'prog_mobject_selected_memory'), 
				base_class = mobject_proxy, 
				verbosities = [10, 1]), 
			lgm.interface_template_gui(
				widgets = ['panel'], 
				layouts = ['vertical'], 
				scrollable = [True], 
				templates = [proxy_templates], 
				box_labels = ['Mobject Proxies'])]
		prog_modules_templates_left = [
			lgm.interface_template_gui(
				widgets = ['splitter'], 
				orientations = [['vertical']], 
				templates = [[prog_modules_templates_top_left[0], 
						prog_modules_templates_bottom_left[0]]])]
		prog_modules_templates_right = [
			lgm.interface_template_gui(
				widgets = ['splitter'], 
				orientations = [['vertical']], 
				templates = [[prog_modules_templates_top_right[0]]+\
							prog_modules_templates_bottom_right])]
		prog_modules_templates.append(
			lgm.interface_template_gui(
				widgets = ['splitter'], 
				orientations = [['horizontal']], 
				templates = [[prog_modules_templates_left[0], 
							prog_modules_templates_right[0]]]))

		sim_modules_templates_top = [lgm.interface_template_gui(
				widgets = ['button_set', 'text'], 
				instances = [None, [self]], 
				keys = [None, ['simulation_module_name']], 
				labels = [['Write Simulation Module', 
					'Generate Simulation Module'], None], 
				bindings = [[self.new_simulation_module, 
					self.output_simulation_module], None], 
				box_labels = [None, 'Module Name'])]
		sim_modules_templates_bottom = [lgm.interface_template_gui(
				widgets = ['text'], 
				multiline = [True], 
				for_code = [True], 
				handles = [(self, 'sim_mod_text_box')], 
				initials = [[self.current_text_sim_mod]], 
				alignments = [['left']], 
				minimum_sizes = [[(786, 256)]], 
				instances = [[self]], 
				keys = [['current_text_sim_mod']])]
		sim_modules_templates.append(
			lgm.interface_template_gui(
				widgets = ['splitter'], 
				orientations = [['vertical']], 
				templates = [[sim_modules_templates_top[0], 
						sim_modules_templates_bottom[0]]]))

		mobjects_templates_top = [lgm.interface_template_gui(
				widgets = ['button_set'], 
				layout = 'horizontal', 
				labels = [['Write Mobject', 
					'Analyze Mobject', 'Run Mobject']], 
				bindings = [[lgb.create_reset_widgets_wrapper(window, 
							self.impose_modular_object_from_analyzer), 
							lgb.create_reset_widgets_wrapper(window, 
									self.analyze_modular_object), 
							lgb.create_function_with_args(
								self.run_modular_object, 
								func_args = (window, ))]])]
		mobjects_templates_bottom = [
			lgm.interface_template_gui(
				widgets = ['text'], 
				layout = 'horizontal', 
				multiline = [True], 
				for_code = [True], 
				handles = [(self, 'mobj_text_box')], 
				initials = [[self.current_text_mobj]], 
				alignments = [['left']], 
				minimum_sizes = [[(786, 256)]], 
				instances = [[self]], 
				keys = [['current_text_mobj']]), 
			lgm.interface_template_gui(
				widgets = ['panel'], 
				layout = 'horizontal', 
				templates = [self.mobject_hierarchy.widg_templates], 
				box_labels = ['Mobject Analyzer'])]
		bottom_splitter = lgm.interface_template_gui(
							widgets = ['splitter'], 
							orientations = ['horizontal'], 
							templates = [mobjects_templates_bottom])
		mobjects_templates.append(
			lgm.interface_template_gui(
				widgets = ['splitter'], 
				orientations = [['vertical']], 
				templates = [[mobjects_templates_top[0], 
									bottom_splitter]]))

		pages = [('Create/Edit Program Modules', prog_modules_templates), 
				('Create/Edit Simulation Modules', sim_modules_templates), 
				('Create/Edit Modular Objects', mobjects_templates), 
				('Create/Edit Programs', programs_templates)]
		return pages

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		wrench_icon_path = os.path.join(
			os.getcwd(), 'resources', 'wrench_icon.png')
		refresh_icon_path = os.path.join(
			os.getcwd(), 'resources', 'refresh.png')
		center_icon_path = os.path.join(
			os.getcwd(), 'resources', 'center.png')
		wrench_icon = lgb.create_icon(wrench_icon_path)
		refresh_icon = lgb.create_icon(refresh_icon_path)
		center_icon = lgb.create_icon(center_icon_path)
		settings_ = lgb.create_action(parent = window, label = 'Settings', 
					bindings = lgb.create_reset_widgets_wrapper(
					window, self.change_settings), icon = wrench_icon, 
					shortcut = 'Ctrl+Shift+S', statustip = 'Settings')
		self.refresh_ = lgb.create_reset_widgets_function(window)
		update_gui_ = lgb.create_action(parent = window, 
			label = 'Refresh GUI', icon = refresh_icon, 
			shortcut = 'Ctrl+G', bindings = self.refresh_, 
			statustip = 'Refresh the GUI (Ctrl+G)')
		center_ = lgb.create_action(parent = window, label = 'Center', 
							icon = center_icon, shortcut = 'Ctrl+C', 
									statustip = 'Center Window', 
									bindings = [window.on_resize, 
												window.on_center])

		self.menu_templates.append(
			lgm.interface_template_gui(
				menu_labels = ['&File', '&File', '&File'], 
				menu_actions = [settings_, center_, update_gui_]))
		self.tool_templates.append(
			lgm.interface_template_gui(
				tool_labels = ['&Tools', '&Tools', '&Tools'], 
				tool_actions = [settings_, center_, update_gui_]))

		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['tab_book'], 
				verbosities = [0], 
				pages = [self.make_tab_book_pages(*args, **kwargs)], 
				initials = [[self.current_tab_index]], 
				handles = [(self, 'tab_ref')], 
				instances = [[self]], 
				keys = [['current_tab_index']]))
		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)







