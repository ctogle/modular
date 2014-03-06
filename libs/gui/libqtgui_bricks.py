import libs.modular_core.libfundamental as lfu

from PySide import QtGui, QtCore
QtGui.QToolTip.setFont(QtGui.QFont('SansSerif', 20))
#QWebView: a WebKit based control to render HTML/CSS/XML/XSLT pages

code_font = QtGui.QFont()
code_font.setFamily('Sans')
code_font.setStyleHint(QtGui.QFont.Monospace);
code_font.setFixedPitch(True);
code_font.setPointSize(10);
code_metrics = QtGui.QFontMetrics(code_font);

#for all uses of lfu.debug_filter
debug_filter_thresh = 5

import types
import ctypes
import glob
import os
import sys
from math import sqrt as sqrt
import threading

import pdb

def set_screensize():
	_screensize_ = QtGui.QApplication.desktop().availableGeometry()
	return _screensize_

def generate_add_function(base_class, parent = None, 
						wheres = [], rewidget = True):

	def add_():
		new = base_class(parent = parent)
		for whar in wheres:
			if type(whar) is types.ListType: whar.append(new)
			elif type(whar) is types.DictionaryType:
				whar[new.label] = new

			else: 'cant add new', base_class, 'to', whar

		if rewidget and not parent is None: parent.rewidget(True)

	return add_

def generate_remove_function(get_selected, parent = None, 
							wheres = [], rewidget = True):

	def remove_():
		select = get_selected()
		if select:
			for whar in wheres:
				if type(whar) is types.ListType:
					try: whar.remove(select)
					except ValueError: pass
					select._destroy_()

				elif type(whar) is types.DictionaryType:
					#del whar[select.label]
					if issubclass(select.__class__, 
							lfu.modular_object_qt):
						whar[select.label]._destroy_()

					else: del whar[select.label]

				else: 'cant remove selected', select, 'from', whar

		if rewidget and not parent is None: parent.rewidget(True)

	return remove_

def generate_selected_function(mobjs, options, handle, offset = 0):

	def select_():
		select = handle[0].__dict__[handle[1]]
		#this is a hack!
		select = select[0].children()[1].currentIndex() - offset
		try: select = lfu.grab_mobj_by_name(options[select], mobjs)
		except IndexError: return
		return select

	return select_

def get_supported_image_extensions():
	formats = QtCore.QImageReader().supportedImageFormats()
	#convert the QByteArrays to strings
	return [str(fmt) for fmt in formats]

def qsize(width, height):
	return QtCore.QSize(width, height)

def create_style(style):
	if style == 'windows': return QtGui.QStyleFactory.create('Windows')
	if style == 'xp': return QtGui.QStyleFactory.create('WindowsXP')
	if style == 'vista':
		return QtGui.QStyleFactory.create('WindowsVista')

	if style == 'motif': return QtGui.QStyleFactory.create('Motif')
	if style == 'cde': return QtGui.QStyleFactory.create('CDE')
	if style == 'plastique':
		return QtGui.QStyleFactory.create('Plastique')

	if style == 'clean':
		return QtGui.QStyleFactory.create('Cleanlooks')

def create_color(r = 0, g = 0, b = 0):
	return QtGui.QColor(r, g, b)

def create_qimage(path):
	image = QtGui.QImage(path)
	image.setSizePolicy(QtGui.QSizePolicy.Expanding,
						QtGui.QSizePolicy.Expanding)
	return image

def create_pixmap(path, wrap = True):
	pix = QtGui.QPixmap(path)
	if wrap:
		wrap = QtGui.QLabel()
		wrap.setPixmap(pix)
		return wrap

	else: return pix

def create_icon(icon_path):
	icon = QtGui.QIcon(icon_path)
	return icon

def create_spin_box(parent = None, double = False, min_val = None, 
				max_val = None, sing_step = None, initial = None, 
					instance = None, key = None, rewidget = True, 
												decimals = 10):

	def spin_function():
		if type(instance) is types.DictionaryType:
			instance[key] = spin.value()

		else: instance.__dict__[key] = spin.value()
		if rewidget and issubclass(instance.__class__, 
			lfu.modular_object_qt): instance.rewidget(True)

	if parent is None and double:
		spin = QtGui.QDoubleSpinBox()
		spin.setDecimals(decimals)
		if max_val is not None: top = max_val
		else: top = sys.float_info.max
		if min_val is not None: bottom = min_val
		else: bottom = -sys.float_info.max

	elif parent is None and not double:
		spin = QtGui.QSpinBox()
		if max_val is not None: top = max_val
		else: top = sys.maxint
		if min_val is not None: bottom = min_val
		else: bottom = 0

	if sing_step is not None: step = sing_step
	else: step = 1

	spin.setMinimum(bottom)
	spin.setMaximum(top)
	spin.setSingleStep(step)

	if initial is not None: spin.setValue(initial)
	else: spin.setValue(1)
	if not instance is None and not key is None:
		spin.valueChanged.connect(spin_function)

	return spin

def create_radios(parent = None, options = [], title = '', 
			initial = None, instance = None, key = None, 
		rewidget = True, refresh = None, window = None):

	def apply_refresh(rads):
		if refresh and hasattr(window, 'set_up_widgets'):
			bind = create_reset_widgets_function(window)
			[rad.clicked.connect(bind) for rad in rads]

	def make_select_func(dex):

		def rad_select_func():
			instance.__dict__[key] = options[dex]
			if rewidget and issubclass(instance.__class__, 
				lfu.modular_object_qt): instance.rewidget(True)

		return rad_select_func

	if parent is None:
		radios = [QtGui.QRadioButton(opt) for opt in options]

	else: radios = [QtGui.QRadioButton(opt, parent) for opt in options]
	if initial in options:
		radios[options.index(initial)].setChecked(True)

	if not (key is None or instance is None):
		[rad.clicked.connect(make_select_func(dex)) 
				for dex, rad in enumerate(radios)]

	apply_refresh(radios)
	group = QtGui.QGroupBox(title = title)
	layout = create_vert_box(radios)
	group.setLayout(layout)
	return group

def create_action(parent = None, label = '', icon = None, 
		shortcut = None, statustip = None, bindings = None):
	if parent is not None: act = QtGui.QAction(label, parent)
	else: act = QtGui.QAction(label)
	if shortcut is not None: act.setShortcut(shortcut)
	if statustip is not None: act.setStatusTip(statustip)
	if bindings is not None:
		if type(bindings) is types.ListType:
			[act.triggered.connect(bind) for bind in bindings]

		else: act.triggered.connect(bindings)

	if icon is not None:
		if type(icon) is types.StringType: icon = create_icon(icon)
		act.setIcon(icon)

	return act

def create_function_with_args(func, func_args = ()):
	def wrap(): func(*func_args)
	return wrap

def create_mobj_rewidget_function(mobj):
	def rewidg():
		if not hasattr(mobj, 'rewidget'):
			if not hasattr(mobj, 'parent'): pass
			elif mobj.parent: mobj.parent.rewidget(True)

		else: mobj.rewidget(True)

	return rewidg

def create_reset_widgets_function(window):
	def reset_widgets_function(): window.set_up_widgets()
	return reset_widgets_function

#function is either a function or a list of functions
# func args is either a tuple or a list of tuples
#refreshes the widgets of the window after function(s) are called
def create_reset_widgets_wrapper(window, function, func_args = ()):

	def wrapped_function():
		function(*func_args)
		window.set_up_widgets()

	def wrapped_functions():
		for func, fargs in zip(function, func_args): func(*fargs)
		window.set_up_widgets()

	if type(function) is types.ListType:
		if not type(func_args) is types.ListType:
			func_args = [func_args]*len(function)

		return wrapped_functions

	else: return wrapped_function

def create_thread_wrapper(function, func_args = ()):

	def wrapped_function():
		t = threading.Thread(target = function, args = func_args)
		t.start()

	def wrapped_functions():
		#for func, fargs in zip(function, func_args): func(*fargs)
		#window.set_up_widgets()
		print 'thread wrapped multiple functions not yet supported'

	if type(function) is types.ListType:
		if not type(func_args) is types.ListType:
			func_args = [func_args]*len(function)

		return wrapped_functions

	else: return wrapped_function

def consider_alignment(widget, alignment = 'center'):
	if alignment == 'center': align = QtCore.Qt.AlignCenter
	elif alignment == 'left': align = QtCore.Qt.AlignLeft
	elif alignment == 'right': align = QtCore.Qt.AlignRight
	else: 
		print 'alignment unrecognized; defaulting to "center"'
		align = QtCore.Qt.AlignCenter

	widget.setAlignment(align)

def create_label(parent = None, text = None, pixmap_path = None, 
						word_wrap = False, alignment = 'center'):
	if text is None: text = ''
	if parent is not None: label = QtGui.QLabel(text, parent)
	else: label = QtGui.QLabel(text)
	label.setWordWrap(word_wrap)
	consider_alignment(label, alignment)
	if pixmap_path is not None:
		label.setPixmap(create_pixmap(pixmap_path))

	#label.setGeometry(160, 40, 80, 30)
	return label

def create_progress_bar(parent = None):
	if parent is not None: pbar = QtGui.QProgressBar(parent)
	else: pbar = QtGui.QProgressBar()
	return pbar

def create_timer(parent = None):
	'''example function for binding
	def timerEvent(self, e):
		if self.step >= 100:
			self.timer.stop()
			self.btn.setText('Finished')
			return
		self.step = self.step + 1
		self.pbar.setValue(self.step)
	'''
	#self.timer.start(100, self)
	if parent is not None: timer = QtCore.QBasicTimer(parent)
	else: timer = QtCore.QBasicTimer()
	return timer

def create_calender(parent = None, show_date_func = None):

	def show_date(self, date): 
		print date.toString()

	if parent is not None: calender = QtGui.QCalendarWidget(parent)
	else: calender = QtGui.QCalendarWidget()
	calender.setGridVisible(True)
	if show_date_func is not None:
		calender.clicked[QtCore.QDate].connect(show_date_func)

	#date = calender.selectedDate()
	#date.toString()
	return calender

def create_panel(templates, mason, collapses = False, layout = 'grid'):

	def get_position(safe, positions):
		for pos in safe:
			if not pos in positions: return pos

	if layout == 'grid':
		try: sq = sqrt(len(templates))
		except TypeError: return QtGui.QLabel()
		if int(sq) == sq: sq = int(sq)
		else: sq = int(sq + 1.0)
		safe_positions = [(x, y) for x in range(sq) for y in range(sq)]

	elif layout == 'vertical':
		safe_positions = [(x, 0) for x in range(len(templates))]

	elif layout == 'horizontal':
		safe_positions = [(0, y) for y in range(len(templates))]

	scroll_flag = False
	widgets = []
	positions = []
	spans = []
	for dex, template in enumerate(templates):
		try:
			scroll_flag = template.panel_scrollable
			memory = template.panel_scroll_memory

		except AttributeError: memory = None
		if hasattr(template, 'mason'): temp_mason = template.mason
		else: temp_mason = mason
		try:
			posit = template.panel_position
			if posit in positions:
				posit = get_position(safe_positions, positions)

		except AttributeError:
			posit = get_position(safe_positions, positions)

		try: span = template.panel_span
		except AttributeError: span = (1, 1)
		widg = central_widget_wrapper(content =\
			temp_mason.interpret_template(template))
		try:
			title = template.panel_label
			group = QtGui.QGroupBox(title = title)
			layout = create_vert_box([widg])
			group.setLayout(layout)
			widgets.append(group)

		except AttributeError: widgets.append(widg)
		positions.append(posit)
		spans.append(span)

	layout = create_grid_box(widgets, positions, spans, spacing = 0)
	#try: collapses = template.collapses
	#except AttributeError: collapses = False
	panel = central_widget_wrapper(
		content = layout, collapses = collapses)
	if scroll_flag: panel = create_scroll_area(panel, None, memory)
	return panel

def create_check_spin_list(inst, key, labels):
	check_spin = [check_spin_widget(
			label, inst, key, labels) 
				for label in labels]
	return check_spin

class check_spin_widget(QtGui.QLabel):

	def __init__(self, label, inst, key, labels, parent = None, 
						min_val = 1, max_val = 1000000, 
			step = 1, spin_init = 1, rewidget = True):
		super(check_spin_widget, self).__init__(parent)
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		self.rewidget = rewidget
		self.parent = parent
		self.label = label
		self.labels = labels
		self.inst = inst
		self.key = key
		self.check = QtGui.QCheckBox(self.label)
		self.check.stateChanged.connect(self.check_func_append)
		self.spin = QtGui.QSpinBox()
		self.spin.setMinimum(min_val)
		self.spin.setMaximum(max_val)
		self.spin.setSingleStep(step)
		self.spin.setValue(spin_init)
		self.spin.valueChanged.connect(self.spin_function)
		self.setLayout(create_horz_box([self.spin, self.check]))
		longest_label = max([len(item) for item in labels])
		set_sizes_limits([[self]], 
			[[(max([50*longest_label, 100]), 40)]])
		self.set_initial_state()

	def set_initial_state(self):
		labels = self.get_label_list()
		if self.label in labels:
			self.check.setCheckState(QtCore.Qt.Checked)
			self.spin.setValue(self.get_value_list()
						[labels.index(self.label)])

	def get_value_list(self):
		tup_list = self.inst.__dict__[self.key]
		values = [tup[1] for tup in tup_list]
		return values

	def get_label_list(self):
		tup_list = self.inst.__dict__[self.key]
		labels = [tup[0] for tup in tup_list]
		return labels

	def check_func_append(self, current_value):
		labels = self.get_label_list()
		if not current_value:
			if self.label in labels:
				self.inst.__dict__[self.key].remove(
					(self.label, self.spin.value()))

			self.handle_rewidget()

		else:
			if not self.label in labels:
				self.inst.__dict__[self.key].append(
					(self.label, self.spin.value()))

			self.handle_rewidget()

	def spin_function(self):
		if self.check.checkState():
			labels = self.get_label_list()
			dex = labels.index(self.label)
			self.inst.__dict__[self.key][dex] =\
				(self.label, self.spin.value())

		self.handle_rewidget()

	def handle_rewidget(self):
		if self.rewidget and issubclass(self.inst.__class__, 
			lfu.modular_object_qt): self.inst.rewidget(True)

def create_file_name_box(inst, key, label, initial, exts = '', 
		directory = False, init_dir = None, rewidget = True, 
				inst_is_list = None, inst_is_dict = None, 
								path_instead = False):

	def apply_to_inst(*args, **kwargs):
		dat = args[0]
		if inst_is_dict:
			if inst_is_dict[0]: inst[key] = dat

		else: inst.__dict__[key] = dat

	def button_bind_file():
		fidlg = lfu.gui_pack.lgd.create_dialog(
			'Choose File', 'File?', 'file', exts, init_dir)
		file_ = fidlg()
		if file_ is not None:
			file_ = file_[file_.rfind('/') + 1:]
			apply_to_inst(file_)
			#inst.__dict__[key] = file_
			text_box.setText(file_)

	def button_bind_directory():
		fidlg = lfu.gui_pack.lgd.create_dialog(
			'Choose File', 'File?', 'directory', None, init_dir)
		file_ = fidlg()
		if file_ is not None:
			apply_to_inst(file_)
			#inst.__dict__[key] = file_
			text_box.setText(file_)

	def button_bind_path():
		fidlg = lfu.gui_pack.lgd.create_dialog(
			'Choose File', 'File?', 'file', exts, init_dir)
		file_ = fidlg()
		if file_ is not None:
			apply_to_inst(file_)
			#inst.__dict__[key] = file_
			text_box.setText(file_)

	if init_dir is None: init_dir = os.getcwd()
	text_box = create_text_box(instance = inst, key = key, 
			initial = initial, bind_events = ['changed'], 
		rewidget = rewidget, inst_is_dict = inst_is_dict)
	if path_instead: button_bind = button_bind_path
	else:
		if directory: button_bind = button_bind_directory
		else: button_bind = button_bind_file

	button = create_buttons([button_bind], [label])[0]
	layout = create_vert_box([text_box, button])
	file_name_box = central_widget_wrapper(content = layout)
	return file_name_box

def set_tooltips(widgs, tooltips):
	if tooltips is not None:
		for widg_group, tip_group in zip(widgs, tooltips):
			if tip_group is not None:
				for widg, tip in zip(widg_group, tip_group):
					widg.setToolTip(''.join(['<b>', tip, '</b>']))

def set_sizes_limits(widgs, sizes, limit = 'min'):
	if sizes is not None:
		for widg_group, size_group in zip(widgs, sizes):
			if size_group is not None:
				for widg, size in zip(widg_group, size_group):
					if size is not None:
						w_size, h_size = lfu.convert_pixel_space(*size)
						#if one dimension is None...
						#widg.setMinimumWidth(285)
						#widg.setMinimumHeight(285)
						if limit == 'min':
							#widg.setMinimumSize(qsize(*size))
							widg.setMinimumSize(qsize(w_size, h_size))

						elif limit == 'max':
							#widg.setMaximumSize(qsize(*size))
							widg.setMinimumSize(qsize(w_size, h_size))

def setup_layout_widget(layout, group, spacers = None):
	if layout == 'vertical': box = create_vert_box
	elif layout == 'horizontal': box = create_horz_box
	elif layout == 'grid': box = create_vert_box
	elif not layout: box = create_vert_box
	return box(group, spacers = spacers)

def consider_widgets_and_layouts(widgets, 
			layouts, layout_widg, spacers):
	if spacers is not None: spacers.append(None)
	else: spacers = [None]*len(widgets)
	if layouts is not None:
		for layout, widget_group in zip(layouts, widgets):
			layout_widg.addLayout(setup_layout_widget(
						layout, widget_group, spacers))

	else:
		for widg, space in zip(widgets, spacers):
			layout_widg.addWidget(widg)
			if space is not None: layout_widg.addStretch(int(space))

#if layouts are provided, each item 
# in widgets should be a list of widgets
#if layouts are not provided, 
# widgets should be a flat list of widgets
def create_vert_box(widgets, layouts = None, spacers = None):
	vert_layout = QtGui.QVBoxLayout()
	consider_widgets_and_layouts(widgets, 
		layouts, vert_layout, spacers)
	return vert_layout

def create_horz_box(widgets, layouts = None, spacers = None):
	horz_layout = QtGui.QHBoxLayout()
	consider_widgets_and_layouts(widgets, 
		layouts, horz_layout, spacers)
	return horz_layout

def create_grid_box(widgets, in_positions = [], spans = [], 
							spacing = 10, layouts = None):

	def check_spans(spans):

		def check(val):
			if val is None: return (1, 1)
			else: return val

		spans = [check(span) for span in spans]
		missing = len(widgets) - len(spans)
		if missing > 0: spans.extend([(1, 1)]*missing)
		return spans

	def get_positions():
		if len(in_positions) >= len(widgets): return in_positions
		else:
			sq = sqrt(len(widgets))
			if int(sq) == sq: sq = int(sq)
			else: sq = int(sq + 1.0)
			return [(x, y) for x in range(sq) for y in range(sq)]

	grid = QtGui.QGridLayout()
	grid.setSpacing(spacing)
	positions = get_positions()
	spans = check_spans(spans)
	if not layouts:
		for widg, position, span in zip(widgets, positions, spans):
			grid.addWidget(widg, position[0], position[1], 
										span[0], span[1])

	else:
		for layout, widget_group, position, span in zip(
					layouts, widgets, positions, spans):
			grid.addLayout(setup_layout_widget(layout, widget_group), 
						position[0], position[1], span[0], span[1])

	return grid

def create_splitter_box(parent = None, templates = [], mason = None, 
			direction = 'vertical', scroll = False, memory = None):
	if direction == 'vertical': split_dir = QtCore.Qt.Vertical
	elif direction == 'horizontal': split_dir = QtCore.Qt.Horizontal
	else: split_dir = QtCore.Qt.Horizontal
	if parent is not None: split = QtGui.QSplitter(split_dir, parent)
	else: split = QtGui.QSplitter(split_dir)
	for template in templates:
		if hasattr(template, 'mason'): temp_mason = template.mason
		else: temp_mason = mason
		if hasattr(template, 'panel_collapses'):
			collapse = template.panel_collapses

		else: collapse = False
		if hasattr(template, 'panel_scroll_memory'):
			memory = template.panel_scroll_memory

		split.addWidget(central_widget_wrapper(
			content = temp_mason.interpret_template(template), 
										collapses = collapse))

	if scroll: return create_scroll_area(split, None, memory)
	return split

#this is a two column list control?
def create_form_box(left_entries, right_entries):
	form_layout = QFormLayout()
	[form_layout.addRow(left, right) for left, right 
				in zip(left_entries, right_entries)]

class image_button(QtGui.QLabel):
	clicked = QtCore.Signal()

	def __init__(self, image_path, parent = None):
		super(image_button, self).__init__(parent)
		self.setPixmap(image_path)
		frame_style = QtGui.QFrame.Raised | QtGui.QFrame.Box
		self.setFrameStyle(frame_style)
		self.setFocusPolicy(QtCore.Qt.StrongFocus)

	def focusInEvent(self, event):
		frame_style = QtGui.QFrame.Sunken | QtGui.QFrame.Panel
		self.setFrameStyle(frame_style)

	def focusOutEvent(self, event):
		frame_style = QtGui.QFrame.Raised | QtGui.QFrame.Box
		self.setFrameStyle(frame_style)

	def keyPressEvent(self, event):
		self.clicked.emit()

	def mousePressEvent(self, event):
		self.clicked.emit()

def create_image_button(path, binding):
	button = image_button(path)
	button.clicked.connect(binding)
	return button

def create_buttons(bindings, labels = None, 
		icons = None, bind_events = None):

	def with_or_without_icon(icon, label):
		if not type(label) is types.StringType and\
			not type(label) is types.UnicodeType:
				pdb.set_trace()

		if icon is None: return QtGui.QPushButton(label)
		else:
			if type(icon) is types.StringType: icon = create_icon(icon)
			#if type(icon) is types.StringType: icon = create_qimage(icon)
			btn = QtGui.QPushButton(icon, label)
			#pdb.set_trace()
			#btn.setIconSize(icon.size())
			return btn

	def do_binding(btn, evt, func):
		if evt is not None:
			if evt == 'pressed': btn.pressed.connect(func)
			elif evt == 'released': btn.released.connect(func)
			elif evt == 'clicked': btn.clicked.connect(func)
			else:
				print 'bind event:', evt,\
					' unrecognized; using "clicked"'
				btn.clicked.connect(func)

		else: btn.clicked.connect(func)

	def do_bindings(btn, evt, func):
		if type(func) is types.ListType:
			for ev, fu in zip(evt, func): do_binding(btn, ev, fu)

		else:
			do_binding(btn, evt, func)

	#btn.setSizePolicy(QtGui.QSizePolicy.Fixed,
	# QtGui.QSizePolicy.Fixed)
	#btn.setCheckable(True)	#do i need to support this?
	#[button.resize(button.sizeHint()) for button in buttons]
	if icons and not labels:
		buttons = [create_image_button(icon, bind) 
			for icon, bind in zip(icons, bindings)]
		return buttons

	if labels is None: labels = ['']*len(bindings)
	if icons is None: icons = [None]*len(bindings)
	if bind_events is None: bind_events = [None]*len(bindings)
	#if icons is shorter/longer than labels - 
	# this neglects to make some of the buttons
	buttons = [with_or_without_icon(icon, label) for 
				icon, label in zip(icons, labels)]
	[do_bindings(button, bind_event, binding) for 
		button, bind_event, binding in 
			zip(buttons, bind_events, bindings)]
	return buttons

def create_slider(instance, key, orientation = 'horizontal', 
				initial = None, minimum = -5, maximum = 5, 
				tick_position = None, tick_interval = None, 
						bind_events = [], bindings = []):
	'''
	the currently set tick position and interval can 
	be queried using the PySide.QtGui.QSlider.tickPosition() and 
	PySide.QtGui.QSlider.tickInterval() functions, respectively.
	Signal 	Description
	PySide.QtGui.QAbstractSlider.valueChanged()
	Emitted when the slider's value has changed. 
	The tracking() determines whether this signal 
	is emitted during user interaction.
	PySide.QtGui.QAbstractSlider.sliderPressed()
	Emitted when the user starts to drag the slider.
	PySide.QtGui.QAbstractSlider.sliderMoved()
	Emitted when the user drags the slider.
	PySide.QtGui.QAbstractSlider.sliderReleased()
	Emitted when the user releases the slider.
	'''
	def slide_function(integer):
		instance.__dict__[key] = integer

	if orientation == 'horizontal': orient = QtCore.Qt.Horizontal
	elif orientation == 'vertical': orient = QtCore.Qt.Vertical
	if initial is None: initial = 0
	if initial not in range(minimum, maximum): initial = maximum
	slide = QtGui.QSlider(orient)
	slide.setMinimum(minimum)
	slide.setMaximum(maximum)
	if bindings is not None and bind_events is not None:
		if len(bindings) < len(bind_events):
			bindings.extend([slide_function for x in range(
						len(bind_events) - len(bindings))])

	if not bind_events: slide.valueChanged[int].connect(slide_function)
	else:
		for bi_ev, bi in zip(bind_events, bindings):
			if bi_ev == 'changed':
				slide.valueChanged[int].connect(bi)

			elif bi_ev == 'released':
				slide.sliderReleased.connect(bi)

			elif bi_ev == 'moved':
				slide.sliderMoved.connect(bi)

			elif bi_ev == 'pressed':
				slide.sliderPressed.connect(bi)

	if tick_position == 'both': tick_position = slide.TicksBothSides
	elif tick_position == 'above': tick_position = slide.TicksAbove
	elif tick_position == 'below': tick_position = slide.TicksBelow
	elif tick_position == 'left': tick_position = slide.TicksLeft
	elif tick_position == 'right': tick_position = slide.TicksRight
	elif tick_position is None: tick_position = slide.NoTicks
	if tick_interval is None: tick_interval = 1
	slide.setTickPosition(tick_position)
	slide.setTickInterval(tick_interval)
	slide.setSingleStep(tick_interval)
	#slide.sliderChange(slide.SliderValueChange)
	#slide.initStyleOption(QtGui.QStyleOptionSlider())
	#	sld.setFocusPolicy(QtCore.Qt.NoFocus)
	#slide.setGeometry(30, 40, 100, 30)
	#	sld.valueChanged[int].connect(self.changeValue)
	slide.setValue(initial)
	return slide

def create_check_boxes(append_instead, keys, instances, labels, 
					inst_is_list = None, inst_is_dict = None, 
					rewidget = True, provide_master = False):
	'''
	def apply_to_inst(*args, **kwargs):
		dat = args[0]
		if inst_is_list:
			pdb.set_trace()
			inst[key] = dat
		else: inst.__dict__[key] = dat

	def remove_from_inst(*args, **kwargs):
		dat = args[0]
		if inst_is_list:
			pdb.set_trace()
			inst[key].remove(dat)
		else: inst.__dict__[key].remove(dat)
		return dat

	def append_to_inst(*args, **kwargs):
		dat = args[0]
		if inst_is_list:
			pdb.set_trace()
			inst[key].append(dat)
		else: inst.__dict__[key].append(dat)
		return dat

	def inquire_from_inst(*args, **kwargs):
		if inst_is_list:
			pdb.set_trace()
			dat = inst.__dict__[key]
		else:
			try: dat = inst.__dict__[key]
			except: pdb.set_trace()
		return dat
	'''

	def generate_check_func_append(check, inst, key, label):

		def check_func_append(current_value):
			if not current_value:
				if label in inst.__dict__[key]:
				#if label in inquire_from_inst():
					inst.__dict__[key].remove(label)
					#remove_from_inst(label)

			else:
				if not label in inst.__dict__[key]:
				#if not label in inquire_from_inst():
					inst.__dict__[key].append(label)
					#append_to_inst(label)

		def check_func_append_inst_dict(current_value):
			if not current_value:
				if label in inst[key]: inst[key].remove(label)

			else:
				if not label in inst[key]: inst[key].append(label)

		if type(inst) is types.DictionaryType:
			return check_func_append_inst_dict

		else: return check_func_append

	def set_initial_state(check, inst, key, label):
		if type(inst) is types.DictionaryType:
			if label in inst[key]:
				check.setCheckState(QtCore.Qt.Checked)

		else:
			if label in inst.__dict__[key]:
			#if label in inquire_from_inst():
				check.setCheckState(QtCore.Qt.Checked)

	def generate_check_func_toggle(inst, key):

		def check_func_toggle(integer):
			if integer == 0: inst.__dict__[key] = False
			#if integer == 0: apply_to_inst(False)
			elif integer == 2: inst.__dict__[key] = True
			#elif integer == 2: apply_to_inst(True)

		def check_func_toggle_inst_dict(integer):
			if integer == 0: inst[key] = False
			elif integer == 2: inst[key] = True

		if type(inst) is types.DictionaryType:
			return check_func_toggle_inst_dict

		else: return check_func_toggle

	def set_initial_state_toggle(check, inst, key):
		if type(inst) is types.DictionaryType:
			if inst[key]: state = QtCore.Qt.Checked
			else: state = QtCore.Qt.Unchecked

		else:
			try:
				if inst.__dict__[key]: state = QtCore.Qt.Checked
				#if inquire_from_inst(): state = QtCore.Qt.Checked
				else: state = QtCore.Qt.Unchecked

			except KeyError:
				print 'mobj with template for nonexistent attribute'
				print inst, key
				print 'adding attribute; as False by default'
				inst.__dict__[key] = False
				state = QtCore.Qt.Unchecked

		check.setCheckState(state)

	def create_master(checks):

		def flip_all(integer):
			[check.stateChanged.emit(integer) for check in checks]
			if integer == 0:
				[check.setCheckState(QtCore.Qt.Unchecked) 
									for check in checks]

			if integer == 2:
				[check.setCheckState(QtCore.Qt.Checked) 
								for check in checks]

		def find_initial_state():
			state_bool = not (False in [check.checkState() 
									for check in checks])
			if state_bool: return QtCore.Qt.Checked
			else: return QtCore.Qt.Unchecked

		master = QtGui.QCheckBox('All')
		master.setCheckState(find_initial_state())
		master.stateChanged.connect(flip_all)
		return master

	checks = [QtGui.QCheckBox(label) for label in labels]
	if append_instead:
		insts = [instances[0]]*len(labels)
		keeys = [keys[0]]*len(labels)
		[check.stateChanged.connect(generate_check_func_append(
				check, inst, key, label)) for 
					check, inst, key, label in 
						zip(checks, insts, keeys, labels)]
		[set_initial_state(check, inst, key, label) for 
					check, inst, key, label in 
						zip(checks, insts, keeys, labels)]

	else:
		[check.stateChanged.connect(
			generate_check_func_toggle(inst, key)) 
			for check, inst, key in zip(checks, instances, keys)]
		[set_initial_state_toggle(check, inst, key) 
			for check, inst, key in zip(checks, instances, keys)]

	if rewidget:
		[check.stateChanged.connect(
		create_mobj_rewidget_function(inst)) 
		for check, inst, key in zip(checks, instances, keys)]

	if provide_master: checks = [create_master(checks)] + checks
	return checks

def create_frame(parent = None):
	if parent is not None: square = QtGui.QFrame(parent)
	else: square = QtGui.QFrame()
	square.setFrameShape(QtGui.QFrame.StyledPanel)
	#square.setGeometry(150, 20, 100, 100)
	#col = create_color()
	#square.setStyleSheet("QWidget { background-color: %s }" % col.name())
	return square

#this is a single column list control
#items are strings, icons are icon paths
def create_list_box(items = None, icons = None):
	#currentItemChanged signal
	# its slots receive two arguments, current and previous
	#clicks, double-clicks, activates, or 
	#presses an item, and when the set of selected items is changed
	#To get the currently selected item, you can either use the 
	# arguments passed by the currentItemChanged signal or 
	# you can use the QListWidget's currentItem method
	qlist = QtGui.QListWidget()
	if items is not None and icons is None:
		if type(items) is not types.ListType: items = list(items)
		icons = [None] * len(items)
	elif items is None and icons is not None:
		if type(icons) is not types.ListType: icons = list(icons)
		items = [None] * len(icons)
	elif items is not None and icons is not None:
		if type(items) is not types.ListType:
			items = list(items)
		if type(icons) is not types.ListType:
			icons = list(icons)
		if len(icons) > len(items):
			[items.append(None) for dex in 
				range(len(icons) - len(items))]
		elif len(items) > len(icons):
			[icons.append(None) for dex in 
				range(len(items) - len(icons))]
	else: return qlist
	[create_qitem(item, icon) for 
		item, icon in zip(items, icons)]
	qlist.addItems(items)
	return qlist

def create_qitem(string = None, icon_path = None, 
			standard = False, bool_setup = None):
	#bool_setup should be a tuple containing ('bi' or 'tri', <default>)
	#generate event which receives item: itemChanged(item)
	if not standard: qitem = QtGui.QListWidgetItem()
	else: qitem = QtGui.QStandardItem()
	if bool_setup is not None and standard:
		if bool_setup[0] == 'bi': qitem.setCheckable(bool_setup[1])
		elif bool_setup[0] == 'tri': qitem.setTriState(bool_setup[1])
		else: print 'bool_setup is unrecognized; ignoring bool_setup'

	if string is not None: qitem.setText(string)
	if icon_path is not None: qitem.setIcon(create_icon(icon_path))
	return qitem

class qlist_image_list(QtGui.QListWidget):
	''' A specialized QListWidget that displays the
	list of all image files in a given directory. '''
	'''
	entry = QLineEdit(win)

	layout.addWidget(entry)

	def on_item_changed(curr, prev):
		entry.setText(curr.text())

	lst.currentItemChanged.connect(on_item_changed)
	'''
	def __init__(self, dirpath, parent = None):
		QListWidget.__init__(self, parent)
		self.set_dirpath(dirpath)

	def set_dirpath(self, dirpath):
		self._dirpath = dirpath
		self._populate()

	def _images(self):
		images = []
		for extension in get_supported_image_extensions():
			pattern = os.path.join(self._dirpath, '*.%s' % extension)
			images.extend(glob(pattern))

		return images

	def _populate(self):
		self.clear()
		for image in self._images():
			item = create_qitem(image, create_icon(image))

def create_qlistview(parent = None, contents = []):
	if parent is not None: qlistview = QListView(parent)
	else: qlistview = QListView()
	model = QStandardItemModel(qlistview)
	for item in contents: model.appendRow(item)
	qlistview.setModel(model)
	return qlistview

def create_qwebview(parent = None):
	'''
	# Interact with the HTML page by calling the completeAndReturnName
	# function; print its return value to the console
	def complete_name():
		frame = view.page().mainFrame()
		print frame.evaluateJavaScript('completeAndReturnName();')
	'''
	view = QtGui.QWebView()
	view.setHtml('''
		<html>
			<head>
				<title>A Demo Page</title>
				<script language="javascript">
					// Completes the full-name control and
					// shows the submit button
					function completeAndReturnName()
					{
						var fname = document.getElementById('fname').value;
						var lname = document.getElementById('lname').value;
						var full = fname + ' ' + lname;
						document.getElementById('fullname').value = full;
						document.getElementById('submit-btn').style.display = 'block';
						return full;
					}
				</script>
			</head>
			<body>
				<form>
					<label for="fname">First name:</label>
					<input type="text" name="fname" id="fname"></input>
					<br />
					<label for="lname">Last name:</label>
					<input type="text" name="lname" id="lname"></input>
					<br />
					<label for="fullname">Full name:</label>
					<input disabled type="text" name="fullname" id="fullname"></input>
					<br />
					<input style="display: none;" type="submit" id="submit-btn"></input>
				</form>
			</body>
		</html>
	''')

def create_treebook(parent = None, pages = [], mason = None, 
		initial = 0, inst = None, key = None, header = None):
	tree = tree_book(mason, inst, key, header)
	tree.set_up_pages(pages)
	if inst is None or key is None: tree.set_current_page(initial[0])
	return tree

def tree_book_panels_from_lookup(panel_template_lookup, 
									window, ensemble):
	#this is a hack!
	infos = (window.settables_infos[0], ensemble)

	def set_up_sub_panel(mobj, mobj_templates, mobj_labels, ltg):
		if issubclass(mobj.__class__, mobj_class):
			if mobj.rewidget(infos = infos): mobj.set_settables(*infos)
			mobj_templates.append(ltg(widgets = ['panel'], 
						templates = [mobj.widg_templates]))
			mobj_labels.append(mobj.label)

	ltg = sys.modules['libs.gui.libqtgui_masons'].interface_template_gui
	mobj_class = sys.modules[
		'libs.modular_core.libfundamental'].modular_object_qt
	panel_templates = []
	sub_panel_templates = []
	sub_panel_labels = []
	for key, panel_template in panel_template_lookup:
		mobj_templates = []
		mobj_labels = []
		if type(ensemble.run_params[key]) == types.ListType:
			for mobj in ensemble.run_params[key]:
				set_up_sub_panel(mobj, mobj_templates, mobj_labels, ltg)

		elif type(ensemble.run_params[key]) == types.DictionaryType:
			for sub_key in ensemble.run_params[key].keys():
				mobj = ensemble.run_params[key][sub_key]
				set_up_sub_panel(mobj, mobj_templates, mobj_labels, ltg)

		panel_templates.append(panel_template)
		sub_panel_templates.append(mobj_templates)
		sub_panel_labels.append(mobj_labels)

	return panel_templates, sub_panel_templates, sub_panel_labels

def create_tab_book(pages, mason, initial = None, 
						inst = None, key = None):

	def keep_index_func(dex): inst.__dict__[key] = dex
	#pages is a list of tuples
	# each tuple: ('page label', page_template_list)
	tabs = tab_book(pages = pages, mason = mason)
	tabs.set_up_pages()
	if initial is None: initial = 0
	tabs.setCurrentIndex(initial)
	if not inst is None and not key is None:
		tabs.currentChanged.connect(keep_index_func)

	return tabs

#this is an example function to connect to QStandardItemModel
# model.itemChanged.connect(on_item_changed)
def on_item_changed(item):
	# If the changed item is not checked, don't bother checking others
	if not item.checkState():
		return

	i = 0
	# loop through the items until you get None, which
	# means you've passed the end of the list
	while model.item(i):
		if not model.item(i).checkState(): return
		i += 1

	print 'the models items must all be checked!'
	print 'do something else now'

def create_text_box(parent = None, instance = None, key = None, 
		read_only = False, binding = None, alignment = 'left', 
			max_length = None, keep_frame = True, initial = '', 
			placeholder = None, multiline = False, bind_events = None, 
				bindings = None, rewidget = True, inst_is_dict = None, 
				for_code = False):

	'''
	When the text changes the PySide.QtGui.QLineEdit.textChanged() 
	signal is emitted; 
	when the text changes other than by calling 
	PySide.QtGui.QLineEdit.setText() the 
	PySide.QtGui.QLineEdit.textEdited() signal is emitted;
	when the cursor is moved the 
	PySide.QtGui.QLineEdit.cursorPositionChanged() signal is emitted;
	and when the Return or Enter key is pressed the 
	PySide.QtGui.QLineEdit.returnPressed() signal is emitted.
	When editing is finished, either because the line edit lost focus 
	or Return/Enter is pressed the 
	PySide.QtGui.QLineEdit.editingFinished() signal is emitted.
	Note that if there is a validator set on the line edit, the 
	PySide.QtGui.QLineEdit.returnPressed() / 
	PySide.QtGui.QLineEdit.editingFinished() signals will only 
	be emitted if the validator returns QValidator.Acceptable.

	These are the signals from the documentation:
		def cursorPositionChanged (arg__1, arg__2)
		def editingFinished ()
		def returnPressed ()
		def selectionChanged ()
		def textChanged (arg__1)
		def textEdited (arg__1)
	
	this mess should be resolved for function binding
				instances = [self], 
				keys = ['label'], 
				icons = [window.gear_icon], 
				bindings = [[window.read_text, window.center]], 
				#if the binding provided is None, 
				#the binding should update instance.__dict__[key]
				bind_events = [['returnPressed', 'textEdited']]))
	'''

	def apply_to_inst(*args, **kwargs):
		dat = args[0]
		if inst_is_dict and inst_is_dict[0]:
			if key is 'label':
				print 'applied to dict inst from lgb', dat
				instance._set_label_(dat)

			elif isinstance(instance, 
				lfu.unique_pool_item) and key is 'value':
					instance._set_(dat)

			instance[key] = dat

		else:
			if key is 'label': instance._set_label_(dat)
			elif isinstance(instance, 
				lfu.unique_pool_item) and key is 'value':
					instance._set_(dat)

			instance.__dict__[key] = dat

	def rewidg_on_inst(*args, **kwargs):
		if inst_is_dict: inst_is_dict[1].rewidget(*args, **kwargs)
		else: instance.rewidget(*args, **kwargs)

	def generate_text_edit_func(box):

		def text_edited_func_rewidget():
			try: apply_to_inst(box.text())
			except AttributeError:
				apply_to_inst(box.toPlainText())

			if rewidget and not instance is None:
				rewidg_on_inst(True)

		def text_edited_func():
			try: instance.__dict__[key] = box.text()
			except AttributeError:
				instance.__dict__[key] = box.toPlainText()

		#def text_edited_func(): apply_to_inst(box.text())
		if rewidget: return text_edited_func_rewidget
		else: return text_edited_func

	def line_only_options(box, max_length):
		if max_length is not None: box.setMaxLength(max_length)
		box.setFrame(keep_frame)

	def multiline_only_options(box, placeholder):
		if placeholder is not None: box.setPlaceHolder(placeholder)

	if parent is not None:
		if multiline:
			box = QtGui.QTextEdit(parent)
			multiline_only_options(box, placeholder)

		else:
			box = QtGui.QLineEdit(parent)
			line_only_options(box, max_length)

	else:
		if multiline:
			box = QtGui.QTextEdit(parent)
			multiline_only_options(box, placeholder)

		else:
			box = QtGui.QLineEdit()
			line_only_options(box, max_length)

	if for_code:
		font = code_font
		box.setFont(font)
		box.setTabStopWidth(code_metrics.width('	'))
		box.setLineWrapMode(QtGui.QTextEdit.NoWrap)

	if read_only: box.setReadOnly(True)
	consider_alignment(box, alignment)
	box.setText(str(initial))
	if bindings is not None and bind_events is not None:
		if len(bindings) < len(bind_events):
			bindings.extend([generate_text_edit_func(box) for 
				x in range(len(bind_events) - len(bindings))])

	elif bind_events is not None:
		bindings = [generate_text_edit_func(box) 
						for evt in bind_events]

	#it would be nice if the box showed red when its 
	#	valued was modified but enter wasnt pressed
	#pressing enter would return the color to normal
	if not bind_events:
		#box.returnPressed.connect(generate_text_edit_func(box))
		box.textChanged.connect(generate_text_edit_func(box))

	else:
		for bi_ev, bi in zip(bind_events, bindings):
			if bi_ev == 'changed': box.textChanged.connect(bi)
			elif bi_ev == 'enter': box.returnPressed.connect(bi)

	return box

def create_combo_box(labels, icons, datas, bindings = None, 
		initial = None, parent = None, bind_event = None, 
				inst = None, key = None, rewidget = True, 
				refresh_widgets = False, window = None):

	def apply_refresh(widg):
		if refresh_widgets and hasattr(window, 'set_up_widgets'):
			bind = create_reset_widgets_function(window)
			widg.activated.connect(bind)
			#if bind_event is 'useronly': widg.activated.connect(bind)
			#else: widg.currentIndexChanged.connect(bind)

		return widg

	def generate_instkey_combo_function(combo, inst, key):

		def instkey_combo_function():
			dex = combo.currentIndex()
			inst.__dict__[key] = labels[dex]
			if rewidget: inst.rewidget(True)

		return instkey_combo_function

	if parent is None: combo = QtGui.QComboBox()
	else: combo = QtGui.QComboBox(parent)
	for label, icon, dater in zip(labels, icons, datas):
		if icon is None:
			if dater is None: combo.addItem(label)
			else: combo.addItem(label, userData = dater)

		else:
			if dater is None: combo.addItem(icon, label)
			else: combo.addItem(icon, label, userData = dater)

	if bindings:
		if bind_event is 'useronly':
			[combo.activated.connect(bind) for bind 
					in bindings if not bind is None]

		else:
			[combo.currentIndexChanged.connect(bind) for bind
							in bindings if not bind is None]

	elif inst and key:
		bind = generate_instkey_combo_function(combo, inst, key)
		if bind_event is 'useronly': combo.activated.connect(bind)
		else: combo.currentIndexChanged.connect(bind)

	combo = apply_refresh(combo)
	if initial:
		try: combo.setCurrentIndex(labels.index(initial))
		except ValueError:
			lfu.debug_filter(''.join(['initial', str(initial), 
				'not found in labels'] + labels), debug_filter_thresh)

	return combo

class tab_book(QtGui.QTabWidget):

	def __init__(self, *args, **kwargs):
		super(tab_book, self).__init__()
		try: self.pages = kwargs['pages']
		except KeyError: self.pages = []
		try: self.mason = kwargs['mason']
		except KeyError: self.mason = lfu.gui_pack.lgm.standard_mason()

	def set_up_pages(self, *args, **kwargs):
		self.clear()
		for page in self.pages:
			layout = QtGui.QVBoxLayout()
			for template in page[1]:
				if hasattr(template, 'mason'):
					mason = template.mason[widg_dex]

				else: mason = self.mason
				layout.addLayout(mason.interpret_template(template))

			widg_wrap = central_widget_wrapper(content = layout)
			self.addTab(widg_wrap, page[0])

class tree_book(QtGui.QHBoxLayout):

	def __init__(self, mason, inst = None, key = None, header = None):
		super(tree_book, self).__init__()
		self.mason = mason
		self.tree = QtGui.QTreeWidget()
		#set_sizes_limits([[self.tree]], [[(200, 500)]], limit = 'max')
		#set_sizes_limits([[self.tree]], [[(200, 400)]])
		if type(header) is types.StringType:
			self.tree.setHeaderLabel(header)

		else: self.tree.setHeaderLabel('')
		self.tree.itemCollapsed.connect(self.remember_collapsed)
		self.tree.itemExpanded.connect(self.remember_expanded)
		self.tree.currentItemChanged.connect(self.change_page)
		split_dir = QtCore.Qt.Horizontal
		self.split = QtGui.QSplitter(split_dir)
		self.addWidget(self.split)
		self.split.addWidget(self.tree)
		if not inst is None and not key is None:
			self.selected_page_dex = inst.__dict__[key][0]
			self.expanded = inst.__dict__[key][1]
			self.maintain_page = True
			self.maintenance_handle = (inst, key)

		else:
			self.selected_page_dex = 0
			self.expanded = []
			self.maintain_page = False

	def set_up_pages(self, pages):
		self.tree.setColumnCount(1)
		self.tree.clear()
		self.tree_items = []
		self.top_levels = []
		self.tree_pages = []
		dex = 0
		for main, sub_temps, key, sub_labels in pages:
			top = QtGui.QTreeWidgetItem(None, [key])
			self.tree_items.append(top)
			self.top_levels.append(top)
			main_page = self.mason.interpret_template(main)
			try: main_page.addStretch(1)
			except AttributeError: pass
			self.tree_pages.append(central_widget_wrapper(
									content = main_page))
			for sub, label in zip(sub_temps, sub_labels):
				bottom = QtGui.QTreeWidgetItem(top, [label])
				self.tree_items.append(bottom)
				if hasattr(sub, 'mason'): mason = sub.mason
				else: mason = self.mason
				sub_page = mason.interpret_template(sub)
				sub_page.addStretch(1)
				self.tree_pages.append(create_scroll_area(
					central_widget_wrapper(content = sub_page)))

			self.tree.addTopLevelItem(top)
			dex += 1

		for page in self.tree_pages:
			self.split.addWidget(page)
			page.hide()

		for dex in self.expanded:
			self.tree.expandItem(self.top_levels[dex])

		self.set_current_page(self.selected_page_dex)

	def remember_expanded(self, item):
		dex = [top is item for top in self.top_levels].index(True)
		#print 'expanded', item, ' at:', dex
		if not dex in self.expanded: self.expanded.append(dex)

	def remember_collapsed(self, item):
		dex = [top is item for top in self.top_levels].index(True)
		#print 'collapsed', item, ' at:', dex
		if dex in self.expanded: self.expanded.remove(dex)

	def expand_all(self):
		[self.tree.expandItem(item) for item in self.top_levels]

	def collapse_all(self):
		[self.tree.collapseItem(item) for item in self.top_levels]		

	def change_page(self, current, previous):
		#print 'page change:', previous, '->', current
		lookup = [item is current for item in self.tree_items]
		new_dex = lookup.index(True)
		self.set_current_page(new_dex)

	def set_current_page(self, page_dex):
		#print 'set page:', page_dex, ' from:', self.selected_page_dex
		self.tree_pages[self.selected_page_dex].hide()
		self.selected_page_dex = page_dex
		self.tree_pages[self.selected_page_dex].show()
		if self.maintain_page:
			self.maintenance_handle[0].__dict__[
				self.maintenance_handle[1]] = [page_dex, self.expanded]

class central_widget_wrapper(QtGui.QWidget):

	def __init__(self, *args, **kwargs):
		super(central_widget_wrapper, self).__init__()
		self.content = kwargs['content']
		try:
			self.collapses = kwargs['collapses']
			if self.collapses:
				gear = os.path.join(os.getcwd(), 
						'resources', 'gear.png')
				self.fold_button = create_buttons([self.toggle], 
							labels = [''], icons = [gear])[0]
				set_sizes_limits([[self.fold_button]], 
								[[(16, 16)]], 'max')
				self.panel = central_widget_wrapper(
							content = self.content)
				content = QtGui.QHBoxLayout()
				lay = create_vert_box([self.fold_button], spacers = [1])
				#content.addWidget(self.fold_button)
				content.addLayout(lay)
				#content.addLayout(self.panel)
				content.addWidget(self.panel)

			else:
				self.collapses = False
				content = self.content

		except KeyError:
			self.collapses = False
			content = self.content

		self.collapsed = False
		self.setLayout(content)

	def toggle(self):
		self.collapsed = not self.collapsed
		if self.collapsed: self.fold()
		else: self.unfold()

	def fold(self):
		self.panel.hide()
		self.panel.setMaximumSize(qsize(16, 16))
		#set_sizes_limits([[self]], [[(16, 16)]], 'max')

	def unfold(self):
		self.panel.show()
		self.panel.setMaximumSize(qsize(256, 256))

class advanced_slider(central_widget_wrapper):

	def __init__(self, *args, **kwargs):
		#try: self.mason = kwargs['mason']
		#except KeyError: self.mason = lfu.gui_pack.lgm.standard_mason()
		super(advanced_slider, self).__init__(
			content = self.make_layout(*args, **kwargs))
		#self.setLayout(self.content)

	def make_layout(self, *args, **kwargs):
		self.make_widgets(*args, **kwargs)
		#self.clear()
		if kwargs['orientation'] == 'vertical':
			layout = QtGui.QVBoxLayout()

		elif kwargs['orientation'] == 'horizontal':
			layout = QtGui.QHBoxLayout()

		for widg in self.widgs:
			layout.addWidget(widg)

		return layout

	def setValue(self, value):
		self.widgs[0].setValue(value)

	def make_widgets(self, *args, **kwargs):
		def update_text_func(): text.setText(str(slide.value()))
		def update_slider_func():
			try: slide.setValue(int(text.text()))
			except ValueError: pass

		initial_value = str(kwargs['inst'].__dict__[kwargs['key']])
		slide = create_slider(kwargs['inst'], kwargs['key'], 
			kwargs['orientation'], kwargs['initial'], kwargs['minimum'], 
							kwargs['maximum'], kwargs['tick_position'], 
					kwargs['tick_interval'], kwargs['bind_events'][0], 
												kwargs['bindings'][0])
		text = create_text_box(instance = kwargs['inst'], 
			key = kwargs['key'], read_only = False, 
						bindings = kwargs['bindings'][1], 
				bind_events = kwargs['bind_events'][1], 
				alignment = 'center', max_length = None, 
								initial = initial_value)
		#slide.sliderReleased.connect(update_text_func)
		slide.valueChanged.connect(update_text_func)
		text.textChanged.connect(update_slider_func)
		self.widgs = [slide, text]

def create_inspector(mobj, mason = None, lay = 'grid'):

	def mobj_to_pairs(mobj, bump = ''):
		try:
			lap = [(bump + key, mobj.__dict__[key]) for 
					key in mobj.__dict__.keys()
					if key in mobj.visible_attributes]
		except:
			print 'inspector problem'; return []
		fixed_lap = []
		for pair in lap:			
			if 	issubclass(pair[1].__class__, lfu.modular_object_qt) or\
				issubclass(pair[1].__class__, lfu.interface_template_new_style):
				if pair[1].visible_attributes:
					bump += ' '*4
					nest = mobj_to_pairs(pair[1], bump)
					will_insert = [('\n' + pair[0], 
						pair[1].__class__.__name__)]
					for sub_pair in nest:
						sub_pair = (sub_pair[0], sub_pair[1])
						will_insert.append(sub_pair)

					fixed_lap.extend(will_insert)

			else:
				fixed_lap.append(pair)

		return fixed_lap

	if mobj is None:
		dummy_inspector = create_label(text = 'No inspectable object')
		return dummy_inspector

	elif hasattr(mobj, '_inspector_is_mobj_panel_') and\
						mobj._inspector_is_mobj_panel_:
		window = lfu.gui_pack.lqg._window_
		mobj.set_settables(window)
		pan = create_panel(mobj.widg_templates, mason, layout = lay)
		x_size = pan.sizeHint().width()
		y_size = pan.sizeHint().height()*2
		set_sizes_limits([[pan]], [[(x_size, y_size)]])
		return pan

	mobj_lines = [mobj.__class__.__name__ + '\n']
	mobj_attrs = mobj_to_pairs(mobj)
	mobj_lines.extend([str(attr[0]) + ' : ' + str(attr[1]) 
								for attr in mobj_attrs])
	mobj_lines = lfu.pagify(mobj_lines, 60)
	inspector = create_label(text = mobj_lines)
	return inspector

class mobj_catalog(QtGui.QVBoxLayout):

	#this class allows display of one panel at a time
	# chosen from a selector widget, with memory, 
	#  each panel corresponding to one mobj
	def __init__(self, temp, mason, mobjs = [], inst = None, 
								key = None, initial = None):
		super(mobj_catalog, self).__init__()
		self.mobjs = mobjs
		self.mason = mason
		self.mobj_labels = ['None'] + lfu.grab_mobj_names(mobjs)
		dummy = [None]*len(self.mobj_labels)
		self.selector = create_combo_box(self.mobj_labels, dummy, dummy)
		self.selector.currentIndexChanged.connect(self.change_page)
		self.addWidget(self.selector)
		self.set_up_pages()
		if not inst is None and not key is None:
			self.selected_page_label = inst.__dict__[key]
			if self.selected_page_label is None:
				self.selected_page_label = 'None'

			self.maintain_page = True
			self.maintenance_handle = (inst, key)

		else:
			self.selected_page_label = 'None'
			self.maintain_page = False

		try: start_dex = self.mobj_labels.index(self.selected_page_label)
		except ValueError: start_dex = 0
		self.selector.setCurrentIndex(start_dex)
		self.set_current_page(start_dex)

	def set_up_pages(self):
		self.pages = [create_inspector(None)]
		if type(self.mobjs) is types.ListType:
			[self.pages.append(create_inspector(mobj, self.mason)) 
										for mobj in self.mobjs]

		elif type(self.mobjs) is types.DictionaryType:
			[self.pages.append(create_inspector(
					self.mobjs[key], self.mason)) 
					for key in self.mobjs.keys()]

		else: print 'cannot create catalog from non-list, \
							non-dictionary mobj collection'

		[self.addWidget(page) for page in self.pages]
		[page.hide() for page in self.pages]

	def change_page(self, new_dex):
		#is it possible to redraw a panel here
		#	if mobj.rewidget()?
		self.set_current_page(new_dex)

	def set_current_page(self, page_dex):
		try:
			self.pages[self.mobj_labels.index(
				self.selected_page_label)].hide()

		except ValueError: pass
		self.selected_page_label = self.mobj_labels[page_dex]
		self.pages[self.mobj_labels.index(
			self.selected_page_label)].show()
		if self.maintain_page:
			self.maintenance_handle[0].__dict__[
				self.maintenance_handle[1]] = self.mobj_labels[page_dex]

def create_mobj_catalog(temp, mobjs = [], mason = None, 
				inst = None, key = None, initial = 0):
	catalog = mobj_catalog(temp, mason, mobjs = mobjs, 
			inst = inst, key = key, initial = initial)
	return central_widget_wrapper(content = catalog)

def create_list_controller(headers, entries):
	controller = QtGui.QTreeWidget()
	controller.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
	controller.setColumnCount(len(headers))
	controller.setHeaderLabels(headers)
	[controller.setColumnWidth(dex, 8*len(head)) 
			for dex, head in enumerate(headers)]
	for dex, entry in enumerate(entries):
		row = QtGui.QTreeWidgetItem(None, [''.join(
			['Positions ', str(entry[0]).rjust(5)])])
		row.setText(1, str(entry[1].trajectory_count))
		for sub_dex, element in enumerate(entry[1]):
			row.setText(sub_dex + 2, str(element))

		controller.addTopLevelItem(row)

	return controller

class trajectory_range_maker(QtGui.QTreeWidget):

	def __init__(self, parent = None):
		QtGui.QTreeWidget.__init__(self, parent)
		headers = ['Axes', 'Set Range', 'Variation']
		self.setHeaderLabels(headers)

def create_scroll_area(central_widget, parent = None, memory = None):
	#scroll_area = QtGui.QScrollArea()
	scroll_area = scroll_area_with_memory(
		parent = parent, memory = memory)
	#scroll_area.setBackgroundRole(QtGui.QPalette.ToolTipBase)
	#scroll_area.setBackgroundRole(QtGui.QPalette.NoRole)
	scroll_area.setBackgroundRole(QtGui.QPalette.Window)
	central_widget._parent = scroll_area
	scroll_area.setWidget(central_widget)
	return scroll_area

class scroll_area_with_memory(QtGui.QScrollArea):

	def __init__(self, *args, **kwargs):
		try: parent = kwargs['parent']
		except: parent = None
		QtGui.QScrollArea.__init__(self, parent)
		try: memory = kwargs['memory']
		except: memory = None
		self.setVerticalScrollBar(scroll_bar_with_memory(
						parent = self, memory = memory))

class scroll_bar_with_memory(QtGui.QScrollBar):

	def __init__(self, *args, **kwargs):
		try: parent = kwargs['parent']
		except: parent = None
		QtGui.QScrollBar.__init__(self, parent)
		try: memory = kwargs['memory']
		except: memory = None
		self.memory = memory
		if memory:
			pos = memory[0].__dict__[memory[1]]
			self.pos = pos
			if self.pos:
				self.setValue(self.pos)

			else: self.pos = 0

			self.actionTriggered.connect(self.memorize)
			self.rangeChanged.connect(self.change_range)

	def change_range(self, min_, max_):
		#print 'minmax', min_, max_
		if max_ - min_ > 0:
			if self.flag:
				val = self.pos
				self.memory[0].__dict__[self.memory[1]] = val
				self.pos = val
				self.setValue(val)
				self.flag = False

		else: self.flag = True

	def memorize(self):
		self.pos = self.value()
		#print 'memorizing', self.pos
		self.memory[0].__dict__[self.memory[1]] = self.pos

def generate_linkage_assertion_funcs(linkages):

	def generate_linkage_assertion_func(linkage):

		def call_after_wrap():
			linkage.assert_dependance()

		return call_after_wrap

	assertions = []
	for linkage in linkages:
		assertions.append(
			generate_linkage_assertion_func(linkage))

	return assertions

if __name__ == '__main__': print 'this is a library!'




