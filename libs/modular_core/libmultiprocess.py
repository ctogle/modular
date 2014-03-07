import libs.modular_core.libfundamental as lfu
import libs.modular_core.libsettings as lset
import libs.gpu.lib_gpu as lgpu

import multiprocessing as mp
import numpy as np
import types
import time

import pdb

if __name__ == 'libs.modular_core.libmultiprocess':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm

if __name__ == '__main__':
	print 'this is a library!'

class multiprocess_plan(lfu.plan):

	def __init__(self, parent = None, label = 'multiprocess plan'):
		self.worker_count = lset.get_setting('worker_processes')
		self.worker_report = []
		self.gpu_worker = lgpu.CL()
		use_plan = lset.get_setting('multiprocessing')
		lfu.plan.__init__(self, parent = parent, label = label, 
										use_plan = use_plan)

	def to_string(self):
		lines = []
		#ENCODE SOMETHING LIKE THE FOLLOWING
		#<product_space> 100
		#	driveamp : value : 50-150;10
		#	driveperiod : value : 20-40;5
		pdb.set_trace()
		return lines

	def make_call_sequence(calls, args):

		def call_sequence():
			for call, arg in zip(calls, args):
				if not arg is None: call(arg)
				else: call()

		return call_sequence

	#args should start with 2 lists of equal length
	def gpu_1to1_operation(self, *args, **kwargs):
		return self.gpu_worker.execute(*args, **kwargs)

	def distribute_work_one_layer(self, method, data_pool, p_space):
		try: processor_count = int(self.worker_count)
		except: 
			print 'defaulting to 4 workers...'
			processor_count = 4

		pool = mp.Pool(processes = processor_count)
		print 'method', method, type(method)
		worker_report = []
		arc_leng = len(p_space.trajectory)
		dex0 = 0
		result_pool = []
		while dex0 < arc_leng:
			runs_left = arc_leng - dex0
			if runs_left >= processor_count: 
				runs_this_round = processor_count

			else: runs_this_round = runs_left % processor_count
			traj_counts = [locale[1].trajectory_count for locale 
					in p_space.trajectory[dex0:runs_this_round]]
			pool_dexes = [dex0]
			for count in traj_counts:
				pool_dexes.append(pool_dexes[-1] + count)

			dex0 += runs_this_round
			print 'pool_dexes', pool_dexes
			result = pool.map_async(method, 
				[data_pool[pool_dexes[dex]:pool_dexes[dex + 1]] 
						for dex in range(len(pool_dexes) - 1)], 
				callback = result_pool.extend)
			result.wait()
			report = ' '.join(['location dex:', str(dex0), 
						'runs this round:', str(runs_this_round), 'in:', 
						str(time.time() - check_time), 'seconds'])
			worker_report.append(report)

		pool.close()
		pool.join()
		self.worker_report = worker_report
		return result_pool

	def distribute_work(self, ensem_reference, target_processes = [], 
									target_counts = [], args = []):
		#each int in target counts specifies a loop to make the nest
		#the last loop always wraps the last process in a separate process
		#the number of layers in the nest is variable!
		def mapping_multi():
			try: processor_count = int(self.worker_count)
			except: 
				print 'defaulting to 4 workers...'
				processor_count = 4

			pool = mp.Pool(processes = processor_count)
			move_to = target_processes[0]
			update_filenames = target_processes[1]
			run_system = target_processes[2]			
			worker_report = []
			data_pool = []
			#data_pool = ensem_reference.data_pool.batch_pool
			dex0 = 0
			while dex0 < target_counts[0]:
				move_to(dex0)
				#del pool
				#pool = mp.Pool(processes = processor_count)
				dex1 = 0
				while dex1 < target_counts[1][dex0]:
					update_filenames()	#this wont work properly this way - 
					#only messes up filenames for individual trajectories
					runs_left = target_counts[1][dex0] - dex1
					if runs_left >= processor_count: 
						runs_this_round = processor_count

					else: runs_this_round = runs_left % processor_count
					check_time = time.time()
					try:
						result = pool.map_async(run_system, 
							args[2]*runs_this_round, callback = \
												data_pool.extend)

					except MemoryError: print 'AMNESIA!'; pdb.set_trace()
					result.wait()
					dex1 += runs_this_round
					report = ' '.join(['location dex:', str(dex0), 
						'runs this round:', str(runs_this_round), 'in:', 
						str(time.time() - check_time), 'seconds'])
					worker_report.append(report)
					print 'multicore reported...', ' location: ', dex0

				dex0 += 1
				#pool.close()
				#pool.join()

			pool.close()
			pool.join()
			print 'dp len', len(data_pool), type(data_pool)
			try:
				ensem_reference.data_pool.batch_pool =\
					np.array(data_pool, dtype = np.float)

			except ValueError: pdb.set_trace()
			self.worker_report = worker_report

		def two_layer_nest():			
			for dex1 in range(target_counts[0]):
				target_processes[0](args[0])
				for dex2 in range(target_counts[1]):
					proc = mp.Process(target = target_processes[1], 
									args = (args[1][0], mp.Queue()))
									#args = (args[1], self.queue))
					proc.start(); proc.join()
					print 'started a process!'

		#self.queue = mp.Queue()
		if len(target_processes) == 2: two_layer_nest()
		elif len(target_processes) == 3: mapping_multi()

	def distribute_work_simple_runs(self, update_func = None, 
			run_func = None, ensem_reference = None, run_count = 1):
		try: processor_count = int(self.worker_count)
		except: 
			print 'defaulting to 8 workers...'
			processor_count = 8

		pool = mp.Pool(processes = processor_count)
		worker_report = []
		result_pool = []
		#result_pool = ensem_reference.data_pool.batch_pool
		dex0 = 0
		while dex0 < run_count:
			check_time = time.time()
			runs_left = run_count - dex0
			if runs_left >= processor_count: 
				runs_this_round = processor_count

			else: runs_this_round = runs_left % processor_count
			dex0 += runs_this_round
			update_func()
			result = pool.map_async(run_func, 
					[ensem_reference]*runs_this_round, 
					callback = result_pool.extend)
			result.wait()
			report = ' '.join(['location dex:', str(dex0), 
						'runs this round:', str(runs_this_round), 'in:', 
						str(time.time() - check_time), 'seconds'])
			worker_report.append(report)
			print 'multicore reported...', ' location: ', dex0

		pool.close()
		pool.join()
		self.worker_report = worker_report
		ensem_reference.data_pool.batch_pool =\
			np.array(result_pool, dtype = np.float)

	def set_settables(self, *args, **kwargs):
		self.handle_widget_inheritance(*args, from_sub = False)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['spin'], 
				initials = [[self.worker_count]], 
				minimum_values = [[2]], 
				maximum_values = [[32]], 
				single_steps = [[2]], 
				instances = [[self]], 
				rewidget = [[True]], 
				keys = [['worker_count']], 
				box_labels = ['Number of worker processes']))
		super(multiprocess_plan, self).set_settables(
							*args, from_sub = True)



