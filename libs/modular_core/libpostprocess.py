import libs.modular_core.libfundamental as lfu
import libs.modular_core.libgeometry as lgeo
import libs.modular_core.libvtkoutput as lvtk
import libs.modular_core.liboutput as lo
import libs.modular_core.libsettings as lset
import libs.gpu.lib_gpu as lgpu

from copy import deepcopy as copy
from numpy import median as median
from numpy import mean as mean
from numpy import std as stddev
from numpy import var as variance
from scipy.stats import pearsonr as correl_coeff
import scipy.ndimage.morphology as morph
import numpy as np
import os
import math
import time
import types

import pdb

if __name__ == 'libs.modular_core.libpostprocess':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__':
	print 'this is a library!'

class post_process_plan(lfu.plan):

	def __init__(self, *args, **kwargs):
		self.impose_default('label', 'post process plan', **kwargs)
		self.impose_default('post_processes', [], **kwargs)
		use = lset.get_setting('postprocessing')
		kwargs['use_plan'] = use
		self.selected_process_label = None
		lfu.plan.__init__(self, *args, **kwargs)

	def enact_plan(self, *args, **kwargs):
		for process in self.post_processes:
			check1 = time.time()
			process(*args, **kwargs)
			print ' '.join(['completed post process:', process.label, 
						'in:', str(time.time() - check1), 'seconds'])

	def reset_process_list(self):
		del self.post_processes[:]
		del self._children_[:]

	def add_process(self, new = None):
		if not new: new = post_process_meanfield(parent = self)
		self.post_processes.append(new)
		self._children_.append(new)
		self.rewidget(True)

	def remove_process(self, selected = None):
		if selected: select = selected
		else: select = self.get_selected()
		if select:
			self.post_processes.remove(select)
			self._children_.remove(select)
			del self.parent.run_params['output_plans'][
							select.label + ' output']
			select._destroy_()

		self.rewidget(True)

	def move_process_up(self, *args, **kwargs):
		select = self.get_selected()
		if select:
			select_dex = lfu.grab_mobj_dex_by_name(
				select.label, self.post_processes)
			self.post_processes.pop(select_dex)
			self.post_processes.insert(select_dex - 1, select)
			#self.set_selected(select_dex - 1)
			self.rewidget_processes()

	def move_process_down(self, *args, **kwargs):
		select = self.get_selected()
		if select:
			select_dex = lfu.grab_mobj_dex_by_name(
				select.label, self.post_processes)
			self.post_processes.pop(select_dex)
			self.post_processes.insert(select_dex + 1, select)
			#self.set_selected(select_dex + 1)
			self.rewidget_processes()

	def rewidget_processes(self, rewidg = True):
		[proc.rewidget(rewidg) for proc in self.post_processes]

	def set_selected(self, sel_dex):
		key = 'process_selector'
		if not hasattr(self, key):
			print 'no selector'; return

		self.__dict__[key][0].setCurrentIndex(sel_dex)

	def get_selected(self):
		key = 'process_selector'
		if not hasattr(self, key):
			print 'no selector'; return

		try:
			dex = self.__dict__[key][0].layout().itemAt(
						0).widget().currentIndex() - 1
			#dex = self.__dict__[key][0].currentIndex()
			select = self.post_processes[dex]
			return select

		except IndexError:
			print 'no post process selected'; return

	def set_settables(self, *args, **kwargs):
		window = args[0]
		#ensemble = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		try: select_label = self.selected_process_label
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
				instances = [[self.post_processes, self], None], 
				keys = [[None, 'selected_process_label'], None], 
				handles = [(self, 'process_selector'), None], 
				labels = [None, ['Add Post Process', 
								'Remove Post Process', 
								'Move Up In Hierarchy', 
								'Move Down In Hierarchy']], 
				initials = [[select_label], None], 
				bindings = [None, [lgb.create_reset_widgets_wrapper(
										window, self.add_process), 
						lgb.create_reset_widgets_wrapper(window, 
								self.remove_process), 
						lgb.create_reset_widgets_wrapper(window, 
								self.move_process_up), 
						lgb.create_reset_widgets_wrapper(window, 
								self.move_process_down)]]))
		lfu.plan.set_settables(self, *args, from_sub = True)

class post_process(lfu.modular_object_qt):

	#ABSTRACT
	'''
	#a post process can:
	#	operate on each trajectory individually, preserving structure
	#	operate on a collection of trajectories
	#		these collections can be organized in a meaningful way
	#			a collection for each location on parameter space
	#				can have its own, or inherit a parameter space for this
	#			should design some other partitioning mechanism, for arbitrary collections
	#		the collection of all trajectories - simplest default behavior
	#
	#	each post_process must specify which of these regimes it can and will obey
	#
	#in general:
	#	self.data contains the result for processing by an output_plan
	#			Note: this is not the current implementation but should be
	#			if necessary to support nontrivial post process hierarchies
	'''

	def _set_label_(self, value):
		before = self.label
		if lfu.modular_object_qt._set_label_(self, value):
			procs = self.parent.post_processes
			for proc in procs:
				if before in proc.input_regime:
					dex = proc.input_regime.index(before)
					proc.input_regime[dex] = value

				if before in proc.valid_inputs:
					dex = proc.valid_inputs.index(before)
					proc.valid_inputs[dex] = value

			del self.parent.parent.run_params[
				'output_plans'][self.output.label]
			self.output.label = self.label + ' output'
			self.parent.parent.run_params['output_plans'][
						self.output.label] = self.output

	def __init__(self, label = 'another post process', parent = None, 
			valid_regimes = None, valid_base_classes = None, 
			regime = None, capture_targets = [], 
			#input_regime = 'simulation', valid_inputs = ['simulation'], 
			input_regime = None, valid_inputs = None, 
			visible_attributes = ['label'], base_class = None):

		if valid_base_classes is None:
			valid_base_classes = valid_postproc_base_classes

		if base_class is None:
			base_class = lfu.interface_template_class(
					object, 'post process abstract')

		if valid_inputs is None:
			valid_inputs = ['simulation']

		if input_regime is None:
			input_regime = ['simulation']

		self.input_regime = input_regime
		self.valid_inputs = valid_inputs
		self.regime = regime
		self.valid_regimes = valid_regimes
		self.capture_targets = capture_targets
		self.brand_new = True
		lfu.modular_object_qt.__init__(self, label = label, 
			parent = parent, valid_base_classes = valid_base_classes, 
							visible_attributes = visible_attributes, 
											base_class = base_class)
		self.output = lo.output_plan(
			label = self.label + ' output', parent = self)
		self._children_ = [self.output]

	def __call__(self, *args, **kwargs):
		self.initialize(*args, **kwargs)
		self.postproc(*args, **kwargs)

	'''
	def _destroy_(self, *args, **kwargs):
		try:
			del self.parent.parent.run_params['output_plans'][
									self.label + ' output']

		except KeyError:
			print 'couldnt destroy output plan!'
			pdb.set_trace()

		lfu.modular_object_qt._destroy_(self)
	'''

	def inputs_to_string(self):
		inps = []
		valid_inputs = self.get_valid_inputs(None, self.parent.parent)
		for input_ in self.input_regime:
			if input_.startswith('simulation'): numb = 0
			else: numb = valid_inputs.index(input_) - 1
			inps.append(numb)

		inps = ', '.join([str(inp) for inp in inps])
		return inps

	def to_string(self):
		return '\t' + self.label + ' : '

	def provide_axes_manager_input(self):
		self.use_line_plot = True
		self.use_color_plot = True
		self.use_bar_plot = True

	def get_source_reference(self, *args, **kwargs):
		sources = args[1].postprocess_plan.post_processes + \
								args[1].fitting_plan.routines
		try:
			inputs = [lfu.grab_mobj_by_name(inp, sources) for inp 
				in self.input_regime if not inp == 'simulation']

		except ValueError:
			self.fix_inputs()
			#return self.get_source_reference(*args, **kwargs)
			return []

		return inputs

	def fix_inputs(self, *args, **kwargs):
		print 'fix_inputs is not yet implemented...'
		pdb.set_trace()

	def get_valid_inputs(self, *args, **kwargs):
		post_procs = args[1].postprocess_plan.post_processes
		self_dex = lfu.grab_mobj_dex_by_name(self.label, post_procs)
		processes = lfu.grab_mobj_names(post_procs)[:self_dex]
		routines = lfu.grab_mobj_names(args[1].fitting_plan.routines)
		return ['simulation'] + processes + routines

	def get_targetables(self, *args, **kwargs):
		targets = []
		if 'simulation' in self.input_regime:
			targets.extend(copy(args[1].run_params['plot_targets']))

		for source in self.get_source_reference(*args, **kwargs):
			targets.extend(copy(source.capture_targets))

		return lfu.uniqfy(targets)

	def initialize(self, *args, **kwargs):
		#modifying kwargs here does not affect kwargs in .postproc()!!
		pass

	def determine_regime(self, *args, **kwargs):
		ensem = args[0]
		if 'per trajectory' in self.valid_regimes:
			self.regime = 'per trajectory'
			self.output.flat_data = False

		elif 'by parameter space map' in self.valid_regimes and\
					ensem.cartographer_plan.use_plan:
			#self.parent.parent.cartographer_plan.use_plan:
			self.regime = 'by parameter space map'
			self.output.flat_data = False

		elif 'all trajectories' in self.valid_regimes:
			self.regime = 'all trajectories'
			self.output.flat_data = False

		else: print 'post process regime could not be resolved', self

	def postproc(self, *args, **kwargs):
		#pool should invariably be a list of 
		#	lists of data objects for each trajectory
		#a method must always be provided by a superclass
		#	a pool and a p_space are optional, default
		#	is to use the ensemble
		self.determine_regime(args[0])
		pool = []
		sources = self.get_source_reference(1, *args, **kwargs)
		#for src in sources: lfu.zip_list(pool, src.data)
		if 'simulation' in self.input_regime:
			#lfu.zip_list(pool, args[0].data_pool.get_batch())
			pool = args[0].data_pool

		for src in sources: lfu.zip_list(pool, src.data)
		if 'p_space' in kwargs.keys(): p_space = kwargs['p_space']
		else: p_space = args[0].cartographer_plan
		self.p_space = p_space
		if self.regime == 'all trajectories':
			self.handle_all_trajectories(kwargs['method'], pool, p_space)

		elif self.regime == 'by parameter space map':
			self.handle_by_parameter_space(kwargs['method'], pool, p_space)

		elif self.regime == 'manual grouping':
			self.handle_manual_grouping(kwargs['method'], pool, p_space)

		elif self.regime == 'per trajectory':
			self.handle_per_trajectory(kwargs['method'], pool, p_space)

	def handle_all_trajectories(self, method, pool, p_space):
		#self.data = method(pool)
		#self.output.flat_data = True

		#is this a hack?? might present a problem
		#not doing this creates bugs with per trajectory processes downstream

		#DATAFLAG - wrap pool in scalers before method()!
		self.data = [method(pool)]

	def handle_by_parameter_space(self, method, pool, p_space):
		self.handle_by_parameter_space_non_mp(method, pool, p_space)

	def handle_by_parameter_space_non_mp(self, method, pool, p_space):
		pool_dex = 0
		result_pool = []
		for locale in p_space.trajectory:
			traj_count = locale[1].trajectory_count
			#temp_pool = pool[pool_dex:pool_dex + traj_count]
			#print 'traj_dex', locale[0]
			temp_pool = pool[locale[0]]
			data = method(temp_pool)
			result_pool.append(data)
			pool_dex += traj_count

		self.data = result_pool

	def handle_manual_grouping(self, method, pool, p_space):
		pdb.set_trace()

	def handle_per_trajectory(self, method, pool, p_space):
		result_pool = []
		#DATAFLAG - wrap trajectory in scalers before method()!
		[result_pool.append(method(trajectory)) 
						for trajectory in pool]
		self.data = result_pool

	def rewidget(self, *args, **kwargs):
		try:
			if type(args[0]) is types.BooleanType:
				if args[0]: self.output.rewidget_ = True
				lfu.modular_object_qt.rewidget(self, *args, **kwargs)

		except IndexError:
			return lfu.modular_object_qt.rewidget(self, *args, **kwargs)

	def sanitize(self, *args, **kwargs):
		lfu.modular_object_qt.sanitize(self, *args, **kwargs)

	def set_settables(self, *args, **kwargs):
		#self.provide_axes_manager_input()
		#window = args[0]
		ensem = args[1]
		if self.brand_new:
			self.brand_new = not self.brand_new
			self.mp_plan_ref = ensem.multiprocess_plan
			ensem.run_params['output_plans'][
				self.label + ' output'] = self.output

		where_reference = ensem.run_params['output_plans']
		self.output.label = self.label + ' output'
		self.handle_widget_inheritance(*args, **kwargs)
		if self.valid_inputs:
			self.widg_templates.append(
				lgm.interface_template_gui(
					panel_position = (0, 2), 
					widgets = ['check_set'], 
					tooltips = [['Requires GUI update (Ctrl+G)' 
							for input_ in self.valid_inputs]], 
					append_instead = [True], 
					instances = [[self]], 
					keys = [['input_regime']], 
					labels = [self.valid_inputs], 
					box_labels = ['Input Data']))

		#recaster = lgm.recasting_mason(parent = window)
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
				box_labels = ['Post Process Method'], 
				labels = [tags], 
				initials = [[self.base_class._tag]]))
		#dictionary_support = lgm.dictionary_support_mason(
		#								parent = window)
		self.widg_templates.append(
			lgm.interface_template_gui(
				keys = [['label']], 
				minimum_sizes = [[(150, 50)]], 
				#widget_mason = dictionary_support, 
				#data_links = [label_data_links], 
				instances = [[self]], 
				widgets = ['text'], 
				#where_store = where_reference, 
				box_labels = ['Post Process Name']))
		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)

class post_process_meanfield(post_process):

	def __init__(self, *args, **kwargs):
		if not 'base_class' in kwargs.keys():
			kwargs['base_class'] = lfu.interface_template_class(
								object, 'standard statistics')

		if not 'label' in kwargs.keys():
			kwargs['label'] = 'standard statistics'

		if not 'valid_regimes' in kwargs.keys():
			kwargs['valid_regimes'] = ['all trajectories', 
								'by parameter space map']

		if not 'regime' in kwargs.keys():
			kwargs['regime'] = 'all trajectories'

		self.impose_default('function_of', None, **kwargs)
		self.impose_default('mean_of', None, **kwargs)
		self.impose_default('bin_count', 100, **kwargs)
		self.impose_default('ordered', True, **kwargs)
		post_process.__init__(self, *args, **kwargs)

	def to_string(self):
		#x stats : standard statistics : 0 : x of time : 10 : ordered
		inps = self.inputs_to_string()
		phrase = ' of '.join([self.mean_of, self.function_of])
		bins = str(self.bin_count)
		if self.ordered: ordered = 'ordered'
		else: ordered = 'unordered'
		return '\t' + ' : '.join([self.label, 'standard statistics', 
								inps, phrase, bins, ordered])

	def postproc(self, *args, **kwargs):
		kwargs['method'] = self.meanfield
		post_process.postproc(self, *args, **kwargs)

	def meanfield(self, *args, **kwargs):
		bin_axes, mean_axes = select_for_binning(
			args[0], self.function_of, self.mean_of)
		bins, vals = bin_scalers(bin_axes, mean_axes, 
						self.bin_count, self.ordered)
		means = [mean(val) for val in vals]
		if 0.0 in means: coeff_var_dont_flag = True
		else: coeff_var_dont_flag = False
		medians = [median(val) for val in vals]
		stddevs = [stddev(val) for val in vals]
		if coeff_var_dont_flag:
			print 'COEFFICIENT OF VARIATIONS WAS SET TO ZERO TO SAVE THE DATA'
			coeff_variations = [0.0 for stddev_, mean_ 
								in zip(stddevs, means)]

		else:
			coeff_variations = [stddev_ / mean_ for stddev_, mean_ 
											in zip(stddevs, means)]

		variances = [variance(val) for val in vals]
		#variances = [mean(val) for val in vals]
		data = lgeo.scalers_from_labels(self.target_list)
		data[0].scalers = bins
		data[1].scalers = means
		data[2].scalers = medians
		data[3].scalers = variances
		data[4].scalers = stddevs
		data[5].scalers = [means[k] + stddevs[k] 
					for k in range(len(means))]
		data[6].scalers = [means[k] - stddevs[k] 
					for k in range(len(means))]
		data[7].scalers = coeff_variations
		return data

	#this is a stupid hack!
	def provide_axes_manager_input(self):
		self.use_line_plot = True
		self.use_color_plot = False
		self.use_bar_plot = False
		self.x_title = self.function_of

	def set_settables(self, *args, **kwargs):
		self.valid_regimes = ['all trajectories', 
			#'by parameter space map', 'manual grouping']
			'by parameter space map']
		self.valid_inputs = self.get_valid_inputs(*args, **kwargs)
		capture_targetable = self.get_targetables(*args, **kwargs)
		if self.mean_of is None and capture_targetable:
			self.mean_of = capture_targetable[0]

		if self.function_of is None and capture_targetable:
			self.function_of = capture_targetable[0]

		self.target_list = [self.function_of, 
			self.mean_of + ' mean', self.mean_of + ' median', 
			self.mean_of + ' variance', '1 stddev of ' + self.mean_of, 
			self.mean_of + ' +1 stddev', self.mean_of + ' -1 stddev', 
			self.mean_of + ' coefficient of variation']
		self.capture_targets = self.target_list
		self.handle_widget_inheritance(*args, from_sub = False)
		self.widg_templates.append(
			lgm.interface_template_gui(
				panel_position = (1, 3), 
				widgets = ['check_set'], 
				append_instead = [False], 
				instances = [[self]], 
				#rewidget = [[True]], 
				keys = [['ordered']], 
				labels = [['Domain is Ordered']], 
				box_labels = ['Ordered Domain']))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['spin'], 
				initials = [[self.bin_count]], 
				minimum_values = [[1]], 
				maximum_values = [[100000]], 
				instances = [[self]], 
				#rewidget = [[True]], 
				keys = [['bin_count']], 
				box_labels = ['Number of Bins']))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['radio'], 
				labels = [capture_targetable], 
				initials = [[self.function_of]], 
				instances = [[self]], 
				keys = [['function_of']], 
				box_labels = ['As a Function of']))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['radio'], 
				labels = [capture_targetable], 
				initials = [[self.mean_of]], 
				instances = [[self]], 
				keys = [['mean_of']], 
				box_labels = ['Statistics of']))
		super(post_process_meanfield, self).set_settables(
									*args, from_sub = True)

class post_process_correlation_values(post_process):

	def __init__(self, *args, **kwargs):
	#def __init__(self, label = 'another correlation', ordered = True, 
	#		target_1 = None, target_2 = None, function_of = None, 
	#		bin_count = 10, fill_value = -100.0, 
	#		regime = 'all trajectories', base_class = None, 
	#		capture_targets = [], input_regime = ['simulation'], 
	#		valid_inputs = ['simulation'], 
	#		valid_regimes = ['all trajectories', 
	#						'by parameter space map']):
							#'by parameter space map', 
							#	'manual grouping']):

		if not 'base_class' in kwargs.keys():
			kwargs['base_class'] = lfu.interface_template_class(
										object, 'correlation')

		if not 'label' in kwargs.keys():
			kwargs['label'] = 'correlation'

		if not 'valid_regimes' in kwargs.keys():
			kwargs['valid_regimes'] = ['all trajectories', 
								'by parameter space map']

		if not 'regime' in kwargs.keys():
			kwargs['regime'] = 'all trajectories'

		self.impose_default('target_1', None, **kwargs)
		self.impose_default('target_2', None, **kwargs)
		self.impose_default('function_of', None, **kwargs)
		self.impose_default('bin_count', 100, **kwargs)
		self.impose_default('ordered', True, **kwargs)
		self.impose_default('fill_value', -100.0, **kwargs)
		#post_process.__init__(self, label = label, regime = regime, 
		#	base_class = base_class, valid_regimes = valid_regimes, 
		#	input_regime = input_regime, valid_inputs = valid_inputs, 
		#	capture_targets = capture_targets)
		post_process.__init__(self, *args, **kwargs)

	def to_string(self):
		#x, y correlation : correlation : 0 : x and y of time : 10 : ordered
		inps = self.inputs_to_string()
		phrase = ' of '.join([' and '.join(
			[self.target_1, self.target_2]), 
				self.function_of])
		bins = str(self.bin_count)
		if self.ordered: ordered = 'ordered'
		else: ordered = 'unordered'
		return '\t' + ' : '.join([self.label, 'correlation', 
						inps, phrase, bins, ordered])

	def provide_axes_manager_input(self):
		self.use_line_plot = True
		self.use_color_plot = False
		self.use_bar_plot = False

	def postproc(self, *args, **kwargs):
		kwargs['method'] = self.correlate
		post_process.postproc(self, *args, **kwargs)

	def correlate(self, *args, **kwargs):

		def verify(val):
			if math.isnan(val): return self.fill_value
			else: return val

		bin_axes, targ_1_axes = select_for_binning(
			args[0], self.function_of, self.target_1)
		bin_axes, targ_2_axes = select_for_binning(
			args[0], self.function_of, self.target_2)
		bins, vals_1 = bin_scalers(bin_axes, targ_1_axes, 
							self.bin_count, self.ordered)
		bins, vals_2 = bin_scalers(bin_axes, targ_2_axes, 
							self.bin_count, self.ordered)
		correlations, p_values = zip(*[correl_coeff(val_1, val_2) 
						for val_1, val_2 in zip(vals_1, vals_2)])
		data = lgeo.scalers_from_labels([self.function_of, 
			'correlation coefficients', 'correlation p-value'])
		data[0].scalers = bins
		data[1].scalers = [verify(val) for val in correlations]
		data[2].scalers = [verify(val) for val in p_values]
		return data

	def set_settables(self, *args, **kwargs):
		self.valid_regimes = ['all trajectories', 
			#'by parameter space map', 'manual grouping']
			'by parameter space map']
		self.valid_inputs = self.get_valid_inputs(*args, **kwargs)
		capture_targetable = self.get_targetables(*args, **kwargs)
		if self.target_1 is None:
			if capture_targetable:
				self.target_1 = capture_targetable[0]

		if self.target_2 is None:
			if capture_targetable:
				self.target_2 = capture_targetable[0]

		if self.function_of is None:
			if capture_targetable:
				self.function_of = capture_targetable[0]

		self.capture_targets = [self.function_of, 
			'correlation coefficients', 'correlation p-value']
		self.handle_widget_inheritance(*args, from_sub = False)
		self.widg_templates.append(
			lgm.interface_template_gui(
				panel_position = (1, 3), 
				instances = [[self]], 
				#rewidget = [[True]], 
				keys = [['ordered']], 
				labels = [['Domain is Ordered']], 
				append_instead = [False], 
				widgets = ['check_set'], 
				box_labels = ['Ordered Domain']))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['spin'], 
				instances = [[self]], 
				#rewidget = [[True]], 
				keys = [['bin_count']], 
				initials = [[self.bin_count]], 
				minimum_values = [[1]], 
				maximum_values = [[100000]], 
				box_labels = ['Number of Bins']))
		self.widg_templates.append(
			lgm.interface_template_gui(
				keys = [['function_of']], 
				instances = [[self]], 
				widgets = ['radio'], 
				panel_label = 'As a Function of', 
				initials = [[self.function_of]], 
				labels = [capture_targetable]))
		self.widg_templates.append(
			lgm.interface_template_gui(
				layout = 'horizontal', 
				keys = [['target_1'], ['target_2']], 
				instances = [[self], [self]], 
				widgets = ['radio', 'radio'], 
				panel_label = 'Correlation of', 
				initials = [[self.target_1], [self.target_2]], 
				labels = [capture_targetable, capture_targetable], 
				box_labels = ['Target 1', 'Target 2']))
		super(post_process_correlation_values, self).set_settables(
											*args, from_sub = True)

class post_process_counts_to_concentrations(post_process):

	def __init__(self, label = 'counts to concentrations', 
			dater_ids = None, volume = 1.0, regime = 'per trajectory', 
			base_class = None, valid_regimes = ['per trajectory'], 
			input_regime = ['simulation'], valid_inputs = ['simulation'], 
			capture_targets = []):
		if base_class is None:
			base_class = lfu.interface_template_class(
					object, 'counts to concentrations')

		self.dater_ids = dater_ids
		self.volume = volume
		post_process.__init__(self, label = label, regime = regime, 
			base_class = base_class, valid_regimes = valid_regimes, 
			input_regime = input_regime, valid_inputs = valid_inputs, 
			capture_targets = capture_targets)

	def to_string(self):
		#label : counts to concentrations : 0 : x and y of time : 10 : ordered
		inps = self.inputs_to_string()
		return '\t' + ' : '.join([self.label, 
			'counts to concentrations', inps])

	def provide_axes_manager_input(self):
		self.use_line_plot = True
		self.use_color_plot = False
		self.use_bar_plot = False

	def initialize(self, *args, **kwargs):
		self.volume = float(self.volume)
		post_process.initialize(self, *args, **kwargs)

	def postproc(self, *args, **kwargs):
		kwargs['method'] = self.count_to_concentration
		#if not self.input_regime == 'simulation':
		#	source = self.get_source_reference(*args, **kwargs)
		#	kwargs['pool'] = source.data
		#	kwargs['p_space'] = source.p_space
		#
		post_process.postproc(self, *args, **kwargs)

	#currently converts # molecules to nM??
	def count_to_concentration(self, *args, **kwargs):
		#FIX THIS TO HANDLE A FULL TRAJECTORY AND NOT JUST ONE SCALER OBJECT
		trajectory = args[0]
		conv_factor = ((6.02*10.0**23)*(10.0**(-9))*self.volume)**(-1)
		data = lgeo.scalers_from_labels([trajectory.label])[0]
		if data.label in self.dater_ids:
			data.scalers = [float(count)*conv_factor 
					for count in trajectory.scalers]

		else:
			data.scalers = trajectory.scalers

		return data

	def set_settables(self, *args, **kwargs):
		self.valid_regimes = ['per trajectory']
		self.valid_inputs = self.get_valid_inputs(*args, **kwargs)
		capture_targetable = self.get_targetables(*args, **kwargs)
		if self.dater_ids is None:
			if capture_targetable:
				self.dater_ids = capture_targetable

		self.capture_targets = capture_targetable
		self.handle_widget_inheritance(*args, from_sub = False)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['spin'], 
				doubles = [[True]], 
				minimum_values = [[0.0]], 
				initials = [[float(self.volume)]], 
				instances = [[self]], 
				keys = [['volume']], 
				box_labels = ['Volume']))
		self.widg_templates.append(
			lgm.interface_template_gui(
				keys = [['dater_ids']], 
				instances = [[self]], 
				#rewidget = [[True]], 
				widgets = ['check_set'], 
				box_labels = ['To Convert'], 
				append_instead = [True], 
				provide_master = [True], 
				labels = [capture_targetable]))
		super(post_process_counts_to_concentrations, 
			self).set_settables(*args, from_sub = True)

class post_process_slice_from_trajectory(post_process):

	def __init__(self, *args, **kwargs):
	#def __init__(self, label = 'slice from trajectory', 
	#		capture_targets = [], dater_ids = None, 
	#		slice_dex = 0, regime = 'per trajectory', 
	#		base_class = None, valid_regimes = ['per trajectory']):
		#if base_class is None:
		#	base_class = lfu.interface_template_class(
		#			object, 'slice from trajectory')

		if not 'base_class' in kwargs.keys():
			kwargs['base_class'] = lfu.interface_template_class(
								object, 'slice from trajectory')

		if not 'label' in kwargs.keys():
			kwargs['label'] = 'slices'

		if not 'valid_regimes' in kwargs.keys():
			kwargs['valid_regimes'] = ['per trajectory']

		if not 'regime' in kwargs.keys():
			kwargs['regime'] = 'per trajectory'

		self.impose_default('dater_ids', None, **kwargs)
		self.impose_default('slice_dex', -1, **kwargs)
	#	post_process.__init__(self, label = label, regime = regime, 
	#		base_class = base_class, valid_regimes = valid_regimes, 
	#		capture_targets = capture_targets)
		post_process.__init__(self, *args, **kwargs)

	def to_string(self):
		#slices : slice from trajectory : 1 : all : -1
		inps = self.inputs_to_string()
		phrase = 'all'
		slice_dex = str(self.slice_dex)
		return '\t' + ' : '.join([self.label, 'slice from trajectory', 
									inps, phrase, slice_dex])

	def provide_axes_manager_input(self):
		self.use_line_plot = True
		self.use_color_plot = False
		self.use_bar_plot = False

	def postproc(self, *args, **kwargs):
		kwargs['method'] = self.slice_from_trajectory
		post_process.postproc(self, *args, **kwargs)

	def slice_from_trajectory(self, *args, **kwargs):
		trajectory = args[0]
		data = lgeo.scalers_from_labels([label 
				for label in self.dater_ids])
		for dater in data:
			try:
				sub_traj = lfu.grab_mobj_by_name(
						dater.label, trajectory)

			except ValueError: continue
			if self.slice_dex.count(':') == 0:
				dater.scalers = [sub_traj.scalers[int(self.slice_dex)]]

			else:
				col_dex = self.slice_dex.index(':')
				slice_1 = int(self.slice_dex[:col_dex])
				slice_2 = int(self.slice_dex[col_dex:])
				dater.scalers = sub_traj.scalers[slice_1:slice_2]

		return data

	def set_settables(self, *args, **kwargs):
		self.valid_regimes = ['per trajectory']
		self.valid_inputs = self.get_valid_inputs(*args, **kwargs)
		capture_targetable = self.get_targetables(*args, **kwargs)
		if self.dater_ids is None:
			self.dater_ids = []

		#is this why output plans require one more update all the time it seems?
		self.capture_targets = self.dater_ids
		self.output.targeted = [targ for targ in self.output.targeted 
									if targ in self.capture_targets]
		self.handle_widget_inheritance(*args, from_sub = False)
		#use a spin widget to select a location in the domain
		#	or a text box to support true slicing
		self.widg_templates.append(
			lgm.interface_template_gui(
				keys = [['slice_dex']], 
				instances = [[self]], 
				#rewidget = [[True]], 
				widgets = ['text'], 
				box_labels = ['Slice Index'], 
				initials = [[self.slice_dex]]))
		self.widg_templates.append(
			lgm.interface_template_gui(
				keys = [['dater_ids']], 
				instances = [[self]], 
				#rewidget = [[True]], 
				widgets = ['check_set'], 
				box_labels = ['To Slice'], 
				append_instead = [True], 
				provide_master = [True], 
				labels = [capture_targetable]))
		super(post_process_slice_from_trajectory, 
			self).set_settables(*args, from_sub = True)

class post_process_reorganize_data(post_process):

	#the purpose of this process is to reorganize data
	#so that measurements are taken as a function of p-space index
	#within the p-space trajectory, to be resolved into color plots
	#representing 2-d subspaces of the p-space
	#thus any process which can use p-space, can be reorganized
	#if not using p-space, data won't be in the proper structure - 
	# this process then cannot be used and must be ignored
	def __init__(self, *args, **kwargs):
	#def __init__(self, label = 'reorganize data', 
	#		capture_targets = [], input_regime = ['simulation'], 
	#		valid_inputs = ['simulation'], dater_ids = None, 
	#		slice_dex = 0, regime = 'all trajectories', 
	#		base_class = None, valid_regimes = ['all trajectories']):
	#	if base_class is None:
	#		base_class = lfu.interface_template_class(
	#						object, 'reorganize data')
		if not 'base_class' in kwargs.keys():
			kwargs['base_class'] = lfu.interface_template_class(
									object, 'reorganize data')

		if not 'label' in kwargs.keys():
			kwargs['label'] = 'reorganize'

		if not 'valid_regimes' in kwargs.keys():
			kwargs['valid_regimes'] = ['all trajectories', 
								'by parameter space map']

		if not 'regime' in kwargs.keys():
			kwargs['regime'] = 'all trajectories'

		self.impose_default('dater_ids', None, **kwargs)
		#post_process.__init__(self, label = label, regime = regime, 
		#	base_class = base_class, valid_regimes = valid_regimes, 
		#	input_regime = input_regime, valid_inputs = valid_inputs, 
		#	capture_targets = capture_targets)
		post_process.__init__(self, *args, **kwargs)

	def to_string(self):
		#reorg : reorganize data : 2 : all
		inps = self.inputs_to_string()
		phrase = 'all'
		return '\t' + ' : '.join([self.label, 
			'reorganize data', inps, phrase])

	def provide_axes_manager_input(self):
		self.use_line_plot = True
		#self.use_line_plot = False
		self.use_color_plot = True
		self.use_bar_plot = False

	def postproc(self, *args, **kwargs):
		if not args[0].cartographer_plan.use_plan:
			print 'ensemble is not mapping p-space' +\
						'\n\treorganize will be ignored'
			return

		kwargs['method'] = self.data_by_trajectory
		#this is a hack to fix an undiagnosed bug
		self.valid_regimes = ['all trajectories']
		post_process.postproc(self, *args, **kwargs)

	def handle_all_trajectories(self, method, pool, p_space):
		self.data = [method(pool, p_space)]
		self.output.flat_data = False

	#take a collection of trajectories in 1 - 1 with p_space trajectory
	#create a dater of indices for that trajectory
	#create new daters in 1 - 1 with that dater, 
	#one for each dater in each trajectory of the original collection, 
	#which aggregates the original collection of trajectories
	def data_by_trajectory(self, *args, **kwargs):
		trajectory = args[0]
		p_space_map = args[1]
		data = lgeo.scalers_from_labels(
				['parameter space location index'] +\
				self.axis_labels + [label for label in self.dater_ids])
		for dex, locale in enumerate(trajectory):
			data[0].scalers.append(dex)
			p_space_locale_values =\
				p_space_map.trajectory[dex][1].location
			[dater.scalers.append(float(loc)) for loc, dater in 
									zip(p_space_locale_values, 
						data[1:len(self.axis_labels) + 1])]
			for dater in data[len(self.axis_labels) + 1:]:
				value = lfu.grab_mobj_by_name(
					dater.label, locale).scalers[-1]
				dater.scalers.append(value)

		surf_targets =\
			['parameter space location index'] + self.dater_ids
		data.append(lgeo.surface_vector(data, self.axis_labels, 
						surf_targets, 'reorg surface vector'))
		return data

	def set_settables(self, *args, **kwargs):
		self.valid_inputs = self.get_valid_inputs(*args, **kwargs)
		capture_targetable = self.get_targetables(*args, **kwargs)
		if self.dater_ids is None: self.dater_ids = []
		try:
			self.axis_labels = [subsp.label for subsp in 
				args[1].cartographer_plan.parameter_space.subspaces]

		except AttributeError: self.axis_labels = []
		self.capture_targets = ['parameter space location index'] +\
				self.axis_labels + [label for label in self.dater_ids]
		self.output.targeted = [targ for targ in self.output.targeted 
									if targ in self.capture_targets]
		self.handle_widget_inheritance(*args, from_sub = False)
		self.widg_templates.append(
			lgm.interface_template_gui(
				keys = [['dater_ids']], 
				instances = [[self]], 
				widgets = ['check_set'], 
				box_labels = ['Relevant Data'], 
				append_instead = [True], 
				provide_master = [True], 
				labels = [capture_targetable]))
		super(post_process_reorganize_data, 
			self).set_settables(*args, from_sub = True)

class post_process_1_to_1_binary_operation(post_process):

	#take a data set - choose two data mobjects and an operator
	#	make a new data mobject containing the result
	def __init__(self, *args, **kwargs):
		if not 'base_class' in kwargs.keys():
			kwargs['base_class'] = lfu.interface_template_class(
						object, 'one to one binary operation')

		if not 'label' in kwargs.keys():
			kwargs['label'] = '1 - 1 binary operation'

		if not 'valid_regimes' in kwargs.keys():
			kwargs['valid_regimes'] = ['per trajectory']

		if not 'regime' in kwargs.keys():
			kwargs['regime'] = 'per trajectory'

		self.impose_default('input_1', None, **kwargs)
		self.impose_default('input_2', None, **kwargs)
		self.impose_default('domain', None, **kwargs)
		self.impose_default('operation', '+', **kwargs)
		self.impose_default('operations', 
			['+', '-', '*', '/'], **kwargs)
		post_process.__init__(self, *args, **kwargs)

	def to_string(self):
		#label : one to one binary operation : 0
		inps = self.inputs_to_string()
		return '\t' + ' : '.join([self.label, 
			'one to one binary operation', inps])

	def provide_axes_manager_input(self):
		self.use_line_plot = True
		self.use_color_plot = False
		self.use_bar_plot = False

	def grab_daters(self, *args, **kwargs):
		trajectory = args[0]
		dater_1 = lfu.grab_mobj_by_name(self.input_1, trajectory)
		dater_2 = lfu.grab_mobj_by_name(self.input_2, trajectory)
		data = lgeo.scalers_from_labels(['_'.join(
			[self.input_1, self.input_2]), self.domain])
		data[1].scalers = lfu.grab_mobj_by_name(
						self.domain, trajectory).scalers
		return dater_1.scalers, dater_2.scalers, data

	def gpu_operation(self, *args, **kwargs):
		dater_1, dater_2, data = self.grab_daters(*args, **kwargs)
		data[0].scalers = self.mp_plan_ref.gpu_1to1_operation(
											dater_1, dater_2)
		return data

	def addition(self, *args, **kwargs):
		dater_1, dater_2, data = self.grab_daters(*args, **kwargs)
		data[0].scalers = [sum(pair) for pair in zip(dater_1, dater_2)]
		return data

	def subtraction(self, *args, **kwargs):
		dater_1, dater_2, data = self.grab_daters(*args, **kwargs)
		data[0].scalers = [pair[0] - pair[1] for 
				pair in zip(dater_1, dater_2)]
		return data

	def multiplication(self, *args, **kwargs):
		dater_1, dater_2, data = self.grab_daters(*args, **kwargs)
		data[0].scalers = [pair[0]*pair[1] for pair 
						in zip(dater_1, dater_2)]
		return data

	def division(self, *args, **kwargs):
		dater_1, dater_2, data = self.grab_daters(*args, **kwargs)
		data[0].scalers = [pair[0]/pair[1] for pair 
						in zip(dater_1, dater_2)]
		return data

	def postproc(self, *args, **kwargs):
		if lgpu.gpu_support:
			self.mp_plan_ref.gpu_worker.initialize()
			method = self.gpu_operation
			if self.operation == '+':
				self.mp_plan_ref.gpu_worker.verify_cl_extension(
								gpu_cl_extension = 'addition')

			if self.operation == '-':
				self.mp_plan_ref.gpu_worker.verify_cl_extension(
								gpu_cl_extension = 'subtraction')

			if self.operation == '*':
				self.mp_plan_ref.gpu_worker.verify_cl_extension(
								gpu_cl_extension = 'multiplication')

			if self.operation == '/':
				self.mp_plan_ref.gpu_worker.verify_cl_extension(
								gpu_cl_extension = 'division')

		else:
			if self.operation == '+':
				method = self.addition

			if self.operation == '-':
				method = self.subtraction

			if self.operation == '*':
				method = self.multiplication

			if self.operation == '/':
				method = self.division

		kwargs['method'] = method
		post_process.postproc(self, *args, **kwargs)

	#this is a stupid hack!
	def provide_axes_manager_input(self):
		post_process.provide_axes_manager_input(self)
		self.x_title = 'time'

	def set_settables(self, *args, **kwargs):
		self.valid_regimes = ['per trajectory']
		self.valid_inputs = self.get_valid_inputs(*args, **kwargs)
		capture_targetable = self.get_targetables(*args, **kwargs)
		if self.input_1 is None and capture_targetable:
				self.input_1 = capture_targetable[0]

		if self.input_2 is None and capture_targetable:
				self.input_2 = capture_targetable[0]

		if self.domain is None and capture_targetable:
				self.domain = capture_targetable[0]

		self.capture_targets = ['_'.join(
			[self.input_1, self.input_2]), self.domain]
		self.handle_widget_inheritance(*args, from_sub = False)
		self.widg_templates.append(
			lgm.interface_template_gui(
				panel_position = (1, 3), 
				keys = [['domain']], 
				instances = [[self]], 
				widgets = ['radio'], 
				box_labels = ['As a Function of'], 
				initials = [[self.domain]], 
				labels = [capture_targetable]))
		self.widg_templates.append(
			lgm.interface_template_gui(
				keys = [['input_2']], 
				instances = [[self]], 
				widgets = ['radio'], 
				box_labels = ['Input 2'], 
				initials = [[self.input_2]], 
				labels = [capture_targetable]))
		self.widg_templates.append(
			lgm.interface_template_gui(
				keys = [['operation']], 
				instances = [[self]], 
				widgets = ['radio'], 
				box_labels = ['Operation'], 
				initials = [[self.operation]], 
				labels = [self.operations]))
		self.widg_templates.append(
			lgm.interface_template_gui(
				keys = [['input_1']], 
				instances = [[self]], 
				widgets = ['radio'], 
				box_labels = ['Input 1'], 
				initials = [[self.input_1]], 
				labels = [capture_targetable]))
		super(post_process_1_to_1_binary_operation, 
			self).set_settables(*args, from_sub = True)

class post_process_period_finding(post_process):

	#the **kwargs keyword dictionary is modified and passed to the 
	# superclass where elements like kwargs['base_class'] are used
	def __init__(self, *args, **kwargs):
		if not 'base_class' in kwargs.keys():
			#class is used for recasting processes as other process instances
			# second argument is a string to look up the appropriate class
			#subsequently also appears in valid_postproc_base_classes
			kwargs['base_class'] = lfu.interface_template_class(
										object, 'period finding')

		#provide a default label - is made unique by superclasses
		if not 'label' in kwargs.keys():
			kwargs['label'] = 'period finder'

		#this process can be run on all trajectories
		# if the parameter space is not being mapped
		#or the process can be run all each p-space location
		# this is equivalent to the first case but run once
		# on each p-space location's collection of trajectories
		if not 'valid_regimes' in kwargs.keys():
			kwargs['valid_regimes'] = ['per trajectory']

		#by default it will attempt to run on all trajectories
		if not 'regime' in kwargs.keys():
			kwargs['regime'] = 'per trajectory'

		self.window = 5
		self.period_of = None

		#always call superclass's init within modular platform
		post_process.__init__(self, *args, **kwargs)

	def to_string(self):
		#label : period finding : 0
		inps = self.inputs_to_string()
		return '\t' + ' : '.join([self.label, 'period finding', inps])

	def provide_axes_manager_input(self):
		self.use_line_plot = True
		self.use_color_plot = False
		self.use_bar_plot = False

	#the superclass actually runs the method, but here the subclass
	# points to the appropriate bound method to use
	def postproc(self, *args, **kwargs):
		if not 'fixed_time' in self.target_list:
			print 'ensemble is captureing fixed time' +\
					'\n\tperiod-finding will be ignored'

		kwargs['method'] = self.find_period
		post_process.postproc(self, *args, **kwargs)

	#this is where the actual algorithm for period finding goes
	# args[0] will be the data set
	# at this function, the data set will always appear to be a list
	# of lists of libs.modular_core.libgeometry.scalers objects
	#each trajectory results in a list of scalers objects
	# these lists are put in a list which is what appears as args[0]
	#use pdb.set_trace() to investigate if this isn't clear
	def find_period(self, *args, **kwargs):
		time_dex = [dater.label == 'fixed_time' for 
						dater in args[0]].index(True)
		targ_dex = [dater.label == self.period_of for 
						dater in args[0]].index(True)
		time = args[0][time_dex]
		targ = args[0][targ_dex]
		periods, amplitudes = self.find_period_in_window(
							time.scalers, targ.scalers)
		data = lgeo.scalers_from_labels(self.target_list)
		data[1].scalers, data[2].scalers = self.fill_in(
					periods, amplitudes, time.scalers)
		data[0].scalers = copy(time.scalers[:len(data[1].scalers)])
		return data

	#fill in values for codomain so that it is 1 - 1 with domain
	def fill_in(self, codomain, follow, domain):
		new_codomain = []
		new_follow = []
		dom_dex = 0
		summed_periods = 0
		for value, fellow in zip(codomain, follow):
			summed_periods += value
			#print 'summed_periods', summed_periods
			while summed_periods > domain[dom_dex]:
				new_codomain.append(value)
				new_follow.append(fellow)
				dom_dex += 1

		return new_codomain, new_follow

	def find_period_in_window(self, t, x):
		w = int(self.window)
		y = morph.grey_dilation(x, size = w)
		t = t[w-1:-w]
		x = x[w-1:-w]
		y = y[w-1:-w]
		inds = np.argwhere(x==y)
		NN = inds.size
		period = np.zeros(NN - 1)
		#period = np.zeros(NN)
		amp = np.zeros(NN - 1)
		#amp = np.zeros(NN)
		for ii in range(NN - 1):
		#for ii in range(1, NN):
			xs = x[inds[ii]:inds[ii + 1]]
			#xs = x[inds[ii] - 1:inds[ii]]
			amp[ii] = 0.5 * (xs[0] + xs[-1] - 2 * np.min(xs))
			period[ii] = t[inds[ii + 1]] - t[inds[ii]]
			#period[ii] = t[inds[ii]] - t[inds[ii - 1]]
			#print np.min(xs)

		return period, amp

	#this function specifies the gui for this object
	# it's a bit difficult to describe when it's called, but anything
	# which is kept up-to-date prior to running is likely kept that way
	# by this function
	#this function is only called to recalculate the widget templates
	# it is NOT called simply to make them, unless necessary
	def set_settables(self, *args, **kwargs):
		self.valid_regimes = ['per trajectory']
		self.valid_inputs = self.get_valid_inputs(*args, **kwargs)
		capture_targetable = self.get_targetables(*args, **kwargs)
		if self.period_of is None and capture_targetable:
			self.period_of = capture_targetable[0]

		self.target_list = ['fixed_time', 
				self.period_of + ' period', 
				self.period_of + ' amplitude']
		self.capture_targets = self.target_list
		self.handle_widget_inheritance(*args, from_sub = False)
		self.widg_templates.append(
			lgm.interface_template_gui(
				keys = [['window']], 
				instances = [[self]], 
				#rewidget = [[True]], 
				widgets = ['text'], 
				box_labels = ['Window'], 
				initials = [[self.window]]))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['radio'], 
				labels = [capture_targetable], 
				initials = [[self.period_of]], 
				instances = [[self]], 
				keys = [['period_of']], 
				box_labels = ['Period/Amplitude of']))
		super(post_process_period_finding, self).set_settables(
										*args, from_sub = True)

#completely unfinished
class post_process_measure_probability(post_process):

	def __init__(self, *args, **kwargs):
	#def __init__(self, label = 'probability measurement', 
	#		bin_counts = [100], fill_values = [-100.0], 
	#		regime = 'all trajectories', base_class = None, 
	#		capture_targets = [], input_regime = ['simulation'], 
	#		valid_inputs = ['simulation'], 
	#		valid_regimes = ['all trajectories', 
	#						'by parameter space map']):
							#'by parameter space map', 
							#	'manual grouping']):

		if not 'base_class' in kwargs.keys():
			#class is used for recasting processes as other process instances
			# second argument is a string to look up the appropriate class
			#subsequently also appears in valid_postproc_base_classes
			kwargs['base_class'] = lfu.interface_template_class(
										object, 'probability')

		if not 'label' in kwargs.keys():
			kwargs['label'] = 'probability measurement'

		if not 'valid_regimes' in kwargs.keys():
			kwargs['valid_regimes'] = ['all trajectories', 
								'by parameter space map']

		if not 'regime' in kwargs.keys():
			kwargs['regime'] = 'all trajectories'

		self.impose_default('bin_counts', [100], **kwargs)
		self.impose_default('fill_values', [-100], **kwargs)
		#post_process.__init__(self, label = label, regime = regime, 
		#	base_class = base_class, valid_regimes = valid_regimes, 
		#	input_regime = input_regime, valid_inputs = valid_inputs, 
		#	capture_targets = capture_targets)
		post_process.__init__(self, *args, **kwargs)

	def to_string(self):
		#label : probability : 0
		inps = self.inputs_to_string()
		return '\t' + ' : '.join([self.label, 'probability', inps])

	def provide_axes_manager_input(self):
		self.use_line_plot = True
		self.use_color_plot = True
		self.use_bar_plot = True

	def postproc(self, *args, **kwargs):
		kwargs['method'] = self.measure_probability
		post_process.postproc(self, *args, **kwargs)

	def measure_probability(self, *args, **kwargs):
		'''
		def verify(val):
			if math.isnan(val): return self.fill_value
			else: return val

		bin_axes, targ_1_axes = select_for_binning(
			args[0], self.function_of, self.target_1)
		bin_axes, targ_2_axes = select_for_binning(
			args[0], self.function_of, self.target_2)
		bins, vals_1 = bin_scalers(bin_axes, targ_1_axes, 
							self.bin_count, self.ordered)
		bins, vals_2 = bin_scalers(bin_axes, targ_2_axes, 
							self.bin_count, self.ordered)
		correlations, p_values = zip(*[correl_coeff(val_1, val_2) 
						for val_1, val_2 in zip(vals_1, vals_2)])
		'''
		pdb.set_trace()
		data = lgeo.scalers_from_labels([self.function_of, 
			'correlation coefficients', 'correlation p-value'])
		#data[0].scalers = bins
		#data[1].scalers = [verify(val) for val in correlations]
		#data[2].scalers = [verify(val) for val in p_values]
		return data

	def set_settables(self, *args, **kwargs):
		self.valid_regimes = ['all trajectories', 
			#'by parameter space map', 'manual grouping']
			'by parameter space map']
		self.valid_inputs = self.get_valid_inputs(*args, **kwargs)
		capture_targetable = self.get_targetables(*args, **kwargs)

		self.capture_targets = ['probability']
		self.handle_widget_inheritance(*args, from_sub = False)
		super(post_process_measure_probability, self).set_settables(
											*args, from_sub = True)

#if this can be made into not an instance method, it can be parallelized
def correlate(self, *args, **kwargs):

	def verify(val):
		if math.isnan(val): return self.fill_value
		else: return val

	print 'correlating', self.target_1, 'and', self.target_2
	bin_axes, targ_1_axes = select_for_binning(
		args[0], self.function_of, self.target_1)
	bin_axes, targ_2_axes = select_for_binning(
		args[0], self.function_of, self.target_2)
	check2 = time.time()
	bins, vals_1 = bin_scalers(bin_axes, targ_1_axes, 
						self.bin_count, self.ordered)
	bins, vals_2 = bin_scalers(bin_axes, targ_2_axes, 
						self.bin_count, self.ordered)
	check3 = time.time()
	print 'binning scalers time: ', check3 - check2
	correlations, p_values = zip(*[correl_coeff(val_1, val_2) 
					for val_1, val_2 in zip(vals_1, vals_2)])
	print 'correlating scalers time: ', time.time() - check3
	data = lgeo.scalers_from_labels([self.function_of, 
		'correlation coefficients', 'correlation p-value'])
	data[0].scalers = bins
	self.fill_value = -100.0
	data[1].scalers = [verify(val) for val in correlations]
	data[2].scalers = [verify(val) for val in p_values]
	return data

def select_for_binning(pool, be_binned, be_meaned):
	#print 'be meaned', be_meaned
	if hasattr(pool, '_flatten_'): flat_pool = pool._flatten_(pool)
	else: flat_pool = [item for sublist in pool for item in sublist]
	bin_lookup  = [pool[k][j].label == be_binned 
						for k in range(len(pool)) 
					for j in range(len(pool[k]))]
	mean_lookup = [pool[k][j].label == be_meaned 
						for k in range(len(pool)) 
					for j in range(len(pool[k]))]
	if not bin_lookup or not mean_lookup:
		pdb.set_trace()

	bin_axes    = [flat_pool[k] for k in range(len(flat_pool)) 
									if bin_lookup[k] == True]
	mean_axes   = [flat_pool[k] for k in range(len(flat_pool)) 
									if mean_lookup[k] == True]
	return bin_axes, mean_axes

def bin_scalers(axes, ax_vals, bin_res, ordered = True):
	bin_min = min([min(ax.scalers) for ax in axes])
	bin_max = max([max(ax.scalers) for ax in axes])
	orders = 1000000000000000000.0
	bin_res = (bin_max - bin_min) / bin_res
	bins = [x / orders for x in 
			range(int(bin_min*orders), 
				int(bin_max*orders), 
				int(bin_res*orders))]
	vals = [[] for k in range(len(bins))]
	bin_bump = bin_res/2.0
	if ordered:
		#for when ordering is monotonically increasing
		j_last = [0]*len(axes)
		for i in range(len(bins)):
			threshold_top = bins[i] + bin_bump
			for k in range(len(axes)):
				last_j = j_last[k]
				for j in range(last_j, len(axes[k].scalers)):

					if axes[k].scalers[j] < threshold_top:
						vals[i].append(ax_vals[k].scalers[j])

					else:
						j_last[k] = j
						break

	else:
		#for when no ordering is assumed
		for i in range(len(bins)):
			try:
				threshold_bottom = threshold_top

			except:
				threshold_bottom = bins[i]

			threshold_top = bins[i] + bin_bump
			for k in range(len(axes)):
				for j in range(len(axes[k].scalers)):
					if axes[k].scalers[j] < threshold_top and axes[k].scalers[j] > threshold_bottom:
						vals[i].append(ax_vals[k].scalers[j])		

	return bins, vals

valid_postproc_base_classes = [lfu.interface_template_class(
						post_process_meanfield, 
								'standard statistics'), 
							lfu.interface_template_class(
						post_process_counts_to_concentrations, 
								'counts to concentrations'), 
							lfu.interface_template_class(
						post_process_correlation_values, 
								'correlation'), 
							lfu.interface_template_class(
						post_process_slice_from_trajectory, 
								'slice from trajectory'), 
							lfu.interface_template_class(
						post_process_reorganize_data, 
								'reorganize data'), 
							lfu.interface_template_class(
						post_process_1_to_1_binary_operation, 
								'one to one binary operation'), 
							lfu.interface_template_class(
						post_process_measure_probability, 
										'probability'), 
							lfu.interface_template_class(
						post_process_period_finding, 
									'period finding')]






