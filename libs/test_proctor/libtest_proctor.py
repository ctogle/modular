import libs.modular_core.libfundamental as lfu
import libs.modular_core.libsettings as lset

import os, imp, traceback, sys

import pdb

if __name__ == 'libs.test_proctor.libtest_proctor':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'

class test_proctor(lfu.modular_object_qt):

	def __init__(self, *args, **kwargs):
		self.settings_manager = lset.settings_manager(parent = self, 
							filename = "test_proctor_settings.txt")
		self.settings = self.settings_manager.read_settings()
		#def_test_dir = os.path.join(os.getcwd(), 
		#		'libs', 'modular_core', 'tests')
		#def_test_dir = os.path.join(os.getcwd(), 
		#		'libs', 'modules', 'chemicallite_support', 'tests')
		def_test_dir = lset.get_setting('test_directory')
		def_test_dir = os.path.join(os.getcwd(), def_test_dir)
		self.impose_default('test_dir', def_test_dir, **kwargs)
		self.impose_default('_tests_results_', {}, **kwargs)
		self.impose_default('_active_tests_', {}, **kwargs)
		self.impose_default('_tests_', {}, **kwargs)
		lfu.modular_object_qt.__init__(self, *args, **kwargs)

	def get_tests(self):
		self._tests_ = {}
		self._active_tests_ = {}
		libs = [f for f in os.listdir(self.test_dir) 
								if f.endswith('.py')]
		for lib in libs:
			if lib.startswith('__init__'): continue
			libpath = os.path.join(self.test_dir, lib)
			try:
				libmod = imp.load_source(lib[:-3], libpath)
				try:
					libtests = libmod._tests_
					for t in libtests.keys():
						test = libtests[t]
						#test_result = test()
						#print 'test', t, ':', test_result
						self._tests_[t] = test
						self._active_tests_[t] = True
				except AttributeError:
					traceback.print_exc(file = sys.stdout)
					print '\nno tests found in lib', lib
			except ImportError:
				traceback.print_exc(file = sys.stdout)
				print '\ncould not import lib', lib
		self.rewidget(True)

	def run_tests(self):
		libtests = self._tests_
		print '-'*50
		for t in libtests.keys():
			if self._active_tests_[t]:
				test, args = libtests[t]
				test_result = test(*args)
				self._tests_results_[t] = test_result
				print 'test', ':', t, ':', test_result
			else:
				self._tests_results_[t] = None
				print 'test', ':', t, 'is not active'
		print '-'*50
		self.rewidget(True)

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, from_sub = False)
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
				widgets = ['directory_name_box'], 
				keys = [['test_dir']], 
				instances = [[self]], 
				initials = [[self.test_dir, None, os.getcwd()]], 
				labels = [['Choose Directory']], 
				box_labels = ['Tests Directory']))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['button_set'], 
				bindings = [[lgb.create_reset_widgets_wrapper(
									window, self.get_tests), 
					lgb.create_reset_widgets_wrapper(
							window, self.run_tests), 
							self.change_settings]], 
				labels = [['Fetch Tests', 'Run Tests', 
								'Change Settings']]))
		t_count = len(self._tests_results_.keys())
		panel_widg_templates = []
		panel_widg_templates.append(
			lgm.interface_template_gui(
				panel_position = (0, 0), 
				widgets = ['check_set'], 
				append_instead = [False], 
				instances = [[self._active_tests_]*t_count], 
				#rewidget = [[True]], 
				inst_is_dict = [[True, self]*t_count], 
				keys = [self._active_tests_.keys()], 
				labels = [self._active_tests_.keys()], 
				box_labels = ['Active Tests']))
		panel_widg_templates.append(
			lgm.interface_template_gui(
				panel_position = (0, 1), 
				widgets = ['text']*t_count, 
				instances = [[self._tests_results_]]*t_count, 
				inst_is_dict = [[True, self]]*t_count, 
				keys = [[x] for x in self._tests_results_.keys()], 
				panel_label = 'Test Results'))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['panel'], 
				templates = [panel_widg_templates]))
		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)





