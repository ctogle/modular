import libs.modular_core.libfundamental as lfu
import libs.gui.libqtgui_bricks as lgb

#import libs.modular_core.libsettings as lset

from PySide import QtGui, QtCore
import types
import os

import pdb

class interface_template_gui(lfu.interface_template_new_style):
	gui_package = 'PySide'
	_depth_lookup_ =\
			{
		'layout' : 0, 
		'grid_spacing' : 0, 
		'widgets' : 1, 
		'layouts' : 1, 
		'handles' : 1, 
		'box_positions' : 1, 
		'widg_positions' : 1, 
		'append_instead' : 1, 
		'provide_master' : 1, 
		'widg_spans' : 1, 
		'keep_frame' : 1, 
		'read_only' : 1, 
		'multiline' : 1, 
		'box_labels' : 1, 
		'parents' : 2, 
		'instances' : 2, 
		'keys' : 2, 
		'datas' : 2, 
		'callbacks' : 2, 
		'minimum_values' : 2, 
		'maximum_values' : 2, 
		'minimum_sizes' : 2, 
		'maximum_sizes' : 2, 
		'max_lengths' : 2, 
		'doubles' : 2, 
		'positions' : 2, 
		'intervals' : 2, 
		'orientations' : 2, 
		'initials' : 2, 
		'labels' : 2, 
		'templates' : 2, 
		'icons' : 2, 
		'single_steps' : 2, 
		'placeholders' : 2, 
		'alignments' : 2, 
		'subspacers' : 2, 
		'tooltips' : 2, 
		'bindings' : 2, 
		'bind_events' : 2, 
			}

	def __init__(self, *args, **kwargs):
		lfu.interface_template_new_style.__init__(self, *args, **kwargs)

	def __str__(self):
		_str = []
		for key in self.__dict__.keys():
			_str.append(' : '.join([key, self.__dict__[key].__str__()]))
		return '\n'.join(_str)

	def __add__(self, other):

		def wrap_none(depth, count):
			if depth == 1: nones = [None]*count
			elif depth == 2: nones = [[None]]*count
			return nones

		def wrap_side(inst, key, depth):
			try: side = inst.__dict__[key]
			except KeyError:
				count = len(inst.widgets)
				if key == 'widg_spans':
					try: count = len(lfu.flatten(inst.labels))
					except: pdb.set_trace()
				side = wrap_none(depth, count)
			return side

		dom_keys = self.__dict__.keys()
		sub_keys = other.__dict__.keys()
		all_keys = lfu.uniqfy(dom_keys + sub_keys)
		new_dict = {}
		for key in all_keys:
			depth = self._depth_lookup_[key]
			if depth == 0:
				try: new_item = self.__dict__[key]
				except KeyError: new_item = other.__dict__[key]
			elif depth == 1 or depth == 2:
				left = wrap_side(self, key, depth)
				right = wrap_side(other, key, depth)
				new_item = left + right
			else: print 'depth cant be >2'; pdb.set_trace()
			new_dict[key] = new_item

		new = interface_template_gui(**new_dict)
		return new

class interface_template_dummy(interface_template_gui):
	gui_package = 'PySide'
	def __init__(self, *args, **kwargs):
		kwargs['widgets'] = ['image']
		kwargs['paths'] = [os.path.join(os.getcwd(), 
							'resources', 'gear.png')]
		lfu.interface_template_new_style.__init__(
							self, *args, **kwargs)

class standard_mason(object):

	def __init__(self, parent = None, label = \
					'standard mason for pyside'):
		self.label = label
		self.parent = parent
		import libs.modular_core.libsettings as lset
		self.lset = lset

	def hide_quiet_widgets(self, widgs, template):
		try:
			verbosities = template.verbosities
			if verbosities is None:
				verbosities = [[1]*len(widg_list) 
						for widg_list in widgs]

			elif len(verbosities) < len(widgs):
				missing = len(widgs) - len(verbosities)
				verbosities.extend([1]*missing)

		except AttributeError:
			verbosities = [[1]*len(widg_list) for widg_list in widgs]

		for dex in range(len(verbosities)):
			widg_list = widgs[dex]
			if not type(verbosities[dex]) is types.ListType:
				verbosities[dex] = [verbosities[dex]]*len(widg_list)

			if len(verbosities[dex]) < len(widg_list):
				missing = len(widg_list) - len(verbosities[dex])
				verbosities[dex].extend([1]*missing)

		try:
			threshold = self.lset.get_setting('interface_verbosity')
			if not threshold: threshold = 1

		except: threshold = 1
		for widg, volume in zip(lfu.flatten(widgs), 
						lfu.flatten(verbosities)):
			if not volume <= threshold: widg.hide()

	def interpret_template(self, template):
		widgs = []
		if not hasattr(template, 'widgets'): pdb.set_trace()
		for widg_dex, widget_type in enumerate(template.widgets):
			if widget_type == 'button_set':
				widg_list = self.interpret_template_button_set(
											template, widg_dex)

			elif widget_type == 'check_set':
				widg_list = self.interpret_template_check_set(
											template, widg_dex)

			elif widget_type == 'text':
				widg_list = self.interpret_template_text_box(
										template, widg_dex)

			elif widget_type == 'selector':
				widg_list = self.interpret_template_combo_box(
											template, widg_dex)

			elif widget_type == 'image':
				widg_list = self.interpret_template_image(
										template, widg_dex)

			elif widget_type == 'spin':
				widg_list = self.interpret_template_spin(
									template, widg_dex)

			elif widget_type == 'slider':
				widg_list = self.interpret_template_slider(
										template, widg_dex)

			elif widget_type == 'slider_advanced':
				widg_list = self.interpret_template_slider_advanced(
												template, widg_dex)

			elif widget_type == 'radio':
				widg_list = self.interpret_template_radio(
										template, widg_dex)

			elif widget_type == 'splitter':
				widg_list = self.interpret_template_splitter(
										template, widg_dex)

			elif widget_type == 'panel':
				widg_list = self.interpret_template_panel(
										template, widg_dex)

			elif widget_type == 'file_name_box':
				widg_list = self.interpret_template_file_name_box(
											template, widg_dex)

			elif widget_type == 'directory_name_box':
				widg_list = self.interpret_template_directory_name_box(
													template, widg_dex)

			elif widget_type == 'full_path_box':
				widg_list = self.interpret_template_full_path_box(
											template, widg_dex)

			elif widget_type == 'check_spin_list':
				widg_list = self.interpret_template_check_spin_list(
												template, widg_dex)

			elif widget_type == 'mobj_inspector':
				widg_list = self.interpret_template_inspector(
										template, widg_dex)

			elif widget_type == 'mobj_catalog':
				widg_list = self.interpret_template_catalog(
										template, widg_dex)

			elif widget_type == 'tab_book':
				widg_list = self.interpret_template_tab_book(
										template, widg_dex)

			elif widget_type == 'tree_book':
				widg_list = self.interpret_template_tree_book(
										template, widg_dex)

			elif widget_type == 'list_controller':
				widg_list = self.interpret_template_list_controller(
												template, widg_dex)

			elif widget_type == 'console_listener':
				widg_list = self.interpret_template_console_listener(
												template, widg_dex)

			elif widget_type == 'opengl_view':
				widg_list = self.interpret_template_opengl_view(
											template, widg_dex)

			elif widget_type == 'plot':
				widg_list = self.interpret_template_plot(
									template, widg_dex)

			else:
				print 'no interpretation of widget type: ' + widget_type
				return None

			try:
				if template.handles[widg_dex]:
					handle = template.handles[widg_dex]
					inst = handle[0]
					key = handle[1]
					inst.__dict__[key] = widg_list
					if not handle in inst._handles_:
						inst._handles_.append(handle)

			except AttributeError: pass
			widgs.append(widg_list)

		self.hide_quiet_widgets(widgs, template)
		try: lgb.set_tooltips(widgs, template.tooltips)
		except AttributeError: pass
		try: lgb.set_sizes_limits(widgs, template.minimum_sizes)
		except AttributeError: pass
		try: lgb.set_sizes_limits(widgs, template.maximum_sizes, 'max')
		except AttributeError: pass
		try: layout = template.layout
		except AttributeError: layout = 'vertical'
		try: subspacers = template.subspacers[widg_dex]
		except AttributeError: subspacers = None
		if layout == 'vertical': box = lgb.create_vert_box
		elif layout == 'horizontal': box = lgb.create_horz_box
		elif layout == 'grid':
			box = lgb.create_grid_box
			try: positions = template.widg_positions
			except AttributeError: positions = []
			try: spans = template.widg_spans
			except AttributeError: spans = []
			try: g_spacing = template.grid_spacing
			except AttributeError: g_spacing = 5
			try: widg_layout = box(widgs, positions, spans, 
								g_spacing, template.layouts)

			except AttributeError:
				widg_layout = box(lfu.flatten(widgs), 
						positions, spans, g_spacing)

			return widg_layout

		else:
			print 'widget layout "', layout,\
				'" unrecognized; returning empty'
			return lgb.create_vert_box([])

		try: widg_layout = box(widgs, template.layouts, subspacers)
		except AttributeError: widg_layout = box(lfu.flatten(widgs))
		return widg_layout

	def interpret_template_button_set(self, template, widg_dex):

		def try_pixmap_paths():
			try:
				paths = template.paths[widg_dex]
				if paths:
					labels = [lgb.create_pixmap(pa) for pa in paths]

			except AttributeError: labels = None
			return labels

		try: icons = template.icons[widg_dex]
		except AttributeError: icons = None
		try: subspacers = template.subspacers[widg_dex]
		except AttributeError: subspacers = None
		try: bind_events = template.bind_events[widg_dex]
		except AttributeError: bind_events = None
		try:
			labels = template.labels[widg_dex]
			if labels is None: labels = try_pixmap_paths()

		except AttributeError: labels = try_pixmap_paths()
		return lgb.create_buttons(template.bindings[widg_dex], 
									labels, icons, bind_events)

	def interpret_template_check_set(self, template, widg_dex):
		try: append_instead = template.append_instead[widg_dex]
		except AttributeError: append_instead = True
		try: keys = template.keys[widg_dex]
		except AttributeError: keys = []
		try: instances = template.instances[widg_dex]
		except AttributeError: instances = []
		try: labels = template.labels[widg_dex]
		except AttributeError: labels = []
		try: is_list = template.instance_is_list[widg_dex]
		except AttributeError: is_list = None
		try: rewidget = template.rewidget[widg_dex][0]
		except AttributeError: rewidget = True
		try: provide_master = template.provide_master[widg_dex]
		except AttributeError: provide_master = False
		try: callbacks = template.callbacks[widg_dex]
		except AttributeError: callbacks = []
		check_widget = lgb.create_check_boxes(append_instead, 
							keys, instances, labels, is_list, 
					None, rewidget, provide_master, callbacks)
		try:
			title = template.box_labels[widg_dex]
			group = QtGui.QGroupBox(title = title)
			layout = lgb.create_vert_box(check_widget)
			group.setLayout(layout)
			return [group]

		except AttributeError: return check_widget

	def interpret_template_text_box(self, template, widg_dex):
		#do text boxes get icons?
		try: icons = template.icons[widg_dex]
		except AttributeError: icons = None
		try: bind_events = template.bind_events[widg_dex]
		except AttributeError: bind_events = None
		try: bindings = template.bindings[widg_dex]
		except AttributeError: bindings = None
		try: placeholder = template.placeholders[widg_dex]
		except AttributeError: placeholder = None
		try: max_leng = template.max_lengths[widg_dex][0]
		except AttributeError: max_leng = None
		try: read_only = template.read_only[widg_dex]
		except AttributeError: read_only = False
		try: multi = template.multiline[widg_dex]
		except AttributeError: multi = False
		try: keep_frame = template.keep_frame[widg_dex]
		except AttributeError: keep_frame = True
		try: for_code = template.for_code[widg_dex]
		except AttributeError: for_code = False
		try: alignment = template.alignments[widg_dex][0]
		except AttributeError: alignment = 'left'
		try: inst_is_dict = template.inst_is_dict[widg_dex]
		except AttributeError: inst_is_dict = None
		try: instance = template.instances[widg_dex][0]
		except AttributeError: instance = None
		try: key = template.keys[widg_dex][0]
		except AttributeError: key = None
		try: initial = template.initials[widg_dex][0]
		except AttributeError:
			if not (instance is None or key is None):
				if key is 'label':
					try: initial = instance._get_label_()
					except: pdb.set_trace()

				else:
					try: initial = instance.__dict__[key]
					except AttributeError:
						try: initial = instance[key]
						except: pdb.set_trace()

			else: initial = ''

		try: rewidget = template.rewidget[widg_dex][0]
		except AttributeError: rewidget = True
		except IndexError: rewidget = True
		text_widget = [lgb.create_text_box(instance = instance, 
			key = key, placeholder = placeholder, max_length = max_leng, 
							multiline = multi, read_only = read_only, 
							alignment = alignment, initial = initial, 
				keep_frame = keep_frame, bind_events = bind_events, 
						bindings = bindings, rewidget = rewidget, 
				inst_is_dict = inst_is_dict, for_code = for_code)]
		try:
			title = template.box_labels[widg_dex]
			group = QtGui.QGroupBox(title = title)
			layout = lgb.create_vert_box(text_widget)
			group.setLayout(layout)
			return [group]

		except AttributeError: return text_widget

	def interpret_template_combo_box(self, template, widg_dex):
		try: labels = template.labels[widg_dex]
		except AttributeError: labels = []
		try: icons = template.icons[widg_dex]
		except AttributeError: icons = []
		try: datas = template.datas[widg_dex]
		except AttributeError: datas = []
		try: initial = template.initials[widg_dex][0]
		except AttributeError: initial = None
		except TypeError: initial = None
		try: bindings = template.bindings[widg_dex]
		except AttributeError: bindings = None
		try: bind_event = template.bind_events[widg_dex]
		except AttributeError: bind_event = None
		try: instance = template.instances[widg_dex][0]
		except AttributeError: instance = None
		except TypeError: instance = None
		try: key = template.keys[widg_dex][0]
		except AttributeError: key = None
		except TypeError: key = None
		try: rewidget = template.rewidget[widg_dex][0]
		except AttributeError: rewidget = True
		try: refresh = template.refresh[widg_dex][0]
		except AttributeError: refresh = False
		except TypeError: refresh = False
		try: window = template.window[widg_dex][0]
		except AttributeError: window = None
		except TypeError: window = None
		if bind_event: bind_event = bind_event[0]
		if labels: lfu.fill_lists([labels, icons, datas], fill = None)
		combo_widget = [lgb.create_combo_box(labels, icons, datas, 
			initial = initial, bindings = bindings, bind_event =\
			bind_event, inst = instance, key = key, rewidget = rewidget, 
							refresh_widgets = refresh, window = window)]
		try:
			title = template.box_labels[widg_dex]
			group = QtGui.QGroupBox(title = title)
			layout = lgb.create_vert_box(combo_widget)
			group.setLayout(layout)
			return [group]

		except AttributeError: return combo_widget

	def interpret_template_image(self, template, widg_dex):
		path = template.paths[widg_dex]
		return [lgb.create_pixmap(path)]

	def interpret_template_spin(self, template, widg_dex):
		try: parent = template.parents[widg_dex][0]
		except AttributeError: parent = None
		try: double = template.doubles[widg_dex][0]
		except AttributeError: double = False
		try: min_val = template.minimum_values[widg_dex][0]
		except AttributeError: min_val = None
		try: max_val = template.maximum_values[widg_dex][0]
		except AttributeError: max_val = None
		try: sing_step = template.single_steps[widg_dex][0]
		except AttributeError: sing_step = None
		try: initial = template.initials[widg_dex][0]
		except AttributeError: initial = None
		try: instance = template.instances[widg_dex][0]
		except AttributeError: instance = None
		try: key = template.keys[widg_dex][0]
		except AttributeError: key = None
		try: rewidget = template.rewidget[widg_dex][0]
		except AttributeError: rewidget = True
		try: callback = template.callbacks[widg_dex][0]
		except AttributeError: callback = None
		spin_widget = [lgb.create_spin_box(parent = parent, 
			double = double, min_val = min_val, max_val = max_val, 
			sing_step = sing_step, initial = initial, 
					instance = instance, key = key, 
					rewidget = rewidget, callback = callback)]
		try:
			title = template.box_labels[widg_dex]
			group = QtGui.QGroupBox(title = title)
			layout = lgb.create_vert_box(spin_widget)
			group.setLayout(layout)
			return [group]

		except AttributeError: return spin_widget

	def interpret_template_slider(self, template, widg_dex):
		try: min_val = template.minimum_values[widg_dex][0]
		except AttributeError: min_val = 0
		try: max_val = template.maximum_values[widg_dex][0]
		except AttributeError: max_val = 50
		try: orientation = template.orientations[widg_dex][0]
		except AttributeError: orientation = 'horizontal'
		try: initial = template.initials[widg_dex][0]
		except AttributeError: initial = 1
		try: tick_pos = template.positions[widg_dex][0]
		except AttributeError: tick_pos = None
		try: tick_int = template.intervals[widg_dex][0]
		except AttributeError: tick_int = 1
		try: bind_events = template.bind_events[widg_dex]
		except AttributeError: bind_events = []
		try: bindings = template.bindings[widg_dex]
		except AttributeError: bindings = []
		slide_widget = [lgb.create_slider(
			template.instances[widg_dex][0], template.keys[widg_dex][0], 
						orientation = orientation, initial = initial, 
								minimum = min_val, maximum = max_val, 
				tick_position = tick_pos, tick_interval = tick_int, 
				bind_events = bind_events, bindings = bindings)]

		try:
			title = template.box_labels[widg_dex]
			group = QtGui.QGroupBox(title = title)
			layout = lgb.create_vert_box(slide_widget)
			group.setLayout(layout)
			return [group]

		except AttributeError: return slide_widget

	def interpret_template_slider_advanced(self, template, widg_dex):
		try: min_val = template.minimum_values[widg_dex][0]
		except AttributeError: min_val = 0
		try: max_val = template.maximum_values[widg_dex][0]
		except AttributeError: max_val = 50
		try: orientation = template.orientations[widg_dex][0]
		except AttributeError: orientation = 'horizontal'
		try: initial = template.initials[widg_dex][0]
		except AttributeError: initial = 1
		try: tick_pos = template.positions[widg_dex][0]
		except AttributeError: tick_pos = None
		try: tick_int = template.intervals[widg_dex][0]
		except AttributeError: tick_int = 1
		try: bind_events = template.bind_events[widg_dex]
		except AttributeError: bind_events = [[None], [None]]
		try: bindings = template.bindings[widg_dex]
		except AttributeError: bindings = [[None], [None]]
		slide_widget = [lgb.advanced_slider(inst =\
			template.instances[widg_dex][0], key =\
			template.keys[widg_dex][0], mason = self, 
			orientation = orientation, initial = initial, 
			minimum = min_val, maximum = max_val, 
			tick_position = tick_pos, tick_interval = tick_int, 
				bind_events = bind_events, bindings = bindings)]

		try:
			title = template.box_labels[widg_dex]
			group = QtGui.QGroupBox(title = title)
			layout = lgb.create_vert_box(slide_widget)
			group.setLayout(layout)
			return [group]

		except AttributeError: return slide_widget

	def interpret_template_radio(self, template, widg_dex):
		try: labels = template.labels[widg_dex]
		except AttributeError: labels = ['...no labels...']
		try: title = template.box_labels[widg_dex]
		except AttributeError: title = ''
		try: initial = template.initials[widg_dex][0]
		except AttributeError: initial = None
		try: instance = template.instances[widg_dex][0]
		except AttributeError: instance = None
		try: key = template.keys[widg_dex][0]
		except AttributeError: key = None
		try: rewidget = template.rewidget[widg_dex][0]
		except AttributeError: rewidget = True
		try: refresh = template.refresh[widg_dex][0]
		except AttributeError: refresh = False
		try: window = template.window[widg_dex][0]
		except AttributeError: window = None
		return [lgb.create_radios(options = labels, title = title, 
				initial = initial, instance = instance, key = key, 
						rewidget = rewidget, refresh = refresh, 
											window = window)]

	def interpret_template_splitter(self, template, widg_dex):
		try: templates = template.templates[widg_dex]
		except AttributeError: templates = []
		try: mason = template.mason
		except AttributeError: mason = self
		try: orientation = template.orientations[widg_dex][0]
		except AttributeError: orientation = 'vertical'
		try: scroll = template.scrollable[widg_dex]
		except AttributeError: scroll = False
		return [lgb.create_splitter_box(parent = None, 
				templates = templates, mason = mason, 
				direction = orientation, scroll = scroll)]

	def interpret_template_panel(self, template, widg_dex):
		try: templates = template.templates[widg_dex]
		except AttributeError: templates = []
		if not templates: return [lgb.create_label()]
		try: mason = template.mason
		except AttributeError: mason = self
		try: scroll = template.scrollable[widg_dex]
		except AttributeError: scroll = False
		try: collapse = template.collapses[widg_dex]
		except AttributeError: collapse = False
		try: lay = template.layouts[widg_dex]
		except AttributeError: lay = 'grid'
		if not lay: lay = 'grid'
		if scroll:
			panel_widget = [lgb.create_scroll_area(
				lgb.create_panel(templates, mason, 
					collapses = collapse, layout = lay))]

		else:
			panel_widget = [lgb.create_panel(templates, mason, 
						collapses = collapse, layout = lay)]

		try:
			title = template.box_labels[widg_dex]
			group = QtGui.QGroupBox(title = title)
			layout = lgb.create_vert_box(panel_widget)
			group.setLayout(layout)
			return [group]

		except AttributeError: return panel_widget

	def interpret_template_file_name_box(self, template, widg_dex):
		try: instance = template.instances[widg_dex][0]
		except AttributeError: instance = None
		try: key = template.keys[widg_dex][0]
		except AttributeError: key = None
		try: label = template.labels[widg_dex][0]
		except AttributeError: label = ''
		try: initial = template.initials[widg_dex][0]
		except AttributeError: initial = ''
		try: exts = template.initials[widg_dex][1]
		except AttributeError: exts = None
		except IndexError: exts = None
		try: init_dir = template.initials[widg_dex][2]
		except AttributeError: init_dir = None
		except IndexError: init_dir = None
		try: rewidget = template.rewidget[widg_dex][0]
		except AttributeError: rewidget = True
		try: is_dict = template.instance_is_dict[widg_dex]
		except AttributeError: is_dict = None
		finame_box = [lgb.create_file_name_box(
			instance, key, label, initial, exts, False, 
					init_dir, rewidget, None, is_dict)]
		try:
			title = template.box_labels[widg_dex]
			group = QtGui.QGroupBox(title = title)
			layout = lgb.create_vert_box(finame_box)
			group.setLayout(layout)
			return [group]

		except AttributeError: return finame_box

	def interpret_template_directory_name_box(self, template, widg_dex):
		try: instance = template.instances[widg_dex][0]
		except AttributeError: instance = None
		try: key = template.keys[widg_dex][0]
		except AttributeError: key = None
		try: label = template.labels[widg_dex][0]
		except AttributeError: label = ''
		try: initial = template.initials[widg_dex][0]
		except AttributeError: initial = ''
		try: exts = template.initials[widg_dex][1]
		except AttributeError: exts = None
		except IndexError: exts = None
		try: init_dir = template.initials[widg_dex][2]
		except AttributeError: init_dir = None
		except IndexError: init_dir = None
		try: rewidget = template.rewidget[widg_dex][0]
		except AttributeError: rewidget = True
		try: is_dict = template.instance_is_dict[widg_dex]
		except AttributeError: is_dict = None
		diname_box = [lgb.create_file_name_box(
			instance, key, label, initial, exts, True, 
					init_dir, rewidget, None, is_dict)]
		try:
			title = template.box_labels[widg_dex]
			group = QtGui.QGroupBox(title = title)
			layout = lgb.create_vert_box(diname_box)
			group.setLayout(layout)
			return [group]

		except AttributeError: return diname_box

	def interpret_template_full_path_box(self, template, widg_dex):
		try: instance = template.instances[widg_dex][0]
		except AttributeError: instance = None
		try: key = template.keys[widg_dex][0]
		except AttributeError: key = None
		try: label = template.labels[widg_dex][0]
		except AttributeError: label = ''
		try: initial = template.initials[widg_dex][0]
		except AttributeError: initial = ''
		try: exts = template.initials[widg_dex][1]
		except AttributeError: exts = None
		except IndexError: exts = None
		try: init_dir = template.initials[widg_dex][2]
		except AttributeError: init_dir = None
		except IndexError: init_dir = None
		try: rewidget = template.rewidget[widg_dex][0]
		except AttributeError: rewidget = True
		try: is_dict = template.instance_is_dict[widg_dex]
		except AttributeError: is_dict = None
		paname_box = [lgb.create_file_name_box(
			instance, key, label, initial, exts, True, 
			init_dir, rewidget, None, is_dict, True)]
		try:
			title = template.box_labels[widg_dex]
			group = QtGui.QGroupBox(title = title)
			layout = lgb.create_vert_box(paname_box)
			group.setLayout(layout)
			return [group]

		except AttributeError: return paname_box

	def interpret_template_check_spin_list(self, template, widg_dex):
		try: instance = template.instances[widg_dex][0]
		except AttributeError: instance = None
		try: key = template.keys[widg_dex][0]
		except AttributeError: key = None
		try: labels = template.labels[widg_dex]
		except AttributeError: labels = []
		check_spin = lgb.create_check_spin_list(instance, key, labels)
		try:
			title = template.box_labels[widg_dex]
			group = QtGui.QGroupBox(title = title)
			layout = lgb.create_vert_box(check_spin)
			group.setLayout(layout)
			return [group]

		except AttributeError: return check_spin

	def interpret_template_inspector(self, template, widg_dex):
		try: instance = template.instances[widg_dex][0]
		except AttributeError: instance = None
		return [lgb.create_inspector(instance)]

	def interpret_template_catalog(self, template, widg_dex):
		try: mobjs = template.instances[widg_dex][0]
		except AttributeError: mobjs = []
		try: mason = template.mason
		except AttributeError: mason = self
		try: initial = template.initials[widg_dex][0]
		except AttributeError: initial = None
		try: instance = template.instances[widg_dex][1]
		except AttributeError: instance = None
		try: key = template.keys[widg_dex][1]
		except AttributeError: key = None
		return [lgb.create_mobj_catalog(template, mobjs = mobjs, 
								mason = mason, inst = instance, 
								key = key, initial = initial)]

	def interpret_template_tab_book(self, template, widg_dex):
		try: pages = template.pages[widg_dex]
		except AttributeError: pages = []
		try: mason = template.mason
		except AttributeError: mason = self
		try: initial = template.initials[widg_dex][0]
		except AttributeError: initial = 0
		try: instance = template.instances[widg_dex][0]
		except AttributeError: instance = None
		try: key = template.keys[widg_dex][0]
		except AttributeError: key = None
		return [lgb.create_tab_book(pages, mason, 
						initial, instance, key)]

	def interpret_template_tree_book(self, template, widg_dex):
		try: pages = template.pages[widg_dex]
		except AttributeError: pages = []
		try: mason = template.mason
		except AttributeError: mason = self
		try: initial = template.initials[widg_dex][0]
		except AttributeError: initial = [0, []]
		try: instance = template.instances[widg_dex][0]
		except AttributeError: instance = None
		try: key = template.keys[widg_dex][0]
		except AttributeError: key = None
		try: header = template.headers[widg_dex][0]
		except AttributeError: header = None
		tree_widget = [lgb.central_widget_wrapper(content =\
						lgb.create_treebook(pages = pages, 
						mason = mason, initial = initial, 
							inst = instance, key = key, 
									header = header))]
		try:
			title = template.box_labels[widg_dex]
			group = QtGui.QGroupBox(title = title)
			layout = lgb.create_vert_box(tree_widget)
			group.setLayout(layout)
			return [group]

		except AttributeError: return tree_widget

	def interpret_template_list_controller(self, template, widg_dex):
		try: labels = template.labels[widg_dex]
		except AttributeError: labels = []
		try: entries = template.entries[widg_dex]
		except AttributeError: entries = []
		return [lgb.create_list_controller(headers = labels, 
										entries = entries)]

	def interpret_template_console_listener(self, template, widg_dex):
		return [lgb.create_console_listener()]

	def interpret_template_opengl_view(self, template, widg_dex):
		return [lgb.create_opengl_view()]

	def interpret_template_plot(self, template, widg_dex):
		data = template.datas[widg_dex]
		return [lgb.create_plot_widget(data)]

class recasting_mason(standard_mason):

	def __init__(self, parent = None, label =\
				'recasting mason for pyside'):
		standard_mason.__init__(self, label = label, parent = parent)

	def interpret_template_radio(self, template, widg_dex):

		def generate_recast_inst_func(dex):

			def recast_inst_func():
				selected = labels[dex]
				new_class = lfu.lookup_pairwise(zip(
					[base._class for base in 
						instance.valid_base_classes], 
					[base._tag for base in 
						instance.valid_base_classes]), selected)
				instance.recast(new_class)
				instance.rewidget(True)

			return recast_inst_func

		try: labels = template.labels[widg_dex]
		except AttributeError: labels = ['...no labels...']
		try: title = template.box_labels[widg_dex]
		except AttributeError: title = ''
		try: initial = template.initials[widg_dex][0]
		except AttributeError: initial = None
		try: inst_tuple = template.instances[widg_dex][0]
		except AttributeError: inst_tuple = None
		try: key = template.keys[widg_dex][0]
		except AttributeError: key = None
		try: rewidget = template.rewidget[widg_dex][0]
		except AttributeError: rewidget = True
		if inst_tuple:
			instance = inst_tuple[1]
			base_class = inst_tuple[0]

		radios = [lgb.create_radios(options = labels, title = title, 
						initial = initial, instance = base_class, 
								key = key, rewidget = rewidget)]
		[rad.clicked.connect(lgb.create_reset_widgets_wrapper(
			self.parent, generate_recast_inst_func(dex))) for 
			dex, rad in enumerate(radios[0].children()[1:])]
		return radios

class cartographer_mason(standard_mason):

	def __init__(self, parent = None, label = \
				'cartographer mason for pyside'):
		standard_mason.__init__(self, label = label, parent = parent)

	def interpret_template_p_sp(self, template):
		try: mason = template.mason
		except AttributeError: mason = self
		p_sp_panel = lgb.create_panel(template.widg_templates, mason)
		return p_sp_panel

	def interpret_template_text_box(self, template, widg_dex):
		#do text boxes get icons?
		try: icons = template.icons[widg_dex]
		except AttributeError: icons = None
		try: bind_events = template.bind_events[widg_dex]
		except AttributeError: bind_events = None
		try: bindings = template.bindings[widg_dex]
		except AttributeError: bindings = None
		try: placeholder = template.placeholders[widg_dex]
		except AttributeError: placeholder = None
		try: max_leng = template.max_lengths[widg_dex][0]
		except AttributeError: max_leng = None
		try: read_only = template.read_only[widg_dex]
		except AttributeError: read_only = False
		try: multi = template.multiline[widg_dex]
		except AttributeError: multi = False
		try: keep_frame = template.keep_frame[widg_dex]
		except AttributeError: keep_frame = True
		try: alignment = template.alignments[widg_dex][0]
		except AttributeError: alignment = 'left'
		try: instance = template.instances[widg_dex][0]
		except AttributeError: instance = None
		try: key = template.keys[widg_dex][0]
		except AttributeError: key = None
		try: initial = template.initials[widg_dex][0]
		except AttributeError:
			if not (instance is None or key is None):
				initial = instance.__dict__[key]

			else: initial = ''

		widgs = [lgb.create_text_box(instance = instance, key = key, 
				placeholder = placeholder, max_length = max_leng, 
				multiline = multi, read_only = read_only, 
				alignment = alignment, initial = initial, 
				keep_frame = keep_frame, bind_events = bind_events, 
											bindings = bindings)]
		try: p_sp_template = template.parameter_space_templates[widg_dex]
		except AttributeError: p_sp_template = None
		if not p_sp_template is None:
			widgs.append(self.interpret_template_p_sp(p_sp_template))

		try:
			title = template.box_labels[widg_dex]
			group = QtGui.QGroupBox(title = title)
			layout = lgb.create_vert_box(widgs)
			group.setLayout(layout)
			return [group]

		except AttributeError: return widgs

	def interpret_template_spin(self, template, widg_dex):
		try: double = template.doubles[widg_dex][0]
		except AttributeError: double = False
		try: min_val = template.minimum_values[widg_dex][0]
		except AttributeError: min_val = 0
		try: max_val = template.maximum_values[widg_dex][0]
		except AttributeError: max_val = 50
		try: sing_step = template.single_steps[widg_dex][0]
		except AttributeError: sing_step = 1
		try: initial = template.initials[widg_dex][0]
		except AttributeError: initial = 1
		try: instance = template.instances[widg_dex][0]
		except AttributeError: instance = None
		try: key = template.keys[widg_dex][0]
		except AttributeError: key = None
		widgs = [lgb.create_spin_box(double = double, 
					min_val = min_val, max_val = max_val, 
				sing_step = sing_step, initial = initial, 
						instance = instance, key = key)]
		p_sp_template = template.parameter_space_templates[widg_dex]
		if not p_sp_template is None:
			widgs.append(self.interpret_template_p_sp(p_sp_template))

		try:
			title = template.box_labels[widg_dex]
			group = QtGui.QGroupBox(title = title)
			layout = lgb.create_vert_box(widgs)
			group.setLayout(layout)
			return [group]

		except AttributeError: return widgs

class dictionary_support_mason(standard_mason):

	def __init__(self, parent = None, label = \
			'another dictionary support mason'):
		standard_mason.__init__(self, parent = parent, label = label)

	def interpret_template_text_box(self, template, widg_dex):

		def generate_update_wheres_func(widg, inst, 
						wheres, template, widg_dex):

			def update_where():
				new_label = widg.text()
				initial = template.initials[widg_dex][0]
				if new_label == initial: return
				template.initials[widg_dex][0] = new_label
				for whar in wheres:
					if type(whar) is types.ListType:
						print 'why update a list?'

					elif type(whar) is types.DictionaryType:
						whar[new_label] = whar[initial]
						#if issubclass(whar[initial].__class__, 
						#				lfu.modular_object_qt):
						#	whar[initial]._destroy_()
						del whar[initial]
						whar[new_label]._set_label_(new_label)

					else: print 'could not update where:', whar

				inst.rewidget(True)

			return update_where

		try: icons = template.icons[widg_dex]
		except AttributeError: icons = None
		try: bind_events = template.bind_events[widg_dex]
		except AttributeError: bind_events = None
		try: bindings = template.bindings[widg_dex]
		except AttributeError: bindings = None
		try: placeholder = template.placeholders[widg_dex]
		except AttributeError: placeholder = None
		try: max_leng = template.max_lengths[widg_dex][0]
		except AttributeError: max_leng = None
		try: read_only = template.read_only[widg_dex]
		except AttributeError: read_only = False
		try: multi = template.multiline[widg_dex]
		except AttributeError: multi = False
		try: keep_frame = template.keep_frame[widg_dex]
		except AttributeError: keep_frame = True
		try: alignment = template.alignments[widg_dex][0]
		except AttributeError: alignment = 'left'
		try: instance = template.instances[widg_dex][0]
		except AttributeError: instance = None
		try: key = template.keys[widg_dex][0]
		except AttributeError: key = None
		try: initial = template.initials[widg_dex][0]
		except AttributeError:
			if not (instance is None or key is None):
				initial = instance.__dict__[key]

			else: initial = ''

		text_widget = [lgb.create_text_box(instance = instance, 
							key = key, placeholder = placeholder, 
						max_length = max_leng, multiline = multi, 
					read_only = read_only, alignment = alignment, 
					initial = initial, keep_frame = keep_frame, 
				bind_events = bind_events, bindings = bindings)]

		if not template.data_links is None:
			if template.data_links[widg_dex]:
				'''
				if widget_type == 'add_rem_drop_list':
					[last_widgs_reference[0].Bind(widg_specific_event, 
						function) for function in 
						lgb.generate_linkage_assertion_funcs(
							template.data_links[widg_dex])]
					[last_widgs_reference[1].Bind(widg_specific_event, 
						function) for function in 
						lgb.generate_linkage_assertion_funcs(
							template.data_links[widg_dex])]
				'''
				#else:
				[text_widget[0].textChanged.connect(function) for 
					function in lgb.generate_linkage_assertion_funcs(
									template.data_links[widg_dex])]

		if not template.wheres[widg_dex] is None:
			text_widget[0].textChanged.connect(
				generate_update_wheres_func(text_widget[0], 
					instance, template.wheres[widg_dex], 
									template, widg_dex))

		try:
			title = template.box_labels[widg_dex]
			group = QtGui.QGroupBox(title = title)
			layout = lgb.create_vert_box(text_widget)
			group.setLayout(layout)
			return [group]

		except AttributeError: return text_widget

def generate_add_remove_select_inspect_box_template(window, key, 
		labels, wheres, parent, selector_handle, memory_handle, 
		base_class, function_handles = None, verbosities = None):
	if wheres[0] is wheres[1]: whars = wheres[:-1]
	else: whars = wheres
	_add_func_ = lgb.generate_add_function(base_class, 
					parent = parent, wheres = whars)
	_sel_func_ = lgb.generate_selected_function(wheres[1], 
							lfu.grab_mobj_names(wheres[1]), 
							selector_handle, offset = 1)
	_rem_func_ = lgb.generate_remove_function(_sel_func_, 
						parent = parent, wheres = wheres)
	template = interface_template_gui(
				layout = 'grid', 
				widg_positions = [(0, 0), (0, 2), (1, 2)], 
				widg_spans = [(3, 2), None, None], 
				grid_spacing = 10, 
				widgets = ['mobj_catalog', 'button_set'], 
				verbosities = verbosities, 
				instances = [[wheres[1], memory_handle[0]], None], 
				keys = [[None, memory_handle[1]], None], 
				handles = [selector_handle, None], 
				labels = [None, labels], 
				initials = [[memory_handle[0].__dict__[
							memory_handle[1]]], None], 
				bindings = [None, [lgb.create_reset_widgets_wrapper(
												window, _add_func_), 
								lgb.create_reset_widgets_wrapper(
										window, _rem_func_)]])
	if function_handles:
		for dex, func in zip(range(3), 
			[_add_func_, _sel_func_, _rem_func_]):
				if function_handles[dex]:
					for hand in function_handles[dex]:
						hand[0].__dict__[hand[1]] = func

	return template

if __name__ == '__main__': print 'this is a library!'




