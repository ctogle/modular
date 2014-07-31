#!python
import modular_core.libfundamental as lfu
lfu.USING_GUI = True
import modular_core.liboutput as lo
import modular_core.libsettings as lset
import modular_core.gui.libqtgui as lqg
lgm = lqg.lgm
lgd = lqg.lgd
lgb = lqg.lgb
import modular_core.libfiler as lf

import os, sys

import pdb

class pkl_handler(lfu.modular_object_qt):
	def __init__(self, *args, **kwargs):
		self.settings_manager = lset.settings_manager(
			parent = self, filename = 'plot_pkls_settings.txt')
		self.settings = self.settings_manager.read_settings()
		self.impose_default('capture_targets', [], **kwargs)
		self.impose_default('pkl_files_directory', os.getcwd(), **kwargs)
		#self.impose_default('output', lo.output_plan(
		#	label = 'pkl handler output', parent = self), **kwargs)
		lfu.modular_object_qt.__init__(self, *args, **kwargs)

	def load_data(self):
		self.provide_axes_manager_input()
		pkl_files = [p for p in os.listdir(
			self.pkl_files_directory) if p.endswith('.pkl')]
		fronts = lfu.uniqfy([p[:p.find('.')] for p in pkl_files])
		outputs = []
		data_ = []
		for outp in fronts:
			outputs.append(lo.output_plan(
				label = outp, parent = self))
			data_.append([])
			self.capture_targets = []
			relev = [p for p in pkl_files if p.startswith(outp)]
			for fi in relev:
				fipath = os.path.join(self.pkl_files_directory, fi)
				dat = lf.load_pkl_object(fipath)
				data_[-1].append(dat.data)
				self.capture_targets.extend([d.label for d in dat.data])
			targs = lfu.uniqfy(self.capture_targets)
			outputs[-1].targeted = targs
			self.capture_targets = targs
			outputs[-1].set_target_settables()
			outputs[-1].flat_data = False

		[outp(lfu.data_container(data = da)) for 
				outp, da in zip(outputs, data_)]

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['directory_name_box'], 
				layout = 'horizontal', 
				keys = [['pkl_files_directory']], 
				instances = [[self]], 
				initials = [[self.pkl_files_directory, 
								None, os.getcwd()]], 
				labels = [['Choose Directory With .pkl Data']], 
				box_labels = ['Data Directory']))
		#self.widg_templates.append(
		self.widg_templates[-1] +=\
			lgm.interface_template_gui(
				widgets = ['button_set'], 
				bindings = [[self.load_data]], 
				labels = [['Load .pkl Data']])
		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)

class pkl_plotter(lqg.application):
	gear_icon = lfu.get_resource_path('gear.png')
	_content_ = [pkl_handler()]

	def __init__(self, *args, **kwargs):
		lqg.application.__init__(self, *args, **kwargs)
		x, y = lfu.convert_pixel_space(784, 256)
		x_size, y_size = lfu.convert_pixel_space(512, 512)
		self._standards_ = {
			'title' : 'Pkl Plotter', 
			'geometry' : (x, y, x_size, y_size), 
			'window_icon' : self.gear_icon}
		lqg._window_.apply_standards(self._standards_)
		lqg.application.setStyle(lgb.create_style('plastique'))

if __name__ == '__main__':
	params = {}
	params['application'] = pkl_plotter
	lfu.initialize_gui(params)










