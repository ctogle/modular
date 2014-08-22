import modular_core.libfundamental as lfu
import modular_core.gui.libqtgui_masons as lgm
import modular_core.gui.libqtgui_bricks as lgb
import modular_core.gui.libqtgui_dialogs as lgd

#from PyQt4 import QtGui, QtCore
from PySide import QtGui, QtCore
import PySide

try:
	import matplotlib
	matplotlib.rcParams['backend.qt4'] = 'PySide'
	from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as figure_canvas
	#from matplotlib.backend_bases import NavigationToolbar2 as plt_toolbar
	import matplotlib.pyplot as plt
	#import matplotlib.patches as patches
	#import matplotlib.path as path
	#from mpl_toolkits.mplot3d import axes3d, Axes3D
except ImportError:
	traceback.print_exc(file=sys.stdout)
	print 'matplotlib could not be imported! - dialogs'

import types
import sys
import os
import time

import pdb

_window_ = None

def initialize_gui(params):
	app = application(params, sys.argv)
	sys.exit(app.exec_())

class application(QtGui.QApplication):

	_content_ = []
	_standards_ = {}
	def __init__(self, params, argv):
		self.params = params
		QtGui.QApplication.__init__(self, argv)
		self.initialize(content = self._content_,
					standards = self._standards_)

	def initialize(self, *args, **kwargs):
		self.main_window = gui_window(*args, **kwargs)

class gui_window(QtGui.QMainWindow):
	#gui_window can hold any number of mobjs, and upon
	# request, can calculate the widgets of any of those
	# mobjs individually, and update its display
	def __init__(self, *args, **kwargs):
		global _window_
		_window_ = self
		super(gui_window, self).__init__()
		self.initialize(*args, **kwargs)

	def initialize(self, *args, **kwargs):
		self.mason = lgm.standard_mason(self)
		self.settables_infos = (self, )
		try: standards = kwargs['standards']
		except KeyError: standards = {}
		self.apply_standards(standards)
		self.statusBar().showMessage('Ready')
		try: self.content = kwargs['content']
		except KeyError: self.content = None
		self.set_up_widgets(*args, **kwargs)
		self.show()

	def apply_standards(self, standards):
		try: title = standards['title']
		except KeyError: title = '--'
		try: geometry = standards['geometry']
		except KeyError:
			x, y = lfu.convert_pixel_space(300, 300)
			x_size, y_size = lfu.convert_pixel_space(512, 512)
			geometry = (x, y, x_size, y_size)

		try: self.setWindowIcon(lgb.create_icon(
					standards['window_icon']))
		except KeyError: pass
		self.setWindowTitle(title)
		self.setGeometry(*geometry)

	def set_up_widg_templates(self, *args, **kwargs):
		if type(self.content) is types.ListType:
			#obliges if mobj needs widgets recalculated
			#uses the mobjs' widgets for the current widget set
			[content.set_settables(*self.settables_infos) for 
				content in self.content if content.rewidget(
						infos = self.settables_infos)]
			self.widg_templates = lfu.flatten([content.widg_templates 
						for content in self.content])
			self.menu_templates = lfu.flatten([content.menu_templates
						for content in self.content])
			self.tool_templates = lfu.flatten([content.tool_templates
						for content in self.content])

		else:
			print 'window content unrecognized; window will be empty'
			self.content = []

	def set_up_widgets(self, *args, **kwargs):
		self.set_up_widg_templates(*args, **kwargs)
		self.set_up_menubars(*args, **kwargs)
		self.set_up_toolbars(*args, **kwargs)
		layout = QtGui.QVBoxLayout()
		for template in self.widg_templates:
			if hasattr(template, 'mason'): mason = template.mason
			else: mason = self.mason
			layout.addLayout(mason.interpret_template(template))

		central_wrap = lgb.central_widget_wrapper(content = layout)
		self.setCentralWidget(central_wrap)

	def set_up_menubars(self, *args, **kwargs):
		menubar = self.menuBar()
		menubar.clear()
		self.menus = []
		added_menus = []
		for template in self.menu_templates:
			for label, action in zip(template.menu_labels, 
									template.menu_actions):
				if not label in added_menus:
					menu = menubar.addMenu(label)
					self.menus.append(menu)
					added_menus.append(label)
				
				else: menu = self.menus[added_menus.index(label)]
				menu.addAction(action)

	def set_up_toolbars(self, *args, **kwargs):
		try: [self.removeToolBar(bar) for bar in self.toolbars]
		except AttributeError: pass
		self.toolbars = []
		added_bars = []
		for template in self.tool_templates:
			for label, action in zip(template.tool_labels, 
						template.tool_actions):
				if not label in added_bars:
					toolbar = self.addToolBar(label)
					self.toolbars.append(toolbar)
					added_bars.append(label)

				else: toolbar = self.toolbars[added_bars.index(label)]
				toolbar.addAction(action)

	def on_close(self):
		lgd.message_dialog(self, 'Are you sure to quit?', 'Message', 
			if_yes = QtCore.QCoreApplication.instance().quit)

	def closeEvent(self, event):
		reply = QtGui.QMessageBox.question(self, 'Message',
			"Are you sure to quit?", QtGui.QMessageBox.Yes | 
				QtGui.QMessageBox.No, QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes: event.accept()
		else: event.ignore()

	def on_center(self):
		qr = self.frameGeometry()
		cp = QtGui.QDesktopWidget().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def on_resize(self):
		x, y = lfu.convert_pixel_space(256, 256)
		x_size, y_size = lfu.convert_pixel_space(1280, 768)
		geometry = (x, y, x_size, y_size)
		self.setGeometry(*geometry)

class plot_page(lfu.modular_object_qt):

	_inspector_is_mobj_panel_ = True

	def __init__(self, parent, pagenum, data, targs, 
			title, xtitle, ytitle, filename, **kwargs):
		#self.impose_default('targets', [], **kwargs)
		#ptypes = ['lines', 'color', 'surface', 'bars']
		#self.impose_default('plot_type', 'lines', **kwargs)
		#self.impose_default('plot_types', ptypes, **kwargs)
		self.pagenum = pagenum
		self.title = title
		self.xtitle = xtitle
		self.ytitle = ytitle
		self.x_log = False
		self.y_log = False
		self.max_line_count = 20
		self.colors = []
		self.cplot_interpolation = 'nearest'
		#Acceptable interpolations are:
		# 'none', 'nearest', 'bilinear', 'bicubic', 'spline16', 'spline36', 
		# 'hanning', 'hamming', 'hermite', 'kaiser', 'quadric', 'catrom', 
		# 'gaussian', 'bessel', 'mitchell', 'sinc', 'lanczos'
		self.fullfilename = filename
		self.filename = filename.split(os.path.sep)[-1]
		self.targs = targs[:]
		self.active_targs = targs[:]
		if data.data: self.xdomain = data.data[0].label
		else: self.xdomain = xtitle
		if data.data: self.ydomain = data.data[0].label
		else: self.ydomain = ytitle
		if data.data: self.zdomain = data.data[0].label
		else: self.zdomain = title
		label = ' : '.join([str(pagenum), self.filename])
		lfu.modular_object_qt.__init__(self, 
			label = label, data = data, parent = parent)

	def get_targets(self):
		return self.targs

	def get_title(self):
		return self.title
	def set_title(self, new):
		self.title = new
		qplot = self.qplot[0]
		qplot.user_title = new

	def get_xtitle(self):
		return self.xtitle
	def set_xtitle(self, new):
		self.xtitle = new
		qplot = self.qplot[0]
		qplot.user_xtitle = new

	def get_ytitle(self):
		return self.ytitle
	def set_ytitle(self, new):
		self.ytitle = new
		qplot = self.qplot[0]
		qplot.user_ytitle = new

	def get_newest_ax(self):
		ax = self.qplot[0].newest_ax
		return ax

	def redraw_plot(self, xlab = None, ylab = None, title = None):
		qplot = self.qplot[0]
		data = self.data
		data.xdomain = self.parent.xdomain
		data.ydomain = self.parent.ydomain
		data.zdomain = self.parent.zdomain
		data.active_targs = self.parent.active_targs
		ptype = self.parent.plot_type
		qplot.plot(data, xlab, ylab, title, ptype = ptype)

	def show_plot(self):
		self.redraw_plot(self.get_xtitle(), 
			self.get_ytitle(), self.get_title())

	def set_settables(self, *args, **kwargs):
		window = args[0]
		toolbar_funcs = [window.get_current_page]
		data = self.data
		self.handle_widget_inheritance(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['plot'], 
				keep_frame = [True], 
				instances = [[
					self.parent.figure, 
					self.parent.canvas]], 
				handles = [(self, 'qplot')], 
				callbacks = [toolbar_funcs], 
				datas = [data]))
		lfu.modular_object_qt.set_settables(
			self, *args, from_sub = True)

class plot_window(lfu.modular_object_qt):

	def __init__(self, *args, **kwargs):
		self.impose_default('selected_page_label', None, **kwargs)
		self.impose_default('page_labels', [], **kwargs)
		self.impose_default('pages', [], **kwargs)
		self.impose_default('title', 'Plot Window', **kwargs)
		self.impose_default('targs', [], **kwargs)
		ptypes = ['lines', 'color', 'surface', 'bars']
		self.impose_default('plot_type', 'lines', **kwargs)
		self.impose_default('plot_types', ptypes, **kwargs)
		self.impose_default('roll_dex', None, **kwargs)
		self.impose_default('max_roll_dex', None, **kwargs)
		self.impose_default('roll_delay', 0.25, **kwargs)

		x, y = lfu.convert_pixel_space(256, 256)
		x_size, y_size = lfu.convert_pixel_space(1024, 768)
		self._geometry_ = (x, y, x_size, y_size)

		self.mason = lgm.standard_mason()
		self.figure = plt.figure()
		self.canvas = figure_canvas(self.figure)
		lfu.modular_object_qt.__init__(self, *args, **kwargs)

	def __call__(self, *args, **kwargs):
		page = self.get_current_page()
		self.active_targs = page.active_targs
		self.xdomain = page.xdomain
		self.ydomain = page.ydomain
		self.zdomain = page.zdomain
		#if not self.check_selection_consistency():
		#	print 'pages options are not consistent:\
		#		 cannot propagate selections...'
		self._display_interface_(self.mason)

	#def check_selection_consistency(self):
	#	active = [pg.active_targs == self.active_targs for pg in self.pages]
	#	xdom = [pg.xdomain == self.xdomain for pg in self.pages]
	#	ydom = [pg.ydomain == self.ydomain for pg in self.pages]
	#	zdom = [pg.zdomain == self.zdomain for pg in self.pages]
	#	consistent = [not False in li for li in [active, xdom, ydom, zdom]]
	#	return not False in consistent

	def get_current_page(self):
		if self.selected_page_label == 'None': return None
		pdex = self.page_labels.index(self.selected_page_label)
		return self.pages[pdex]

	def using_surfaces(self):
		return self.plot_type in ['surface', 'color']

	def set_up_widgets(self):
		current_page = self.get_current_page()
		if self.using_surfaces(): self.update_slice_panel() 
		if not current_page is None: current_page.redraw_plot()

	def set_plot_info(self, dcontainer, filename, specs, title = 'title', 
			x_ax_title = 'xtitle', y_ax_title = 'ytitle'):
		pagenum = len(self.pages) + 1
		self.pages.append(plot_page(self,pagenum,dcontainer,specs,
				title,x_ax_title,y_ax_title,filename))
		self.page_labels.append(self.pages[-1].label)
		self.targs += self.pages[-1].targs
		self.targs = lfu.uniqfy(self.targs)
		if not self.selected_page_label:
			self.selected_page_label = self.pages[-1].label

	def roll_pages(self):
		cata = self._catalog_[0].children()[0]
		sele = cata.selector
		rdelay = 0.02
		rdex = 1
		max_rdex = len(cata.pages) - 1
		while rdex <= max_rdex:
			sele.setCurrentIndex(rdex)
			cata.pages[rdex].repaint()
			rdex += 1
			time.sleep(rdelay)

	def update_slice_panel(self):
		pan = self.slice_panel[0]
		pdb.set_trace()

	def make_slice_templates(self):
		page = self.get_current_page()
		data = page.data
		pdb.set_trace()
		slice_templates = []
		for lab, sca, def_ in zip(ax_labs, ax_vals, ax_defs):
			#slice_templates.append(
			#	lgm.interface_template_gui(
			#		widgets = ['selector'], 
			#		labels = [[]]
			#		))
			print lab, def_, sca
		return slice_templates

	def set_settables(self, *args, **kwargs):
		self.handle_widget_inheritance(*args, **kwargs)
		[pg.set_settables(self, **kwargs) for pg in self.pages]
		self.widg_templates.append(
			lgm.interface_template_gui(
				layout = 'grid', 
				panel_position = (0,3), 
				widgets = ['mobj_catalog'], 
				instances = [[self.pages,self]], 
				keys = [['selected_page_label']], 
				handles = [(self, '_catalog_')], 
				callbacks = [[(self.set_up_widgets,), 
						self.roll_pages]], 
				minimum_sizes = [[(1024, 768)]], 
				initials = [[self.selected_page_label]]))
		self.widg_templates.append(
			lgm.interface_template_gui(
				panel_position = (0,0), 
				widgets = ['selector'], 
				layout = 'vertical', 
				labels = [self.targs], 
				initials = [[self.xdomain]], 
				instances = [[self]], 
				keys = [['xdomain']], 
				refresh = [[True]], 
				window = [[self]], 
				box_labels = ['X-Domain']))
		self.widg_templates[-1] +=\
			lgm.interface_template_gui(
				widgets = ['selector'], 
				labels = [self.targs], 
				initials = [[self.ydomain]], 
				instances = [[self]], 
				keys = [['ydomain']], 
				refresh = [[True]], 
				window = [[self]], 
				box_labels = ['Y-Domain'])
		self.widg_templates[-1] +=\
			lgm.interface_template_gui(
				widgets = ['selector'], 
				labels = [self.targs], 
				initials = [[self.zdomain]], 
				instances = [[self]], 
				keys = [['zdomain']], 
				refresh = [[True]], 
				window = [[self]], 
				box_labels = ['Surface Target'])
		self.widg_templates[-1] +=\
			lgm.interface_template_gui(
				widgets = ['radio'], 
				instances = [[self]], 
				keys = [['plot_type']], 
				initials = [[self.plot_type]], 
				labels = [self.plot_types], 
				refresh = [[True]], 
				window = [[self]], 
				box_labels = ['Plot Type'])
		self.widg_templates.append(
			lgm.interface_template_gui(
				panel_position = (0,1), 
				widgets = ['check_set'], 
				callbacks = [[self.set_up_widgets]], 
				instances = [[self]], 
				keys = [['active_targs']], 
				labels = [self.targs], 
				box_labels = ['Targets'], 
				append_instead = [True]))
		if not self.using_surfaces():
			slice_templates = []
			slice_templates.append(
				lgm.interface_template_gui(
					widgets = ['image'], 
					verbosities = [10], 
					paths = [lfu.get_resource_path('gear.png')], 
					))
			slice_verb = 10
		else:
			slice_templates = self.make_slice_templates()
			slice_verb = 1
		self.widg_templates.append(
			lgm.interface_template_gui(
				panel_position = (0,2), 
				widgets = ['panel'], 
				verbosities = [slice_verb], 
				handles = [(self, 'slice_panel')], 
				box_labels = ['Additional Axis Handling'], 
				templates = [slice_templates]))
		lfu.modular_object_qt.set_settables(
			self, *args, from_sub = True)

if __name__ == '__main__': 'this is a library!'





