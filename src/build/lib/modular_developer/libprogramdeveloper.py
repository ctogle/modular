import modular_core.libfundamental as lfu
import modular_core.libfiler as lf
import modular_developer.libcodegenerator as lcg

import os, importlib
import pdb

class program_manager(lfu.modular_object_qt):
	#	create programs
	#	add/remove program modules (from anywhere)
	def __init__(self, *args, **kwargs):
		self._program_name_ = ''
		self._program_run_option_ = ''
		self._program_description_ = ''
		self._program_gui_entry_text_ = ''
		self._program_base_class_text_ = ''
		self._program_selected_ = ''
		self._code_writer_ = lcg.code_writer()
		lfu.modular_object_qt.__init__(self, *args, **kwargs)

	def new_program(self, program_name = '_new_program_'):
		if self._program_name_:
			program_name = self._program_name_.replace(' ','_')

		# write the base libmodule for the program
		p_text = self._code_writer_.make_prog_module(
			program = program_name, module = program_name)
		p_mobj = self._code_writer_.make_mobject(
			name = program_name, setting_manager = True)
		p_text = self.parent.pmod_mngr.\
			add_mobject_to_module(p_text, p_mobj, ['lset'])
		p_text = p_text.replace('<program_name>', program_name)
		self._program_base_class_widg_[0].children()[1].setText(p_text)
		self._program_base_class_text_ = p_text

		# write the programs gui entry point
		self._program_gui_entry_text_ =\
			self._code_writer_.make_program(
				program_name, program_name, program_name)
		self._program_gui_entry_widg_[0].children()[1].setText(
								self._program_gui_entry_text_)

	def output_program(self, program_name = '_new_program_', 
				program_description = 'run _new_program_', 
						program_run_option = 'newprog'):
		if self._program_name_:
			program_name = self._program_name_.replace(' ','_')
		if self._program_run_option_:
			program_run_option = self._program_run_option_
		if self._program_description_:
			program_description = self._program_description_

		program_path = os.path.join(os.getcwd(), 'libs', 
			'gui', 'libqtgui_' + program_name + '.py')
		if lf.output_lines([self._program_gui_entry_text_], 
							program_path, overwrite = True):
			program_directory = os.path.join(
				os.getcwd(), 'libs', program_name)
			if not os.path.exists(program_directory):
				os.makedirs(program_directory)

			init_file_path = os.path.join(os.getcwd(), 
				'libs', program_name, '__init__.py')
			lf.output_lines([self._code_writer_.make__init_()], 
							init_file_path, overwrite = True)

			mod_text = self._program_base_class_text_
			base_module_class =\
				self.parent.pmod_mngr.name_from_text(mod_text)
			self.parent.pmod_mngr.output_module(mod_text, 
				program = program_name, module = base_module_class)

			prog_setting_file = os.path.join(os.getcwd(), 
				'resources', program_name + '_settings.txt')
			lf.output_lines([lcg.ex_setting_file], 
				prog_setting_file, overwrite = True)

			lfu.add_program_to_registry(program_name, 
				program_run_option, program_description)
			print 'generated program:', program_name

	def remove_program(self):
		if self._program_selected_ == 'modular_core':
			print 'cannot remove modular_core!'
			return

		prog_guilib_filename = 'libqtgui_' + self._program_selected_
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
						'libs', self._program_selected_)
			for fi in os.listdir(program_lib_path):
				try: os.remove(os.path.join(program_lib_path, fi))
				except: print fi, 'is already missing...'

			os.removedirs(program_lib_path)
			lfu.remove_program_from_registry(self._program_selected_)
			print 'removed program:', self._program_selected_
			self._program_selected_ = 'modular_core'
			self.rewidget(True)

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)

		programs = ['modular_core'] + lfu.get_modular_program_list()
		top1 = lgm.interface_template_gui(
			widgets = ['button_set'], 
			layout = 'grid', 
			widg_positions = [(0, 0), (1, 0), (2, 0)], 
			labels = [['Write Program',
				'Generate Program','Remove Program']], 
			bindings = [[self.new_program,
				self.output_program,self.remove_program]])
		top2 = lgm.interface_template_gui(
			widgets = ['text', 'text', 'text'], 
			widg_positions = [(0, 2), (1, 2), (2, 2)], 
			instances = [[self], [self], [self]], 
			keys = [['_program_name_'], 
				['_program_run_option_'], 
				['_program_description_']], 
			initials = [
				[self._program_name_], 
				[self._program_run_option_], 
				[self._program_description_]], 
			box_labels = ['Program Name', 
				'Program Run Extension', 
				'Program Description'])
		top3 = lgm.interface_template_gui(
			widgets = ['radio'], 
			widg_positions = [(0, 1)], 
			widg_spans = [(3, 1)], 
			instances = [[self]], 
			keys = [['_program_selected_']], 
			labels = [programs], 
			initials = [[self._program_selected_]], 
			box_labels = ['Select Program'])
		top = top1 + top2 + top3
		bottom_inner = [lgm.interface_template_gui(
				widgets = ['text', 'text'], 
				layout = 'horizontal', 
				multiline = [True, True], 
				for_code = [True, True], 
				handles = [
					(self, '_program_gui_entry_widg_'), 
					(self, '_program_base_class_widg_')], 
				initials = [
					[self._program_gui_entry_text_], 
					[self._program_base_class_text_]], 
				alignments = [['left'], ['left']], 
				minimum_sizes = [[(786, 384)], [(786, 384)]], 
				instances = [[self], [self]], 
				keys = [
					['_program_gui_entry_text_'], 
					['_program_base_class_text_']], 
				box_labels = ['GUI Entry Point', 
					'New Base Class Module'])]
		bottom = lgm.interface_template_gui(
				widgets = ['panel'], 
				box_labels = ['New Program Essential Files'], 
				#scrollable = [True], 
				templates = [bottom_inner])
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['splitter'], 
				orientations = [['vertical']], 
				templates = [[top, bottom]]))
		lfu.modular_object_qt.set_settables(
			self, *args, from_sub = True)

if __name__ == 'modular_developer.libprogramdeveloper':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'


