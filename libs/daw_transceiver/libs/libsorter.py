import libs.modular_core.libfundamental as lfu
import libs.daw_transceiver.libs.libinstruction as lir

import subprocess
import thread
import types
import time
import sys
import os

import pdb

#this class only handles script based sorting
class sorter_script(lfu.modular_object_qt):
	label = 'script sorter'
	check_file_time_delay = 1
	instruction_manager = lir.instruction_manager(delay = 0.5)
	image_directory = os.path.join(
		os.getcwd(), 'resources')
	script = os.path.join(os.getcwd(), 
		'get_total_project_lines.py')

	def __call__(self, *args, **kwargs):
		subp = subprocess.Popen([sys.executable, self.script], 
									stdout=subprocess.PIPE)
		value, err  = subp.communicate()
		print 'script', self.script
		print 'returned', value
		#example: 'DECISION: ||', total, '||'
		return value.split('||')[1]

	def check_new_files(self):
		return [fi for fi in os.listdir(self.image_directory) 
						if not fi in self.processed_files]

	def sort(self, *args, **kwargs):
		while not self.aborted:
			time.sleep(self.check_file_time_delay)
			new_files = self.check_new_files()
			if new_files:
				new_result = self(new_files)
				self.sort_results.append(new_result)
				self.processed_files.extend(new_files)

	def on_begin_sorting(self, *args, **kwargs):
		self.aborted = False
		self.processed_files = []
		self.sort_results = []
		try: message_function = self.parent.on_speak_message
		except AttributeError: message_function = self.default_speak
		start_time = time.time()
		thread.start_new_thread(self.sort, (start_time, ))
		thread.start_new_thread(self.handle_sort_results, 
						(start_time, message_function))

	def handle_sort_results(self, *args, **kwargs):
		start_time = args[0]
		speak_func = args[1]
		handled = []
		self.instruction_manager.begin_checking()
		while not self.aborted:
			if len(self.sort_results) > len(handled):
				result = self.sort_results[-1]
				self.handle_result(result, speak_func)
				handled.append(result)

	def handle_result(self, result, speak):

		def issue(message, delay):
			instr_num = len(self.instruction_manager.queued)
			instruction_label = 'instruction-' + str(instr_num)
			instruction_time = time.time() + delay
			self.instruction_manager.queued.append(
				lir.instruction(instruction_time, 
					call = (speak, str(message)), 
					label = instruction_label))

		def parse(entry):

			def fail(entry):
				print 'could not parse result', entry

			def check_lrz(ent):
				if ent in ['left', 'right', 'zero']:
					return True

			try: return int(entry), 0.0
			except ValueError:
				check = check_lrz(entry)
				if check: return entry, 0.0
				try:
					pair = eval(entry)
					if type(pair) is types.TupleType:
						try: delay = float(pair[1])
						except: fail(entry)
						try: return int(pair[0]), delay
						except ValueError:
							check = check_lrz(pair[0])
							if check: return pair[0], delay
							else: fail(entry)

					else: fail(entry)

				except: fail(entry)

		#message should be left, right, zero, or an integer
		print 'result handling', result
		split = result.split(':')
		parsed = [parse(entry) for entry in split]
		[issue(message, delay) for message, delay in parsed]

	def default_speak(self, message):
		print message

	def on_abort(self): 
		self.aborted = True

	def on_output_sort_results(self):
		try: print self.sort_results
		except AttributeError: print 'gotta sort to get results!'

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['button_set'], 
				labels = [['Begin Script Sorting', 'Abort Sorting', 
						'Print Sort Results']], 
				bindings = [[self.on_begin_sorting, self.on_abort, 
						self.on_output_sort_results]]))
		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)

if __name__ == 'libs.daw_transceiver.libs.libsorter':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgb = lfu.gui_pack.lgb
	lgd = lfu.gui_pack.lgd

if __name__ == '__main__': print 'this is a library!'





