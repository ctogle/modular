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
		lfu.plan.__init__(self, parent = parent, 
			label = label, use_plan = use_plan)

	def to_string(self):
		lines = [' : '.join(['\tworkers', str(self.worker_count)])]
		return lines

	#args should start with 2 lists of equal length
	def gpu_1to1_operation(self, *args, **kwargs):
		return self.gpu_worker.execute(*args, **kwargs)

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
			#data_pool = []
			#data_pool = ensem_reference.data_pool.batch_pool
			dex0 = 0
			while dex0 < target_counts[0]:
				move_to(dex0)
				dex1 = 0
				data_pool = []
				while dex1 < target_counts[1][dex0]:
					#update_filenames()
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

				#ensem_reference.data_pool.live_pool =\
				#	np.array(data_pool, dtype = np.float)
				ensem_reference.data_pool.live_pool = data_pool
				ensem_reference.data_pool._rid_pool_(dex0)
				dex0 += 1

			pool.close()
			pool.join()
			try:
				ensem_reference.data_pool.batch_pool =\
					np.array(data_pool, dtype = np.float)

			except ValueError: pdb.set_trace()
			self.worker_report = worker_report

		mapping_multi()

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

def run_with_time_out(run_func, args, pool, 
			time_out = 10, worker = None):
	#this function should not work if callback does not extend properly
	begin = len(pool)
	new = False
	if not worker:
		worker_pool = mp.Pool(processes = 1)
		new = True

	else: worker_pool = worker
	result = worker_pool.map_async(run_func, 
				args, callback = pool.extend)
	worker_pool.close()
	start_time = time.time()
	time.sleep(0.1)
	timed_out = time.time() - start_time > time_out
	finished = len(pool) > begin
	while not timed_out and not finished:
		time.sleep(0.5)
		timed_out = time.time() - start_time > time_out
		finished = len(pool) > begin
		#print 'waiting...', finished, timed_out

	if timed_out:
		worker_pool.terminate()
		if new: worker_pool.join()
		#print 'timed out...'
		return True

	else:
		if new: worker_pool.join()
		#worker_pool.join()
		return False

