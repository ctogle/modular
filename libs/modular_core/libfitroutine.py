import libs.modular_core.libfundamental as lfu
import libs.modular_core.libfiler as lf
import libs.modular_core.liboutput as lo
import libs.modular_core.libgeometry as lgeo
import libs.modular_core.libcriterion as lc
import libs.modular_core.libvtkoutput as lvtk
import libs.modular_core.libiteratesystem as lis
import libs.modular_core.libsettings as lset
import libs.modular_core.libmath as lm
import libs.modular_core.libmultiprocess as lmp

import multiprocessing as mp
import traceback
import numpy as np
import time
import math
import os
import random
import sys

import pdb

if __name__ == 'libs.modular_core.libfitroutine':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'

class fit_routine_plan(lfu.plan):

	def __init__(self, *args, **kwargs):
		self.impose_default('label', 'fit routine plan', **kwargs)
		self.impose_default('routines', [], **kwargs)
		self.impose_default('selected_routine', None, **kwargs)
		self.impose_default('selected_routine_label', None, **kwargs)
		self.impose_default('show_progress_plots', True, **kwargs)
		kwargs['use_plan'] = lset.get_setting('fitting')
		lfu.plan.__init__(self, *args, **kwargs)

	def __call__(self, *args, **kwargs):
		if self.show_progress_plots:
			if self.parent.multithread_gui:
				app = lgb.QtGui.QApplication(sys.argv)

			else: self.show_progress_plots = False

		self.enact_plan(*args, **kwargs)

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

def parse_fitting_line(data, ensem, procs, routs):
	split = [item.strip() for item in data.split(':')]
	for fit_type in valid_fit_routine_base_classes:
		if split: name = split[0]
		if len(split) > 1:
			if split[1].strip() == fit_type._tag:
				rout = fit_type._class(label = name, 
					parent = ensem.fitting_plan)
				routs.append(rout)

			if len(split) > 2: rout.regime = split[2].strip()

	ensem.fitting_plan.add_routine(new = rout)
	rout.set_settables(0, ensem)
	return rout

class fit_routine(lfu.modular_object_qt):

	#ABSTRACT
	#base class should not assume scalers are the data object
	'''
	fit_routine subclasses should have several regimes
	fine: runs the routine on the parameter space as specified
	coarse-magnitude: coerce the parameter space into a discrete 
		parameter space; impose new bounds on the old 
		parameter space (which is not in general discrete) based
		on the best fit
	coarse-decimate: coerce the parameter space into a discrete 
		space with bounds and increments such that each space has
		ten values; impose results as coarse-magnitude does
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
		self.impose_default('many_steps', 1, **kwargs)
		self.impose_default('p_sp_trajectory', [], **kwargs)
		self.impose_default('p_sp_step_factor', 1.0, **kwargs)
		self.impose_default('capture_targets', [], **kwargs)
		self.impose_default('bAbort', False, **kwargs)
		self.impose_default('brand_new', True, **kwargs)
		self.impose_default('iteration', 0, **kwargs)
		self.impose_default('auto_overwrite_key', True, **kwargs)
		self.impose_default('initial_creep_factor', 4, **kwargs)
		self.impose_default('display_frequency', 100, **kwargs)
		self.impose_default('max_sim_wait_time', 2, **kwargs)
		self.impose_default('last_best', 0, **kwargs)
		self.impose_default('timeouts', 0, **kwargs)
		self.impose_default('use_time_out', True, **kwargs)
		self.impose_default('regime', 'fine', **kwargs)
		self.impose_default('valid_regimes', 
			['fine', 'coarse-magnitude', 'coarse-decimate'], **kwargs)

		self.impose_default('metrics', [], **kwargs)
		self.metrics.append(
			lgeo.metric_avg_ptwise_diff_on_domain(parent = self))
		self.metrics.append(
			lgeo.metric_slope_1st_derivative(parent = self))
		self.metrics.append(
			lgeo.metric_slope_2nd_derivative(parent = self))
		#self.metrics.append(
		#	lgeo.metric_slope_3rd_derivative(parent = self))
		#self.metrics.append(
		#	lgeo.metric_integral_fit_quality(parent = self))
		self.impose_default('metric_weights', [
				met.acceptance_weight for met 
				in self.metrics], **kwargs)
		#self.metric_weights = [1.0, 1.0, 1.0, 1.0]
		self.metric_weights = [1.0, 1.0, 1.0/2.0, 1.0/6.0]
		#self.metric_weights = [1.0, 0.5, 0.5, 0.25]
		#self.metric_weights = [1.0, 0.75, 0.5, 0.25]
		#self.metric_weights = [1.0, 0.5, 0.25, 0.125]
		#self.metric_weights = [1.0, 0.85, 0.7, 0.55]
		self.impose_default('prime_metric', 0, **kwargs)
		self.prime_metric =\
			self.metric_weights.index(max(self.metric_weights))
		self.metrics[self.prime_metric].is_heaviest = True

		self.impose_default('fitted_criteria', [], **kwargs)
		self.fitted_criteria.append(lc.criterion_iteration(
					parent = self, max_iterations = 10000))
		self.fitted_criteria.append(criterion_impatient(
					parent = self, max_timeouts = 50, 
								max_last_best = 500))

		self.impose_default('fitter_criteria', [], **kwargs)
		self.fitter_criteria.append(
			criterion_minimize_measures(parent = self))

		self.impose_default('data_to_fit_to', None, **kwargs)
		self.impose_default('input_data_file', '', **kwargs)
		self.impose_default('input_data_domain', '', **kwargs)
		self.impose_default('input_data_codomains', [], **kwargs)
		self.input_data_file = os.path.join(os.getcwd(), 
			'chemicallite', 'output', 'ensemble_output.1.pkl')
		self.input_data_domain = 'time'
		#self.input_data_codomains = ['ES_Complex', 'Product', 
		#								'Enzyme', 'Substrate']
		#self.input_data_codomains = ['ES_Complex', 'Product']
		self.input_data_codomains = ['ES_Complex']

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
		#self._children_ = [self.output] + self.metrics +\
		#	self.fitted_criteria + self.fitter_criteria
		self._children_ = [self.output]

	def __call__(self, *args, **kwargs):
		self.initialize(*args, **kwargs)				
		run_func = lis.run_system
		#worker = mp.Pool(processes = 1)
		worker = None
		while not self.bAbort and not self.verify_criteria_list(
									self.fitted_criteria, self):
			self.iterate(run_func, worker)

		if worker: worker.join()
		self.finalize(*args, **kwargs)

	def get_input_data(self):
		relevant = [self.input_data_domain] + self.input_data_codomains
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
		self.timeouts = 0
		self.parameter_space =\
			self.parent.parent.cartographer_plan.parameter_space
		if self.regime == 'coarse-magnitude':
			self.parameter_space, valid =\
				lgeo.generate_coarse_parameter_space_from_fine(
						self.parameter_space, magnitudes = True)
			if not valid:
				traceback.print_exc(file=sys.stdout)
				lgd.message_dialog(None, 
					'P-Spaced couldnt be coarsened!', 'Problem')

		elif self.regime == 'coarse-decimate':
			self.parameter_space, valid =\
				lgeo.generate_coarse_parameter_space_from_fine(
						self.parameter_space, decimates = True)
			if not valid:
				traceback.print_exc(file=sys.stdout)
				lgd.message_dialog(None, 
					'P-Spaced couldnt be coarsened!', 'Problem')

		elif self.regime == 'fine':
			#self.parameter_space =\
			#	self.parent.parent.cartographer_plan.parameter_space
			print 'REGIME', self.regime

		self.parameter_space.set_start_pt()
		for metric in self.metrics:
			metric.initialize(self, *args, **kwargs)

		self.data = lgeo.scalers_from_labels(['fitting iteration'] +\
				[met.label + ' measurement' for met in self.metrics])

	def iterate(self, run_func, worker = None):
		data_pool = self.ensemble.data_pool.batch_pool
		if self.use_time_out:
			timed_out = lmp.run_with_time_out(run_func, 
					(self.ensemble,), data_pool, 
					time_out = self.max_sim_wait_time, 
									worker = worker)

			if timed_out:
				print 'location timed out...', self.iteration
				self.move_in_parameter_space(bypass = True)
				#self.parameter_space.undo_step()
				self.iteration += 1
				self.timeouts += 1
				return False

			else: run_data = data_pool[-1]

		else:
			run_data = run_func(self.ensemble)
			data_pool.append(run_data)

		run_data = [lgeo.scalers(label = dater, scalers = dats) 
			for dater, dats in zip(self.run_targets, run_data)]
		display = self.iteration % self.display_frequency == 0
		if display:
			print ' '.join(['\niteration:', str(self.iteration), 
						'temperature:', str(self.temperature)])

		self.last_best += 1
		for met_weight, metric in zip(self.metric_weights, self.metrics):
			metric.measure(self.data_to_fit_to, 
					run_data, display = display, 
							weight = met_weight)
			last_dat_dex = len(metric.data[0].scalers) - 1
			if metric.best_measure == last_dat_dex and\
									metric.is_heaviest:
				self.last_best = 0

		self.capture_plot_data()
		self.p_sp_trajectory.append(
			self.parameter_space.get_current_position())
		self.move_in_parameter_space()
		self.iteration += 1
		return True

	def finalize(self, *args, **kwargs):
		def get_interped_y(label, data, x, x_to):
			run_y = lfu.grab_mobj_by_name(label, data)
			run_interped = lgeo.scalers(
				label = 'interpolated best result - ' + label, 
				scalers = lm.linear_interpolation(
					x.scalers, run_y.scalers, 
					x_to.scalers, 'linear'))
			return run_interped

		self.best_fits = [(met.best_measure, 
			met.data[0].scalers[met.best_measure]) 
			for met in self.metrics]
		self.handle_fitting_key()
		best_run_data = self.ensemble.data_pool[
			self.best_fits[self.prime_metric][0]]
		best_run_data_x = lfu.grab_mobj_by_name(
			self.data_to_fit_to[0].label, best_run_data)
		best_run_data_ys = [get_interped_y(
			lab, best_run_data, best_run_data_x, self.data_to_fit_to[0]) 
				for lab in lfu.grab_mobj_names(self.data_to_fit_to[1:])]
		for metric in self.metrics:
			metric.finalize(*args, **kwargs)

		print 'fit routine:', self.label, 'best fit:', self.best_fits
		print 'ran using regime:', self.regime
		lgd.quick_plot_display(self.data_to_fit_to[0], 
			self.data_to_fit_to[1:] + best_run_data_ys, delay = 5)
		if self.regime.startswith('coarse'):
			self.impose_coarse_result_to_p_space()

	def impose_coarse_result_to_p_space(self):

		def locate(num, vals):
			delts = [abs(val - num) for val in vals]
			where = delts.index(min(delts))
			found = vals[where]
			return found

		fine_space = self.ensemble.cartographer_plan.parameter_space
		print 'fine p-space modified by coarse p-space'
		print '\tbefore'
		for sub in fine_space.subspaces:
			print sub.label
			print sub.inst.__dict__[sub.key], sub.increment, sub.bounds

		orders = [10**k for k in [val - 20 for val in range(40)]]
		for spdex, finesp, subsp in zip(range(len(fine_space.subspaces)), 
				fine_space.subspaces, self.parameter_space.subspaces):
			wheres = range(len(subsp.scalers))
			best_val = float(self.p_sp_trajectory[
				self.best_fits[self.prime_metric][0]][spdex][-1])
			delts = [abs(val - best_val) for val in subsp.scalers]
			where = delts.index(min(delts))
			finesp.inst.__dict__[finesp.key] = best_val
			#cut = int(len(wheres) / 4)
			cut = int(len(wheres) / 6)
			print 'THE CUT', cut

			#if len(wheres) >= 4:
			if cut > 0:
				if where in wheres[2*cut:-2*cut]:
					keep = subsp.scalers[cut:-cut]
					print 'keep middle', where, wheres
					print keep

				elif where in wheres[:-2*cut]:
					keep = subsp.scalers[:-cut]
					print 'keep left', where, wheres
					print keep

				elif where in wheres[2*cut:]:
					keep = subsp.scalers[cut:]
					print 'keep right', where, wheres
					print keep

				else:
					keep = subsp.scalers[:]
					print 'keep all', where, wheres
					print keep

			else:
				print 'CUT IS ZERO', cut
				if self.regime.endswith('decimate'):
					pdb.set_trace()

				elif self.regime.endswith('magnitude'):
					current = subsp.scalers[where]
					if current in orders[:2]:
						left = orders[0]
						right = orders[4]
						print 'PINNED', left, right

					elif current in orders[-2:]:
						left = orders[-5]
						right = orders[-1]
						print 'PINNED', left, right

					else:
						left = locate(current/100.0, orders)
						right = locate(current*100.0, orders)

					if left < finesp.perma_bounds[0]:
						left = locate(finesp.perma_bounds[0], orders)
						right = orders[orders.index(left) + 5]
						print 'out of bounds left', left, right

					if right > finesp.perma_bounds[1]:
						right = locate(finesp.perma_bounds[1], orders)
						left = orders[orders.index(right) - 5]
						print 'out of bounds right', left, right

					keep = [left, right]
					print 'slid from', subsp.scalers[wheres[0]:wheres[-1]+1], 'to', keep

				else:
					print 'WHAT SHOULD HAPPEN HERE??'
					pdb.set_trace()

			finesp.bounds = [keep[0], keep[-1]]

		print '\tafter'
		for sub in fine_space.subspaces:
			print sub.label
			print sub.inst.__dict__[sub.key], sub.increment, sub.bounds

	def capture_plot_data(self, *args, **kwargs):
		self.data[0].scalers.append(self.iteration)
		bump = 1#number of daters preceding metric daters
		for dex, met in enumerate(self.metrics):
			try:
				self.data[dex + bump].scalers.append(
						met.data[0].scalers[-1])
			except IndexError: pdb.set_trace()

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
			lines.append('\n')
			location_to_lines(0, dex)

		lf.output_lines(lines, self.output.save_directory, 
			'fitting_key.txt', dont_ask = self.auto_overwrite_key)

	#def move_in_parameter_space(self, bypass = False, many_steps = 3):
	def move_in_parameter_space(self, bypass = False):
		if not bypass and self.verify_criteria_list(
				self.fitter_criteria, self.metrics):
			power = 1.0/(self.parameter_space.step_normalization*2)
			creep_factor = self.initial_creep_factor*\
				(self.parameter_space.initial_factor/\
						self.p_sp_step_factor)**(power)
			#print 'creepin', creep_factor
			self.parameter_space.take_biased_step_along_axis(
						#factor = self.p_sp_step_factor/4.0)
				factor = self.p_sp_step_factor/creep_factor)
						#	factor = self.p_sp_step_factor)

		else:
			self.parameter_space.undo_step()
			self.parameter_space.take_proportional_step(
						factor = self.p_sp_step_factor, 
						many_steps = self.many_steps)



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
			self.final_iteration =\
				self.fitted_criteria[0].max_iterations
			lam = -1.0 * np.log(self.max_temperature)/\
								self.final_iteration
			#lam = -1.0 * np.log(self.max_temperature) / (2*final_iteration)
			cooling_domain = np.array(range(self.final_iteration))
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
		#initial_factor = self.parameter_space.initial_factor
		#self.metric_weights = [(self.temperature/initial_factor)
		fit_routine.iterate(self, *args, **kwargs)

	def capture_plot_data(self, *args, **kwargs):
		fit_routine.capture_plot_data(self, *args, **kwargs)
		self.data[-1].scalers.append(self.temperature/\
					self.parameter_space.initial_factor)

	def move_in_parameter_space(self, *args, **kwargs):
		self.p_sp_step_factor = self.temperature
		initial_factor = self.parameter_space.initial_factor
		#many_steps = 1 + int(self.parameter_space.dimensions*\
		#				((self.temperature/initial_factor)**\
		#				(self.parameter_space.dimensions/2)))
		#dims = self.parameter_space.dimensions
		#old_many_steps = self.many_steps
		#self.many_steps =\
		#	int(dims**((self.temperature/initial_factor)**(dims**(-2.0))))
		#		#(1-self.iteration/self.final_iteration))

		self.many_steps = int(max([1, abs(random.gauss(0, 
					self.parameter_space.dimensions))*\
					(self.temperature/initial_factor)]))

		#if not self.many_steps == old_many_steps:
		#	print ' '.join(['changed number of axial steps:', 
		#		str(old_many_steps), 'to', str(self.many_steps), 
		#							'at', str(self.iteration)])
		fit_routine.move_in_parameter_space(self, *args, **kwargs)

	def set_settables(self, *args, **kwargs):
		self.capture_targets =\
				['fitting iteration'] +\
				[met.label + ' measurement' 
					for met in self.metrics] +\
					['annealing temperature']
		self.handle_widget_inheritance(*args, from_sub = False)
		fit_routine.set_settables(self, *args, from_sub = True)

class criterion_impatient(lc.criterion):

	def __init__(self, *args, **kwargs):
		if not 'label' in kwargs.keys():
			kwargs['label'] = 'timeout criterion'

		if not 'base_class' in kwargs.keys():
			kwargs['base_class'] = lfu.interface_template_class(
							criterion_impatient, 'timeout limit')

		self.impose_default('max_timeouts', 100, **kwargs)
		self.impose_default('max_last_best', 100, **kwargs)
		lc.criterion.__init__(self, *args, **kwargs)

	def to_string(self):
		return '\ttimeout limit : ' + str(self.max_timeouts)

	def initialize(self, *args, **kwargs):
		self.max_timeouts = float(self.max_timeouts)

	def verify_pass(self, *args):
		obj = args[0]
		try:
			#print 'TIMEOUTS', obj.timeouts, self.max_timeouts
			too_many_timeouts = obj.timeouts >= self.max_timeouts
			no_longer_better = obj.last_best >= self.max_last_best
			if too_many_timeouts or no_longer_better: return True

		except AttributeError:
			print 	'timeout criterion applied \
					\n to object without .timeouts'
			return True

		return False

	def set_uninheritable_settables(self, *args, **kwargs):
		self.visible_attributes = ['label', 'base_class', 
							'bRelevant', 'max_timeouts']

	def set_settables(self, *args, **kwargs):
		self.handle_widget_inheritance(*args, from_sub = False)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['spin'], 
				doubles = [[False]], 
				initials = [[int(self.max_timeouts)]], 
				minimum_values = [[0]], 
				maximum_values = [[sys.maxint]], 
				instances = [[self]], 
				keys = [['max_timeouts']], 
				box_labels = ['Timeout Limit']))
		criterion.set_settables(self, *args, from_sub = True)

class criterion_minimize_measures(lc.criterion):

	def __init__(self, *args, **kwargs):
		lc.criterion.__init__(self, *args, **kwargs)
		self.rejects = 1
		self.accepts = 1
		self.reject_probability = 0.5
		self.use_window = False

	def verify_pass(self, *args):
		metrics = args[0]
		#ratio = float(self.accepts)/\
		#	(float(self.accepts) + float(self.rejects))
		#print 'crit accept ratio: ', ratio
		improves = []
		for met in metrics:
			sca = met.data[0].scalers
			if len(sca) <= 100 or not self.use_window:
				improves.append(sca[-1] - min(sca) <=\
						#(np.mean(sca) - min(sca))*ratio)
						(np.mean(sca) - min(sca))/20.0)
						#(np.mean(sca) - min(sca))/10.0)

			else:
				improves.append(sca[-1] - min(sca) <=\
						(np.mean(sca[-100:]) - min(sca))/20.0)
					#(np.mean(sca) - min(sca)))
					#(np.mean(sca) - min(sca))/(len(sca)+1))

		weights = [met.acceptance_weight for met in metrics]
		weights = [we/sum(weights) for we, imp in 
					zip(weights, improves) if imp]
		weight = sum(weights)
		#if weight >= self.reject_probability:
		if improves.count(True) > int(len(improves)/2):
		#if improves.count(True) == len(improves):
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











