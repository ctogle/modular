import modular_core.libfundamental as lfu
import modular_core.libmath as lm
import modular_core.gui.libqtgui_bricks as lgb
import modular_core.gui.libqtgui_masons as lgm
from PySide import QtGui, QtCore

import traceback, sys
import six
import numpy as np
import itertools as it
from copy import deepcopy as copy
import types
import time
import os

try:
	import matplotlib
	matplotlib.rcParams['backend.qt4'] = 'PySide'
	#matplotlib.use('Qt4Agg')

	from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
	from matplotlib.backend_bases import NavigationToolbar2

	import matplotlib.pyplot as plt
	import matplotlib.patches as patches
	import matplotlib.path as path
	from matplotlib import animation
except ImportError:
	traceback.print_exc(file=sys.stdout)
	print 'matplotlib could not be imported! - dialogs'

from mpl_toolkits.mplot3d import axes3d, Axes3D

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
		self.button_icons =\
			[lfu.get_resource_path('make.png'), 
			lfu.get_resource_path('back.png')]
		if 'button_regime' in kwargs.keys():
			reg = kwargs['button_regime']
			if reg.startswith('apply'):
				self.button_icons[0]=lfu.get_resource_path('apply.png')

			if reg.endswith('cancel'):
				self.button_icons[1]=lfu.get_resource_path('cancel.png')

		self.setWindowIcon(lgb.create_icon(
			lfu.get_resource_path('gear.png')))
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
		panel = lgb.create_panel(self.widg_templates, self.mason)
		button_template = lgm.interface_template_gui(
				widgets = ['button_set'], 
				verbosities = [0], 
				layout = 'horizontal', 
				bindings = [[self.on_make, self.reject]], 
				#labels = [['make', 'cancel']], 
				icons = [self.button_icons], 
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

###################
#plotting business#
###################
class labels_dialog(create_obj_dialog):

	def __init__(self, *args, **kwargs):
		if 'newtitle' in kwargs.keys():
			self.newtitle = kwargs['newtitle']
		else: self.newtitle = 'new title'

		if 'newxtitle' in kwargs.keys():
			self.newxtitle = kwargs['newxtitle']
		else: self.newxtitle = 'new x-title'
		if 'x_log' in kwargs.keys():
			self.x_log = kwargs['x_log']
		else: self.x_log = False

		if 'newytitle' in kwargs.keys():
			self.newytitle = kwargs['newytitle']
		else: self.newytitle = 'new y-title'
		if 'y_log' in kwargs.keys():
			self.y_log = kwargs['y_log']
		else: self.y_log = False

		if 'max_line_count' in kwargs.keys():
			self.max_line_count = kwargs['max_line_count']

		else: self.max_line_count = 20
		if 'plot_targets' in kwargs.keys():
			self.plot_targets = kwargs['plot_targets']

		else: self.plot_targets = ['NO TARGETS']
		if 'domain' in kwargs.keys():
			self.domain = kwargs['domain']

		else: self.domain = None
		if 'cplot_interpolation' in kwargs.keys():
			self.cplot_interpolation = kwargs['cplot_interpolation']

		else: self.cplot_interpolation = None
		if self.plot_targets: self.target = self.plot_targets[0]
		else: self.target = None
		colormap = plt.get_cmap('jet')
		if 'colors' in kwargs.keys(): self.colors = kwargs['colors']
		else:
			self.colors = [colormap(i) for i in np.linspace(
							0, 0.9, min([self.max_line_count, 
							len(self.plot_targets) - 1]))]

		mason = lgm.standard_mason(parent = self.parent)
		if 'title' in kwargs.keys(): title = kwargs['title']
		else: title = 'Change Plot Labels'

		create_obj_dialog.__init__(self, None, mason = mason, 
				title = title, button_regime = 'apply-cancel', 
				from_sub = True)
		self.set_settables()

	def pick_color(self):
		col = QtGui.QColorDialog.getColor()
		if col.isValid():
			targ_dex = self.plot_targets.index(self.target) - 1
			self.colors[targ_dex] = col.getRgbF()

	def set_settables(self, *args, **kwargs):
		self.widg_templates = []
		title_box = lgm.interface_template_gui(
			widgets = ['text'], 
			keys = [['newtitle']], 
			instances = [[self]], 
			box_labels = ['New Title'])
		title_panel = lgm.interface_template_gui(
			widgets = ['panel'], 
			layout = 'vertical', 
			templates = [[title_box]], 
			box_labels = ['General Settings'])
		x_title_box = lgm.interface_template_gui(
			widgets = ['text'], 
			keys = [['newxtitle']], 
			instances = [[self]], 
			box_labels = ['New X-Title'])
		x_log_box = lgm.interface_template_gui(
			widgets = ['check_set'], 
			labels = [['Use Log Scale']], 
			append_instead = [False], 
			instances = [[self]], 
			keys = [['x_log']])
		x_panel = lgm.interface_template_gui(
			widgets = ['panel'], 
			layout = 'vertical', 
			templates = [[x_title_box, x_log_box]], 
			box_labels = ['X-Axis Settings'])
		y_title_box = lgm.interface_template_gui(
			widgets = ['text'], 
			keys = [['newytitle']], 
			instances = [[self]], 
			box_labels = ['New Y-Title'])
		y_log_box = lgm.interface_template_gui(
			widgets = ['check_set'], 
			labels = [['Use Log Scale']], 
			append_instead = [False], 
			instances = [[self]], 
			keys = [['y_log']])
		y_panel = lgm.interface_template_gui(
			widgets = ['panel'], 
			layout = 'vertical', 
			templates = [[y_title_box, y_log_box]], 
			box_labels = ['Y-Axis Settings'])
		left_panel = title_panel + x_panel + y_panel
		self.widg_templates.append(left_panel)
		codomains = [item for item in self.plot_targets 
							if not item == self.domain]
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['radio', 'button_set'], 
				labels = [codomains, ['Change Line Color']], 
				initials = [[self.target], None], 
				instances = [[self], None], 
				keys = [['target'], None], 
				bindings = [None, [self.pick_color]], 
				panel_label = 'Line Colors', 
				box_labels = ['Plot Target', None]))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['radio'], 
				instances = [[self]], 
				keys = [['cplot_interpolation']], 
				labels = [['bicubic', 'bilinear', 'nearest']], 
				initials = [[self.cplot_interpolation]], 
				box_labels = ['Color Plot Settings']))
		self.set_up_widgets()

def change_labels_dialog(title, x_ax, y_ax, max_lines, 
		colors, targets, domain, xlog, ylog, cintrp):
	dlg = labels_dialog(newtitle = title, newxtitle = x_ax, 
		newytitle = y_ax, max_line_count = max_lines, colors = colors, 
					plot_targets = targets, domain = domain, 
			x_log = xlog, y_log = ylog, cplot_interpolation = cintrp)
	made = dlg()
	if made:
		return (dlg.newtitle, dlg.newxtitle, 
				dlg.newytitle, dlg.colors, 
				dlg.x_log, dlg.y_log, dlg.cplot_interpolation)

	else: return False

class plot_page(QtGui.QWidget):

	def __init__(self, plt_window, label, figure, canvas, 
			data_container, specifics, axes, filename, title, 
									x_ax_title, y_ax_title):
		super(plot_page, self).__init__()
		self.parent = plt_window
		self.page_label = label
		self.figure = figure
		self.canvas = canvas
		self.colors = []
		self.rolling = False
		self.roll_dex = 0
		self.roll_delay = 0.1
		self.max_roll_dex = None

		self._data_ = data_container
		self._plot_targets_ = specifics
		self._axis_labels_ = axes
		self._filename_ = filename
		self.max_line_count = 20
		self.title = title
		self.x_ax_title = x_ax_title
		self.y_ax_title = y_ax_title
		self.x_log = False
		self.y_log = False
		self.surf_target = title

		self.cplot_interpolation = 'bicubic'

	def change_domain(self, dom_dex = 0):
		self.x_ax_title = self._plot_targets_[dom_dex]
		self.show_plot()

	def change_color_domain_y(self, dom_dex = 0):
		self.y_ax_title = self._plot_targets_[dom_dex]
		self.show_plot()

	def change_color_surface_target(self, rng_dex):
		self.surf_target = self._plot_targets_[rng_dex]
		self.show_plot()

	def resolve_domain(self, widg, domain):
		targs = self._plot_targets_
		widg.clear()
		widg.addItems(targs)
		if not self.__dict__[domain] in targs:
			if targs: self.__dict__[domain] = targs[0]
			else:
				message_dialog(None, 'Nothing was outputted;\
							\n cant plot nothing!', 'Problem')
				return
		tdex = targs.index(self.__dict__[domain])
		widg.setCurrentIndex(tdex)

	def resolve_x_domain(self):
		widg = self.parent.domain_selector[0].children()[1]
		self.resolve_domain(widg, 'x_ax_title')

	def resolve_y_domain(self):
		widg = self.parent.y_domain_selector[0].children()[1]
		self.resolve_domain(widg, 'y_ax_title')

	def resolve_surf_target(self):
		widg = self.parent.surf_target_selector[0].children()[1]
		self.resolve_domain(widg, 'surf_target')

	def hide(self, *args, **kwargs):
		#print 'hide', self.page_label
		lay = self.parent.layout()
		lay.removeWidget(self)
		QtGui.QWidget.hide(self)

	def inspect_data(self):
		#the purpose of this function is to verify that self._data_ is valid - preset things for all plotting types!
		dat = self._data_.data
		if type(dat) is types.ListType:
			if not False in [hasattr(da, 'tag') for da in dat]:
				tags = [da.tag for da in dat]
				#print 'tags', tags, self.parent.plot_type
				return True
			else: return False
		else: return False

	def show_plot(self, *args, **kwargs):
		valid = self.inspect_data()
		if valid:
			if self.parent.plot_type is 'lines':
				drw = self.show_plot_lines(*args, **kwargs)

			elif self.parent.plot_type is 'color':
				drw = self.show_plot_color(*args, **kwargs)

			elif self.parent.plot_type is 'surface':
				drw = self.show_plot_surface(*args, **kwargs)

			elif self.parent.plot_type is 'bars':
				drw = self.show_plot_bars(*args, **kwargs)

			if drw: self.canvas.draw()
		else: print 'plot page is confused...'
		lay = self.parent.layout()
		lay.addWidget(self)

	def get_mpl_line_data(self, data, ax = None):
		#interpolate y so that it covers domain x
		def fill_via_interpolation(x, y):
			print 'interpolation for incorrectly '+\
				'structured data is not supported'

		def get_line(x, y, label, col):
			if not x.size == y.size: x, y = fill_via_interpolation(x, y)
			try:
				line = matplotlib.lines.Line2D(
					x, y, color = self.colors[col])
			except IndexError: print 'too many lines!'; return
			except: pdb.set_trace()
			line.set_label(label)
			return line

		x_ax = lfu.grab_mobj_by_name(self.x_ax_title, data)
		if not hasattr(x_ax, 'scalars'):
			print 'current domain is not proper data type...'
			return
		y_axes = [dater for dater in data if dater.label 
			in self._plot_targets_ and not dater.label is x_ax.label 
									and hasattr(dater, 'scalars')]
		if len(y_axes) == 0:
			print 'no lines to plot...'
			return
		x = np.array(x_ax.scalars, dtype = float)
		ys = [np.array(y_ax.scalars, dtype = float) for y_ax in y_axes]
		ylabs = [dater.label for dater in y_axes]
		lines = [get_line(x, y, label, col_dex) for 
			x, y, label, col_dex in 
			zip([x]*len(ys), ys, ylabs, range(len(ys)))]
		if not ax is None:
			ax.axis([x.min(), x.max(), 
				min([y.min() for y in ys]), 
				max([y.max() for y in ys])])
		return lines

	def show_plot_lines(self, *args, **kwargs):
		self.resolve_x_domain()
		ax = self.add_plot()
		ax.grid(True)
		data = self._data_.data
		lines = self.get_mpl_line_data(data, ax)
		if lines is None: return False
		[ax.add_line(li) for li in lines if not li is None]
		ax.legend()
		return True

	def get_surface_svr(self, surf_vect):
		x_ax = lfu.grab_mobj_by_name(self.x_ax_title, 
								surf_vect.axis_values)
		y_ax = lfu.grab_mobj_by_name(self.y_ax_title, 
								surf_vect.axis_values)
		x = np.array(x_ax.scalars, dtype = float)
		y = np.array(y_ax.scalars, dtype = float)
		try:
			surf = np.array(surf_vect.reduced[1].scalars, 
					dtype = float).reshape(len(x), len(y))
			return x, y, surf
		except ValueError: return None

	def get_surface_sv(self, surf_vect):
		xleng = surf_vect.data.shape[1]
		yleng = surf_vect.data.shape[2]
		x = np.arange(xleng)
		y = np.arange(yleng)
		if not self.rolling: s_dex = surf_vect.axis_defaults[0]
		else: s_dex = self.roll_dex
		surf = surf_vect.data[s_dex]
		self.max_roll_dex = surf_vect.data.shape[0]
		return x, y, surf

	def get_mpl_surf_data(self, data, ax = None):
		data = [da for da in data if da.tag.startswith('surface')]
		if not data:
			print 'no surfafce data objects'
			return None, None, None

		slabs = [d.label for d in data]
		if self.surf_target in slabs:
			surf_vect = data[slabs.index(self.surf_target)]
		else: surf_vect = data[0]
		made_surf =\
			surf_vect.make_surface(
				x_ax = self.x_ax_title, 
				y_ax = self.y_ax_title, 
				surf_target = self.surf_target)
		if not made_surf:
			print 'surface was not resolved'
			return None, None, None

		self.title = self.surf_target
		if surf_vect.tag == 'surface':
			x, y, surf = self.get_surface_svr(surf_vect)
		elif surf_vect.tag == 'surface_vector':
			x, y, surf = self.get_surface_sv(surf_vect)
		if surf is None:
			print 'not organized properly to colorplot...'
			return None, None, None

		surf = surf.transpose()
		x_min, x_max = x.min(), x.max()
		y_min, y_max = y.min(), y.max()
		z_min, z_max = surf.min(), surf.max()

		delx = [x[i+1] - x[i] for i in range(len(x) - 1)]
		dely = [y[i+1] - y[i] for i in range(len(y) - 1)]
		xdels = lfu.uniqfy(delx)
		ydels = lfu.uniqfy(dely)
		z_flag = False

		if z_min == z_max:
			z_flag = True
			print 'no variation in surface data...'

		uneven_flag = True
		if len(xdels) == 1 and len(ydels) == 1:
			uneven_flag = False

		#	#Acceptable interpolations are 'none', 'nearest', 'bilinear', 'bicubic', 'spline16', 'spline36', 'hanning', 'hamming', 
		#	#'hermite', 'kaiser', 'quadric', 'catrom', 'gaussian', 'bessel', 'mitchell', 'sinc', 'lanczos'
			pc_mesh = ax.imshow(surf, aspect = 'auto', 
				interpolation = self.cplot_interpolation, 
				#interpolation = 'nearest', 
				#interpolation = 'bilinear', 
				#interpolation = 'bicubic', 
				cmap = plt.get_cmap('jet'), vmin = z_min, vmax = z_max, 
				origin = 'lower', extent = (x_min, x_max, y_min, y_max))

		else:
			print 'axes values are not evenly spaced; plot will be boxy'
			pc_mesh = ax.pcolormesh(x,y,surf,cmap = plt.get_cmap('jet'), 
						shading = 'gouraud', vmin = z_min, vmax = z_max)

		if not ax is None:
			ax.set_title(self.title)
			ax.axis([x_min, x_max, y_min, y_max])
		return pc_mesh, z_flag, uneven_flag

	def show_plot_color(self, *args, **kwargs):
		self.resolve_x_domain()
		self.resolve_y_domain()
		self.resolve_surf_target()
		ax = self.add_plot()
		data = self._data_.data
		surf, z_flag, uneven_flag = self.get_mpl_surf_data(data, ax) 
		if surf is None: return
		'''
		surf_vect = data[0]

		made_surf =\
			surf_vect.make_surface(
				x_ax = self.x_ax_title, 
				y_ax = self.y_ax_title, 
				surf_target = self.surf_target)
		if not made_surf:
			print 'surface was not resolved'
			return

		self.title = self.surf_target
		ax.set_title(self.title)
		if surf_vect.tag == 'surface':
			x, y, surf = self.get_surface_svr(surf_vect)
		elif surf_vect.tag == 'surface_vector':
			x, y, surf = self.get_surface_sv(surf_vect)
		if surf is None:
			print 'not organized properly to colorplot...'
			return

		surf = surf.transpose()
		x_min, x_max = x.min(), x.max()
		y_min, y_max = y.min(), y.max()
		z_min, z_max = surf.min(), surf.max()

		delx = [x[i+1] - x[i] for i in range(len(x) - 1)]
		dely = [y[i+1] - y[i] for i in range(len(y) - 1)]
		xdels = lfu.uniqfy(delx)
		ydels = lfu.uniqfy(dely)
		z_flag = False

		if z_min == z_max:
			z_flag = True
			print 'no variation in surface data...'
		'''
		#if len(xdels) == 1 and len(ydels) == 1:
		'''
		if not uneven_flag:
			#Acceptable interpolations are 'none', 'nearest', 'bilinear', 'bicubic', 'spline16', 'spline36', 'hanning', 'hamming', 
			#'hermite', 'kaiser', 'quadric', 'catrom', 'gaussian', 'bessel', 'mitchell', 'sinc', 'lanczos'
			pc_mesh = ax.imshow(surf, interpolation = 'bicubic', 
				cmap = plt.get_cmap('jet'), vmin = z_min, vmax = z_max, 
				origin = 'lower', extent = (x_min, x_max, y_min, y_max))
		else:
			print 'axes values are not evenly spaced; plot will be boxy'
			pc_mesh = ax.pcolormesh(x,y,surf,cmap = plt.get_cmap('jet'), 
						shading = 'gouraud', vmin = z_min, vmax = z_max)
		'''
		#ax.axis([x_min, x_max, y_min, y_max])
		ax.grid(True)
		#if not z_flag: self.figure.colorbar(pc_mesh)
		if not z_flag: self.figure.colorbar(surf)
		return True

	def show_plot_surface(self, *args, **kwargs):
		self.resolve_x_domain()
		self.resolve_y_domain()
		self.resolve_surf_target()
		self.figure.clf()
		ax = Axes3D(self.figure)
		self.newest_ax = ax
		ax.cla()
		ax.grid(False)

		data = [da for da in self._data_.data 
			if da.tag.startswith('surface')]
		if not data: return
		surf_vect = data[0]

		made_surf =\
			surf_vect.make_surface(
				x_ax = self.x_ax_title, 
				y_ax = self.y_ax_title, 
				surf_target = self.surf_target)
		if not made_surf:
			print 'surface was not resolved'
			return

		ax.set_xlabel(self.x_ax_title, fontsize = 18)
		ax.set_ylabel(self.y_ax_title, fontsize = 18)
		ax.set_zlabel(self.surf_target, fontsize = 18)
		self.title = self.surf_target
		ax.set_title(self.title)
		x_ax = lfu.grab_mobj_by_name(self.x_ax_title, 
								surf_vect.axis_values)
		y_ax = lfu.grab_mobj_by_name(self.y_ax_title, 
								surf_vect.axis_values)
		x = np.array(x_ax.scalars, dtype = float)
		y = np.array(y_ax.scalars, dtype = float)
		try:
			if hasattr(surf_vect, 'reduced'):
				surf = np.array(surf_vect.reduced[1].scalars, 
						dtype = float).reshape(len(x), len(y))
			else:
				s_dex = 0
				surf = surf_vect.data[s_dex]
		except ValueError:
			print 'not organized properly to colorplot...'
			return

		surf = surf.transpose()
		x_min, x_max = x.min(), x.max()
		y_min, y_max = y.min(), y.max()
		z_min, z_max = surf.min(), surf.max()

		x, y = np.meshgrid(x, y)
		ax.set_zlim(z_min, z_max)
		ax.axis([x_min, x_max, y_min, y_max])
		surf = ax.plot_surface(x, y, surf, 
			cmap = plt.get_cmap('jet'), shade = True, 
			rstride = 1, cstride = 1, linewidth = 0, 
				antialiased = False, zorder = 1.0)
		#ax.zaxis.set_major_locator(LinearLocator(10))
		#ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))
		self.figure.colorbar(surf, shrink = 0.75)
		return True

	def show_plot_bars(self, *args, **kwargs):		
		fig = self.figure
		ax = self.add_plot()
		#for now, assume only one bin_vectors object in the data set
		try:
			pdb.set_trace()
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
		return True

	def add_plot(self, code = 111):
		self.figure.clf()
		#ax = self.figure.add_subplot(code)
		#if projection: ax = self.figure.gca(projection='3d')
		ax = self.figure.gca()
		self.newest_ax = ax
		ax.cla()
		ax.set_xlabel(self.x_ax_title, fontsize = 18)
		ax.set_ylabel(self.y_ax_title, fontsize = 18)
		ax.set_title(self.title)
		#self.colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
		#colormap = plt.cm.gist_stern
		#colormap = plt.cm.gist_ncar
		#colormap = plt.cm.gist_earth
		#colormap = plt.cm.gist_heat
		#colormap = plt.cm.gist_rainbow
		self.colormap = plt.get_cmap('jet')
		if not self.colors or\
				len(self.colors) < len(self._plot_targets_) - 1:
			self.colors = [self.colormap(i) for i in 
				np.linspace(0, 0.9, min([self.max_line_count, 
							len(self._plot_targets_) - 1]))]

		if self.x_log: ax.set_xscale('log')
		if self.y_log: ax.set_yscale('log')
		return ax

class plot_window_toolbar(NavigationToolbar2, QtGui.QToolBar):
	message = QtCore.Signal(str)
	if hasattr(NavigationToolbar2, 'toolitems'):
		toolitems = [t for t in NavigationToolbar2.toolitems 
						if t[0] in ('Pan', 'Zoom', 'Save')]
	else: toolitems = []
	#toolitems = [t for t in NavigationToolbar2.toolitems 
	#				if t[0] in ('Pan', 'Zoom', 'Save')]
	toolitems.append(('Labels', 
		'Change the title and axes labels', 'gear', 'labels'))
	toolitems.append(('Roll', 
		'Roll through a series of plots', 'gear', 'roll'))
	toolitems.append(('RollToMovie', 
		'Create a movie from the roll function', 'gear', 'movie'))

	def __init__(self, canvas, parent, coordinates=True):
		""" coordinates: should we show the coordinates on the right? """
		self.canvas = canvas
		self.parent = parent
		self.coordinates = coordinates
		self._actions = {}
		"""A mapping of toolitem method names to their QActions"""
		QtGui.QToolBar.__init__(self, parent)
		NavigationToolbar2.__init__(self, canvas)

	def _icon(self, name):
		if name in ['move.png', 'zoom_to_rect.png', 'filesave.png']:
			return QtGui.QIcon(os.path.join(self.basedir, name))
		else: return QtGui.QIcon(lfu.get_resource_path(name))

	def _init_toolbar(self):
		self.basedir = os.path.join(
			matplotlib.rcParams['datapath'], 'images')
		for text, tooltip_text, image_file, callback in self.toolitems:
			if text is None: self.addSeparator()
			else:
				a = self.addAction(self._icon(image_file + '.png'),
				 text, getattr(self, callback))
				self._actions[callback] = a

			if callback in ['zoom', 'pan']: a.setCheckable(True)
			if tooltip_text is not None: a.setToolTip(tooltip_text)

		self.buttons = {}

		# Add the x,y location widget at the right side of the toolbar
		# The stretch factor is 1 which means any resizing of the toolbar
		# will resize this label instead of the buttons.
		if self.coordinates:
			self.locLabel = QtGui.QLabel("", self)
			self.locLabel.setAlignment(
			QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
			self.locLabel.setSizePolicy(
			QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,
			  QtGui.QSizePolicy.Ignored))
			labelAction = self.addWidget(self.locLabel)
			labelAction.setVisible(True)

		# reference holder for subplots_adjust window
		self.adj_window = None

	def _update_buttons_checked(self):
		#sync button checkstates to match active mode
		self._actions['pan'].setChecked(self._active == 'PAN')
		self._actions['zoom'].setChecked(self._active == 'ZOOM')

	def pan(self, *args):
		super(plot_window_toolbar, self).pan(*args)
		self._update_buttons_checked()

	def zoom(self, *args):
		super(plot_window_toolbar, self).zoom(*args)
		self._update_buttons_checked()

	def movie(self):
		# First set up the figure, the axis, and the plot element we want to animate
		#fig = plt.figure()
		#ax = plt.axes(xlim=(0, 2), ylim=(-2, 2))
		#line, = ax.plot([], [], lw=2)
		fig = self.figure

		# initialization function: plot the background of each frame
		def init():
			line.set_data([], [])
			return line,

		# animation function.  This is called sequentially
		def animate(i):
			x = np.linspace(0, 2, 1000)
			y = np.sin(2 * np.pi * (x - 0.01 * i))
			line.set_data(x, y)
			return line,

		# call the animator.  blit=True means only re-draw the parts that have changed.
		anim = animation.FuncAnimation(fig, animate, init_func=init,
								frames=200, interval=20, blit=True)

		# save the animation as an mp4.  This requires ffmpeg or mencoder to be
		# installed.  The extra_args ensure that the x264 codec is used, so that
		# the video can be embedded in html5.  You may need to adjust this for
		# your system: for more information, see
		# http://matplotlib.sourceforge.net/api/animation_api.html
		#anim.save('basic_animation.mp4', fps=30, 
		anim.save('basic_animation.avi', fps=30, 
				extra_args=['-vcodec', 'libx264'])

		def _roll():
			page = self.parent.get_current_page()
			if page.max_roll_dex is None:
				print 'cant roll through this data...'
				return

			page.rolling = True
			while page.roll_dex < page.max_roll_dex:
				#page.show_plot_bars()
				page.show_plot()
				time.sleep(page.roll_delay)
				page.roll_dex += 1

			page.rolling = False
			page.roll_dex = 0
			self._update_buttons_checked()

		roll_ = lgb.create_thread_wrapper(_roll)
		roll_()

	def roll(self):

		def _roll():
			page = self.parent.get_current_page()
			if page.max_roll_dex is None:
				print 'cant roll through this data...'
				return

			page.rolling = True
			while page.roll_dex < page.max_roll_dex:
				#page.show_plot_bars()
				page.show_plot()
				time.sleep(page.roll_delay)
				page.roll_dex += 1

			page.rolling = False
			page.roll_dex = 0
			self._update_buttons_checked()

		roll_ = lgb.create_thread_wrapper(_roll)
		roll_()

	def labels(self):
		page = self.parent.get_current_page()
		domain = self.parent.get_current_page().x_ax_title
		labels_dlg = change_labels_dialog(page.title, 
					page.x_ax_title, page.y_ax_title, 
					page.max_line_count, page.colors, 
						page._plot_targets_, domain, 
			page.x_log, page.y_log, page.cplot_interpolation)
		if not labels_dlg: return
		new_title,new_x_label,new_y_label,colors,xlog,ylog,cintrp = labels_dlg
		page.title = new_title
		page.x_ax_title = new_x_label
		page.x_log = xlog
		page.y_ax_title = new_y_label
		page.y_log = ylog
		page.colors = colors
		page.cplot_interpolation = cintrp
		ax = page.newest_ax
		ax.set_xlabel(new_x_label, fontsize = 18)
		ax.set_ylabel(new_y_label, fontsize = 18)
		if self.parent.plot_type in ['surface']:
			ax.set_zlabel(new_title, fontsize = 18)
		ax.set_title(new_title)
		#self.canvas.draw()
		self.parent.get_current_page().show_plot()

	def dynamic_update(self):
		self.canvas.draw()

	def set_message(self, s):
		self.message.emit(s)
		if self.coordinates:
			self.locLabel.setText(s.replace(', ', '\n'))

	def set_cursor(self, cursor):
		DEBUG = False
		if DEBUG:
			print('Set cursor', cursor)
			self.canvas.setCursor(cursord[cursor])

	def draw_rubberband(self, event, x0, y0, x1, y1):
		height = self.canvas.figure.bbox.height
		y1 = height - y1
		y0 = height - y0

		w = abs(x1 - x0)
		h = abs(y1 - y0)

		rect = [int(val)for val in (min(x0, x1), min(y0, y1), w, h)]
		self.canvas.drawRectangle(rect)

	def configure_subplots(self):
		image = os.path.join(matplotlib.rcParams['datapath'],
		 'images', 'matplotlib.png')
		dia = SubplotToolQt(self.canvas.figure, self.parent)
		dia.setWindowIcon(QtGui.QIcon(image))
		dia.exec_()

	def save_figure(self, *args):
		filetypes = self.canvas.get_supported_filetypes_grouped()
		sorted_filetypes = list(six.iteritems(filetypes))
		sorted_filetypes.sort()
		default_filetype = self.canvas.get_default_filetype()

		startpath = matplotlib.rcParams.get('savefig.directory', '')
		startpath = os.path.expanduser(startpath)
		start = os.path.join(startpath, 
			self.canvas.get_default_filename())
		filters = []
		selectedFilter = None
		for name, exts in sorted_filetypes:
			exts_list = " ".join(['*.%s' % ext for ext in exts])
			filter = '%s (%s)' % (name, exts_list)
		if default_filetype in exts:
			selectedFilter = filter
			filters.append(filter)
			filters = ';;'.join(filters)

		#fname = _getSaveFileName(self.parent, 
		#	"Choose a filename to save to",
		#	start, filters, selectedFilter)
		fname = create_dialog('Choose File', 'File?', 'file_save', 
								'Image (*.png, *.pdf)', startpath)
		fname = fname()
		if fname:
			if startpath == '':
				# explicitly missing key or empty str signals to use cwd
				matplotlib.rcParams['savefig.directory'] = startpath
			else:
				# save dir for next time
				savefig_dir = os.path.dirname(six.text_type(fname))
				matplotlib.rcParams['savefig.directory'] = savefig_dir
			try:
				self.canvas.print_figure(six.text_type(fname))
			except Exception as e:
				QtGui.QMessageBox.critical(
					self, "Error saving file", str(e),
					QtGui.QMessageBox.Ok, QtGui.QMessageBox.NoButton)

class plot_window(create_obj_dialog):

	def __call__(self, *args, **kwargs):	
		self.show()
		self.activateWindow()

	def __init__(self, *args, **kwargs):
		self.codes = range(10000000)
		self.selected_page_label = None
		self.page_labels = []
		self.pages = []

		self._all_plot_targets_ = []
		self.current_targets = []
		self.targets_layout = lgb.create_vert_box([])
		self.check_group = None

		self.surface_vector_flag = False
		self._all_plot_axes_ = []
		self._current_axes_ = []
		self.slice_layout = lgb.create_vert_box([])
		self.slice_group = None
		self.slice_selectors = []

		self.plot_type = 'lines'
		self.plot_types = kwargs['plot_types']
		mason = lgm.standard_mason(parent = self)
		if 'title' in kwargs.keys(): title = kwargs['title']
		else: title = 'Plot Window'
		create_obj_dialog.__init__(self, None, mason = mason, 
							title = title, from_sub = True)

		x, y = lfu.convert_pixel_space(256, 256)
		x_size, y_size = lfu.convert_pixel_space(1024, 768)
		geometry = (x, y, x_size, y_size)
		self.setGeometry(*geometry)
		self.figure = plt.figure()
		self.canvas = FigureCanvas(self.figure)
		self.setBackgroundRole(QtGui.QPalette.Window)
		#self.canvas.setSizePolicy(
		#	QtGui.QSizePolicy.Expanding,
		#	QtGui.QSizePolicy.Expanding)
		#self.canvas.updateGeometry()
		self.toolbar = plot_window_toolbar(self.canvas, self)
		self.set_settables()

	def get_verbosities(self):
		if self.plot_type == 'lines':
			verbs = [0, 0, 0, 0, 10, 10, 0, 10]

		elif self.plot_type == 'color':
			verbs = [0, 0, 0, 0, 0, 0, 0, 0]

		elif self.plot_type == 'surface':
			verbs = [0, 0, 0, 0, 0, 0, 0, 0]

		elif self.plot_type == 'bars':
			verbs = [0, 0, 0, 10, 10, 10, 10, 0]

		return verbs

	def set_settables(self, *args, **kwargs):
		self.widg_templates = []
		#self.plot_types = ['lines', 'color', 'surface', 'bars']
		verbs = self.get_verbosities()
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['selector', 'button_set', 'radio', 
						'selector', 'selector', 'selector'], 
				verbosities = verbs[:-2], 
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
		split = QtGui.QSplitter(QtCore.Qt.Horizontal)
		split.addWidget(panel)
		split.addWidget(lgb.central_widget_wrapper(
					content = self.targets_layout))
		split.addWidget(lgb.central_widget_wrapper(
					content = self.slice_layout))
		split.addWidget(lgb.central_widget_wrapper(
					content = lgb.create_vert_box(
					[self.canvas, self.toolbar])))

		layout = lgb.create_horz_box([split])
		self.setLayout(layout)

	def create_plot_page(self, page_label, data_container, 
			specifics, axes, filename, title, x_ax_title, y_ax_title):
		return plot_page(self, page_label, self.figure, self.canvas, 
				data_container, specifics, axes, filename, title, 
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
			self.current_axes = copy(self._all_plot_axes_[page_dex])
			self.update_check_boxes(page_dex)
			self.update_axes_slicing(page_dex)
			self.pages[page_dex]._plot_targets_ = self.current_targets
			self.pages[page_dex]._axis_labels_ = self.current_axes
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
		provide_master = True
		check_widget = lgb.create_check_boxes(append_instead, keys, 
			instances, labels, None, None, False, provide_master)

		for check in check_widget:
			dex = self.page_labels.index(self.selected_page_label)
			check.stateChanged.connect(self.pages[dex].show_plot)

		title = 'Curves Shown'
		self.check_group = QtGui.QGroupBox(title = title)
		layout = lgb.create_vert_box(check_widget)
		self.check_group.setLayout(lgb.create_vert_box([
			lgb.create_scroll_area(lgb.central_widget_wrapper(
								content = layout))]))
		self.targets_layout.addWidget(self.check_group)

	def get_surf_dex(self, page_dex):
		surf_vector_dex = None
		reduced = False
		daters = self.pages[page_dex]._data_.data
		try:
			surf_vector_dex = [dater.tag == 'surface_vector' 
							for dater in daters].index(True)
			reduced = False
		except ValueError:
			try:
				surf_vector_dex = [hasattr(dater, 'reduced') 
							for dater in daters].index(True)
				reduced = True
			except ValueError: print 'no surface_vectors found!'
		return surf_vector_dex, reduced

	def change_axis_slice(self, page_dex):
		daters = self.pages[page_dex]._data_.data
		surf_vector_dex = self.get_surf_dex(page_dex)[0]
		if not surf_vector_dex: return
		surf_vect = daters[surf_vector_dex]
		cur_slices = [sel.currentText() for sel in self.slice_selectors]
		str_defaults = [str(val) for val in surf_vect.axis_defaults]
		changed = [(not cur == def_) for cur, def_ in 
						zip(cur_slices, str_defaults)]
		changed_dex = changed.index(True)
		surf_vect.axis_defaults[changed_dex] =\
			surf_vect.axis_values[changed_dex].scalars[
				self.slice_selectors[changed_dex].currentIndex()]
		self.pages[page_dex].show_plot()

	def update_axes_slicing(self, page_dex):
		self.slice_layout.removeWidget(self.slice_group)
		if self.slice_group: self.slice_group.deleteLater()
		labels = copy(self._all_plot_axes_[page_dex])
		daters = self.pages[page_dex]._data_.data
		surf_vector_dex = self.get_surf_dex(page_dex)[0]
		if not surf_vector_dex: return
		surf_vect = daters[surf_vector_dex]
		ax_labs, ax_vals = surf_vect.axis_labels, surf_vect.axis_values
		slice_widgets = []
		self.slice_widgets = slice_widgets
		self.slice_selectors = []
		for lab, sca, def_ in zip(ax_labs, ax_vals, 
							surf_vect.axis_defaults):
			dummy = [None]*len(sca.scalars)
			selector = lgb.create_combo_box(
				sca.as_string_list(), dummy, dummy)
			if hasattr(sca.scalars, 'index'):
				initial = sca.scalars.index(def_)

			else: initial = np.nonzero(sca.scalars == def_)[0][0]
			selector.setCurrentIndex(initial)
			self.slice_selectors.append(selector)
			selector.currentIndexChanged.connect(
				lgb.create_function_with_args(
				self.change_axis_slice, (page_dex, )))
			ax_box = QtGui.QGroupBox(title = lab)
			ax_box.setLayout(lgb.create_vert_box([selector]))
			slice_widgets.append(ax_box)
			#determine if ax_box corresponds to a domain axis
			# hide it if so

		#title = 'P-Space Axis Handling'
		title = 'Data Axis Handling'
		self.slice_group = QtGui.QGroupBox(title = title)
		layout = lgb.create_vert_box(slice_widgets)
		self.slice_group.setLayout(lgb.create_vert_box([
			lgb.create_scroll_area(lgb.central_widget_wrapper(
								content = layout))]))
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
		axes = []
		for dater in data_container.data:
			if hasattr(dater, 'axis_labels'):
				self.surface_vector_flag = True
				axes.extend(dater.axis_labels)

		self._all_plot_axes_.append(axes)
		page = self.create_plot_page(new_page, data_container, 
			specifics, axes, filename, title, x_ax_title, y_ax_title)
		self.pages.append(page)

	def get_code(self):
		try: return self.codes.pop(0)
		except IndexError:
			print 'no codes left'; return 111

	def remake_plot(self):
		dex = self.page_labels.index(self.selected_page_label)
		if not self.current_targets:
			self.current_targets = copy(self._all_plot_targets_[dex])
			if not self.current_targets:
				print 'nothing to plot; renabling curves'; return

		self.update_check_boxes(dex)
		self.update_axes_slicing(dex)
		self.pages[dex]._plot_targets_ = self.current_targets
		self.hide_irrelevant_widgets()
		self.pages[dex].show_plot()

	def hide_irrelevant_widgets(self):
		verbs = self.get_verbosities()
		if self.slice_group:
			if verbs[7] > 0:
				try: self.slice_group.hide()
				except AttributeError: pass

			else:
				page = self.get_current_page()
				xy_axes = (page.x_ax_title, page.y_ax_title)
				for widg in self.slice_widgets:
					if widg.title() in xy_axes: widg.hide()
					else: widg.show()

				self.slice_group.show()

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
		self.hide_irrelevant_widgets()

	def change_y_domain(self, new_dex):
		dex = self.page_labels.index(self.selected_page_label)
		self.pages[dex].change_color_domain_y(new_dex)
		self.hide_irrelevant_widgets()

	def change_surf_target(self, new_dex):
		dex = self.page_labels.index(self.selected_page_label)
		self.pages[dex].change_color_surface_target(new_dex)
		self.hide_irrelevant_widgets()

def quick_plot_display(domain, codomains, delay = 1):
	qp = quick_plot(domain.scalars, [co.scalars for co in codomains], 
						domain.label, [co.label for co in codomains])
	time.sleep(delay)
	qp.close()

qp_fig = None
class quick_plot(QtGui.QWidget):

	def __init__(self, x, ys, x_lab, y_labs):
		super(quick_plot, self).__init__()
		global qp_fig
		if qp_fig is None: qp_fig = plt.figure()
		self.max_line_count = 20
		self.set_up_widgets()
		self.set_geometry()
		self.plot(x, ys, x_lab, y_labs)
		self.show()
		self.repaint()

	def set_up_widgets(self):
		self.canvas = FigureCanvas(qp_fig)
		self.setBackgroundRole(QtGui.QPalette.Window)
		self.toolbar = plot_window_toolbar(self.canvas, self)
		#layout = lgb.create_vert_box([self.canvas, self.toolbar])
		layout = lgb.create_vert_box([self.canvas])
		self.setLayout(layout)

	def set_geometry(self):
		x, y = lfu.convert_pixel_space(256, 256)
		x_size, y_size = lfu.convert_pixel_space(1024, 768)
		geometry = (x, y, x_size, y_size)
		self.setGeometry(*geometry)

	def plot(self, x, ys, x_lab, y_labs):

		def plot_(x, y, label):
			line = matplotlib.lines.Line2D(
				x, y, color = self.colors.pop())
			line.set_label(label)
			ax.add_line(line)

		qp_fig.clf()
		ax = qp_fig.gca()
		ax.cla()
		ax.grid(True)
		ax.set_xlabel(x_lab, fontsize = 18)
		ax.set_ylabel(y_labs[0], fontsize = 18)
		colormap = plt.get_cmap('jet')
		self.colors = [colormap(i) for i in 
			np.linspace(0, 0.9, min([self.max_line_count, len(ys)]))]
		[plot_(x, y, label) for x, y, label 
			in zip([x]*len(ys), ys, y_labs)]
		ax.axis([x.min(), x.max(), min([y.min() for y in ys]), 
								max([y.max() for y in ys])])
		ax.legend()
		self.canvas.draw()

###################
#plotting business#
###################

##########################
#parameter space business#
##########################
class trajectory_dialog(create_obj_dialog):

	def __init__(self, *args, **kwargs):
		mason = lgm.standard_mason(parent = self.parent)
		if 'title' in kwargs.keys(): title = kwargs['title']
		else: title = 'Create Trajectory Window'
		import modular_core.libgeometry as lgeo
		self.p_sp_proxy = lgeo.p_space_proxy(*args, **kwargs)
		if self.p_sp_proxy.NO_AXES_FLAG and lfu.using_gui():
			lgd.message_dialog(self.parent, 
				'Parameter Space has no axes!', 'Problem')
			self.reject()
		''''
		self.base_object = kwargs['base_object']
		self.p_space = kwargs['p_space']
		self.parent = kwargs['parent']

		self.result_string = None
		self.result = None
		self.constructed = []
		self.max_locations = 10000
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
		'''
		create_obj_dialog.__init__(self, None, mason = mason, 
							title = title, from_sub = True)
		self.set_settables()

	def set_settables(self, *args, **kwargs):
		self.widg_templates = []
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['radio'], 
				labels = [self.p_sp_proxy.comp_methods], 
				instances = [[self.p_sp_proxy]], 
				keys = [['composition_method']], 
				initials = [[self.p_sp_proxy.composition_method]],  
				box_labels = ['Composition Method']))
		self.set_up_widgets()

	def set_up_widgets(self):
		range_makers, variations = create_ranger_makers(
							self.p_sp_proxy, 'variations')
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

	def on_make(self):
		self.p_space_proxy.on_make()
		self.result = self.p_sp_proxy.constructed
		self.result_string = self.p_sp_proxy.result_string
		if self.dialoging: create_obj_dialog.on_make(self)
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
		ranges, valid = lm.make_range(self._range_)
		return ranges, valid

	def handle_rewidget(self):
		if self.rewidget and issubclass(self.inst.__class__, 
			lfu.modular_object_qt): self.inst.rewidget(True)

##########################
#parameter space business#
##########################

if __name__ == '__main__': print 'this is a library!'


