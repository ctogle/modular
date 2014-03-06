from threading import Thread
import multiprocessing

import sys
import os
import pickle

import pdb

from PySide import QtCore

class worker_finished(QtCore.QObject):
    worker_fin = QtCore.Signal()

#needs to fire an event to the ensemble_manager to perform output for 
# all simulations as well as post processes
class worker_thread(Thread):

	def __init__(self, ensem, target, index):
		Thread.__init__(self)
		self.ensem = ensem
		self.target_func = target
		self.index = index
		self.aborted = False
		self.daemon = True
		try: self.start()
		except EOFError: print 'EOFFFFFFFFFF'

		self.fin_ = worker_finished()
		self.fin_.worker_fin.connect(self.ensem.produce_output)

	def run(self):
		self.process = multiprocessing.Process(
			target = self.target_func, args = ())
		try:
			self.process.start()
			self.process.join()

		except IOError:
			print 'IOError: pipe close hopefully without leaking'

		except pickle.PicklingError:
			print 'purge!'
			self.ensem._q_purge_()

		print 'process finished by aborting: ' + str(self.aborted)
		if not self.aborted: self.fin_.worker_fin.emit()

	def abort(self):
		self.aborted = True
		self.process.terminate()

if __name__ == '__main__': print 'this is a library!'



