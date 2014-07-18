import libs.modular_core.libfundamental as lfu
import libs.modular_core.libfiler as lf
import libs.developer.libcodegenerator as lcg

import os
import pdb

module_dependencies = {
		'lset' : 'import libs.modular_core.libsettings as lset', 
					}

class module_manager(lfu.modular_object_qt):
	#	create modules associated with any program or modular_core
	#	add/remove modular objects
	def __init__(self, *args, **kwargs):
		self._code_writer_ = lcg.code_writer()
		lfu.modular_object_qt.__init__(self, *args, **kwargs)

	# read the name of a module from the its text
	def name_from_text(self, text):
		name_dex = text.find('__name__ ==')
		name_end_dex = text[name_dex:].find(':')
		name_in = text[name_dex:name_dex + name_end_dex]
		name = name_in[name_in.rfind('lib') + 3:-1]
		return name

	# return the modules text with the mobject added
	def add_mobject_to_module(self,module_text,mobject_text,deps = []):
		def trim(text): return text[:-2]
		while module_text.endswith('\n') or module_text.endswith('\t'):
			module_text = trim(module_text)
		module_text += '\n\n' + mobject_text
		for dep in deps:
			depline = module_dependencies[dep]
			if not module_text.count(depline):
				module_text = lfu.insert_substring(module_text, 
							depline, module_text.find('\n') +1)

		return module_text

	# generates the module file - requires module as single string
	def output_module(self, module_text, 
				program = 'modular_core', 
				module = '_new_module_'):
		module_filename = ''.join(['lib', module, '.py'])
		module_path = os.path.join(os.getcwd(), 
			'libs', program, module_filename)
		if lf.output_lines([module_text],module_path,overwrite = True):
			print 'generated new module:', module_filename
		else: print 'failed to generate module:', module_filename

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)


		'''
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
		'''


		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)

class simulation_module_manager(module_manager):
	#	create simulation modules for Modular Simulator
	#	there are many options for this - encapsulate
	def __init__(self, *args, **kwargs):
		self.impose_default('_module_text_', '', **kwargs)
		self.impose_default('_module_name_', '', **kwargs)
		self.impose_default('_module_motif_', '', **kwargs)
		module_manager.__init__(self, *args, **kwargs)

	def new_module(self, 
			module = '_new_simulation_module_', motif = 'cython'):
		if self._module_name_: module = self._module_name_
		if self._module_motif_: motif = self._module_motif_
		s_text = self._code_writer_.make_sim_module(module, motif)
		self._module_text_ = s_text
		self._module_text_widg_[0].setText(self._module_text_)
		print 'wrote new simulation module'

	def output_module(self):
		if self._module_name_: module = self._module_name_
		module_filename = ''.join(['lib', module, '.py'])
		module_path = os.path.join(os.getcwd(), 
			'libs', 'modules', module_filename)
		if lf.output_lines([self._module_text_], 
				module_path, overwrite = False):
			print 'generated new simulation module:', module_filename

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		button_template = lgm.interface_template_gui(
			widgets = ['button_set'], 
			labels = [['Write Simulation Module', 
					'Generate Simulation Module']], 
			bindings = [[self.new_module, 
					self.output_module]])
		text_template = lgm.interface_template_gui(
			widgets = ['text'], 
			instances = [[self]], 
			keys = [['_module_name_']], 
			box_labels = ['Module Name'])
		top_template = button_template + text_template
		bottom_template = lgm.interface_template_gui(
			widgets = ['text'], 
			multiline = [True], 
			for_code = [True], 
			handles = [(self, '_module_text_widg_')], 
			initials = [[self._module_text_]], 
			alignments = [['left']], 
			minimum_sizes = [[(786, 256)]], 
			instances = [[self]], 
			keys = [['_module_text_']])
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['splitter'], 
				orientations = [['vertical']], 
				templates = [[top_template, bottom_template]]))
		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)

if __name__ == 'libs.developer.libmoduledeveloper':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'


