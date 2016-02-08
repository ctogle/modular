from threading import Thread
import multiprocessing

import sys
import os
import pickle
import types

import pdb

from PySide import QtCore

if __name__ == '__main__': print 'threadwork of modular_core'

class worker_finished(QtCore.QObject):
    worker_fin = QtCore.Signal()

#needs to fire an event to the ensemble_manager to perform output for 
# all simulations as well as post processes
class worker_thread(Thread):

    def __init__(self, ensem, target, index, args = ()):
        Thread.__init__(self)
        self.ensem = ensem
        self.target_func = target
        self.args = args
        self.index = index
        self.aborted = False
        self.daemon = True
        try: self.start()
        except EOFError: print 'EOFFFFFFFFFF'

        self.fin_ = worker_finished()
        self.fin_.worker_fin.connect(self.ensem._output)

    def run(self):
        self.process = multiprocessing.Process(
            target = self.target_func, args = self.args)
        try:
            self.process.start()
            self.process.join()

        except IOError:
            print 'IOError: pipe close hopefully without leaking'

        print 'process finished by aborting: ' + str(self.aborted)
        if not self.aborted: self.fin_.worker_fin.emit()

    def abort(self):
        self.aborted = True
        self.process.terminate()




