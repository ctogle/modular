import libs.modular_core.libfundamental as lfu
import libs.gui.libqtgui_masons as lgm
import libs.gui.libqtgui_bricks as lgb
import libs.gui.libqtgui_dialogs as lgd

#from PyQt4 import QtGui, QtCore
from PySide import QtGui, QtCore
import PySide

import types
import sys
import os

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

if __name__ == '__main__': 'this is a library!'




