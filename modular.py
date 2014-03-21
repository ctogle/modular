#!/usr/bin/env python
import os
import sys
import time

class sys_pipe_mirror(object):

	def __init__(self, std_out, terminal = None):
		self.terminal = terminal
		self._stdout = std_out
		std_out = self
		self.so_far = []
		self._qt = None

	def set_terminal(self, term, qt_ref):
		self._qt = qt_ref
		self.terminal = term
		self.handle_output('\n'.join(self.so_far))

	def write(self, text):
		if self.terminal:
			self.handle_output(text)

		self.so_far.append(text)
		self._stdout.write(self, text)
		if len(self.so_far) > 100:
			self.so_far = self.so_far[-100:]

	def handle_output(self, text):
		self.terminal.moveCursor(self._qt.QTextCursor.End)
		self.terminal.insertPlainText(text)

#pipe_mirror = sys_pipe_mirror(sys.stdout)
import libs.modular_core.libfundamental as lfu
#lfu.pipe_mirror = pipe_mirror

import libs.gui.libqtgui as lqg

import pstats, cProfile

import argparse

import pdb

def run(options, registry):
	params = {}

	#if any programs were specified, run the first one appearing 
	# in resources/program_registry.txt
	for reg in registry:
		if options.__dict__[reg[1]]:
			params['gui_lib'] = '.'.join(['libs', 
					'gui', 'libqtgui_' + reg[0]])

	#default program is modular simulator
	#else:
	if not 'gui_lib' in params.keys():
		params['gui_lib'] = 'libs.gui.libqtgui_modular'

	lfu.set_gui_pack(params['gui_lib'])
	#likely a problem without an application
	# unless gui_pack will provide alternative
	if hasattr(lfu.gui_pack, '_application_'):
		params['application'] = lfu.gui_pack._application_

	#gui_pack has chance to override default initialize_gui
	if hasattr(lfu.gui_pack, 'initialize_gui'):
		lfu.gui_pack.initialize_gui(params)

	#default initialize_gui simply runs chosen application
	else: lfu.initialize_gui(params)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--prof', action = "store_true", 
			default = False, help = 'perform profiling')
	reg = lfu.parse_registry()
	for prog in reg:
		parser.add_argument('--' + prog[1], action = "store_true", 
								default = False, help = prog[2])

	options = parser.parse_args()
	if options.prof:
		cProfile.runctx('run(options, reg)', 
			globals(), locals(), 'Profile.prof')
		s = pstats.Stats('Profile.prof')
		#s.strip_dirs().sort_stats('calls').print_stats(0.1)
		s.strip_dirs().sort_stats('time').print_stats(0.1)

	else: run(options, reg)




