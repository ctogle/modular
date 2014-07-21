#!/usr/bin/env python
import os, sys, time, pstats, cProfile, argparse

import libs.modular_core.libfundamental as lfu
import libs.gui.libqtgui as lqg

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




