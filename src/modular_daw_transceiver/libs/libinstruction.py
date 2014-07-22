import libs.modular_core.libfundamental as lfu
import libs.modular_core.libworkerthreads as lwt

import time
from threading import Timer
from threading import Thread

class timer_event(lfu.modular_object_qt):
	label = 'timer event'
	active = True

	def __init__(self, function, delay, func_args = ()):
		lfu.modular_object_qt.__init__(self)
		self.function = function
		self.delay = delay
		self.func_args = func_args
		self.thread = Thread(target = self.be_active, args = ())
		self.thread.daemon = True
		self.thread.start()

	def be_active(self):
		while self.active:
			time.sleep(self.delay)
			Timer(self.delay, self.function, 
					self.func_args).start()

class instruction_manager(lfu.modular_object_qt):
	label = 'instruction manager'
	queued = []
	to_remove = []
	performed = []

	def __init__(self, delay = 1.0):
		lfu.modular_object_qt.__init__(self)
		self.delay = delay

	def begin_checking(self):
		self.timer = timer_event(self.check_instructions, self.delay)

	def stop_checking(self):
		self.timer.active = False

	def check_instructions(self):
		check_time = time.time()
		for instruction, dex in zip(self.queued, range(len(self.queued))):
			if not dex in self.to_remove:
				if instruction.call_time + instruction.tolerance <\
													check_time:
					#print 'time for instruction has expired!'
					pass

				elif instruction.call_time - instruction.tolerance >\
													check_time:
					#print 'not time for instruction yet!'
					pass

				else:
					if instruction():
						self.performed.append(instruction)
						self.to_remove.append(dex)

class instruction(lfu.modular_object_qt):

	def __init__(self, call_time, call = (None, ()), 
			tolerance = 1.0, label = 'an instruction'):
		lfu.modular_object_qt.__init__(self)
		self.call_time = call_time
		self.call = call
		self.tolerance = tolerance

	def __call__(self):
		try:
			self.call[0](self.call[1])
			return True

		except:
			print 'instruction failed!'
			return False

if __name__ == 'libs.daw_transceiver.libs.libinstruction':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgb = lfu.gui_pack.lgb
	lgd = lfu.gui_pack.lgd

if __name__ == '__main__': print 'this is a library!'




