import modular_core as mc
import modular_core.resources as mcrsrc
import modular_core.libfundamental as lfu
import modular_core.libworkerthreads as lwt
import modular_core.liboutput as lo
import modular_core.libfiler as lf
import modular_core.libcriterion as lc
import modular_core.libfitroutine as lfr
import modular_core.libgeometry as lgeo
import modular_core.libpostprocess as lpp
import modular_core.libmultiprocess as lmp
import modular_core.libiteratesystem as lis
import modular_core.libsettings as lset

import pstats, cProfile, StringIO

from copy import deepcopy as copy
import os
import fnmatch
import sys
import traceback
import types
import time
from math import sqrt as sqrt
import numpy as np

import pdb

manager = None

class ensemble(lfu.modular_object_qt):

	current_tab_index = 0

	def __init__(self, *args, **kwargs):
		#self.impose_default('current_tab_index', 0, **kwargs)
		#self.current_tab_index = 0
		self.aborted = False
		self.data_pool = lfu.data_container(
			data = [], postproc_data = [])
		self.data_scheme = None
		self.__dict__ = lfu.dictionary()
		if 'parent' in kwargs.keys(): self.parent = kwargs['parent']
		self.cancel_make = False
		self.skip_simulation = False
		self.mcfg_path = ''
		#self.num_trajectories = 1
		num_traj = lset.get_setting('trajectory_count')
		if num_traj: self.num_trajectories = num_traj
		else: self.num_trajectories = 1
		self.data_pool_descr = ''
		self.treebook_memory = [0, [], []]
		self._module_memory_ = []

		self.simulation_plan = simulation_plan(parent = self)
		self.output_plan = lo.output_plan(
			label = 'Simulation', parent = self)
		self.fitting_plan = lfr.fit_routine_plan(parent = self)
		self.cartographer_plan = lgeo.cartographer_plan(
				label = 'Parameter Scan', parent = self)
		self.postprocess_plan = lpp.post_process_plan(
			label = 'Post Process Plan', parent = self, 
				_always_sourceable_ = ['simulation'])
		self.multiprocess_plan = lmp.multiprocess_plan(parent = self)

		self.run_params = lfu.dictionary(parent = self)
		self.run_params['end_criteria'] = \
			self.simulation_plan.end_criteria
		self.run_params['capture_criteria'] = \
			self.simulation_plan.capture_criteria
		self.run_params['plot_targets'] = \
			self.simulation_plan.plot_targets
		self.run_params['output_plans'] = {
			'Simulation' : self.output_plan}
		self.run_params['fit_routines'] = \
				self.fitting_plan.routines
		self.run_params['post_processes'] = \
			self.postprocess_plan.post_processes
		self.run_params['p_space_map'] = None
		self.run_params['multiprocessing'] = None

		self.__dict__.create_partition('template owners', 
			['output_plan', 'fitting_plan', 'cartographer_plan', 
			'postprocess_plan', 'multiprocess_plan', 'run_params', 
			'simulation_plan'])

		if 'label' not in kwargs.keys(): kwargs['label'] = 'ensemble'

		if 'module_options' in kwargs.keys():
			opts = kwargs['module_options']

		else:
			print 'no modules detected; requesting from manager'
			opts = self.parent.find_module_options()

		if len(opts) == 0:
			if lfu.using_gui():
				lgd.message_dialog(None, 
					'No module options detected!', 'Problem')
			else: print 'Problem! : No module options detected!'
			self.cancel_make = True
			return

		elif len(opts) == 1: module = opts[0]
		else:
			module_choice_container = lfu.data_container(data = opts[0])
			module_options_templates = [lgm.interface_template_gui(
					layout = 'horizontal', 
					widgets = ['radio'], 
					verbosities = [0], 
					labels = [opts], 
					initials = [[module_choice_container.data]], 
					instances = [[module_choice_container]], 
					keys = [['data']], 
					box_labels = ['Ensemble Module'], 
					minimum_sizes = [[(250, 50)]])]
			mod_dlg = lgd.create_dialog(title = 'Choose Ensemble Module', 
				templates = module_options_templates, variety = 'templated')
			module = mod_dlg()
			if module: module = module_choice_container.data
			else:
				self.cancel_make = True
				return

		self.impose_default('module', module, **kwargs)
		self._children_ = [self.simulation_plan, self.output_plan, 
						self.fitting_plan, self.cartographer_plan, 
					self.postprocess_plan, self.multiprocess_plan]
		self.load_module(reset_params = True)
		self.mcfg_dir = os.path.join(os.getcwd(), self.module)
		if not os.path.isdir(self.mcfg_dir): self.mcfg_dir = os.getcwd()
		lfu.modular_object_qt.__init__(self, *args, **kwargs)
		self.data_pool_id = lfu.get_new_pool_id()
		self.data_pool_pkl = os.path.join(os.getcwd(), 'data_pools', 
				'.'.join(['data_pool', self.data_pool_id, 'pkl']))

	def get_module_reference(self):
		module = mc.modules.__dict__[self.module]
		'''
		try: module = sys.modules['modular_core.modules.' + self.module]
		except KeyError:
			pdb.set_trace()
			self.parent.put_module_in_use(self.module)
			module = sys.modules['modular_core.modules.' + self.module]		
			#module = sys.modules['libs.modules.lib' + self.module]		
		'''
		return module

	def load_module(self, reset_params = False, parse_params = False):
		module = self.get_module_reference()
		if reset_params: module.set_parameters(self)
		if parse_params:
			lf.parse_lines(self.mcfg_path, module.parse_mcfg, 
						parser_args = (self.run_params, self))

	def run(self, *args, **kwargs):
		profiling = lset.get_setting('profile', 
				file_ = 'modular_settings.txt')
		if profiling:
			pr = cProfile.Profile()
			pr.enable()

		start_time = time.time()
		print 'start time: ', time.strftime('%Y-%m-%d %H:%M:%S', 
									time.localtime(start_time))

		save = False
		if self.skip_simulation:
			save = self.perform_post_processing(load = True)

		else:
			if self.fitting_plan.use_plan:
				if not self.cartographer_plan.parameter_space:
					print 'fitting requires a parameter space!'
					return False

				else: self.fitting_plan(self)

			else:
				
				if not self.cartographer_plan.parameter_space and\
								self.cartographer_plan.use_plan:
					print 'no parameter space; ignoring map request'
					self.cartographer_plan.use_plan = False

				if self.multiprocess_plan.use_plan and\
						self.cartographer_plan.use_plan:
					self.run_systems_multiproc_mapping()

				elif not self.multiprocess_plan.use_plan and\
							self.cartographer_plan.use_plan:
					self.run_systems_mapping()

				elif self.multiprocess_plan.use_plan and not\
							self.cartographer_plan.use_plan:
					self.run_systems_mutliproc()

				elif not self.multiprocess_plan.use_plan and not\
								self.cartographer_plan.use_plan:
					self.run_systems_boring()

			save = True
			print 'duration of simulations: ', time.time() - start_time
			self.perform_post_processing(load = False)

		if save: self.save_data_pool()
		print 'finished last simulation run: exiting'
		print 'duration: ', time.time() - start_time, ' seconds'
		if profiling:
			pr.disable()
			s = StringIO.StringIO()
			sortby = 'cumulative'
			ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
			ps.print_stats(0.1)
			print s.getvalue()

		return True

	def perform_post_processing(self, load = False):
		if self.postprocess_plan.use_plan:
			try:
				print 'performing post processing...'
				if load: self.data_pool = self.load_data_pool().data
				check = time.time()
				self.postprocess_plan(self)
				print 'duration of post procs: ', time.time() - check
				return True

			except:
				traceback.print_exc(file=sys.stdout)
				print 'failed to run post processes'
				return False

	def on_run(self, *args, **kwargs):
		global manager
		print 'running ensemble: ', self.label
		try:
			self.multithread_gui = lset.get_setting('multithread_gui')
			self.sanitize()
			self.__dict__.rid_widg_templates('template owners')
			self.set_data_scheme()
			self.parent = None
			if self.multithread_gui:
				manager.worker_threads.append(lwt.worker_thread(self, 
							self.run, len(manager.worker_threads)))

			else:
				self.run()
				self.produce_output()

			time.sleep(1)
			self.parent = manager

		except:
			traceback.print_exc(file=sys.stdout)
			lgd.message_dialog(None, 'Failed to run ensemble!', 'Problem')
			time.sleep(2)
			self.parent = manager

	def describe_data_pool(self, pool):
		proc_pool = pool.postproc_data
		try: sim_pool = pool.data.batch_pool
		except AttributeError: sim_pool = '<couldnt read batch object>'
		if not pool: self.data_pool_descr = 'Empty'
		else:
			try: sim_pool_count = len(sim_pool)
			except TypeError: sim_pool_count = 0
			try: proc_pool_count = len(proc_pool)
			except TypeError: proc_pool_count = 0
			self.data_pool_descr = ' '.join(['Data', 'Pool', 'Holds', 
					str(sim_pool_count), 'Simulation', 'Trajectories', 
								'and', str(proc_pool_count), 'Post', 
												'Process', 'Pools'])

	def save_data_pool(self):
		print 'saving data pool...'
		check = time.time()
		proc_data = None
		if self.postprocess_plan.use_plan:
			proc_data = [proc.data for proc in 
				self.postprocess_plan.post_processes]

		rout_data = None
		if self.fitting_plan.use_plan:
			rout_data = [rout.data for rout in 
					self.fitting_plan.routines]

		self.data_pool = lfu.data_container(data = self.data_pool, 
			postproc_data = proc_data, routine_data = rout_data)
		self.describe_data_pool(self.data_pool)
		if self.data_scheme == 'smart_batch':
			self.data_pool.data.live_pool = []
			self.data_pool_pkl = os.path.join(lfu.get_data_pool_path(), 
										'.'.join(['data_pool', 'smart', 
											self.data_pool_id, 'pkl']))

		elif self.data_scheme == 'batch':
			self.data_pool_pkl = os.path.join(lfu.get_data_pool_path(), 
					'.'.join(['data_pool', self.data_pool_id, 'pkl']))

		else:
			print 'data_scheme is unresolved... assuming "batch"'
			self.data_pool_pkl = os.path.join(lfu.get_data_pool_path(), 
					'.'.join(['data_pool', self.data_pool_id, 'pkl']))

		lf.save_pkl_object(self.data_pool, self.data_pool_pkl)
		print 'saved data pool: ', time.time() - check

	def load_data_pool(self):
		print 'loading data pool...'
		check_time = time.time()
		self.set_data_scheme()
		data_pool = lf.load_pkl_object(self.data_pool_pkl)
		self.describe_data_pool(data_pool)
		check2 = time.time()
		print 'loaded data pool: ', check2 - check_time
		return data_pool

	def produce_output(self):
		if not self.output_plan.use_plan:
			print 'skipping output...'
			return

		print 'producing output...'
		check_0 = time.time()
		#self.output_plan.flat_data = False
		pool = self.load_data_pool()
		if pool.data.override_targets:
			override_targets = pool.data.pool_names
		else: override_targets = None
		data_ = lfu.data_container(data = pool.data, 
				override_targets = override_targets)
		if self.output_plan.must_output(): self.output_plan(data_)
		if not pool.postproc_data is None:
			processes = self.postprocess_plan.post_processes
			for dex, proc in enumerate(processes):
				if proc.output.must_output():
					proc.provide_axes_manager_input()
					data_ = lfu.data_container(
						data = pool.postproc_data[dex])
					proc.determine_regime(self)
					proc.output(data_)

		if not pool.routine_data is None:
			routines = self.fitting_plan.routines
			for dex, rout in enumerate(routines):
				if rout.output.must_output():
					rout.provide_axes_manager_input()
					data_ = lfu.data_container(
						data = pool.routine_data[dex])
					rout.output(data_)

		print 'produced output: ', time.time() - check_0

	def set_data_scheme(self):
		smart = lset.get_setting('use_smart_pool')
		if smart and self.cartographer_plan.use_plan and\
						not self.fitting_plan.use_plan:
			data_pool = lgeo.batch_data_pool(
				self.run_params['plot_targets'], 
						self.cartographer_plan)
			self.data_scheme = 'smart_batch'
			self.output_plan.flat_data = False
			self.data_pool_pkl = os.path.join(os.getcwd(), 'data_pools', 
										'.'.join(['data_pool', 'smart', 
											self.data_pool_id, 'pkl']))

		else:
			data_pool = lgeo.batch_scalars(
				self.run_params['plot_targets'])
			self.data_scheme = 'batch'
			self.output_plan.flat_data = False
			self.data_pool_pkl = os.path.join(os.getcwd(), 'data_pools', 
					'.'.join(['data_pool', self.data_pool_id, 'pkl']))

		return data_pool

	#no multiprocessing, no parameter variation, and no fitting
	def run_systems_boring(self):
		self.data_pool = self.set_data_scheme()
		#self.data_pool = lgeo.batch_scalars(
		#	self.run_params['plot_targets'])
		current_trajectory = 1
		while current_trajectory <= self.num_trajectories:
			self.output_plan.update_filenames()
			self.data_pool.batch_pool.append(lis.run_system(
					self, identifier = current_trajectory))
			#lis.run_system(self)
			current_trajectory += 1

	#multiprocessing, no parameter variation, no fitting
	def run_systems_mutliproc(self):
		self.data_pool = self.set_data_scheme()
		#self.data_pool = lgeo.batch_scalars(
		#	self.run_params['plot_targets'])
		self.multiprocess_plan.distribute_work_simple_runs(
			update_func = self.output_plan.update_filenames, 
			run_func = lis.run_system, ensem_reference = self, 
							run_count = self.num_trajectories)

	#no multiprocessing, parameter variation, no fitting
	def run_systems_mapping(self):
		self.data_pool = self.set_data_scheme()
		run_func = lis.run_system
		move_func = self.cartographer_plan.move_to
		arc_length = len(self.cartographer_plan.trajectory)
		iteration = self.cartographer_plan.iteration
		while iteration < arc_length:
			move_func(iteration)
			self.data_pool._prep_pool_(iteration)
			for dex in range(self.cartographer_plan.trajectory[
								iteration][1].trajectory_count):
				self.output_plan.update_filenames()
				ID = int(str(iteration) + str(dex))
				self.data_pool.live_pool.append(
					run_func(self, identifier = ID))
				#run_func(self)
				print 'location dex:', iteration, 'run dex:', dex

			iteration += 1

		self.data_pool._rid_pool_(iteration - 1)
		self.cartographer_plan.iteration = 0

	#multiprocessing with parameter variation, no fitting
	def run_systems_multiproc_mapping(self):
		self.data_pool = self.set_data_scheme()
		#self.data_pool = lgeo.batch_data_pool(
		#	self.run_params['plot_targets'], 
		#			self.cartographer_plan)
		#self.data_pool = lgeo.batch_scalars(
		#	self.run_params['plot_targets'])
		self.multiprocess_plan.distribute_work(self, 
			target_processes =\
				[self.cartographer_plan.move_to, 
				self.output_plan.update_filenames, lis.run_system], 
				target_counts = [len(self.cartographer_plan.trajectory), 
					[traj[1].trajectory_count for traj in 
					self.cartographer_plan.trajectory], 1], 
							args = [('dex'), (), (self,)])

	def on_save(self):
		dirdlg = lgd.create_dialog('Choose File', 'File?', 'directory')
		save_dir = dirdlg()
		if save_dir != '':
			#this should probably be restructured as was done with
			# the binding associated with 'Alt+R'
			self.sanitize()
			self.parent = None
			self.__dict__.rid_widg_templates('template owners')
			lf.save_pkl_object(self, os.path.join(
				save_dir, self.label + '.ensempkl'))
			self.get_parent()
			print 'saved ensemble: ', self.label

	def get_parent(self):
		global manager
		self.parent = manager

	def on_reset(self):
		#this is currently affecting every ensemble...
		self.load_module(reset_params = True)

	def on_choose_mcfg(self, file_ = None):
		self.choose_mcfg_flag = False
		if not os.path.isfile(self.mcfg_path):
			fidlg = lgd.create_dialog('Choose File', 'File?', 'file', 
					'Modular config files (*.mcfg)', self.mcfg_dir)
			file_ = fidlg()

		if file_:
			self.mcfg_path = file_
			try: self.mcfg_text_box_ref[0].setText(self.mcfg_path)
			except TypeError:
				lgd.message_dialog(None, 'Refresh Required!', 'Problem')

			self.choose_mcfg_flag = True
			self.rewidget(True)

	def on_parse_mcfg(self, *args, **kwargs):
		try:
			self.load_module(reset_params = True, parse_params = True)
			self.rewidget(True)

		except IOError:
			if self.choose_mcfg_flag:
				traceback.print_exc(file = sys.stdout)
				lgd.message_dialog(None, 
					'Failed to parse file!', 'Problem')

	def on_write_mcfg(self, *args, **kwargs):
		try:
			if not self.mcfg_path:
				fidlg = lgd.create_dialog('Choose File', 'File?', 'file', 
					'Modular config files (*.mcfg)', self.mcfg_dir)
				file_ = fidlg()
				if not file_: return

			else: file_ = self.mcfg_path
			module = self.get_module_reference()
			lf.output_lines(module.write_mcfg(
				self.run_params, self), file_)

		except:
			traceback.print_exc(file = sys.stdout)
			lgd.message_dialog(None, 'Failed to write file!', 'Problem')

	def sanitize(self, *args, **kwargs):
		self._module_memory_ = []
		self._make_rxn_ = None
		self._make_spec_ = None
		self.data_pool = []
		lfu.modular_object_qt.sanitize(self)

	def rewidget__children_(self, *args, **kwargs):
		kwargs['infos'] = (kwargs['infos'][0], self)
		for child in self._children_:
			if child.rewidget(**kwargs):
				child.set_settables(*kwargs['infos'])

	def set_settables(self, *args, **kwargs):
		self.provide_axes_manager_input()
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		config_file_box_template = lgm.interface_template_gui(
				layout = 'grid', 
				widg_positions = [(0, 0), (1, 0), (1, 1), (2, 0)], 
				widg_spans = [(1, 2), None, None, None], 
				#minimum_sizes = [[(400, 35)], None, None], 
				widgets = ['text', 'button_set'], 
				tooltips = [['Current mcfg file', 
					'Parse the contents of the mcfg file', 
					'Generate an mcfg file based on the\
					\ncurrent run parameters']], 
				verbosities = [0, 0], 
				handles = [(self, 'mcfg_text_box_ref'), None], 
				keys = [['mcfg_path'], None], 
				instances = [[self], None], 
				initials = [[self.mcfg_path], None], 
				bindings = [[None], [lgb.create_reset_widgets_wrapper(
					window, [self.on_choose_mcfg, self.on_parse_mcfg]), 
						lgb.create_reset_widgets_wrapper(
							window, self.on_write_mcfg)]], 
				labels = [None, ['Parse mcfg File', 
							'Generate mcfg File']])
		if not self.parent: self.get_parent()
		top_half_template = lgm.interface_template_gui(
				layout = 'grid', 
				panel_scrollable = True, 
				widg_positions = [(0, 0), (0, 3), (0, 1), 
								(1, 2), (1, 0), (0, 2)], 
				layouts = ['vertical', 'vertical', 'vertical', 
							'vertical', 'vertical', 'vertical'], 
				#widg_spans = [None, (2, 1), (2, 1), None, None, None], 
				widg_spans = [None, None, (2, 1), None, None, None], 
				grid_spacing = 10, 
				box_labels = ['Ensemble Name', None, 'Run Options', 
					'Number of Trajectories', 'Data Pool Description', 
							'Configuration File'], 
				widgets = ['text', 'button_set', 
					'check_set', 'spin', 'text', 'panel'], 
				#verbosities = [0, [0, 0, 0, 0, 2], 0, 0, 2, 0], 
				verbosities = [0, [0, 0, 0, 5], 0, 0, 2, 0], 
				multiline = [False, None, None, None, True, None], 
				templates = [None, None, None, None, None, 
							[config_file_box_template]], 
				append_instead = [None, None, False, None, None, None], 
				read_only = [None, None, None, None, True, None], 
				#instances = [[self], [None], [self.output_plan, 
				instances = [[self], [None], [
					self.fitting_plan, self.cartographer_plan, 
					self.postprocess_plan, self.multiprocess_plan, 
							self, self], [self], [self], [None]], 
				#keys = [['label'], [None], ['use_plan', 'use_plan', 
				keys = [['label'], [None], ['use_plan', 
								'use_plan', 'use_plan', 'use_plan', 
							'skip_simulation'], 
					['num_trajectories'], ['data_pool_descr'], [None]], 
				labels = [[None], ['Run Ensemble', 'Save Ensemble', 
							#'Reset Ensemble', 'Update Ensemble', 
							'Update Ensemble', 'Print Label Pool'], 
							#['use output plan', 'use fitting plan', 
							['use fitting plan', 
					'map parameter space', 'use post processing', 
					'use multiprocessing', 'skip simulation', 
						], [None], [None], [None]], 
				initials = [[self.label], None, None, 
							[self.num_trajectories], 
						[self.data_pool_descr], None], 
				minimum_values = [None, None, None, 
								[1], None, None], 
				maximum_values = [None, None, None, 
								[1000000], None, None], 
				bindings = [[None], [self.parent.run_current_ensemble, 
					self.on_save, 
					#self.on_save, lgb.create_reset_widgets_wrapper(
					#						window, self.on_reset), 
					lgb.create_reset_widgets_function(window), 
										lfu.show_label_pool], 
									None, None, None, None])
		_modu_ = self.get_module_reference()
		main_panel_templates, sub_panel_templates, sub_panel_labels =\
						_modu_.generate_gui_templates_qt(window, self)
				#sys.modules['mc.modules.' + self.module\
				#			].generate_gui_templates_qt(window, self)
		run_param_keys = _modu_.run_param_keys
		tree_half_template = lgm.interface_template_gui(
				widgets = ['tree_book'], 
				verbosities = [1], 
				handles = [(self, 'tree_reference')], 
				initials = [[self.treebook_memory]], 
				instances = [[self]], 
				keys = [['treebook_memory']], 
				pages = [[(page_template, template_list, 
							param_key, sub_labels) for 
						page_template, template_list, 
							param_key, sub_labels in 
						zip(main_panel_templates, sub_panel_templates, 
								run_param_keys, sub_panel_labels)]], 
				headers = [['Ensemble Run Parameters']])
		#self.widg_templates.append(
		#	lgm.interface_template_gui(
		#		widgets = ['splitter'], 
		#		verbosities = [0], 
		#		orientations = [['vertical']], 
		#		templates = [[top_half_template, tree_half_template]]))
		#self.widg_templates.append(
		#	lgm.interface_template_gui(
		#		widgets = ['tab_book'], 
		#		verbosities = [0], 
		#		pages = [[('Main', [top_half_template]), 
		#				('Run Parameters', [tree_half_template])]]))
		#if not hasattr(self, 'current_tab_index'):
		#	print 'yea'
		#	self.current_tab_index = 0
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['tab_book'], 
				verbosities = [0], 
				handles = [(self, 'tab_ref')], 
				pages = [[('Main', [top_half_template]), 
						('Run Parameters', [tree_half_template])]], 
				initials = [[self.current_tab_index]], 
				instances = [[self]], 
				keys = [['current_tab_index']]))
		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)

class ensemble_manager(lfu.modular_object_qt):
	ensembles = []
	worker_threads = []
	_children_ = ensembles

	def __init__(self, label = 'ensemble manager', parent = None):
		global manager
		manager = self
		self.current_tab_index = 0
		self.settings_manager = lset.settings_manager(
			parent = self, filename = 'modular_settings.txt')
		self.settings = self.settings_manager.read_settings()
		lfu.modular_object_qt.__init__(self, 
			label = label, parent = parent)
		if lset.get_setting('auto_clear_data_pools'):
			self.clean_data_pools()

	def clean_data_pools(self):

		def pool_name(ensem):
			pa = os.path.join(os.getcwd(), ensem)
			en = lf.load_pkl_object(pa)
			return en.data_pool_pkl

		pool_matches = []
		ensem_matches = []
		for root, dirnames, filenames in os.walk('data_pools'):
			[pool_matches.append(os.path.join(root, finame)) for 
				finame in fnmatch.filter(filenames, 'data_pool.*.pkl')]

		for mod_dir in os.listdir(os.getcwd()):
			for root, dirnames, filenames in os.walk(mod_dir):
				[ensem_matches.append(os.path.join(root, finame)) for 
					finame in fnmatch.filter(filenames, '*.ensempkl')]

		saved_pools = [pool_name(en) for en in ensem_matches]
		del_pools = [item for item in pool_matches if 
			os.path.join(os.getcwd(), item) not in saved_pools]
		for pool in del_pools:
			try:
				if pool.count('smart') > 0:
					sm_pool = lf.load_pkl_object(pool)
					for sub_pool in sm_pool.data.data_pool_ids:
						os.remove(os.path.join(os.getcwd(), 
								'data_pools', sub_pool))

				os.remove(os.path.join(os.getcwd(), pool))
			except OSError, e:
				print ("Error: %s - %s." % (e.filename, e.strerror))

	def change_settings(self):
		self.settings_manager.display()

	def run_all_ensembles(self):
		[ensem.on_run() for ensem in self.ensembles]

	def run_current_ensemble(self):
		if self.current_tab_index > 0:
			current_ensem = self.ensembles[self.current_tab_index - 1]
			current_ensem.on_run()

	def abort_runs(self):
		[thread.abort() for thread in self.worker_threads]
		self.worker_threads = []

	def find_module_options(self):
		'''
		#a module will be available if there exist a python file
		# following the naming convention: 'lib' + module_name + '.py'
		#  found within the Modular/libs/modules directory
		#this file must at least contain one line which reads: 
		# 'module_name = ' + module_name
		#  Note: within the module file, this line should use the ' character
		#   in lieu of the " character... this is ridiculous and must be fixed
		def named_module(mod):
			mod_fi = os.path.join(modules_directory, mod)
			with open(mod_fi, 'r') as handle: lines = handle.readlines()
			namelines = [line[:line.find('\n')] for line in lines if 
									line.startswith('module_name')]
			if not namelines: return None
			else:
				name = namelines[0]
				left_ = name.find('\'') + 1
				right_ = name.rfind('\'')
				return name[left_:right_]

		modules_directory = os.path.join(os.getcwd(), 'libs', 'modules')
		modules = [name for name in os.listdir(modules_directory) if 
					name.startswith('lib') and name.endswith('.py')]
		modules = [named_module(mod) for mod 
			in modules if named_module(mod)]
		'''
		modules = mc.modules.mods
		return modules

	def add_ensemble(self):
		new = ensemble(parent = self, 
			module_options = self.find_module_options())
		if new.cancel_make: return
		else: self.ensembles.append(new)
		self.current_tab_index = len(self.ensembles)
		self.rewidget(True)
		return new

	def get_selected_ensemble(self):
		if not hasattr(self, 'ensem_selector'):
			print 'no selector'; return

		try:
			select = self.ensembles[
				self.ensem_selector[0].currentIndex()]
			return select

		except IndexError:
			print 'no ensemble selected to remove'; return

	def remove_ensemble(self):
		select = self.get_selected_ensemble()
		if select: self.ensembles.remove(select)
		self.rewidget(True)

	def put_module_in_use(self, module):
		#__import__('libs.modules.lib' + module)
		try: __import__('mc.modules.' + module)
		except ImportError: pdb.set_trace()

	def save_ensemble(self):
		select = self.get_selected_ensemble()
		if select: select.on_save()

	def load_ensemble(self):
		fidlg = lgd.create_dialog('Choose File', 'File?', 'file')
		file_ = fidlg()
		if file_ is not None:
			self.ensembles.append(lf.load_pkl_object(file_))
			self.put_module_in_use(self.ensembles[-1].module)
			self.ensembles[-1].rewidget(True)
			self.ensembles[-1].parent = self
			self.ensembles[-1].rewidget(True)
			_to_ = 'template owners'
			self.ensembles[-1].__dict__.restore_widg_templates(
					partition_key = _to_, settable_infos = (
								self.ensembles[-1], self))
			self.ensembles[-1].__dict__.clean_partition(_to_)
			self._restore_label_pool_()
			lfu.clean_label_pool()
			print 'loaded ensemble: ', self.ensembles[-1].label

	def expand_tree(self):
		if self.current_tab_index > 0:
			current_ensem = self.ensembles[self.current_tab_index - 1]
			if not current_ensem.tree_reference: self.refresh_()
			current_ensem.tree_reference[0].children()[0].expand_all()

	def collapse_tree(self):
		if self.current_tab_index > 0:
			current_ensem = self.ensembles[self.current_tab_index - 1]
			if not current_ensem.tree_reference: self.refresh_()
			current_ensem.tree_reference[0].children()[0].collapse_all()

	def cycle_current_tab(self):
		self.current_tab_index += 1
		if self.current_tab_index >= self.tab_ref[0].count():
			self.current_tab_index = 0
		self.tab_ref[0].setCurrentIndex(self.current_tab_index)

	def cycle_current_ensem_tab(self):
		current_ensem = self.ensembles[self.current_tab_index - 1]
		current_ensem.current_tab_index += 1
		if current_ensem.current_tab_index > 1:
			current_ensem.current_tab_index = 0
		if not current_ensem.tab_ref: current_ensem.rewidget(True)
		else:
			current_ensem.tab_ref[0].setCurrentIndex(
					current_ensem.current_tab_index)

	def choose_mcfg(self):
		if self.current_tab_index > 0:
			current_ensem = self.ensembles[self.current_tab_index - 1]
			current_ensem.on_choose_mcfg()

	def parse_mcfg(self):
		if self.current_tab_index > 0:
			current_ensem = self.ensembles[self.current_tab_index - 1]
			current_ensem.on_parse_mcfg()

	def write_mcfg(self):
		if self.current_tab_index > 0:
			current_ensem = self.ensembles[self.current_tab_index - 1]
			current_ensem.on_write_mcfg()

	def make_tab_book_pages(self, *args, **kwargs):
		window = args[0]
		#img_path = os.path.join(os.getcwd(), 'resources', 'gear.png')
		#img_path = os.path.join(mcrsrc.__path__[0], 'gear.png')
		img_path = lfu.get_resource_path('gear.png')
		main_templates = []
		main_templates.append(
			lgm.interface_template_gui(
				layout = 'grid', 
				widg_positions = [	(0, 1), (1, 0), (2, 0), 
									(1, 2), (2, 2), (3, 2), 
									(4, 2), (1, 1), (2, 1), 
													(5, 2)	], 
				#widg_spans = [None, (2, 1), (1, 2), None], 
				#grid_spacing = 10, 
				widgets = ['image', 'button_set', 'selector'], 
				verbosities = [1, 0, 0], 
				paths = [img_path, None, None], 
				handles = [None, None, (self, 'ensem_selector')], 
				labels = [None, ['Run All Ensembles', 'Abort Runs', 
					'Add Ensemble', 'Remove Ensemble', 'Save Ensemble', 
					'Load Ensemble', 'Update GUI', 'Clean Data Pools'], 
							[ensem.label for ensem in self.ensembles]], 
				bindings = [None, 
					[self.run_all_ensembles, self.abort_runs, 
					lgb.create_reset_widgets_wrapper(
						window, self.add_ensemble), 
					lgb.create_reset_widgets_wrapper(
						window, self.remove_ensemble), 
					lgb.create_reset_widgets_wrapper(
						window, self.save_ensemble), 
					lgb.create_reset_widgets_wrapper(
						window, self.load_ensemble), 
					lgb.create_reset_widgets_function(window), 
							self.clean_data_pools], [None]]))
		pages = [('Main', main_templates)]
		for ensem in self.ensembles:
			pages.append((ensem.label, ensem.widg_templates))

		return pages

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				#widgets = ['tab_book', 'console_listener'], 
				widgets = ['tab_book'], 
				pages = [self.make_tab_book_pages(
							*args, **kwargs), None], 
				initials = [[self.current_tab_index], None], 
				handles = [(self, 'tab_ref'), (self, 'console_ref')], 
				instances = [[self], None], 
				keys = [['current_tab_index'], None]))
		gear_icon_path = lfu.get_resource_path('gear.png')
		wrench_icon_path = lfu.get_resource_path('wrench_icon.png')
		save_icon_path = lfu.get_resource_path('save.png')
		#copy_icon_path = os.path.join(
		#	os.getcwd(), 'resources', 'copy.png')
		#paste_icon_path = os.path.join(
		#	os.getcwd(), 'resources', 'paste.png')
		#analyze_icon_path = os.path.join(
		#	os.getcwd(), 'resources', 'analyze.png')
		center_icon_path = lfu.get_resource_path('center.png')
		MakeEnsemble_path = lfu.get_resource_path('make_ensemble.png')
		RunEnsemble_path = lfu.get_resource_path('run.png')
		Refresh = lfu.get_resource_path('refresh.png')
		Next = lfu.get_resource_path('Next.png')
		Open = lfu.get_resource_path('open.png')
		Quit = lfu.get_resource_path('quit.png')
		Expand = lfu.get_resource_path('Expand.png')
		Collapse = lfu.get_resource_path('Collapse.png')
		find = lfu.get_resource_path('find.png')
		generate = lfu.get_resource_path('generate.png')
		attach_icon_path = lfu.get_resource_path('attach.png')
		gear_icon = lgb.create_icon(gear_icon_path)
		wrench_icon = lgb.create_icon(wrench_icon_path)
		save_icon = lgb.create_icon(save_icon_path)
		#copy_icon = lgb.create_icon(copy_icon_path)
		#paste_icon = lgb.create_icon(paste_icon_path)
		#analyze_icon = lgb.create_icon(analyze_icon_path)
		center_icon = lgb.create_icon(center_icon_path)
		MakeEnsemble = lgb.create_icon(MakeEnsemble_path)
		RunEnsemble = lgb.create_icon(RunEnsemble_path)
		Refresh = lgb.create_icon(Refresh)
		Next = lgb.create_icon(Next)
		Expand = lgb.create_icon(Expand)
		Collapse = lgb.create_icon(Collapse)
		find = lgb.create_icon(find)
		generate = lgb.create_icon(generate)
		attach_icon = lgb.create_icon(attach_icon_path)
		settings_ = lgb.create_action(parent = window, label = 'Settings', 
						bindings = lgb.create_reset_widgets_wrapper(
						window, self.change_settings), icon = wrench_icon, 
					shortcut = 'Ctrl+Shift+S', statustip = 'Settings')
		save_ = lgb.create_action(parent = window, label = 'Save',
						bindings = lgb.create_reset_widgets_wrapper(
						window, self.save_ensemble), icon = save_icon,
					shortcut =  'Ctrl+S', statustip = 'Save')
		#copy_ = lgb.create_action(parent = window, label = 'Copy',
		#				bindings = lgb.create_reset_widgets_wrapper(
		#				window, self.copy), icon = copy_icon,
		#			shortcut =  'Ctrl+C', statustip = 'Copy')
		#paste_ = lgb.create_action(parent = window, label = 'Paste',
		#				bindings = lgb.create_reset_widgets_wrapper(
		#				window, self.paste), icon = paste_icon,
		#			shortcut =  'Ctrl+V', statustip = 'Paste')
		#analyze_ = lgb.create_action(parent = window, label = 'Analyze',
		#				bindings = lgb.create_reset_widgets_wrapper(
		#				window, self.analyze), icon = analyze_icon,
		#			shortcut =  'Ctrl+A', statustip = 'Analyze')
		open_file = lgb.create_action(parent = window, label = 'Open', 
						bindings = lgb.create_reset_widgets_wrapper(
						window, self.load_ensemble), icon = Open, 
					shortcut = 'Ctrl+O', statustip = 'Open New File')
		quit_ = lgb.create_action(parent = window, label = 'Quit', 
							icon = Quit, shortcut = 'Ctrl+Q', 
							statustip = 'Quit the Application', 
									bindings = window.on_close)
		center_ = lgb.create_action(parent = window, label = 'Center', 
							icon = center_icon, shortcut = 'Ctrl+C', 
									statustip = 'Center Window', 
									bindings = [window.on_resize, 
												window.on_center])
		make_ensem_ = lgb.create_action(parent = window, 
			label = 'Make Ensemble', icon = MakeEnsemble, 
			shortcut = 'Ctrl+E', statustip = 'Make New Ensemble', 
					bindings = lgb.create_reset_widgets_wrapper(
									window, self.add_ensemble))
		expand_ = lgb.create_action(parent = window, 
			label = 'Expand Parameter Tree', icon = Expand, 
			shortcut = 'Ctrl+T', bindings = self.expand_tree, 
			statustip = 'Expand Run Parameter Tree (Ctrl+T)')
		collapse_ = lgb.create_action(parent = window, 
			label = 'Collapse Parameter Tree', icon = Collapse, 
			shortcut = 'Ctrl+W', bindings = self.collapse_tree, 
			statustip = 'Collapse Run Parameter Tree (Ctrl+W)')
		find_mcfg_ = lgb.create_action(parent = window, 
			label = 'Find mcfg', icon = find, shortcut = 'Ctrl+M', 
			bindings = lgb.create_reset_widgets_wrapper(
				window, [self.choose_mcfg, self.parse_mcfg]), 
			statustip = 'Select *.mcfg file to parse (Ctrl+M)')
		make_mcfg_ = lgb.create_action(parent = window, 
			label = 'Generate mcfg', icon = generate, shortcut = 'Alt+M', 
			bindings = lgb.create_reset_widgets_wrapper(
								window, self.write_mcfg), 
			statustip = 'Generate *.mcfg file from ensemble (Alt+M)')
		self.refresh_ = lgb.create_reset_widgets_function(window)
		update_gui_ = lgb.create_action(parent = window, 
			label = 'Refresh GUI', icon = Refresh, shortcut = 'Ctrl+G', 
			#bindings = lgb.create_reset_widgets_function(window), 
			bindings = self.refresh_, 
			statustip = 'Refresh the GUI (Ctrl+G)')
		cycle_tabs_ = lgb.create_action(parent = window, 
			label = 'Next Tab', icon = Next, shortcut = 'Ctrl+Tab', 
			bindings = self.cycle_current_tab, 
			statustip = 'Display The Next Tab (Ctrl+Tab)')
		cycle_ensem_tabs_ = lgb.create_action(parent = window, 
			label = 'Next Tab', icon = Next, shortcut ='E+Tab', 
			bindings = self.cycle_current_ensem_tab, 
			statustip = 'Display The Ensemble\'s Next Tab (E+Tab)')
		run_current_ = lgb.create_action(parent = window, 
			label = 'Run Current Ensemble', icon = RunEnsemble, 
			shortcut = 'Alt+R', bindings = self.run_current_ensemble, 
			statustip = 'Run The Current Ensemble (Alt+R)')

		self.menu_templates.append(
			lgm.interface_template_gui(
				menu_labels = ['&File', '&File', '&File',
					'&File', '&File', '&File', '&File', '&File',
					'&File', '&File', '&File', '&File'], 
				menu_actions = [settings_, center_, make_ensem_, 
					run_current_, update_gui_, cycle_tabs_, expand_,
					collapse_, find_mcfg_, make_mcfg_, open_file, quit_]))
		self.tool_templates.append(
			lgm.interface_template_gui(
				tool_labels = ['&Tools', '&Tools', '&Tools', 
						'&Tools', '&Tools', '&Tools', 
						'&Tools', '&Tools', '&Tools', 
						'&EnsemTools', '&EnsemTools', '&EnsemTools', 
						'&EnsemTools', '&EnsemTools'], 
				tool_actions = [settings_, save_, open_file, 
						center_, make_ensem_, run_current_, 
						update_gui_, cycle_tabs_, quit_, 
						expand_, collapse_, cycle_ensem_tabs_, 
						find_mcfg_, make_mcfg_]))
		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)

class simulation_plan(lfu.plan):

	_always_targetable_ = ['iteration', 'time']

	def __init__(self, label = 'simulation plan', parent = None):
		self.end_criteria = []
		self.selected_end_crit = None
		self.selected_end_crit_label = None
		self.capture_criteria = []
		self.selected_capt_crit = None
		self.selected_capt_crit_label = None
		self.plot_targets = []
		lfu.plan.__init__(self, label = label, parent = parent)
		#self._children_.extend(self.end_criteria)
		#self._children_.extend(self.capture_criteria)
		self._children_ = []

	def enact_plan(self, *args, **kwargs):
		print 'simulation plan does not enact...'

	def sanitize(self, *args, **kwargs):
		self.widg_templates_end_criteria = []
		self.widg_templates_capture_criteria = []
		self.widg_templates_plot_targets = []
		lfu.plan.sanitize(self)

	def reset_criteria_lists(self):
		del self.end_criteria[:]
		del self.capture_criteria[:]
		del self._children_[:]
		self.rewidget(True)

	def add_end_criteria(self, crit = None):
		if crit is None: new = lc.criterion_sim_time(parent = self)
		else:
			new = crit
			new.parent = self

		self.end_criteria.append(new)
		self._children_.append(new)
		self.rewidget(True)

	def add_capture_criteria(self, crit = None):
		if crit is None:
			new = lc.criterion_scalar_increment(parent = self)

		else:
			new = crit
			new.parent = self

		self.capture_criteria.append(new)
		self._children_.append(new)
		self.rewidget(True)

	def clear_criteria(self):
		def clear(crits):
			for crit in crits: crits.remove(crit)

		clear(self.end_criteria)
		clear(self.capture_criteria)
		self._children_ = []
		self.rewidget(True)

	def remove_end_criteria(self, crit = None):
		if crit: select = crit
		else: select = self.get_selected_criteria('end')
		if select:
			self.end_criteria.remove(select)
			self._children_.remove(select)
			select._destroy_()

		self.rewidget(True)

	def remove_capture_criteria(self, crit = None):
		if crit: select = crit
		else: select = self.get_selected_criteria('capture')
		if select:
			self.capture_criteria.remove(select)
			self._children_.remove(select)
			select._destroy_()

		self.rewidget(True)

	def get_selected_criteria(self, type_):
		if type_ is 'end': key = 'end_crit_selector'
		elif type_ is 'capture': key = 'capt_crit_selector'
		else: key = 'nonsense'
		if not hasattr(self, key):
			print 'no selector'; return

		try:
			select = self.__dict__[type_ + '_criteria'][
				self.__dict__[key][0].children()[1].currentIndex() - 1]
			return select

		except IndexError:
			print 'no criterion selected'; return

	def set_selected_criteria(self, dex):
		select = self.capture_criteria[dex]
		self.selected_capt_crit = select
		self.rewidget(True)

	def verify_plot_targets(self, targs):
		targets = self.parent.run_params['plot_targets']
		targets = [targ for targ in targets if targ in targs]
		self.parent.run_params['plot_targets'] = targets
		self.parent.run_params.partition['system'][
						'plot_targets'] = targets
		self.parent.run_params['output_plans'][
					'Simulation'].rewidget(True)

	def set_settables(self, *args, **kwargs):
		window = args[0]
		ensem = args[1]
		self.handle_widget_inheritance(*args, **kwargs)
		const_targs = self._always_targetable_
		targs = ensem.run_params['plot_targets']
		self.plot_targets = ensem.run_params['plot_targets']
		#all_targets = list(set(targs) | set(const_targs))
		all_targets = lfu.uniqfy(const_targs + targs)
		plot_target_labels = all_targets
		self.verify_plot_targets(plot_target_labels)
		try: self.selected_end_crit_label = self.selected_end_crit.label
		except AttributeError: self.selected_end_crit_label = None
		try: self.selected_capt_crit_label = self.selected_capt_crit.label
		except AttributeError: self.selected_capt_crit_label = None
		self.widg_templates_end_criteria.append(
			lgm.interface_template_gui(
				layout = 'grid', 
				widg_positions = [(0, 0), (0, 2), (1, 2)], 
				widg_spans = [(3, 2), None, None], 
				grid_spacing = 10, 
				widgets = ['mobj_catalog', 'button_set'], 
				verbosities = [1, 1], 
				instances = [[self.end_criteria, self], None], 
				keys = [[None, 'selected_end_crit_label'], None], 
				handles = [(self, 'end_crit_selector'), None], 
				labels = [None, ['Add End Criterion', 
							'Remove End Criterion']], 
				initials = [[self.selected_end_crit_label], None], 
				bindings = [None, [lgb.create_reset_widgets_wrapper(
									window, self.add_end_criteria), 
					lgb.create_reset_widgets_wrapper(window, 
						self.remove_end_criteria)]]))
		self.widg_templates_capture_criteria.append(
			lgm.interface_template_gui(
				layout = 'grid', 
				widg_positions = [(0, 0), (0, 2), (1, 2)], 
				widg_spans = [(3, 2), None, None], 
				grid_spacing = 10, 
				widgets = ['mobj_catalog', 'button_set'], 
				verbosities = [1, 1], 
				instances = [[self.capture_criteria, self], None], 
				keys = [[None, 'selected_capt_crit_label'], None], 
				handles = [(self, 'capt_crit_selector'), None], 
				labels = [None, ['Add Capture Criterion', 
							'Remove Capture Criterion']], 
				initials = [[self.selected_capt_crit_label], None], 
				bindings = [None, [lgb.create_reset_widgets_wrapper(
								window, self.add_capture_criteria), 
					lgb.create_reset_widgets_wrapper(window, 
						self.remove_capture_criteria)]]))
		targets_template =\
			[lgm.interface_template_gui(
				widgets = ['check_set'], 
				verbosities = [1], 
				append_instead = [True], 
				provide_master = [True], 
				instances = [[self.parent.run_params]], 
				keys = [['plot_targets']], 
				labels = [plot_target_labels])]
				#labels = [self.plot_targets])]
		self.widg_templates_plot_targets.append(
			lgm.interface_template_gui(
				widgets = ['panel'], 
				box_labels = ['Capture Targets'], 
				scrollable = [True], 
				templates = [targets_template]))
		lfu.plan.set_settables(self, *args, from_sub = True)

class sim_system_python(lfu.modular_object_qt):

	identifier = 0

	#def __init__(self, ensem, label = 'another system', params = {}):
	def __init__(self, ensem, params = {}):
		self.ensemble = ensem
		#self.parameters = copy(params)
		self.parameters = params
		try: self.end_criteria = self.parameters['end_criteria']
		except KeyError: self.end_criteria = [lc.criterion_iteration()]
		try: self.capture_criteria = self.parameters['capture_criteria']
		except KeyError: self.capture_criteria = []
		try:
			self.end_bool_expression =\
				self.parameters['bool_expressions']['end']
			self.capt_bool_expression =\
				self.parameters['bool_expressions']['capt']

		except KeyError: 
			self.end_bool_expression = ''
			self.end_capture_expression = ''

		try:
			data = lgeo.scalars_from_labels(
				self.parameters['plot_targets'])

		except KeyError: print 'simulating with no resultant data!'
		self.bAbort = False
		self.time = []
		self.iteration = 0
		if not self.end_criteria:
			self.end_criteria = [lc.criterion_iteration()]

		self.determine_end_valid_data = (None, (None))
		#lfu.modular_object_qt.__init__(self, label = label, data = data)
		lfu.modular_object_qt.__init__(self, data = data)

	#dummy function to be overridden in superclass
	def initialize(self):
		pass

	def handle_mobj_initializations(self):
		for crit in self.end_criteria + self.capture_criteria:
			try:
				crit.initialize()

			except AttributeError:
				pass

	#dummy function to be overridden in superclass
	def iterate(self):
		pass

	#dummy function to be overridden in superclass
	def decommission(self):
		pass

	#dummy function to be overridden in superclass
	def capture_plot_data(self):
		pass

	def toss_bad_daters(self):
		validation = self.determine_end_valid_data
		if not hasattr('__call__', validation[0]):
			print 'no dater toss method specified'
			return

		baddex = validation[0](validation[1])
		for data_obj in self.data:
			try:
				del data_obj.scalars[baddex:]

			except MemoryError:
				pdb.set_trace()
			#data_obj.scalars = data_obj.scalars[:baddex]

	def verify_capture_criteria(self):
		if not self.capture_criteria:
			return True

		else:
			return self.verify_criteria_list_boolean(
						self.capture_criteria, (self), 
				bool_expression = self.capt_bool_expression)

	def verify_end_criteria(self):
		return self.verify_criteria_list_boolean(
						self.end_criteria, (self), 
			bool_expression = self.end_bool_expression)

class sim_system_external(sim_system_python):
	bAbort = False
	timeout = False
	capture_criteria = False

	def __init__(self, ensem = None, params = {}):
		self.ensemble = ensem
		self.params = params

	def read_criteria(self, crits, start_string):
		for crit in crits:
			if issubclass(crit.__class__, lc.criterion_iteration):
				value = crit.max_iterations
				start_string += 'iteration>=' + str(value)

			elif issubclass(crit.__class__, lc.criterion_sim_time):
				value = crit.max_time
				start_string += 'time>=' + str(value)

			elif issubclass(crit.__class__, 
					lc.criterion_scalar_increment):
				target = crit.key
				value = str(crit.increment)
				start_string += ':'.join(['increment', target, value])

		return start_string

	def initialize(self, *args, **kwargs):
		self.iteration = 0
		self.encode()

	def toss_bad_daters(self, *args, **kwargs):
		pass

	def finalize_data(self, data, targets, toss = None):
		if data is False:
			self.bAbort = True
			return data

		data = [dater for dater in data if len(dater) > 1]
		reorder = []
		for name in self.params['plot_targets']:
			dex = targets.index(name)
			reorder.append(np.array(data[dex][:toss], dtype = np.float))

		return np.array(reorder, dtype = np.float)

	def verify_end_criteria(self):
		return self.iteration == 1

	def encode(self):
		self.system_string = 'base class system string'
		print 'base class encode'

	def iterate(self):
		print 'base class iterate'

if __name__ == 'modular_core.libsimcomponents':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'




