#!/usr/bin/python
import os, sys, time, pstats, cProfile, argparse

import modular_core.libfundamental as lfu
lfu.USING_GUI = True
import modular_core.gui.libqtgui as lqg

import pdb

def handle_programs():
	progs = [m[0] for m in lfu.parse_registry()]
	prog_count = len(progs)
	input_ = ':'
	while not input_ == 'q':
		print 'you may add or remove programs from the registry'
		print 'currently there are', prog_count, 'programs available'
		if prog_count > 0: print 'they are:'
		for prog in progs: print '\t', prog
		print '\n-a <program> will attempt to add program <program>'
		print '-r <program> will attempt to remove program <program>\n'
		input_ = raw_input('\n:::: ').strip()
		if input_.startswith('-a '):
			prog = input_[3:]
			ext_ = raw_input('\t\twhat extension will this program use?\t')
			desc_ = raw_input('\t\twhat description will this program have?\t')
			pmod_ = raw_input('\t\twhat module provides this program?\t')
			added = lfu.add_program_to_registry(prog, ext_, desc_, pmod_)
			print '-'*50
			if added: print '\nprogram', prog, 'was successfully added\n'
			else: print '\nprogram', prog, 'could not be added...\n'
			print '-'*50
		elif input_.startswith('-r '):
			prog = input_[3:]
			removed = lfu.remove_program_from_registry(prog)
			print '-'*50
			if removed: print '\nprogram', prog, 'was successfully removed\n'
			else: print '\nprogram', prog, 'could not be removed...\n'
			print '-'*50
		elif not input_ == 'q':
			print '-'*50,'\ninput not recognized... :',input_,'\n'+'-'*50
		progs = [m[0] for m in lfu.parse_registry()]
		prog_count = len(progs)

	print '\n\tfinished editing program registry!\n\n'

def handle_modules():
	mods = [m[0] for m in lfu.parse_module_registry()]
	mod_count = len(mods)
	input_ = ':'
	while not input_ == 'q':
		print 'you may add or remove modules from the registry'
		print 'currently there are', mod_count, 'modules available'
		print 'they are:'
		for mod in mods: print '\t', mod
		print '\n-a <module> will attempt to add module <module>'
		print '-r <module> will attempt to remove module <module>\n'
		input_ = raw_input('\n:::: ').strip()
		if input_.startswith('-a '):
			mod = input_[3:]
			added = lfu.add_module_to_registry(mod)
			print '-'*50
			if added: print '\nmodule', mod, 'was successfully added\n'
			else: print '\nmodule', mod, 'could not be added...\n'
			print '-'*50
		elif input_.startswith('-r '):
			mod = input_[3:]
			removed = lfu.remove_module_from_registry(mod)
			print '-'*50
			if removed: print '\nmodule', mod, 'was successfully removed\n'
			else: print '\nmodule', mod, 'could not be removed...\n'
			print '-'*50
		elif not input_ == 'q':
			print '-'*50,'\ninput not recognized... :',input_,'\n'+'-'*50
		mods = [m[0] for m in lfu.parse_module_registry()]
	print '\n\tfinished editing module registry!\n\n'

def run(options, registry):
	params = {}

	#if any programs were specified, run the first one appearing 
	# in resources/program_registry.txt
	for reg in registry:
		if options.__dict__[reg[1]]:
			params['gui_lib'] = '.'.join([reg[3], 
					'gui', 'libqtgui_' + reg[0]])

	#default program is modular simulator
	if not 'gui_lib' in params.keys():
		params['gui_lib'] = 'modular_core.gui.libqtgui_modular'

	if lfu.using_gui(): lfu.set_gui_pack(params['gui_lib'])
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
	parser.add_argument('--programs', action = "store_true", 
			default = False, help = 'load/unload programs')
	parser.add_argument('--modules', action = "store_true", 
			default = False, help = 'load/unload modules')
	reg = lfu.parse_registry()
	for prog in reg:
		parser.add_argument('--' + prog[1], action = "store_true", 
					default = False, help = prog[2])

	options = parser.parse_args()
	if options.programs: handle_programs()
	elif options.modules: handle_modules()
	else:
		if options.prof:
			cProfile.runctx('run(options, reg)', 
				globals(), locals(), 'Profile.prof')
			s = pstats.Stats('Profile.prof')
			#s.strip_dirs().sort_stats('calls').print_stats(0.1)
			s.strip_dirs().sort_stats('time').print_stats(0.1)
		else: run(options, reg)

