import libs.modular_core.libfundamental as lfu

import types
import os

import pdb

settings = {}

if __name__ == 'libs.modular_core.libsettings':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'

class settings_manager(lfu.modular_object_qt):

	def __init__(self, *args, **kwargs):
		self.cfg_path = os.path.join(os.getcwd(), 'resources')
		self.true_strings = ['true', 'True', 'On', 'on']
		self.false_strings = ['false', 'False', 'Off', 'off']
		self.settings = {}
		self.settings_types = {}
		self.mason = lgm.standard_mason()
		if 'filename' in kwargs.keys():
			self.filename = kwargs['filename']

		else: self.filename = None
		lfu.modular_object_qt.__init__(self, *args, **kwargs)

	def write_settings(self, filename = 'settings.txt'):
		if self.filename: filename = self.filename
		settings_path = os.path.join(self.cfg_path, filename)
		lines = ['']
		for key in self.settings.keys():
			lines.append('')
			lines.append('<' + key + '>')
			for sub_key in self.settings[key].keys():
				lines.append(' = '.join([sub_key, str(
						self.settings[key][sub_key])]))

		with open(settings_path, 'w') as handle:
			handle.writelines([line + '\n' for line in lines])

	def read_settings(self, filename = 'settings.txt'):
		if self.filename: filename = self.filename
		settings_path = os.path.join(self.cfg_path, filename)
		try:
			with open(settings_path, 'r') as handle:
				lines = handle.readlines()

		except IOError:
			print 'count not find settings file!', settings_path
			return

		parser = ''
		key_lines = [line.strip() for line in lines if 
					line.strip().startswith('<') and 
						line.strip().endswith('>')]
		for line in lines:
			if line.startswith('#') == True or line.strip() == '':
				continue

			#elif line.startswith('<defaults>'):
			elif line.strip() in key_lines:
				#parser = 'defaults'
				parser = line.strip()[1:-1]
				if not parser in self.settings.keys():
					self.settings[parser] = {}
					self.settings_types[parser] = {}

				continue

			else:
				eq_dex = line.find('=')
				value = line[eq_dex + 1:].strip()
				key = line[:eq_dex].strip()
				#if the value is some variant of 'true'
				if value in self.true_strings:
					self.settings[parser][key] = True
					self.settings_types[parser][key] = bool

				#elif the value is some variant of 'false'
				elif value in self.false_strings:
					self.settings[parser][key] = False
					self.settings_types[parser][key] = bool

				else:
					try:
						#if int cast is equivalent to float cast, int
						if int(value) == float(value):
							self.settings[parser][key] = int(value)
							self.settings_types[parser][key] = int

						#else float cast is assumed equivalent
						else:
							self.settings[parser][key] = float(value)
							self.settings_types[parser][key] = float

					#if not boolean, int, or float, assumed string
					except ValueError:
						self.settings[parser][key] = value
						self.settings_types[parser][key] = str

		global settings
		settings = self.settings
		return self.settings

	def revert_settings(self):
		self.read_settings()
		self.display()

	def display(self):
		self.set_settables()
		self.panel = lgb.create_scroll_area(
			lgb.create_panel(self.widg_templates, self.mason))
		self.panel.setGeometry(150, 120, 384, 512)
		self.panel.show()

	def generate_bool_widget_template(self, key, sub_key):
		template = lgm.interface_template_gui(
					widgets = ['check_set'], 
					verbosities = [0], 
					#tooltips = [['Enable multiprocessing by default']], 
					instances = [[self.settings[key]]], 
					append_instead = [False], 
					keys = [[sub_key]], 
					labels = [[sub_key]])
		return template

	def generate_int_widget_template(self, key, sub_key):
		template = lgm.interface_template_gui(
					widgets = ['spin'], 
					verbosities = [0], 
					instances = [[self.settings[key]]], 
					keys = [[sub_key]], 
					initials = [[self.settings[key][sub_key]]], 
					box_labels = [sub_key])
		return template

	def generate_string_widget_template(self, key, sub_key):
		print 'untested string setting thing!!'
		template = lgm.interface_template_gui(
					widgets = ['text'], 
					verbosities = [0], 
					instances = [[self.settings[key]]], 
					keys = [[sub_key]], 
					initials = [[self.settings[key][sub_key]]], 
					box_labels = [sub_key])
		return template

	def set_settables(self, *args, **kwargs):
		self.handle_widget_inheritance(*args, **kwargs)
		sub_panel_templates = []
		for key in self.settings.keys():
			sub_panel_templates.append((key, []))
			for sub_key in self.settings[key].keys():
				setting_type = self.settings_types[key][sub_key]
				if setting_type is types.BooleanType:
					sub_panel_templates[-1][1].append(
						self.generate_bool_widget_template(
											key, sub_key))

				elif setting_type is types.IntType:
					sub_panel_templates[-1][1].append(
						self.generate_int_widget_template(
											key, sub_key))

				elif setting_type is types.StringType:
					sub_panel_templates[-1][1].append(
						self.generate_string_widget_template(
												key, sub_key))

		[self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['panel'], 
				verbosities = [0], 
				templates = [sub_panel_templates[panel_dex][1]], 
				box_labels = [sub_panel_templates[panel_dex][0]], 
				panel_position = (panel_dex + 1, 0))) for 
					panel_dex in range(len(self.settings.keys()))]
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['button_set'], 
				verbosities = [0], 
				layouts = ['horizontal'], 
				bindings = [[self.write_settings, self.revert_settings]], 
				labels = [['Save Settings', 'Revert Settings']]))
		lfu.modular_object_qt.set_settables(self, *args, from_sub = True)

def get_setting(setting, fail_silent = False, 
		default_from_file = True, file_ = ''):
	for key in settings.keys():
		if setting in settings[key].keys():
			return settings[key][setting]

	if default_from_file and file_:
		man = settings_manager(filename = file_)
		man.read_settings()
		sett = get_setting(setting, fail_silent = False)
		print 'found setting', setting, ': ', sett, 'in default file', file_
		return sett

	if not fail_silent: print 'coult not find setting', setting



