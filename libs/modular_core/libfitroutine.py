import libs.modular_core.libfundamental as lfu
import libs.modular_core.libfiler as lf
import libs.modular_core.liboutput as lo
import libs.modular_core.libgeometry as lgeo
import libs.modular_core.libcriterion as lc
import libs.modular_core.libvtkoutput as lvtk
import libs.modular_core.libiteratesystem as lis
import libs.modular_core.libsettings as lset
import libs.modular_core.libmath as lm

import traceback
import numpy as np
import time
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
		self.selected_routine_label = None
		use = lset.get_setting('fitting')
		lfu.plan.__init__(self, parent = parent, 
				label = label, use_plan = use)

	def enact_plan(self, *args, **kwargs):
		for routine in self.routines:
			check1 = time.time()
			routine(*args, **kwargs)
			print ' '.join(['completed fit routine:', routine.label, 
						'in:', str(time.time() - check1), 'seconds'])

	def add_routine(self, new = None):
		if not new: new = fit_routine_simulated_annealing(parent = self)
		self.routines.append(new)
		self._children_.append(new)
		self.rewidget(True)

	def remove_routine(self, selected = None):
		if selected: select = selected
		else: select = self.get_selected()
		if select:
			self.routines.remove(select)
			self._children_.remove(select)
			del self.parent.run_params['output_plans'][
							select.label + ' output']
			select._destroy_()

		self.rewidget(True)

	def remove_routine(self):
		select = self.get_selected()
		if select:
			self.routines.remove(select)
			self._children_.remove(select)

		self.rewidget(True)

	def move_routine_up(self, *args, **kwargs):
		select = self.get_selected()
		if select:
			select_dex = lfu.grab_mobj_dex_by_name(
						select.label, self.routines)
			self.routines.pop(select_dex)
			self.routines.insert(select_dex - 1, select)
			#self.set_selected(select_dex - 1)
			self.rewidget_routines()

	def move_routine_down(self, *args, **kwargs):
		select = self.get_selected()
		if select:
			select_dex = lfu.grab_mobj_dex_by_name(
						select.label, self.routines)
			self.routines.pop(select_dex)
			self.routines.insert(select_dex + 1, select)
			#self.set_selected(select_dex + 1)
			self.rewidget_routines()

	def rewidget_routines(self, rewidg = True):
		[rout.rewidget(rewidg) for rout in self.routines]

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
		self.widg_templates.append(
			lgm.interface_template_gui(
				layout = 'grid', 
				widg_positions = [(0, 0), (0, 2), (1, 2), 
								(2, 2), (3, 2), (4, 2)], 
				widg_spans = [(3, 2), None, None, None, None, None], 
				grid_spacing = 10, 
				widgets = ['mobj_catalog', 'button_set'], 
				verbosities = [1, 1], 
				instances = [[self.routines, self], None], 
				keys = [[None, 'selected_routine_label'], None], 
				handles = [(self, 'routine_selector'), None], 
				labels = [None, ['Add Fit Routine', 
								'Remove Fit Routine', 
								'Move Up In Hierarchy', 
								'Move Down In Hierarchy']], 
				initials = [[select_label], None], 
				bindings = [None, [lgb.create_reset_widgets_wrapper(
										window, self.add_routine), 
						lgb.create_reset_widgets_wrapper(window, 
								self.remove_routine), 
						lgb.create_reset_widgets_wrapper(window, 
								self.move_routine_up), 
						lgb.create_reset_widgets_wrapper(window, 
								self.move_routine_down)]]))
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

		img_path = os.path.join(os.getcwd(), 
			'resources', 'coming-soon.png')
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['image'], 
				paths = [img_path]))
		'''
		lfu.plan.set_settables(self, *args, from_sub = True)

class fit_routine(lfu.modular_object_qt):

	#ABSTRACT
	#base class should not assume scalers are the data object
	'''
	fit_routine subclasses should have several regimes
	fine: runs the routine on the parameter space as specified
	coarse: coerce the parameter space into a discrete 
		parameter space; impose new bounds on the old 
		parameter space (which is not in general discrete) based
		on the best fit
	these two regimes can run in either of the above two regimes
		=> 4 modes of operation
	on_simulation: run a simulation; use its output as input 
		any relevant metrics
	on_process: run a batch of simulations; feed its output into
		a series of post processes whose results are used as input
		to any relevant metrics

	fitting routines can be used in series, which is particularly 
		useful when each provides information for the next
		this is the express purpose of the coarse regime
		but the fine regime should also allow this option
			the option will be on available on both

	fitting routines should be able to run on each other - 
		use a fitting routine to hone another fitting routine

		this could allow a single recursing routine which 
		runs the coarse regime several times and then the fine
		regime or whatever is desired

	fitting routines can have many metrics and many criteria for
		both accepting a parameter space step and for the end of 
		the fitting routine which are for now assumed to be 
		implicitly joined by AND statements

	fitting routines can accept any number of lines as input 
		for metric minimization (the assumed criterion for fitterness
		for now)

	input data should be identical to the output of modular via
		pkl format - scalers objects wrapped in a data_container
	'''
	def __init__(self, *args, **kwargs):
		self.impose_default('parameter_space', None, **kwargs)
		self.impose_default('p_sp_trajectory', [], **kwargs)
		self.impose_default('p_sp_step_factor', 1.0, **kwargs)
		self.impose_default('fitter_criteria', [], **kwargs)
		self.impose_default('fitted_criteria', [], **kwargs)
		self.impose_default('metrics', [], **kwargs)
		self.impose_default('data_to_fit_to', None, **kwargs)
		self.impose_default('input_data_file', '', **kwargs)
		self.impose_default('input_data_domain', '', **kwargs)
		self.impose_default('input_data_codomain', '', **kwargs)

		#self.metrics.append(
		#	lgeo.metric_slope_fit_quality(parent = self))
		#self.metrics.append(
		#	lgeo.metric_integral_fit_quality(parent = self))
		self.metrics.append(
			lgeo.metric_avg_ptwise_diff_on_domain(parent = self))
		self.fitted_criteria.append(
			lc.criterion_iteration(parent = self, 
						max_iterations = 10000))
		self.fitter_criteria.append(
			criterion_minimize_measures(parent = self))
		self.input_data_file = os.path.join(os.getcwd(), 
			'chemicallite', 'output', 'ensemble_output.1.pkl')
		self.input_data_domain = 'time'
		self.input_data_codomain = 'ES_Complex'

		self.impose_default('capture_targets', [], **kwargs)
		self.impose_default('bAbort', False, **kwargs)
		self.impose_default('brand_new', True, **kwargs)
		self.impose_default('iteration', 0, **kwargs)
		self.impose_default('display_frequency', 500, **kwargs)
		self.impose_default('regime', 'fine', **kwargs)
		self.impose_default('valid_regimes', 
				['fine', 'coarse'], **kwargs)
		if not 'visible_attributes' in kwargs.keys():
			kwargs['visible_attributes'] = None

		if not 'valid_base_classes' in kwargs.keys():
			kwargs['valid_base_classes'] =\
				valid_fit_routine_base_classes

		if not 'base_class' in kwargs.keys():
			kwargs['base_class'] = lfu.interface_template_class(
								object, 'fit routine abstract')

		lfu.modular_object_qt.__init__(self, *args, **kwargs)
		self.output = lo.output_plan(label = ' '.join(
				[self.label, 'output']), parent = self)
		self._children_ = [self.output] + self.metrics +\
			self.fitted_criteria + self.fitter_criteria

	def __call__(self, *args, **kwargs):
		self.initialize(*args, **kwargs)				
		run_func = lis.run_system
		while not self.bAbort and not self.verify_criteria_list(
									self.fitted_criteria, self):
			self.iterate(run_func)

		self.finalize(*args, **kwargs)

	def get_input_data(self):
		relevant = [self.input_data_domain, self.input_data_codomain]
		data = lf.load_pkl_object(self.input_data_file)
		data = [dater for dater in data.data 
				if dater.label in relevant]
		return data

	def initialize(self, *args, **kwargs):
		self.output.flat_data = True
		self.ensemble = self.parent.parent
		self.ensemble.data_pool = self.ensemble.set_data_scheme()
		self.data_to_fit_to = self.get_input_data()
		self.run_targets = self.ensemble.run_params['plot_targets']
		self.iteration = 0
		self.parameter_space =\
			self.parent.parent.cartographer_plan.parameter_space
		if self.regime == 'coarse':
			self.parameter_space, valid =\
				lgeo.generate_coarse_parameter_space_from_fine(
										self.parameter_space)
			if not valid:
				traceback.print_exc(file=sys.stdout)
				lgd.message_dialog(None, 
					'P-Spaced couldnt be coarsened!', 'Problem')

		self.parameter_space.set_start_pt()
		for metric in self.metrics:
			metric.initialize(self, *args, **kwargs)

		self.data = lgeo.scalers_from_labels(['fitting iteration'] +\
				[met.label + ' measurement' for met in self.metrics])

	def iterate(self, run_func):
		run_data = run_func(self.ensemble)
		self.ensemble.data_pool.batch_pool.append(run_data)
		run_data = [lgeo.scalers(label = dater, scalers = dats) 
			for dater, dats in zip(self.run_targets, run_data)]
		display = self.iteration % self.display_frequency == 0
		if display:
			print ' '.join(['\niteration:', str(self.iteration), 
						'temperature:', str(self.temperature)])

		for metric in self.metrics:
			metric.measure(self.data_to_fit_to, 
					run_data, display = display)

		self.capture_plot_data()
		self.p_sp_trajectory.append(
			self.parameter_space.get_current_position())
		self.move_in_parameter_space()
		self.iteration += 1

	def finalize(self, *args, **kwargs):
		self.best_fits = [(met.best_measure, 
			met.data[0].scalers[met.best_measure]) 
			for met in self.metrics]
		self.handle_fitting_key()
		best_run_data = self.ensemble.data_pool[
							self.best_fits[0][0]]
		best_run_data_x = lfu.grab_mobj_by_name(
			self.data_to_fit_to[0].label, best_run_data)
		best_run_data_y = lfu.grab_mobj_by_name(
			self.data_to_fit_to[1].label, best_run_data)
		best_run_interped = lgeo.scalers(
			label = 'interpolated best result', 
			scalers = lm.linear_interpolation(
				best_run_data_x.scalers, best_run_data_y.scalers, 
				self.data_to_fit_to[0].scalers, 'linear'))
		for metric in self.metrics:
			metric.finalize(*args, **kwargs)

		print 'fit routine:', self.label, 'best fit:', self.best_fits
		print 'ran using regime:', self.regime
		lgd.quick_plot_display(self.data_to_fit_to[0], 
			[self.data_to_fit_to[1], best_run_interped], delay = 5)
		if self.regime == 'coarse':
			self.impose_coarse_result_to_p_space()

	def impose_coarse_result_to_p_space(self):
		pdb.set_trace()

	def capture_plot_data(self, *args, **kwargs):
		self.data[0].scalers.append(self.iteration)
		bump = 1#number of daters preceding metric daters
		for dex, met in enumerate(self.metrics):
			self.data[dex + bump].scalers.append(
						met.data[0].scalers[-1])

	def handle_fitting_key(self):

		def location_to_lines(k, met_dex):
			loc_measure = self.metrics[met_dex].data[0].scalers[k]
			lines.append(' : '.join(['Best fit from metric', 
				self.metrics[met_dex].label, str(loc_measure)]))
			lines.append('\tTrajectory : ' + str(k + 1))
			for ax in self.p_sp_trajectory[k]:
				lines.append('\t\t' + ' : '.join(ax))

		lines = ['Fit Routine Fitting Key: ']
		for dex, met_best in enumerate(self.best_fits):
			k = met_best[0]
			lines.append('\n')
			location_to_lines(k, dex)
			location_to_lines(0, dex)

		lf.output_lines(lines, self.output.save_directory, 
										'fitting_key.txt')

	def move_in_parameter_space(self, bypass = False, many_steps = 3):
		if self.verify_criteria_list(self.fitter_criteria, 
							self.metrics) and not bypass:
			self.parameter_space.take_biased_step_along_axis(
						factor = self.p_sp_step_factor/5.0)

		else:
			self.parameter_space.undo_step()
			self.parameter_space.take_proportional_step(
						factor = self.p_sp_step_factor, 
							many_steps = many_steps)



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
		ensem = args[1]
		if self.brand_new:
			self.brand_new = not self.brand_new
			self.mp_plan_ref = ensem.multiprocess_plan
			ensem.run_params['output_plans'][
				self.label + ' output'] = self.output

		self.output.label = self.label + ' output'
		self.handle_widget_inheritance(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['radio'], 
				labels = [self.valid_regimes], 
				initials = [[self.regime]], 
				instances = [[self]], 
				keys = [['regime']], 
				box_labels = ['P-Space Walk Regime']))
		recaster = lgm.recasting_mason()
		classes = [template._class for template 
					in self.valid_base_classes]
		tags = [template._tag for template 
				in self.valid_base_classes]
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['radio'], 
				mason = recaster, 
				keys = [['_class']], 
				instances = [[(self.base_class, self)]], 
				box_labels = ['Routine Method'], 
				labels = [tags], 
				initials = [[self.base_class._tag]]))
		self.widg_templates.append(
			lgm.interface_template_gui(
				keys = [['label']], 
				minimum_sizes = [[(150, 50)]], 
				instances = [[self]], 
				widgets = ['text'], 
				box_labels = ['Fit Routine Name']))
		'''
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
		'''
		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)

class fit_routine_simulated_annealing(fit_routine):

	def __init__(self, *args, **kwargs):
		if not 'label' in kwargs.keys():
			kwargs['label'] = 'simulated annealing routine'

		if not 'base_class' in kwargs.keys():
			kwargs['base_class'] = lfu.interface_template_class(
								object, 'simulated annealing')

		self.impose_default('cooling_curve', None, **kwargs)
		self.impose_default('max_temperature', 1000, **kwargs)
		self.impose_default('temperature', None, **kwargs)
		fit_routine.__init__(self, *args, **kwargs)

	def initialize(self, *args, **kwargs):
		if not self.cooling_curve:
			final_iteration = self.fitted_criteria[0].max_iterations
			lam = -1.0 * np.log(self.max_temperature) / final_iteration
			#lam = -1.0 * np.log(self.max_temperature) / 2*final_iteration
			cooling_domain = np.array(range(final_iteration))
			cooling_codomain = self.max_temperature*np.exp(
										lam*cooling_domain)
			self.cooling_curve = lgeo.scalers(
				label = 'cooling curve', scalers = cooling_codomain)

		fit_routine.initialize(self, *args, **kwargs)
		self.data.extend(lgeo.scalers_from_labels(
						['annealing temperature']))
		self.temperature = self.cooling_curve.scalers[self.iteration]
		self.parameter_space.initial_factor = self.temperature

	def iterate(self, *args, **kwargs):
		self.temperature = self.cooling_curve.scalers[self.iteration]
		fit_routine.iterate(self, *args, **kwargs)

	def capture_plot_data(self, *args, **kwargs):
		fit_routine.capture_plot_data(self, *args, **kwargs)
		self.data[-1].scalers.append(self.temperature)

	def move_in_parameter_space(self, *args, **kwargs):
		self.p_sp_step_factor = self.temperature
		initial_factor = self.parameter_space.initial_factor
		many_steps = 1 + int(self.parameter_space.dimensions*\
						((self.temperature/initial_factor)**3))
		fit_routine.move_in_parameter_space(self, *args, 
					many_steps = many_steps, **kwargs)

	def set_settables(self, *args, **kwargs):
		self.capture_targets =\
				['fitting iteration'] +\
				[met.label + ' measurement' 
					for met in self.metrics] +\
					['annealing temperature']
		self.handle_widget_inheritance(*args, from_sub = False)
		'''
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
		fit_routine.set_settables(self, *args, from_sub = True)
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

class criterion_minimize_measures(lc.criterion):

	def __init__(self, *args, **kwargs):
		lc.criterion.__init__(self, *args, **kwargs)
		self.rejects = 0
		self.accepts = 0

	def verify_pass(self, *args):
		metrics = args[0]
		if self.accepts > 0:
			ratio = str(float(self.rejects)/float(self.accepts))

		else: ratio = 'all rejections so far'
		#print 'crit accept ratio: ' + ratio
		improves = []
		for met in metrics:
			sca = met.data[0].scalers
			improves.append(sca[-1] - min(sca) <=\
					(np.mean(sca) - min(sca))/10.0)
					#(np.mean(sca) - min(sca))/(len(sca)+1))

		if improves.count(True) > int(len(improves)/2):
			self.accepts += 1
			return True

		self.rejects += 1
		return False




valid_fit_routine_base_classes = [
	lfu.interface_template_class(
		fit_routine_simulated_annealing, 
				'simulated annealing')]

'''
#information about routine type specific metrics/criteria
#[metrics, fitter, fitted]
valid_fit_routine_base_classes_supports = [
	[[lfu.interface_template_class(
		lgeo.metric_avg_ptwise_diff_on_domain, 
					'pointwise difference')], 
	[lfu.interface_template_class(
		criterion_minimize_measures, 
			'minimize measurement')], 
	[lfu.interface_template_class(
			lc.criterion_iteration, 
			'iteration limit')]]]
'''











