import modular_core.libfundamental as lfu
import modular_developer.libcodegenerator as lcg

import os
import pdb

class modular_object_manager(lfu.modular_object_qt):
	#	create modular objects
	#	add/remove widgets and methods
	#	test these by running them locally as a program
	def __init__(self, *args, **kwargs):
		self.mobject_analyzer = mobject_analyzer(parent = self)
		self.mobject_hierarchy = mobject_hierarchy(parent = self)
		self._active_mobj_text_ = ''
		self._code_writer_ = lcg.code_writer()
		lfu.modular_object_qt.__init__(self, *args, **kwargs)
		self._children_ =\
			[self.mobject_analyzer, 
			self.mobject_hierarchy]

	def new_modular_object(self, name = '_new_mobject_', 
			attributes = [], methods = [], imposed = False):
		if self.mobject_analyzer._active_mobject_name_ and not imposed:
			name = self.mobject_analyzer._active_mobject_name_
		attrs = self.mobject_analyzer._active_mobject_attributes_
		if attrs and not imposed: attributes = attrs
		meths = self.mobject_analyzer._active_mobject_methods_
		if meths and not imposed: methods = meths
		self._active_mobj_text_ = self._code_writer_.make_mobject(
			name = name, attributes = attributes, methods = methods)
		self._active_mobj_widg_[0].setText(self._active_mobj_text_)
		self.mobject_analyzer.analyze_mobject_text(
							self._active_mobj_text_)
		self.rewidget(True)

	def impose_modular_object(self, name = '_new_mobject_', 
								attrs = [], methods = []):
		if self.mobject_analyzer._active_mobject_name_:
			name = self.mobject_analyzer._active_mobject_name_
		if self.mobject_analyzer._active_mobject_attributes_:
			attrs = self.mobject_analyzer._active_mobject_attributes_
		if self.mobject_analyzer._active_mobject_methods_:
			methods = self.mobject_analyzer._active_mobject_methods_
		self.new_modular_object(name = name, attributes = attrs, 
							methods = methods, imposed = True)

	def analyze_modular_object(self):
		self.mobject_analyzer.analyze_mobject_text(
							self._active_mobj_text_)



	def run_modular_object(self, window):
		self.mobject_hierarchy.mobject_analysis_set_settables(
						window, mobj = self.current_text_mobj)
		templates = self.mobject_hierarchy.mobject_analysis_templates
		attr_panel = lgm.interface_template_gui(
						widgets = ['panel'], 
						box_labels = ['Mobjects Interface'], 
						templates = [templates])
		methods = self.mobject_hierarchy.mobject_analysis_methods
		helpers = [meth.generate_template() for meth in methods]
		helper_panel = lgm.interface_template_gui(
						widgets = ['panel'], 
						layouts = ['vertical'], 
						box_labels = ['Additional Test Controls'], 
						templates = [helpers])
		splitter = lgm.interface_template_gui(
					widgets = ['splitter'], 
					orientations = [['horizontal']], 
					templates = [[attr_panel, helper_panel]])
		self.mobject_analysis_panel = lgb.create_scroll_area(
					lgb.create_panel([splitter], self.mason))
		panel_x = self.mobject_analysis_panel.sizeHint().width()*1.5
		panel_y = self.mobject_analysis_panel.sizeHint().height()*1.25
		panel_x, panel_y = min([panel_x, 1600]), min([panel_y, 900])
		self.mobject_analysis_panel.setGeometry(
					150, 120, panel_x, panel_y)
		self.mobject_analysis_panel.show()



	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		mobjects_templates_top =\
			lgm.interface_template_gui(
				widgets = ['button_set'], 
				layout = 'horizontal', 
				labels = [['Write Mobject', 
					'Analyze Mobject', 'Run Mobject']], 
				bindings = [[
					lgb.create_reset_widgets_wrapper(window, 
								self.impose_modular_object), 
					lgb.create_reset_widgets_wrapper(window, 
								self.analyze_modular_object), 
					lgb.create_function_with_args(
						self.run_modular_object, 
						func_args = (window,))]])
		mobjects_templates_bottom = [
			lgm.interface_template_gui(
				widgets = ['text'], 
				multiline = [True], for_code = [True], 
				handles = [(self, '_active_mobj_widg_')], 
				initials = [[self._active_mobj_text_]], 
				alignments = [['left']], 
				minimum_sizes = [[(786, 256)]], 
				instances = [[self]], 
				keys = [['_active_mobj_text_']]), 
			lgm.interface_template_gui(
				widgets = ['panel'], 
				layout = 'horizontal', 
				templates = [self.mobject_analyzer.widg_templates], 
				box_labels = ['Mobject Analyzer'])]
		bottom_splitter = lgm.interface_template_gui(
							widgets = ['splitter'], 
							orientations = ['horizontal'], 
							templates = [mobjects_templates_bottom])
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['splitter'], 
				orientations = [['vertical']], 
				templates = [[mobjects_templates_top, 
									bottom_splitter]]))
		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)

class mobject_analyzer(lfu.modular_object_qt):

	def __init__(self, *args, **kwargs):
		self.temp_mobj_code_path = os.path.join(os.getcwd(), 'libs', 
						'developer', 'libdeveloper_temp_module.py')
		self._panel_scroll_memory_ = None
		self._active_mobject_ = None
		self._active_mobject_name_ = ''
		self._active_mobject_methods_ = []
		self._active_mobject_attributes_ = []

		'''
		self.mobject_subclasses = []
		self.mobject_names = []

		self.mobject_analysis_name = ''
		self.mobject_analysis_attributes = []
		self.mobject_analysis_attr_labels = []
		self.mobject_analysis_methods = []
		self.mobject_analysis_arrangements = []

		self.method_selector = None
		self.attribute_selector = None
		self.method_selected_memory = None
		self.attribute_selected_memory = None
		self.arrangement_selected_memory = None
		'''

		self._code_writer_ = lcg.code_writer()
		lfu.modular_object_qt.__init__(self, *args, **kwargs)

	def read_mobject_name(self, text, 
			super_ = '(lfu.modular_object_qt)'):
		class_dex = text.find('class ') + len('class ')
		class_name_end_dex = text[class_dex:].find(super_) + class_dex
		name = text[class_dex:class_name_end_dex]
		return name



	def make_attribute_templates(self, *args, **kwargs):
		templates = []
		for attr in self.mobject_analysis_attributes:
			attr.set_settables(*args, **kwargs)
			templates.extend(attr.widg_templates)

		return templates

	def make_method_templates(self, *args, **kwargs):
		templates = []
		for meth in self.mobject_analysis_methods:
			meth.set_settables(*args, **kwargs)
			templates.extend(meth.widg_templates)

		return templates

	def analyze_mobject_text(self, text):
		name = self.read_mobject_name(text)
		self._active_mobject_name_ = name

		self.mobject_analysis_name_box[0].children()[1].setText(name)
		self.mobject_analysis_attr_labels = []
		self.mobject_analysis_attributes =\
			self.read_mobject_attributes(text)
		self.mobject_analysis_methods =\
			self.read_mobject_methods(text)
		self.rewidget(True)



	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		split_one = lgm.interface_template_gui(
				widgets = ['text'], 
				handles = [(self, '_active_mobject_name_widg_')], 
				minimum_sizes = [[(150, 75)]], 
				panel_position = (0, 0), 
				panel_scrollable = True, 
				panel_scroll_memory = (self, '_panel_scroll_memory_'), 
				instances = [[self]], 
				keys = [['_active_mobject_name_']], 
				box_labels = ['Mobject Name'])

		'''
		attribute_templates =\
			self.make_attribute_templates(*args, **kwargs)
		method_templates =\
			self.make_method_templates(*args, **kwargs)
		mobj_attribute_templates = [
			lgm.generate_add_remove_select_inspect_box_template(
				window = window, key = 'mobject_analysis_attributes', 
				labels = ['Add Attribute', 'Remove Attribute'], 
				wheres = [self.mobject_analysis_attributes, 
						self.mobject_analysis_attributes], 
				parent = self, 
				selector_handle = (self, 'attribute_selector'), 
				memory_handle = (self, 'attribute_selected_memory'), 
				base_class = mobject_attribute)]
		mobj_method_templates = [
			lgm.generate_add_remove_select_inspect_box_template(
				window = window, key = 'mobject_analysis_methods', 
				labels = ['Add Method', 'Remove Method'], 
				wheres = [self.mobject_analysis_methods, 
						self.mobject_analysis_methods], 
				parent = self, 
				selector_handle = (self, 'method_selector'), 
				memory_handle = (self, 'method_selected_memory'), 
				base_class = mobject_method)]
		split_three = lgm.interface_template_gui(
				widgets = ['panel', 'panel', 'panel', 'panel'], 
				widg_positions = [(1, 0), (1, 1), (0, 0), (0, 1)], 
				layout = 'grid', 
				panel_position = (2, 0), 
				layouts = ['vertical', 'vertical', None, None], 
				scrollable = [True, True, False, False], 
				templates = [attribute_templates, method_templates, 
					mobj_attribute_templates, mobj_method_templates], 
				box_labels = ['Attributes', 'Methods', 
					'Mobjects Attributes', 'Mobjects Methods'])
		'''

		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['splitter'], 
				scrollable = [True], 
				orientation = ['vertical'], 
				templates = [[split_one]]))
				#templates = [[split_one, split_three, split_two]]))
		lfu.modular_object_qt.set_settables(
			self, *args, from_sub = True)

class mobject_hierarchy(lfu.modular_object_qt):

	def __init__(self, *args, **kwargs):
		self._code_writer_ = lcg.code_writer()
		lfu.modular_object_qt.__init__(self, *args, **kwargs)

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		lfu.modular_object_qt.set_settables(
			self, *args, from_sub = True)

if __name__ == 'modular_developer.libmobjectdeveloper':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'


