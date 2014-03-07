import libs.modular_core.libfundamental as lfu
import libs.modular_core.libmath as lm
import libs.gui.libqtgui_bricks as lgb
import libs.gui.libqtgui_masons as lgm
from PySide import QtGui, QtCore

#hacks to fix installer build
#import scipy.interpolate as sp
#from scipy.integrate import simps as integrate
#import xml.dom.minidom
#from scipy.stats import pearsonr as correl_coeff
#import pyopencl
#end hacks

import matplotlib
matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4'] = 'PySide'
import matplotlib.backends.backend_qt4agg as mpqt

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.path as path

mpqt.figureoptions = None

import numpy as np
import itertools as it
from copy import deepcopy as copy
import types
import time
import os
import sys
import traceback

import pdb

def message_dialog(window, message, dialog_title, if_yes = None):
	if if_yes is not None:
		reply = QtGui.QMessageBox.question(window, dialog_title, 
				message, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, 
												QtGui.QMessageBox.No)
		if hasattr(if_yes, '__call__'):
			if reply == QtGui.QMessageBox.Yes: if_yes()

		elif type(if_yes) is types.BooleanType:
			if reply == QtGui.QMessageBox.Yes: return True
			elif reply == QtGui.QMessageBox.No: return False

	else: reply = QtGui.QMessageBox.question(window, dialog_title, 
								message, QtGui.QMessageBox.Ok)

def create_dialog(title = 'Dialog', message = '', variety = 'input', 
					fi_exts = None, initial = None, parent = None, 
								templates = None, mason = None):

	def show_dialog_input():
		text, ok = QtGui.QInputDialog.getText(parent, title, message)
		if ok: return text

	def show_dialog_color():
		col = QtGui.QColorDialog.getColor()
		if col.isValid():
			some_frame.setStyleSheet(
				"QWidget { background-color: %s }" % col.name())

	def show_dialog_font():
		font, ok = QtGui.QFontDialog.getFont()
		if ok: some_label.setFont(font)

	def show_dialog_file():
		fname, _ = QtGui.QFileDialog.getOpenFileName(
			parent, 'Open file', initial, fi_exts)
		return fname

	def show_dialog_file_save():
		fname, _ = QtGui.QFileDialog.getSaveFileName(
			parent, 'Choose filename', initial, fi_exts)
		return fname

	def show_dialog_dir():
		return QtGui.QFileDialog.getExistingDirectory(
						parent, 'Open file', initial)

	def show_dialog_templated():
		if templates is None: temps = []
		else: temps = templates
		if mason is None: mas = lgm.standard_mason()
		else: mas = mason
		diag = create_obj_dialog(templates = temps, mason = mas)
		return diag

	if fi_exts is None: fi_exts = ''
	if initial is None: initial = os.getcwd()
	if variety == 'input': return show_dialog_input
	elif variety == 'color': return show_dialog_color
	elif variety == 'font': return show_dialog_font
	elif variety == 'file': return show_dialog_file
	elif variety == 'file_save': return show_dialog_file_save
	elif variety == 'directory': return show_dialog_dir
	elif variety == 'templated': return show_dialog_templated()
	else:
		print 'variety unrecognized; defaulting to "input"'
		return show_dialog_input

class create_obj_dialog(QtGui.QDialog):
	made = False

	def __call__(self, *args, **kwargs):
		self.dialoging = True
		self.exec_()
		if self.made: return True
		else: return False

	def __init__(self, *args, **kwargs):
		super(create_obj_dialog, self).__init__(None)
		self.dialoging = False
		try: self.mason = kwargs['mason']
		except KeyError: self.mason = lgm.standard_mason()
		try: self.widg_templates = kwargs['templates']
		except KeyError: self.widg_templates = []
		try: self.title = kwargs['title']
		except KeyError: self.title = 'Make MObject'
		self.setWindowTitle(self.title)
		self.setWindowIcon(lgb.create_icon(os.path.join(
				os.getcwd(), 'resources', 'gear.png')))
		if 'from_sub' not in kwargs.keys(): self.set_up_widgets()
		else:
			if not kwargs['from_sub']: self.set_up_widgets()

	def rewidget(self, *args, **kwargs):
		try:
			if type(args[0]) is types.BooleanType:
				self.rewidget_ = args[0]

			else: print 'unrecognized argument for rewidget; ignoring'

		except IndexError: return self.rewidget_

	def set_up_widgets(self, layout = None):
		path = os.getcwd()
		panel = lgb.create_panel(self.widg_templates, self.mason)
		button_icons = [os.path.join(path, 'resources', 'make.png'), 
						os.path.join(path, 'resources', 'back.png')]
		button_template = lgm.interface_template_gui(
				widgets = ['button_set'], 
				verbosities = [0], 
				layout = 'horizontal', 
				bindings = [[self.on_make, self.reject]], 
				#labels = [['make', 'cancel']], 
				icons = [button_icons], 
				minimum_sizes = [[(100, 50), (100, 50)]])
		buttons = self.mason.interpret_template(button_template)
		buttons.itemAt(0).widget().setFocus()

		if layout: layout.addWidget(panel)
		else: layout = lgb.create_vert_box([panel])
		layout.addLayout(buttons)
		self.delete_layout()
		self.setLayout(layout)
			
		#self.layout().addWidget(panel)
		#self.layout().addLayout(buttons)

	def delete_layout(self):
		try:
			old = self.layout()
			# this is probably the way to replace layout items, in lieu of deleting a layout...
			#child = layout.takeAt(0)
			#while child:
			#	...
			#	del child
			old.deleteLater()

		except AttributeError: pass

	def on_make(self):
		self.made = True
		if self.dialoging: self.accept()

class plot_page(QtGui.QWidget):

	def __init__(self, plt_window, label, figure, canvas, 
			data_container, specifics, filename, title, 
							x_ax_title, y_ax_title):
		super(plot_page, self).__init__()
		self.parent = plt_window
		self.page_label = label
		self.figure = figure
		self.canvas = canvas
		self.roll_dex = 0
		self.roll_delay = 0.1

		self._data_ = data_container
		self._plot_targets_ = specifics
		self._filename_ = filename
		self.max_line_count = 20
		self.title = title
		self.x_ax_title = x_ax_title
		self.y_ax_title = y_ax_title
		self.surf_target = title

	def change_domain(self, dom_dex = 0):
		self.x_ax_title = self._plot_targets_[dom_dex]
		self.show_plot()

	def change_color_domain_y(self, dom_dex = 0):
		self.y_ax_title = self._plot_targets_[dom_dex]
		self.show_plot()

	def change_color_surface_target(self, rng_dex):
		self.surf_target = self._plot_targets_[rng_dex]
		self.show_plot()

	def resolve_x_domain(self):
		self.parent.domain_selector[0].children()[1].clear()
		self.parent.domain_selector[0].children()[1].addItems(
										self._plot_targets_)
		try:
			self.parent.domain_selector[0].children()[1].setCurrentIndex(
							self._plot_targets_.index(self.x_ax_title))

		except ValueError:
			try: self.x_ax_title = self._plot_targets_[0]
			except IndexError:
				message_dialog(None, 'Nothing was outputted;\
							\n cant plot nothing!', 'Problem')
				return

			self.parent.domain_selector[0].children()[1].setCurrentIndex(
							self._plot_targets_.index(self.x_ax_title))

	def resolve_y_domain(self):
		self.parent.y_domain_selector[0].children()[1].clear()
		self.parent.y_domain_selector[0].children()[1].addItems(
										self._plot_targets_)
		try:
			self.parent.y_domain_selector[0].children()[1].setCurrentIndex(
								self._plot_targets_.index(self.y_ax_title))

		except ValueError:
			self.y_ax_title = self._plot_targets_[0]
			self.parent.y_domain_selector[0].children()[1].setCurrentIndex(
								self._plot_targets_.index(self.y_ax_title))

	def resolve_surf_target(self):
		self.parent.surf_target_selector[0].children()[1].clear()
		self.parent.surf_target_selector[0].children()[1].addItems(
											self._plot_targets_)
		try:
			self.parent.surf_target_selector[0].children()[
				1].setCurrentIndex(self._plot_targets_.index(
											self.surf_target))

		except ValueError:
			self.surf_target = self._plot_targets_[0]
			self.parent.surf_target_selector[0].children()[
				1].setCurrentIndex(self._plot_targets_.index(
											self.surf_target))

	def hide(self, *args, **kwargs):
		#print 'hide', self.page_label
		pass

	def show_plot(self, *args, **kwargs):
		if self.parent.plot_type is 'lines':
			self.show_plot_lines(*args, **kwargs)

		elif self.parent.plot_type is 'color':
			self.show_plot_color(*args, **kwargs)

		elif self.parent.plot_type is 'bars':
			self.show_plot_bars(*args, **kwargs)

		else: print 'plot page is confused...'

	def show_plot_lines(self, *args, **kwargs):

		#interpolate y so that it covers domain x
		def fill_via_interpolation(x, y):
			print 'interpolation for incorrectly '+\
				'structured data is not supported'

		def plot_(x, y, label):
			if not x.size == y.size: x, y = fill_via_interpolation(x, y)
			line = matplotlib.lines.Line2D(
				x, y, color = self.colors.pop())
			line.set_label(label)
			ax.add_line(line)

		self.resolve_x_domain()
		ax = self.add_plot()
		ax.grid(True)
		x_ax = lfu.grab_mobj_by_name(self.x_ax_title, self._data_.data)
		y_axes = [dater for dater in self._data_.data if dater.label 
			in self._plot_targets_ and not dater.label is x_ax.label]
		x = np.array(x_ax.scalers)
		ys = [np.array(y_ax.scalers) for y_ax in y_axes 
							if hasattr(y_ax, 'scalers')]
		[plot_(x, y, label) for x, y, label in 
			zip([x]*len(ys), ys, [dater.label for dater in y_axes])]
		ax.axis([x.min(), x.max(), min([y.min() for y in ys]), 
								max([y.max() for y in ys])])
		ax.legend()
		self.canvas.draw()

	def show_plot_color(self, *args, **kwargs):
		self.resolve_x_domain()
		self.resolve_y_domain()
		self.resolve_surf_target()
		self.fixed_axis_values = [2, 6, 8]

		ax = self.add_plot()

		try:
			surf_vector_dex = [hasattr(dater, 'reduced') 
				for dater in self._data_.data].index(True)

		except ValueError:
			print 'no surface_vector found!'; return

		surf_vect = self._data_.data[surf_vector_dex]
		surf_vect.make_surface(axis_defaults = self.fixed_axis_values, 
			x_ax = self.x_ax_title, y_ax = self.y_ax_title, 
							surf_target = self.surf_target)
		x_ax = lfu.grab_mobj_by_name(self.x_ax_title, 
								surf_vect.reduced[0])
		y_ax = lfu.grab_mobj_by_name(self.y_ax_title, 
								surf_vect.reduced[0])
		x = np.array(x_ax.scalers, dtype = float)
		y = np.array(y_ax.scalers, dtype = float)
		try:
			surf = np.array(surf_vect.reduced[1].scalers, 
					dtype = float).reshape(len(x), len(y))

		except ValueError:
			print 'not organized properly to colorplot...'
			return

		surf = surf.transpose()
		z_min, z_max = surf.min(), surf.max()
		#plt.xscale('log')
		#plt.yscale('log')
		pc_mesh = ax.pcolormesh(x, y, surf, cmap = 'autumn', 
			shading = 'gouraud', vmin = z_min, vmax = z_max)
		ax.axis([x.min(), x.max(), y.min(), y.max()])
		#try: self.figure.delaxes(self.figure.axes[1])
		#except IndexError: pass
		self.figure.colorbar(pc_mesh)
		self.canvas.draw()

	def show_plot_bars(self, *args, **kwargs):		
		fig = self.figure
		ax = self.add_plot()
		#for now, assume only one bin_vectors object in the data set
		try:
			bin_vectors_dex = [hasattr(dater, 'bins') for dater 
								in self._data_.data].index(True)

		except ValueError:
			print 'no bin_vectors found!'; return

		counts_ = self._data_.data[bin_vectors_dex].counts
		self.max_roll_dex = len(counts_)
		n = counts_[self.roll_dex]
		bins = self._data_.data[bin_vectors_dex].bins
		# get the corners of the rectangles for the histogram
		left = np.array(bins[:-1])
		right = np.array(bins[1:])
		bottom = np.zeros(len(left))
		top = bottom + n
		# we need a (numrects x numsides x 2) numpy array for the path helper
		# function to build a compound path
		XY = np.array([[left,left,right,right], [bottom,top,top,bottom]]).T
		# get the Path object
		barpath = path.Path.make_compound_path_from_polys(XY)
		# make a patch out of it
		patch = patches.PathPatch(barpath, facecolor='blue', 
								edgecolor='gray', alpha=0.8)
		ax.add_patch(patch)
		# update the view limits
		ax.set_xlim(left[0], right[-1])
		ax.set_ylim(bottom.min(), top.max())
		#plt.show()
		self.canvas.draw()

	def add_plot(self, code = 111):
		self.figure.clf()
		ax = self.figure.add_subplot(code)
		ax.cla()
		ax.set_xlabel(self.x_ax_title, fontsize = 18)
		ax.set_ylabel(self.y_ax_title, fontsize = 18)
		ax.set_title(self.title)
		#self.colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
		#colormap = plt.cm.gist_stern
		colormap = plt.cm.gist_ncar
		#colormap = plt.cm.gist_earth
		#colormap = plt.cm.gist_heat
		#colormap = plt.cm.gist_rainbow
		self.colors = [colormap(i) for i in 
			np.linspace(0, 0.9, self.max_line_count)]
		return ax

class plot_window_toolbar(NavigationToolbar):

	toolitems = [t for t in NavigationToolbar.toolitems 
					if t[0] in ('Pan', 'Zoom', 'Save')]

	""" Subclasses the matplotlib toolbar so we can integrate more widgets into it """
	def __init__(self, canvas, parent):
		self._plt_window_ = parent
		NavigationToolbar.__init__(self, canvas, parent)
		#print 'new tool bar __init__', type(self)  # Built_in_function_or_method ?

	def roll(self):
		page = self._plt_window_.get_current_page()
		while page.roll_dex < page.max_roll_dex:
			#print page.roll_dex
			page.show_plot_bars()
			time.sleep(page.roll_delay)
			page.roll_dex += 1

		page.roll_dex = 0

	def _init_toolbar(self):
		""" Add our extra widgets """
		#print '_init_toolbar method'
		NavigationToolbar._init_toolbar(self)
		#self.layout().addWidget(QtGui.QPushButton("test"))  # Fails, layout has no addWidget method
		gear_icon_path = os.path.join(
			os.getcwd(), 'resources', 'gear.png')
		gear_icon = lgb.create_icon(gear_icon_path)
		roll_action = lgb.create_action(
			parent = self, label = 'Roll Plots', 
			bindings = lgb.create_thread_wrapper(self.roll), 
					icon = gear_icon, shortcut = 'Alt+P', 
					statustip = 'Roll Through Bar Plots')
		self.addAction(roll_action)

class plot_window(create_obj_dialog):

	def __call__(self, *args, **kwargs):	
		self.show()
		self.activateWindow()

	def __init__(self, *args, **kwargs):
		self.codes = range(1000)
		self.selected_page_label = None
		self.page_labels = []
		self.pages = []

		self._all_plot_targets_ = []
		self.current_targets = []
		self.targets_layout = lgb.create_vert_box([])
		self.check_group = None

		self.slice_layout = lgb.create_vert_box([])
		self.slice_group = None

		self.plot_type = 'lines'
		self.plot_types = kwargs['plot_types']
		mason = lgm.standard_mason(parent = self)
		if 'title' in kwargs.keys(): title = kwargs['title']
		else: title = 'Plot Window'
		create_obj_dialog.__init__(self, None, mason = mason, 
							title = title, from_sub = True)

		self.figure = plt.figure()
		self.canvas = FigureCanvas(self.figure)
		self.setBackgroundRole(QtGui.QPalette.Window)
		#self.canvas.setSizePolicy(
		#	QtGui.QSizePolicy.Expanding,
		#	QtGui.QSizePolicy.Expanding)
		#self.canvas.updateGeometry()

		#this stupid class is buggy as hell... make it yourself...
		#self.toolbar = NavigationToolbar(self.canvas, self)
		self.toolbar = plot_window_toolbar(self.canvas, self)
		self.set_settables()

	def get_verbosities(self):
		if self.plot_type == 'lines': verbs = [0, 0, 0, 0, 10, 10, 0]
		elif self.plot_type == 'color': verbs = [0, 0, 0, 0, 0, 0, 10]
		elif self.plot_type == 'bars': verbs = [0, 0, 0, 10, 10, 10, 10]
		return verbs

	def set_settables(self, *args, **kwargs):
		self.widg_templates = []
		#self.plot_types = ['lines', 'color', 'bars']
		verbs = self.get_verbosities()
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['selector', 'button_set', 'radio', 
						'selector', 'selector', 'selector'], 
				verbosities = verbs[:-1], 
				layout = 'vertical', 
				initials = [None, None, ['lines'], None, None, None], 
				instances = [None, None, [self], None, None, None], 
				keys = [None, None, ['plot_type'], None, None, None], 
				bindings = [[self.change_page], [self.remake_plot], 
					None, [self.change_domain], [self.change_y_domain], 
						[self.change_surf_target]], 
				bind_events = [None, None, None, ['useronly'], 
									['useronly'], ['useronly']], 
				handles = [(self, 'page_selector'), None, 
							None, (self, 'domain_selector'), 
								(self, 'y_domain_selector'), 
								(self, 'surf_target_selector')], 
				labels = [self.page_labels, ['Plot'], 
						self.plot_types, [], [], []], 
				box_labels = [None, None, 'Plot Type', 
					'Domain', 'Y-Domain', 'Surface Target'], 
				minimum_sizes = [None, [(100, 50)], 
						None, None, None, None]))
		self.set_up_widgets()

	def set_up_widgets(self):
		panel = lgb.create_panel(self.widg_templates, self.mason)
		layout = lgb.create_horz_box([panel])
		layout.addLayout(self.targets_layout)
		bottom_layout = lgb.create_vert_box([self.canvas, self.toolbar])
		layout.addLayout(bottom_layout)
		#layout.addWidget(self.canvas)
		#layout.addWidget(self.toolbar)
		#self.delete_layout()
		self.setLayout(layout)

	def create_plot_page(self, page_label, data_container, specifics, 
							filename, title, x_ax_title, y_ax_title):
		return plot_page(self, page_label, self.figure, self.canvas, 
						data_container, specifics, filename, title, 
											x_ax_title, y_ax_title)

	def change_page(self, new_dex):
		self.set_current_page(new_dex)

	def set_current_page(self, page_dex):
		try:
			self.pages[self.page_labels.index(
				self.selected_page_label)].hide()

		except ValueError: pass
		except IndexError: pass
		self.selected_page_label = self.page_labels[page_dex]
		#print 'changed page', self.selected_page_label
		try:
			page_dex = self.page_labels.index(self.selected_page_label)
			self.current_targets = copy(self._all_plot_targets_[page_dex])
			self.update_check_boxes(page_dex)
			self.update_axes_slicing(page_dex)
			self.pages[page_dex]._plot_targets_ = self.current_targets
			#self.pages[page_dex].show_plot(page_dex)
			self.pages[page_dex].show_plot()

		except IndexError: pass

	def get_current_page(self):
		dex = self.page_labels.index(self.selected_page_label)
		return self.pages[dex]

	def update_check_boxes(self, page_dex):
		self.targets_layout.removeWidget(self.check_group)
		if self.check_group: self.check_group.deleteLater()
		append_instead = True
		keys = ['current_targets']
		instances = [self]
		labels = copy(self._all_plot_targets_[page_dex])
		provide_master = False
		check_widget = lgb.create_check_boxes(append_instead, keys, 
			instances, labels, None, None, False, provide_master)

		for check in check_widget:
			dex = self.page_labels.index(self.selected_page_label)
			check.stateChanged.connect(self.pages[dex].show_plot)

		title = 'Curves Shown'
		self.check_group = QtGui.QGroupBox(title = title)
		layout = lgb.create_vert_box(check_widget)
		self.check_group.setLayout(layout)
		self.targets_layout.addWidget(self.check_group)

	def update_axes_slicing(self, page_dex):
		self.slice_layout.removeWidget(self.slice_group)
		if self.slice_group: self.slice_group.deleteLater()

		'''
		append_instead = True
		keys = ['current_targets']
		instances = [self]
		labels = copy(self._all_plot_targets_[page_dex])
		provide_master = True
		check_widget = lgb.create_check_boxes(append_instead, keys, 
			instances, labels, None, None, False, provide_master)

		for check in check_widget:
			dex = self.page_labels.index(self.selected_page_label)
			check.stateChanged.connect(self.pages[dex].show_plot)
		'''
		slice_widgets = []

		title = 'P-Space Axis Handling'
		self.slice_group = QtGui.QGroupBox(title = title)
		layout = lgb.create_vert_box(slice_widgets)
		self.slice_group.setLayout(layout)
		self.slice_layout.addWidget(self.slice_group)

	def set_plot_info(self, data_container, filename, specifics, 
						title = 'title', x_ax_title = 'x-axis', 
										y_ax_title = 'y-axis'):
		new_page = 'page ' + str(self.get_code())
		self.page_labels.append(new_page)
		self.selected_page_label = new_page
		self.page_selector[0].children()[1].addItem(
						new_page, userData = None)
		self._all_plot_targets_.append(specifics)
		page = self.create_plot_page(new_page, data_container, 
			specifics, filename, title, x_ax_title, y_ax_title)
		self.pages.append(page)
		lay = self.layout()
		lay.addWidget(page)

	def get_code(self):
		try: return self.codes.pop(0)
		except IndexError:
			print 'no codes left'; return 111

	def pre_plot(self):
		return self.add_plot()

	def add_plot(self, code = 111):
		ax = self.figure.add_subplot(code)
		ax.cla()
		ax.set_xlabel(self.x_ax_title, fontsize = 18)
		ax.set_ylabel(self.y_ax_title, fontsize = 18)
		ax.set_title(self.title)
		self.colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
		return ax

	def remake_plot(self):
		dex = self.page_labels.index(self.selected_page_label)
		if not self.current_targets:
			print 'nothing to plot; renabling curves'
			self.current_targets = copy(self._all_plot_targets_[dex])

		self.update_check_boxes(dex)
		self.update_axes_slicing(dex)
		self.pages[dex]._plot_targets_ = self.current_targets
		#self.set_current_page(dex)
		self.hide_irrelevant_widgets()
		self.pages[dex].show_plot()

	def hide_irrelevant_widgets(self):
		verbs = self.get_verbosities()
		if verbs[6] > 0: self.check_group.hide()
		else: self.check_group.show()
		if verbs[5] > 0: self.surf_target_selector[0].hide()
		else: self.surf_target_selector[0].show()
		if verbs[4] > 0: self.y_domain_selector[0].hide()
		else: self.y_domain_selector[0].show()
		if verbs[3] > 0: self.domain_selector[0].hide()
		else: self.domain_selector[0].show()

	def change_domain(self, new_dex):
		dex = self.page_labels.index(self.selected_page_label)
		self.pages[dex].change_domain(new_dex)

	def change_y_domain(self, new_dex):
		dex = self.page_labels.index(self.selected_page_label)
		self.pages[dex].change_color_domain_y(new_dex)

	def change_surf_target(self, new_dex):
		dex = self.page_labels.index(self.selected_page_label)
		self.pages[dex].change_color_surface_target(new_dex)

class trajectory_dialog(create_obj_dialog):

	def __init__(self, *args, **kwargs):
		mason = lgm.standard_mason(parent = self.parent)
		if 'title' in kwargs.keys(): title = kwargs['title']
		else: title = 'Create Trajectory Window'

		self.base_object = kwargs['base_object']
		self.p_space = kwargs['p_space']
		self.parent = kwargs['parent']

		self.result = None
		self.constructed = []
		#variations is a list (in 1-1 with subspaces)
		#	of lists of values
		self.variations = [None]*len(self.p_space.subspaces)
		if not self.variations:
			lgd.message_dialog(self.parent, 
				'Parameter Space has no axes!', 'Problem')
			self.reject()

		self.comp_methods = ['Product Space', '1 - 1 Zip']
		self.axis_labels = [subsp.label for subsp in 
							self.p_space.subspaces]
		#self.composition_method = 'Product Space'
		if 'composition_method' in kwargs.keys():
			self.composition_method = kwargs['composition_method']

		else: self.composition_method = 'Product Space'
		create_obj_dialog.__init__(self, None, mason = mason, 
							title = title, from_sub = True)
		self.set_settables()

	def set_settables(self, *args, **kwargs):
		self.widg_templates = []
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['radio'], 
				labels = [self.comp_methods], 
				instances = [[self]], 
				keys = [['composition_method']], 
				initials = [[self.composition_method]],  
				box_labels = ['Composition Method']))
		self.set_up_widgets()

	def set_up_widgets(self):
		range_makers, variations = create_ranger_makers(
									self, 'variations')
		axis_widgets = lgb.central_widget_wrapper(content =\
			lgb.create_vert_box([lgb.central_widget_wrapper(content =\
				lgb.create_vert_box([lgb.create_label(
				text = axis), range_maker])) for axis, range_maker 
						in zip(self.axis_labels, range_makers)]))
		variations = lgb.central_widget_wrapper(content =\
						lgb.create_vert_box(variations))
		panel = lgb.create_scroll_area(lgb.central_widget_wrapper(
			content = lgb.create_horz_box([axis_widgets, variations])))
		layout = lgb.create_vert_box([panel])
		create_obj_dialog.set_up_widgets(self, layout)

	def wrap_nones(self):
		for dex in range(len(self.variations)):
			if not self.variations[dex]:
				self.variations[dex] = [None]

	def create_product_space_locations(self):
		from libs.modular_core.libgeometry import parameter_space_location
		self.wrap_nones()
		
		tuple_table = it.product(*self.variations)
		for tup in tuple_table:
			fixed_tup = []
			for elem, dex in zip(tup, range(len(tup))):
				if elem is None:
					fixed_tup.append(self.base_object[0][dex])

				else: fixed_tup.append(tup[dex])

			self.constructed.append(parameter_space_location(
								location = list(fixed_tup)))

	def create_one_to_one_locations(self):
		from libs.modular_core.libgeometry import parameter_space_location
		self.wrap_nones()
		max_leng = max([len(variant) for variant in self.variations])
		for dex in range(len(self.variations)):
			if self.variations[dex][0] is None:
				self.variations[dex] =\
					[self.base_object[0][dex]]*max_leng

			elif len(self.variations[dex]) < max_leng:
				leng_diff = max_leng - len(self.variations[dex])
				last_value = self.variations[dex][-1]
				[self.variations[dex].append(last_value) for k in
												range(leng_diff)]

		for dex in range(max_leng):
			locale = [var[dex] for var in self.variations] 
			self.constructed.append(parameter_space_location(
										location = locale))

	def on_make(self):
		if self.composition_method == 'Product Space':
			self.create_product_space_locations()

		elif self.composition_method == '1 - 1 Zip':
			self.create_one_to_one_locations()

		self.result = self.constructed
		if self.dialoging:
			create_obj_dialog.on_make(self)

		else: self.made = True

def create_ranger_makers(inst, key):
	makers = []
	displays = []
	for dex in range(len(inst.__dict__[key])):
		displays.append(range_maker_display(inst, key, dex))
		makers.append(range_maker(displays[-1]))

	return makers, displays

class range_maker_display(QtGui.QLabel):

	def __init__(self, inst, key, dex, parent = None):
		super(range_maker_display, self).__init__(parent)
		self.inst = inst
		self.key = key
		self.dex = dex
		self._range_ = ''
		self.box = lgb.create_text_box(parent = self, 
			instance = self, key = '_range_', alignment = 'center', 
			initial = self._range_, multiline = True, rewidget = False)
		self.box.textChanged.connect(self.update_variation)
		self.setLayout(lgb.create_horz_box([self.box]))
		lgb.set_sizes_limits([[self]], [[(100, 80)]])

	def update_variation(self):
		valid = []
		for val in self._range_.split(','):
			try: valid.append(float(val))
			except: pass

		self.inst.__dict__[self.key][self.dex] = valid

class range_maker(QtGui.QLabel):

	def __init__(self, display, parent = None):
		super(range_maker, self).__init__(parent)
		self.display = display
		self._range_ = ''
		self.box = lgb.create_text_box(parent = self, 
			instance = self, key = '_range_', alignment = 'center', 
			initial = self._range_, multiline = False, rewidget = False)
		self.box.returnPressed.connect(self.update_display)
		self.setLayout(lgb.create_horz_box([self.box]))
		lgb.set_sizes_limits([[self]], [[(max([25*10, 100]), 40)]])
		#self.setFocusPolicy(QtCore.Qt.StrongFocus)

	def update_display(self):
		rng, valid = self.make_range()
		if valid: self.display.box.setText(rng)

	def make_range(self):
		'''
		def strip_separate(stg, delim = ':'):
			return [item.strip() for item in stg.split(delim)]

		def parse_range(stg):
			if stg.strip() == '': return ''
			elif not stg.count('-') > 0 and not stg.count(';') > 0:
				res = ', '.join([str(float(item)) 
					for item in stg.split(',')])
				return res

			elif stg.count('-') > 0 and not stg.count(';') > 0:
				res = ', '.join([str(item) for item in np.arange(
					float(stg[:stg.find('-')]), 
					float(stg[stg.find('-') + 1:]) + 1.0, 1.0)])
				return res

			elif stg.count('-') > 0 and stg.count(';') > 0:
				interval = float(stg[stg.rfind(';') + 1:])
				front = float(stg[:stg.find('-')])
				back = float(stg[stg.find('-') + 1:stg.find(';')])
				values = list(np.arange(front, back, interval))
				if back - values[-1] >= interval:
					values.append(values[-1] + interval)

				res = ', '.join([str(item) for item in values])
				return res

			elif not stg.count('-') > 0 and stg.count(';') > 0:
				res = ', '.join([str(float(item)) for 
					item in stg[:stg.find(';')].split(',')])
				return res
		'''
		#ranges = strip_separate(self._range_, ':')
		#ranges = [parse_range(stg) for stg in ranges]
		#ranges = ', '.join(ranges)
		ranges, valid = lm.make_range(self._range_)
		return ranges, valid

	def handle_rewidget(self):
		if self.rewidget and issubclass(self.inst.__class__, 
			lfu.modular_object_qt): self.inst.rewidget(True)

if __name__ == '__main__': print 'this is a library!'


