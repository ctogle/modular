import libs.modular_core.libfundamental as lfu
import libs.gui.libqtgui as lqg
lgm = lqg.lgm
lgd = lqg.lgd
lgb = lqg.lgb

import sys

class qt_widget_demo_mobject(lfu.modular_object_qt):
	child = lfu.modular_object_qt()
	_children_ = [child]
	menu_templates = []
	tool_templates = []
	
	def __init__(self, *args, **kwargs):
		lfu.modular_object_qt.__init__(self, *args, **kwargs)
		self.label = 'demo_mobject_qt'
		self.dummy_list = ['a', 'b']
		self.abool = True
		self.bbool = False
		self.domain_units = None
		self.range_scheme = None
		self.slide_value = 3
		self.spin_value = 9
	
	def printlist(self):
		print self.dummy_list
		print 'abool', self.abool
		print 'bbool', self.bbool
		print self.slide_value
		print self.spin_value

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		##########
		#slider widget demos
		##########
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['slider'], 
				initials = [[self.slide_value]], 
				orientations = [['horizontal']], 
				minimum_values = [[-10]], 
				maximum_values = [[10]], 
				positions = [['above']], 
				intervals = [[5]], 
				instances = [[self]], 
				keys = [['slide_value']], 
				box_labels = ['Slider Example']))

		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['slider_advanced'], 
				initials = [[self.slide_value]], 
				orientations = [['horizontal']], 
				minimum_values = [[-10]], 
				maximum_values = [[10]], 
				positions = [['above']], 
				intervals = [[5]], 
				instances = [[self]], 
				keys = [['slide_value']], 
				bind_events = [[None, None]], 
				bindings = [[None, None]], 
				box_labels = ['ADV! Slider Example']))

		##########
		#radio widget demos
		##########
		self.widg_templates.append(
			lgm.interface_template_gui(
				layout = 'horizontal', 
				widgets = ['radio', 'radio'], 
				labels = [['seconds', 'minutes', 
						'hours', 'milliseconds'], 
					['absolute', 'normalized', 'differential']], 
				initials = [[self.domain_units], [self.range_scheme]], 
				instances = [[self], [self]], 
				keys = [['domain_units'], ['range_scheme']], 
				box_labels = ['Delay Units', 'Position Units']))

		##########
		#splitter widget demo
		##########
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['splitter'], 
				orientations = [['vertical']], 
				templates = [[self.widg_templates[0], 
							self.widg_templates[1]]]))

		##########
		#check_set widget demos
		##########
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['check_set'], 
				append_instead = [True], 
				provide_master = [True], 
				instances = [[self]],
				keys = [['dummy_list']],
				labels = [['a', 'b']]))
				
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['check_set'], 
				append_instead = [False], 
				provide_master = [True], 
				instances = [[self, self]],
				keys = [['abool', 'bbool']],
				labels = [['abl', 'bbl']]))

		##########
		#file_name_box widget demos
		##########
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['file_name_box'], 
				keys = [['save_filename']], 
				instances = [[self]], 
				initials = [[self.save_filename, 
					'Possible Outputs (*.vtk *.txt)']], 
				labels = [['Choose Filename']], 
				box_labels = ['Default Base Filename']))

		##########
		#directory_name_box widget demos
		##########
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['directory_name_box'], 
				keys = [['save_directory']], 
				instances = [[self]], 
				initials = [[self.save_directory, None, 
					os.path.join(os.getcwd(), 'resources')]], 
				labels = [['Choose Directory']], 
				box_labels = ['Default Save Directory']))

		##########
		#file_name_box widget demos
		##########
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['full_path_box'], 
				keys = [['path']], 
				instances = [[self]], 
				initials = [[self.path, 
					'Possible Outputs (*.*)']], 
				labels = [['Choose File Path']], 
				box_labels = ['File Path']))

		##########
		#spin widget demos
		##########
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['spin'], 
				doubles = [[False]], 
				initials = [[self.spin_value]], 
				minimum_values = [[-10]],
				maximum_values = [[17]],
				single_steps = [[2]], 
				instances = [[self]], 
				keys = [['spin_value']]))

		##########
		#button_set widget demos
		##########
		#this is a maximally complicated button_set template
		self.widg_templates.append(
			lgm.interface_template_gui(
				layout = 'vertical', 
				layouts = ['horizontal'], 
				widgets = ['button_set'], 
				labels = [['Quit', 'Center', 'Read']], 
				tooltips = [['Quit', 'Center Window', 'Read Text']], 
				#icons = [[window.gear_icon, window.gear_icon, None]], 
				minimum_sizes = [[None, (150, 150), None]], 
				maximum_sizes = [[None, None, (20, 20)]], 
				subspacers = [[2, 1]], 
				bindings = [[window.on_close, 
					window.on_close, window.on_close]], 
				#	[window.center, window.read_text], 
				#			window.read_text]], 
				bind_events = [['clicked', 
					#['pressed', 'released'], None]]))
					'released', None]]))
		#this is a minimally complicated button_set template
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['button_set'], 
				bindings = [[window.on_close, window.on_close]]))

		##########
		#text box widget demos
		##########
		#this is the maximally complicated text template
		self.widg_templates.append(
			lgm.interface_template_gui(
				layout = 'vertical', 
				layouts = ['vertical'], 
				widgets = ['text'], 
				read_only = [True], 
				multiline = [False], 
				initials = [[self.label]], 
				tooltips = [['Mobj Label']], 
				#placeholders = ['placeholder'], #this is only for multilines
				alignments = [['center']], 
				#icons = [window.gear_icon], 
				minimum_sizes = [[(150, 150)]], 
				keep_frame = [True], 
				max_lengths = [[100]], 
				#these need to be resolved in libqtgui_bricks
				instances = [[self]], 
				keys = [['label']], 
				#if the binding provided is None, 
				#the binding should update instance.__dict__[key]
				#bindings = [[window.read_text, window.center]], 
				bind_events = [['enter', 'changed']]))
		#this is the minimally complicated text template
		self.widg_templates.append(
			lgm.interface_template_gui(widgets = ['text']))

		##########
		#tabbook widget demos
		##########
		#try: labels = template.labels[widg_dex]
		#except AttributeError: labels = []
		#try: icons = template.icons[widg_dex]
		#except AttributeError: icons = []
		#try: datas = template.datas[widg_dex]
		#except AttributeError: datas = []

		#self.widg_templates.append(
		#	lgm.interface_template_gui(
		#		widgets = ['tab_book'], 
		#		pages = [self.make_tab_book_pages(*args, **kwargs)]))

		##########
		#panel widget demos
		##########
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['panel'], 
				templates = [self.child.widg_templates]))

		##########
		#selector layout widget demos
		##########
		self.widg_templates.append(
			lgm.interface_template_gui(
				layout = 'grid', 
				widg_positions = [(0, 0), (1, 0), (0, 1), (1, 1)], 
				widg_spans = [None, (2, 1), (1, 2), None], 
				grid_spacing = 10, 
				widgets = ['button_set', 'selector'], 
				handles = [None, (self, 'ensem_selector')], 
				labels = [[	'Add Ensemble', 
							'Remove Ensemble', 
							'Update GUI'], 
							[item for item in self.dummy_list]], 
							#[ensem.label for ensem 
							#	in self.ensembles]], 
				bindings = [[
					lgb.create_reset_widgets_wrapper(
						window, self.printlist), 
					lgb.create_reset_widgets_wrapper(
						window, self.printlist), 
					lgb.create_reset_widgets_function(
						window)], [None]]))

		##########
		#grid layout widget demos
		##########
		self.widg_templates.append(
			lgm.interface_template_gui(
				layout = 'grid', 
				box_positions = [(0, 0), (1, 0), (0, 1), (1, 1)], 
				widg_spans = [None, (2, 1), (1, 2), None], 
				grid_spacing = 10, 
				widgets = ['button_set', 'selector'], 
				handles = [None, (self, 'ensem_selector')], 
				labels = [[	'Add Ensemble', 
							'Remove Ensemble', 
							'Update GUI'], 
							[item for item in self.dummy_list]], 
							#[ensem.label for ensem 
							#	in self.ensembles]], 
				bindings = [[
					lgb.create_reset_widgets_wrapper(
						window, self.printlist), 
					lgb.create_reset_widgets_wrapper(
						window, self.printlist), 
					lgb.create_reset_widgets_function(
						window)], [None]]))

		##########
		#image widget demos
		##########
		#self.widg_templates.append(
		#	lgm.interface_template_gui(
		#		widgets = ['image'], 
		#		paths = [img_path]))

		##########
		lfu.modular_object_qt.set_settables(self, *args, 
										from_sub = True)

class application_widget_dev(lqg.application):
	_content_ = [qt_widget_demo_mobject()]

	def __init__(self, *args, **kwargs):
		lqg.application.__init__(self, *args, **kwargs)
		#lqg.application.setStyle(lgb.create_style('windows'))
		#lqg.application.setStyle(lgb.create_style('xp'))
		#lqg.application.setStyle(lgb.create_style('vista'))
		#lqg.application.setStyle(lgb.create_style('motif'))
		#lqg.application.setStyle(lgb.create_style('cde'))
		lqg.application.setStyle(lgb.create_style('plastique'))
		#lqg.application.setStyle(lgb.create_style('clean'))

def initialize_gui(params):
	app = application_widget_dev(params, sys.argv)
	sys.exit(app.exec_())

