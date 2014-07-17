import libs.modular_core.libfundamental as lfu
import libs.modular_core.libgeometry as lgeo
import libs.modular_core.libsettings as lset
import libs.modular_core.libfiler as lf

import numpy as np
import os
import matplotlib.pyplot as plt

import pdb



if __name__ == 'libs.imager.libimager':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'

class imager(lfu.modular_object_qt):

	def __init__(self, *args, **kwargs):
		self.impose_default('input_path', '', **kwargs)
		self.impose_default('input_dir', os.getcwd(), **kwargs)

		self.impose_default('domain', [], **kwargs)
		self.impose_default('codomains', [], **kwargs)
		self.impose_default('domain_data', [], **kwargs)
		self.impose_default('codomain_datas', [], **kwargs)

		self.impose_default('data', None, **kwargs)
		self.impose_default('out_filename', os.path.join(os.getcwd(), 
								'imager', 'fit_data.pkl'), **kwargs)

		self.settings_manager = lset.settings_manager(
			parent = self, filename = 'imager_settings.txt')
		self.settings = self.settings_manager.read_settings()
		lfu.modular_object_qt.__init__(self, *args, **kwargs)

	def on_write_data(self, *args, **kwargs):
		if not self.domain:
			self.domain = ['x']
			self.codomains = ['y1', 'y2', 'y3']
			self.domain_data = np.linspace(0, 10, 100)
			self.codomain_datas = [
				np.exp(self.domain_data)/np.exp(self.domain_data[-1]), 
				np.sin(self.domain_data), np.cos(2*self.domain_data)]
			print 'USED FAKE TEST DATA!!'

		#the data should be normalized -1, 1 on both axes
		x = self.domain_data
		ys = self.codomain_datas
		[plt.plot(x, y) for y in ys]
		plt.show()
		self.out_data = lfu.data_container(
			data = [lgeo.scalars(label = lab, scalars = dat) for
					lab, dat in zip(self.domain + self.codomains, 
					[self.domain_data] + self.codomain_datas)])
		lf.save_pkl_object(self.out_data, self.out_filename)

	def examine(self, *args, **kwargs):
		pdb.set_trace()

	def verify_parse_result(self, x_lab, y_labs, x, ys):
		self.domain = x_lab
		self.codomains = y_labs
		self.domain_data = np.array(x, dtype = float)
		self.codomain_datas = [np.array(y, dtype = float) for y in ys]
		print 'found', len(y_labs) + 1, 'curves'

	def parse_png(self, *args, **kwargs):
		pdb.set_trace()

	def parse_csv(self, *args, **kwargs):
		data = zip(*[line.strip().split(',') for line in args[0]])
		(x_lab, x) = ([data[0][0]], [float(val) for val in data[0][1:]])
		(y_labs, ys) = ([data[dex][0] for dex in range(1, len(data))], 
								[[float(val) for val in data[dex][1:]] 
									for dex in range(1, len(data))])
		self.parse_results = self.verify_parse_result(
								x_lab, y_labs, x, ys)

	def parse_txt(self, *args, **kwargs):

		def to_tuple(string):
			split = string.split(',')
			return (split[0], split[1])

		lines = [line[:line.rfind('\n')] for line in args[0]]
		lines = [to_tuple(line) for line in lines]
		self.parse_results = self.verify_parse_result(lines)

	def on_parse_input(self, *args, **kwargs):
		print 'parse', self.input_path
		#set self.domain, self.domain_data, 
		# self.codomain, self.codomain_datas
		#  based on the information in the input
		self.parse_results = {}
		if self.input_path.endswith('.csv'):
			parser = self.parse_csv

		lf.parse_lines(self.input_path, parser, 
			parser_args = (self.parse_results))

	def on_choose_input(self, file_ = None):
		self.choose_inp_flag = False
		if not os.path.isfile(self.input_path):
			fidlg = lgd.create_dialog('Choose File', 'File?', 
				'file', 'Input file (*.*)', self.input_dir)
			file_ = fidlg()

		if file_:
			self.input_path = file_
			try: self.inp_text_box_ref[0].setText(self.input_path)
			except TypeError:
				lgd.message_dialog(None, 'Refresh Required!', 'Problem')

			self.choose_inp_flag = True
			self.rewidget(True)

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		inp_file_box_template = lgm.interface_template_gui(
				layout = 'grid', 
				widg_positions = [(0, 0), (1, 0), (1, 1), (2, 0)], 
				widg_spans = [(1, 2), None, None, None], 
				widgets = ['text', 'button_set'], 
				tooltips = [['Current input file', 
					'Parse the input file for curve data', 
					'Generate input data for fitting']], 
				verbosities = [0, 0], 
				handles = [(self, 'inp_text_box_ref'), None], 
				keys = [['input_path'], None], 
				instances = [[self], None], 
				initials = [[self.input_path], None], 
				bindings = [[None], 
					[lgb.create_reset_widgets_wrapper(window, 
						[self.on_choose_input, self.on_parse_input]), 
								lgb.create_reset_widgets_wrapper(
								window, self.on_write_data)]], 
				labels = [None, ['Choose/Parse Input File', 
									'Generate Data File']])
		self.widg_templates.append(
			lgm.interface_template_gui(
				layout = 'vertical', 
				box_labels = ['Input File', 'Output Data'], 
				widgets = ['panel', 'button_set'], 
				bindings = [None, [self.examine]], 
				labels = [None, ['Examine data with pdb']], 
				templates = [[inp_file_box_template], None]))
		lfu.modular_object_qt.set_settables(
			self, *args, from_sub = True)




