import libs.modular_core.libfundamental as lfu
import libs.modular_core.libfiler as lf
import libs.modular_core.liboutput as lo
import libs.modular_core.libgeometry as lgeo
import libs.modular_core.libcriterion as lc
import libs.modular_core.libvtkoutput as lvtk
import libs.modular_core.libiteratesystem as lis

import math
import os
import random

import pdb

if __name__ == 'libs.modular_core.libfitroutine':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'

class fit_routine_plan(lfu.plan):

	def __init__(self, parent = None, label = 'fit routine plan', 
							routines = [], fit_criterion = None):
		self.routines = routines
		self.selected_routine = None
		lfu.plan.__init__(self, parent = parent, label = label)

	def enact_plan(self, *args, **kwargs):
		for routine in self.routines:
			check1 = time.time()
			routine(*args, **kwargs)
			print ' '.join(['completed fit routine:', routine.label, 
						'in:', str(time.time() - check1), 'seconds'])

	def add_routine(self):
		new = fit_routine_simulated_annealing(parent = self)
		self.routines.append(new)
		self._children_.append(new)
		self.rewidget(True)

	def remove_routine(self):
		select = self.get_selected()
		if select:
			self.routines.remove(select)
			self._children_.remove(select)

		self.rewidget(True)

	def get_selected(self):
		key = 'routine_selector'
		if not hasattr(self, key):
			print 'no selector'; return

		try:
			select = self.__dict__[key][
				self.__dict__[key][0].currentIndex()]
			return select

		except IndexError:
			print 'no routine selected'; return

	def set_settables(self, *args, **kwargs):
		window = args[0]
		#ensemble = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		'''
		if not selected_routine is None:
			where_reference = ensemble.run_params['output_plans']
			rout_remove_data_links = [lfu.interface_template_dependance(
				(where_reference, selected_routine.label, True), 
				linkages = [(where_reference, selected_routine.label, 
											True, 'direct_remove')])]

		else:
			where_reference = None
			rout_remove_data_links = None
		'''
		try: select_label = self.selected_routine.label
		except AttributeError: select_label = None
		'''
		self.widg_templates.append(
			lgm.interface_template_gui(
				layout = 'grid', 
				widg_positions = [(0, 0), (0, 2), (1, 2), (2, 2)], 
				widg_spans = [(3, 2), None, None, None], 
				grid_spacing = 10, 
				widgets = ['mobj_inspector', 'button_set', 'selector'], 
				instances = [[self.selected_routine], None, None], 
				handles = [None, None, (self, 'routine_selector')], 
				labels = [None, ['Add Fit Routine', 
								'Remove Fit Routine'], 
						lfu.grab_mobj_names(self.routines)], 
				initials = [None, None, [select_label]], 
				bindings = [None, [lgb.create_reset_widgets_wrapper(
										window, self.add_routine), 
						lgb.create_reset_widgets_wrapper(window, 
								self.remove_routine)], None]))
		'''
		img_path = os.path.join(os.getcwd(), 
			'resources', 'coming-soon.png')
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['image'], 
				paths = [img_path]))
		lfu.plan.set_settables(self, *args, from_sub = True)

class fit_routine(lfu.modular_object_qt):

	#ABSTRACT
	#base class should not assume scalers are the data object
	def __init__(self, label = 'another fit routine', 
			iteration = 1, ensemble = None, bAbort = False, 
			fitter_criteria = [], fitted_criteria = [], data = [], 
			valid_base_classes = None, capture_targets = [], 
			visible_attributes = ['label'], base_class = None, 
			selected_fitter_criterion = None, 
			fitter_bool_expression = None, 
			selected_fitted_criterion = None, 
			fitted_bool_expression = None, 

		fit_data = [], fit_domain = [], 
		run_data = [], 
		data_id_x = None, data_id_y = None, 
		metrics = [], routine = None, 
		parameter_space = None, p_sp_trajectory = []):


		self.__dict__ = lfu.dictionary()
		self.brand_new = True
		if valid_base_classes is None:
			self.valid_base_classes =\
				valid_fit_routine_base_classes

		if base_class is None:
			base_class = lfu.interface_template_class(
					object, 'fit routine abstract')

		self.bAbort = bAbort
		self.fitter_criteria = fitter_criteria
		self.fitted_criteria = fitted_criteria
		self.selected_fitter_criterion = selected_fitter_criterion
		self.selected_fitted_criterion = selected_fitted_criterion
		self.fitter_bool_expression = fitter_bool_expression
		self.fitted_bool_expression = fitted_bool_expression
		#self.__dict__.create_partition('template owners', [])

		#self.data_id_y_list = data_id_y_list
		self.iteration = iteration
		self.ensemble = ensemble
		#self.run_data = run_data
		#self.data_id_x = data_id_x
		#self.data_id_y = data_id_y
		self.metrics = metrics
		self.capture_targets = capture_targets

		lfu.modular_object_qt.__init__(self, label = label, data = data, 
							valid_base_classes = valid_base_classes, 
							visible_attributes = visible_attributes, 
											base_class = base_class)
		self.output = lo.output_plan(label = self.label, parent = self)


		self.parameter_space = parameter_space
		self.p_sp_trajectory = p_sp_trajectory

	def __call__(self, *args, **kwargs):
		self.initialize(*args, **kwargs)				
		run_func = lis.run_system
		while not self.bAbort and not\
				self.verify_criteria_list(
					self.fitted_criteria):
			self.iterate(run_func)

		self.handle_fitting_key()
		if self.output.must_output(): self.output(self)

	def initialize(self, *args, **kwargs):
		pass

	def iterate(self, run_func = None):
		pass

	def handle_fitting_key(self):
		pdb.set_trace()
		lines = ['Fit Routine Fitting Key: ']
		for k in range(len(self.p_sp_trajectory)):
			lines.append('\tTrajectory : ' + str(k + 1))
			for ax in self.p_sp_trajectory[k]:
				lines.append('\t\t' + ax[0] + ' : ' + ax[1])

			lines.append('\n')

		lf.output_lines(lines, self.output.save_directory, 
										'fitting_key.txt')





	def gather_plot_targets(self, ensem):
		print 'override this function!'

	#def update_output_plan(self):
	#	self.output.targets = {'OUTPUTABLES': self.targets,
	#						'WRITE_FUNCS': [[LVTK.write_unstructured], [LO.write_pkl], [], []], 
	#						'WRITE_TAGS': [['Unstructured Scalers'], ['Any Data'], [], []]}

	def move_in_parameter_space(self):
		print 'override this function!'

	def attach_data_to_metrics(self):
		dex_x = [dater.name for dater in self.run_data].index(self.data_id_x)
		y_daters = [dater for dater in self.run_data 
					if dater.name in self.data_id_y_list]
		dater_x = self.run_data[dex_x]
		for metric in self.metrics:
			metric.to_compare = (dater_x, y_daters)

	#def verify_end_criteria(self):
	#	for crit in self.fitted_criteria:
	#		if crit.verify_pass(self):
	#			return True

	#	return False

	def verify_fitter_criteria(self):
		metric_daters = [metric.dater for metric in self.metrics]
		for (crit, dater) in (self.fitter_criteria, metric_daters):
			if crit.verify_pass(dater):
				return True

		return False

	def generate_add_crit_func(self, frame, select = 'fitter'):

		def on_add_crit(event):
			targets = self.__dict__['_'.join([
						select, 'criteria'])]
			targets.append(lc.criterion_iteration())
			targets[-1].set_settables(
				*frame.settables_infos)

		return on_add_crit

	def generate_remove_crit_func(self, frame, select = 'fitter'):

		def on_remove_crit(event):
			try:
				selected = self.__dict__['_'.join([
					'selected', select, 'criterion'])]
				targets = self.__dict__['_'.join([
							select, 'criteria'])]
				targets.remove(selected)
				selected = targets[-1]

			except AttributeError:
				pass

			except IndexError:
				selected = None

		return on_remove_crit

	def generate_select_crit_func(self, frame, select = 'fitter'):

		def on_select_crit(event):
			key = '_'.join(['selected', select, 'criterion'])
			targets = self.__dict__['_'.join([select, 'criteria'])]
			self.__dict__[key] = lfu.grab_mobj_by_name(
				event.GetEventObject().GetLabel(), targets)

		return on_select_crit

	def set_settables(self, *args, **kwargs):
		ensem = args[0]
		frame = args[1]
		recaster = lgm.recasting_mason(frame)
		dictionary_support = lgm.dictionary_support_mason(frame)
		if self.brand_new:
			self.brand_new = not self.brand_new
			ensem.run_params['output_plans'][self.label] = self.output

		where_reference = ensem.run_params['output_plans']
		label_data_links = [lfu.interface_template_dependance(
						(self, 'label', self.label), linkages =\
						[(where_reference[self.label], 'label', 
											True, 'direct')])]
		self.handle_widget_inheritance(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widget_layout = 'vert', 
				widget_mason = dictionary_support, 
				data_links = [label_data_links], 
				where_store = where_reference, 
				key = ['label'], 
				instance = [self], 
				widget = ['text'], 
				box_label = 'Fit Routine Name', 
				initial = [self.label], 
				sizer_position = (0, 0)))
		classes = [template._class for template 
					in self.valid_base_classes]
		tags = [template._tag for template 
				in self.valid_base_classes]
		self.widg_templates.append(
			lgm.interface_template_gui(
				widget_mason = recaster, 
				widget_layout = 'vert', 
				key = ['_class'], 
				instance = [[self.base_class, self]], 
				widget = ['rad'], 
				hide_none = [True], 
				box_label = 'Routine Type', 
				initial = [self.base_class._tag], 
				possibles = [tags], 
				possible_objs = [classes], 
				sizer_position = (1, 0)))
		#widgets for sources
		self.widg_templates.append(
			lgm.interface_template_gui(
				widget_mason = recaster, 
				widget_layout = 'vert', 
				key = ['_class'], 
				instance = [[self.base_class, self]], 
				widget = ['rad'], 
				hide_none = [True], 
				box_label = 'Data Sources', 
				initial = [self.base_class._tag], 
				possibles = [tags], 
				possible_objs = [classes], 
				sizer_position = (0, 1)))
		if not self.selected_fitter_criterion is None:
			selected_fitter_crit_label =\
				self.selected_fitter_criterion.label
			self.selected_fitter_criterion.set_settables(*args, **kwargs)
			self.widg_templates.append(
				lgm.interface_template_gui(
					widget_layout = 'vert', 
					box_label = 'Is Fitter Criterion', 
					widget = ['panel'], 
					sizer_position = (0, 3), 
					instance = self.selected_fitter_criterion, 
					frame = frame, 
					widget_mason = frame.mason, 
					widget_templates =\
						self.selected_fitter_criterion.widg_templates))

		else:
			selected_fitter_crit_label = None

		if not self.selected_fitted_criterion is None:
			selected_fitted_crit_label =\
				self.selected_fitted_criterion.label
			self.selected_fitted_criterion.set_settables(*args, **kwargs)
			self.widg_templates.append(
				lgm.interface_template_gui(
					widget_layout = 'vert', 
					box_label = 'Is Fitted Criterion', 
					widget = ['panel'], 
					sizer_position = (1, 3), 
					instance = self.selected_fitted_criterion, 
					frame = frame, 
					widget_mason = frame.mason, 
					widget_templates =\
						self.selected_fitted_criterion.widg_templates))

		else:
			selected_fitted_crit_label = None

		if self.fitter_bool_expression is None:
			self.fitter_bool_expression = ''

		if self.fitted_bool_expression is None:
			self.fitted_bool_expression = ''

		self.widg_templates.append(
			lgm.interface_template_gui(
				widget = ['button_set', 'selector', 'text'], 
				widget_layout = 'vert', 
				key = [None, None, 'fitter_bool_expression'], 
				instance = [None, None, self], 
				functions = [[	self.generate_add_crit_func(frame), 
							self.generate_remove_crit_func(frame)], 
							[self.generate_select_crit_func(frame)], 
															None], 
				gui_labels = [	[	'Add Fitter Criterion', 
									'Remove Fitter Criterion'	], 
								[	crit.label for crit 
									in self.fitter_criteria	], None	], 
				initial = [None, selected_fitter_crit_label, 
								self.fitter_bool_expression], 
				sub_box_labels = [	'', '', 
									'Boolean Expression of Criteria'], 
				sizer_proportions = [1, 1, 1, 2], 
				box_label = 'Is Fitter Criteria', 
				sizer_position = (0, 2)))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widget = ['button_set', 'selector', 'text'], 
				widget_layout = 'vert', 
				key = [None, None, 'fitted_bool_expression'], 
				instance = [None, None, self], 
				functions = [[self.generate_add_crit_func(
								frame, select = 'fitted'), 
							self.generate_remove_crit_func(
								frame, select = 'fitted')], 
							[self.generate_select_crit_func(
								frame, select = 'fitted')], None], 
				gui_labels = [	[	'Add Fitted Criterion', 
									'Remove Fitted Criterion'	], 
								[	crit.label for crit 
									in self.fitted_criteria	], None	], 
				initial = [None, selected_fitted_crit_label, 
								self.fitted_bool_expression], 
				sub_box_labels = [	'', '', 
									'Boolean Expression of Criteria'], 
				sizer_proportions = [1, 1, 1, 2], 
				box_label = 'Is Fitted Criteria', 
				sizer_position = (1, 2)))

		#widgets for parameter space
		#widgets for metrics
		#widgets for controlling pyplot display

class fit_routine_simulated_annealing(fit_routine):

	def __init__(self, *args, **kwargs):
		if not 'label' in kwargs.keys():
			kwargs['label'] = 'another simulated annealing routine'

		if not 'base_class' in kwargs.keys():
			kwargs['base_class'] = lfu.interface_template_class(
								object, 'simulated annealing')

		if not 'data' in kwargs.keys():
			kwargs['data'] = lgeo.scalers_from_labels(
				['simulated annealing iteration', 'temperature'])

		fit_routine.__init__(self, *args, **kwargs)
		self.impose_default('cooling_dex', 0, **kwargs)
		self.impose_default('cooling_curve', None, **kwargs)
		self.impose_default('temperature', None, **kwargs)
		self.__dict__.create_partition('template owners', 
										['cooling_curve'])

	def initialize(self, ensem):
		#self.best_match = [(1e10, 0)]
		self.ensemble = ensem
		self.temperature = self.cooling_curve.scalers[self.cooling_dex]
		self.parameter_space =\
			lgeo.generate_parameter_space_from_run_params(
										self, 
										ensem.run_params, 
										[template.name 
											for template 
											in ensem.templates])
		self.parameter_space.initial_factor = self.temperature
		self.parameter_space.set_start_pt()
		
		pdb.set_trace()
		for metric in self.metrics:
			metric.initialize()
			metric.compare_to = self.compare_to
			metric.compare_to_id_x = self.compare_to_id_x
			metric.compare_to_id_y_list = self.compare_to_id_y_list

		self.iteration = 0

	def iterate(self, run_func):
		pdb.set_trace()
		print '\niteration: ' + str(self.iteration) + ' temperature: ' + str(self.temperature)
		self.run_data = run_func(self.ensemble)
		self.attach_data_to_metrics()
		for metric in self.metrics:
			metric.measure()

		self.capture_plot_data()
		print '\n'
		self.iteration += 1



	def gather_plot_targets(self, ensem):
		new_daters = [[LGEO.scalers(name = metric.label +\
									' measure of ' + name) 
						for name in self.data_id_y_list] 
								for metric in self.metrics]
		self.data = self.data[0:2] + [item for sublist in new_daters 
												for item in sublist]
		self.targets = [dater.name for dater in self.data]

	def capture_plot_data(self):
		self.data[0].scalers.append(self.iteration)
		self.data[1].scalers.append(self.temperature)
		bump = 0
		for j in range(len(self.metrics)):
			for k in range(bump, bump + len(self.metrics[j].data)):
				for dater in self.metrics[j]:
					self.data[k].scalers.append(dater.scalers[-1])			

			bump += len(self.metrics[j].data)

		'''
		if True in [math.isnan(measure) for measure in 
			[meas[0] for meas in self.run_fit_qualities]] or \
				min([meas[2] for meas in self.run_fit_qualities[:-1]]) <= 100 or\
					True in [math.isnan(measure) for measure in 
							[meas[3] for meas in self.run_fit_qualities[:-1]]]:
								print 'invalid run measurement: forcing undo ' +\
									'and unbiased next step - not capturing!'
								self.move_in_parameter_space(bypass = True)

		else:
			#self.data[0].scalers.append(self.run_fit_quality_x)
			#self.data[1].scalers.append(self.iteration)
			#self.data[2].scalers.append(self.temperature)
			self.data[0].scalers.append(self.iteration)
			self.data[1].scalers.append(self.temperature)
			for k in range(2, len(self.data)):
				self.data[k].scalers.append(
					self.run_fit_qualities[k - 2][0])

			for k in range(len(self.data_2)):
				self.data_2[k].scalers.append(
					self.run_fit_qualities[k][3])

			for k in range(len(self.data_3)):
				self.data_3[k].scalers.append(
					self.run_fit_qualities[k][4])
		'''

		self.p_sp_trajectory.append(
			self.parameter_space.get_current_position())
		
		self.move_in_parameter_space()

	def move_in_parameter_space(self, bypass = False, 
										many_steps = 10):
		try:
			self.temperature =\
				self.cooling_curve.scalers[self.cooling_dex]

		except IndexError:
			self.temperature = self.cooling_curve.scalers[-1]

		self.cooling_dex += 1
		if self.verify_fitter_criteria() and bypass == False:
			self.parameter_space.take_biased_step_along_axis(
											self.temperature)

		else:
			self.parameter_space.undo_step()
			#for k in range(many_steps):
			#	self.parameter_space.take_proportional_step(
			#								self.temperature)
			self.parameter_space.take_proportional_step(
									factor = self.temperature, 
									many_steps = many_steps)



	def set_settables(self, *args, **kwargs):
		ensem = args[0]
		frame = args[1]
		self.handle_widget_inheritance(*args, from_sub = False)
		if hasattr(self, 'cooling_curve'):
			if self.cooling_curve is None:
				self.cooling_curve = lgeo.scalers_exponential_curve(
						label = 'sim-ann expo-curve', parent = self)

		else:
			self.cooling_curve = lgeo.scalers_exponential_curve(
					label = 'sim-ann expo-curve', parent = self)

		self.cooling_curve.set_settables(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widget_layout = 'vert', 
				box_label = 'Cooling Curve', 
				widget = ['panel'], 
				sizer_position = (2, 0), 
				sizer_span = (1, 4), 
				minimum_size = (980, 256), 
				instance = self.cooling_curve, 
				frame = frame, 
				widget_mason = frame.mason, 
				widget_templates =\
					self.cooling_curve.widg_templates))
		'''
		self.widg_templates.append(
			lgm.interface_template_gui(
						widget_layout = 'vert', 
						key = [	'max_time'	], 
						instance = [self], 
						widget = ['text'],
						box_label = 'Max Simulation Time', 
						initial = [self.max_time], 
						sizer_position = (0, 2)))
		'''
		super(fit_routine_simulated_annealing, self).set_settables(
											*args, from_sub = True)
		'''
		self.templates = []
		curve_name_list = ['Exponential', 'Piecewise']
		curve_func_list = [LGEO.exponential_curve, LGEO.piecewise_curve]
		curve = self.cooling_curve
		try:
			initial_curve_label =\
					curve_name_list[[isinstance(curve, curve_class) 
						for curve_class in curve_func_list].index(True)]
			self.cooling_curve.set_settables()
			self.templates.extend(self.cooling_curve.templates)

		except ValueError:
			initial_curve_label = 'none'

		self.templates.append(
			LFU.interface_template(
					name = 'cooling_curve', 
					instance = self, 
					gui_widg = 'rad', 
					gui_label = 'Cooling Curve', 
					sizer_position = (0, 0), 
					values = curve_name_list, 
					valuables = curve_func_list, 
					initial_valuable = curve, 
					initial_value = initial_curve_label, 
					nested_obj = True))
		self.templates.append(
			LFU.interface_template(
					name = 'data_id_x', 
					instance = self, 
					gui_widg = 'rad', 
					gui_label = 'Data To Compare(x-axis)', 
					sizer_position = (0, 1), 
					values = ensem.output.targeted,
					valuables = ensem.output.targeted, 
					initial_value = self.data_id_x))
		self.templates.append(
			LFU.interface_template(
					name = 'data_id_y_list', 
					instance = self, 
					gui_widg = 'check_list', 
					gui_label = 'Data To Compare(y-axis)', 
					sizer_position = (0, 2), 
					values = ensem.output.targeted,
					valuables = ensem.output.targeted, 
					initial_value = self.data_id_y_list))
		fit_done_crit_names = [	'1000 iterations', 
								'100 undo levels', 
								'0 temperature'	]
		fit_done_crit_classes = [	lc.criterion, 
									sa_undo_criterion, 
									sa_temp_criterion	]
		self.templates.append(
			LFU.interface_template(
					name = 'fitted_criteria', 
					instance = self, 
					gui_widg = 'fetch_obj', 
					gui_label = 'Fit Complete Criteria', 
					sizer_position = (0, 3), 
					values = fit_done_crit_names,
					valuables = fit_done_crit_classes, 
					initial_valuable = self.fitted_criteria, 
					diag_class = LGDIG.make_crit_dialog, 
					append_instead = True))
		self.templates.append(
			LFU.interface_template(
					name = 'compare_to', 
					instance = self, 
					gui_widg = 'fetch_obj', 
					gui_label = 'Grab Some Data', 
					sizer_position = (0, 4), 
					initial_valuable = self.compare_to, 
					diag_class = LGDIG.load_pkl_dialog))
		if self.compare_to is not None:
			compare_to_dater_names = [dater.name for dater 
									in self.compare_to.data]

		else:
			compare_to_dater_names = []

		self.templates.append(
			LFU.interface_template(
					name = 'compare_to_id_x', 
					instance = self, 
					gui_widg = 'rad', 
					gui_label = 'Data To Compare To (x-axis)', 
					sizer_position = (0, 5), 
					values = compare_to_dater_names,
					valuables = compare_to_dater_names, 
					initial_value = self.compare_to_id_x))
		self.templates.append(
			LFU.interface_template(
					name = 'compare_to_id_y_list', 
					instance = self, 
					gui_widg = 'check_list', 
					gui_label = 'Data To Compare To (y-axis)', 
					sizer_position = (0, 6), 
					values = compare_to_dater_names,
					valuables = compare_to_dater_names, 
					initial_value = self.compare_to_id_y_list))

		'''
		'''fitter_crit_names = ['minimize fit quality measurement', 
							'minimize metric measurements']
		fitter_crit_classes = [sa_minim_run_fit_quality_criterion, 
								criterion_sa_minimize_measures]
		self.templates.append(
			LFU.interface_template(
					name = 'fitter_criteria', 
					instance = self, 
					gui_widg = 'fetch_obj', 
					gui_label = 'Fit Is Closer Criteria', 
					sizer_position = (0, 4), 
					values = fitter_crit_names,
					valuables = fitter_crit_classes, 
					initial_valuable = self.fitter_criteria, 
					diag_class = LGDIG.make_crit_dialog, 
					append_instead = True))
		metric_name_list = [	'Average Pt-Wise Difference', 
								'Integral Fitness', 
								'Slope Fitness'		]
		metric_func_list = [LGEO.metric_avg_ptwise_diff_on_domain, 
							LGEO.metric_integral_fit_quality, 
							LGEO.metric_slope_fit_quality]
		metric = self.metric
		try:
			initial_metric_label =\
					metric_name_list[[isinstance(metric, metric_class) 
						for metric_class in metric_func_list].index(True)]
			self.metric.set_settables()
			self.templates.extend(self.metric.templates)

		except ValueError:
			initial_metric_label = 'none'

		self.templates.append(
			LFU.interface_template(
					name = 'metric', 	#constaints on valid metrics depend on functional setup
					instance = self, 
					gui_widg = 'rad', 
					gui_label = 'Fit Metric', 
					sizer_position = (0, 0), 
					values = metric_name_list, 
					valuables = metric_func_list, 
					initial_valuable = metric, 
					initial_value = initial_metric_label, 
					nested_obj = True))'''














class sa_undo_criterion(lc.criterion):

	def __init__(self, label = 'undo level criterion', value = 100):
		lc.criterion.__init__(self, label = label, value = value)

	def verify_pass(self, sa_routine):
		if sa_routine.parameter_space.undo_level > self.value:
			print 'passed undo level limit: ending fit routine'
			return True
		
		return False

class sa_temp_criterion(lc.criterion):

	def __init__(self, label = 'temperature criterion', value = 0):
		lc.criterion.__init__(self, label = label, value = value)

	def verify_pass(self, sa_routine):
		if sa_routine.temperature <= self.value:
			print 'temperature has reached zero: ending fit routine'
			return True

		return False

class sa_minim_run_fit_quality_criterion(lc.criterion):

	def __init__(self):
		lc.criterion.__init__(self)
		self.undos = 5.0		#running tally of undos
		self.continues = 10.0		#running tally of continues
		self.undo_ratio = 0.5
		self.fact = 1000.0
		#self.sensitivity = 500.0
		#self.sensiv_check = [True]*3 + [False]

	def verify_pass(self, sa_routine):
		try:
			#time_autofail_relaxation = 1.0
			#if not False in self.sensiv_check:
			#	self.sensitivity += 100.0

			#elif not True in self.sensiv_check:
			#	self.sensitivity = max(200.0, self.sensitivity - 100.0)

			undo_level = sa_routine.parameter_space.undo_level
			self.undo_ratio = self.undos/self.continues
			print 'undo ratio: ' + str(self.undo_ratio)
			#if self.undo_ratio > 0.5:
			if self.undo_ratio > 1.0:
				self.fact = max(250.0, self.fact - 250.0)
			#	del self.sensiv_check[0]
			#	self.sensiv_check.append(True)
			#	self.fact = max(1000.0, 
			#					self.fact - self.sensitivity)

			else:
				self.fact += 250.0
			#	del self.sensiv_check[0]
			#	self.sensiv_check.append(False)
			#	self.fact += self.sensitivity

			check_integrals = [dater.scalers[-1] - dater.scalers[-2] < 0.0 
											for dater in sa_routine.data_2]
			check_real_integrals = [abs(dater.scalers[-1] - dater.scalers[-2]) 
											for dater in sa_routine.data_2]
			best_integ_match_dexes = [dater.scalers.index(min(dater.scalers)) for dater in sa_routine.data_2]

			check_measures = [dater.scalers[-1] - dater.scalers[-2] < 0.0 
										for dater in sa_routine.data[2:]]
			check_inits = [dater.scalers[-1] - dater.scalers[-2] < 0.0 
										for dater in sa_routine.data_3]
			check_real_inits = [abs(dater.scalers[-1] - dater.scalers[-2]) for dater in sa_routine.data_3]
			
			#check_measures_extensive = [not False in [dater.scalers[-1] - dater.scalers[k] < 0.0
			#									for k in range(- 2 - undo_level, -1)] 
			#										for dater in sa_routine.data[2:]]
			check_real_measures = [abs(dater.scalers[-1] - dater.scalers[-2]) 
											for dater in sa_routine.data[2:]]
			#check_prob = random.random()

			#for k in range(len(check_measures_extensive)):
			#	if check_measures_extensive[k] == True:
			#			check_real_measures[k] *= 10
			#			time_autofail_relaxation *= 10.0
			#			print 'may be much better'

			print 'check em!: ' + str(check_measures)
			print 'check em!: ' + str([dater.name for dater 
									in sa_routine.data[2:]])
			print 'check em!: ' + str([check for check in check_real_measures])

			#print 'undos: ' + str(undo_level) + '\tcheck_prob: ' + str(check_prob)

			#if sum([check_real_inits[k] for k in range(len(check_real_inits)) if check_inits[k]]) > sum([check_real_inits[k] for k in range(len(check_real_inits)) if not check_inits[k]]) and\
			#		(check_measures[-1] or check_real_measures[-1] < 0.01):
			#	print 'initial counts got better - accepting'
			#	sa_routine.parameter_space.undo_level = 0
			#	self.continues += 1
			#	return True

			val1 = sum([check_real_measures[k] for k in range(len(check_real_measures)) 
						if check_measures[k] == True and check_real_measures[k] > 1.0])
			val2 = sum([math.sqrt(check_real_integrals[k]) 
						for k in range(len(check_real_integrals)) 
						if check_integrals[k] == True and check_real_integrals[k] > 1.0])
			val1bad = sum([check_real_measures[k] for k in range(len(check_real_measures)) 
						if check_measures[k] == False and check_real_measures[k] > 1.0])
			val2bad = sum([math.sqrt(check_real_integrals[k]) 
						for k in range(len(check_real_integrals)) 
						if check_integrals[k] == False and check_real_integrals[k] > 1.0])

			if val1 < val1bad and val2 < val2bad:
				print 'hard rejection'
				self.undos += 1
				return False

			#1 - sample from gauss with std val1 avg value of 1
			#always most likely to reject
			#equally likely to accept if the fit is good
			accept_prob = val1
			other_accept = val2
			#accept_prob = 1.0 - random.gauss(1.0, val1/self.fact)/(5.0*val1/self.fact)

			print 'undos: ' + str(undo_level)			# + ' accept_prob: ' + str(accept_prob) + '/' + str(other_accept) + ' fact: ' + str(self.fact)
			#if other_accept > self.fact**2 and check_real_measures[-1] > 1.0:
			#if math.sqrt(other_accept) > self.fact:
			#	print 'the integrals got better!! - keeping!'
			#	sa_routine.parameter_space.undo_level = 0
			#	self.continues += 1
			#	return True				

			#says val1 must be at least double self.fact
			#if check_measures[-1] and check_real_measures[-1] > 1.0:
			#	print 'force accepting since time was closer!'
			#	sa_routine.parameter_space.undo_level = 0
			#	self.continues += 1
			#	return True

			#elif not check_measures[-1] and check_real_measures[-1] > 0.1*time_autofail_relaxation:
			#elif not check_measures[-1] and check_real_measures[-1] > 0.1:
			#	self.undos += 1
			#	return False

			#if sa_routine.iteration in best_integ_match_dexes and\
			#	(check_measures[-1] or check_real_measures[-1] < 0.01):
			#		sa_routine.best_match.append(
			#			(sum([dater.scalers[sa_routine.iteration] 
			#					for dater in sa_routine.data_2]), 
			#							sa_routine.iteration))
			#		print 'accepting because someone is looking their finest!'
			#		sa_routine.parameter_space.undo_level = 0
			#		self.continues += 1
			#		return True

			#if (math.sqrt(other_accept) > self.fact or accept_prob > self.fact) and (check_measures[-1] or check_real_measures[-1] < 0.01):
			if 	(sum([check_real_inits[k] for k in range(len(check_real_inits)) if check_inits[k]]) >\
				sum([check_real_inits[k] for k in range(len(check_real_inits)) if not check_inits[k]]) or\
				(val2 > val2bad or val1 > val1bad)) and\
				(check_measures[-1] or check_real_measures[-1] < 0.005):
			#if accept_prob > float(check_measures.count(False))\
			#						/float(len(check_measures)):
			#if check_measures.count(True) == len(sa_routine.data[2:]):
				print 'acceptance'
				sa_routine.parameter_space.undo_level = 0
				self.continues += 1
				return True
			'''
			if sa_routine.data[0].scalers[-1] -\
				sa_routine.data[0].scalers[-2] < 0.0:
				#0.2*min(sa_routine.data[0].scalers):
					sa_routine.parameter_space.undo_level = 0
					return True
			'''
			'''
			check_recent_x_measures =\
					[	sa_routine.data[0].scalers[-1] -\
						sa_routine.data[0].scalers[k] <\
						0.5*min(sa_routine.data[0].scalers)
								for k in 
						range(- 2 - undo_level, -1)		]
			if not False in check_recent_x_measures:
				sa_routine.parameter_space.undo_level = 0
				return True
			'''
		except IndexError:
			if len(sa_routine.data[0].scalers) > 2:
				print 'something probably aint working right!'
				pdb.set_trace()

			elif sa_routine.iteration in [0, 1]:
				print 'base case: assuming False for fitter'
				self.undos += 1
				return False

		self.undos += 1
		return False

class criterion_sa_minimize_measures(lc.criterion):

	def __init__(self):
		lc.criterion.__init__(self)
		self.best_measure = None
		self.rejects = 0
		self.accepts = 0

	def verify_pass(self, data):
		print 'crit accept ratio: ' + str(float(self.rejects)/float(self.accepts))
		improves = [dater[-1] - min(dater) < 0.0 for dater in data]
		changed_by = [dater[-1] - min(dater) for dater in data]
		improves_by = [changed_by[k] for k in 
					range(len(changed_by)) if improves[k]]
		worsens_by = [changed_by[k] for k in 
					range(len(changed_by)) if improves[k]]
		if improves_by > worsens_by:
			print 'betterer than worserer'
			self.accepts += 1
			return True

		self.rejects += 1
		return False









valid_fit_routine_base_classes = [
	lfu.interface_template_class(
		fit_routine_simulated_annealing, 
				'simulated annealing')]












