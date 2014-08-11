import modular_core.libfundamental as lfu
#import libs.modular_core.libfundamental as lfu

import cPickle as pickle
import os, traceback, sys

import pdb

def save_pkl_object(obj, filename):
	output = open(filename, 'wb')
	pickle.dump(obj, output)
	output.close()

def load_pkl_object(filename):
	if not os.path.isfile(filename):
		#dp_path = lfu.get_data_pool_path()
		dp_path = os.getcwd()
		filename = os.path.join(dp_path, filename.split(os.path.sep)[-1])
	try:
		pkl_file = open(filename, 'rb')
		data = pickle.load(pkl_file)
	except:
		try:
			pkl_file = open(filename, 'r')
			data = pickle.load(pkl_file)
		except pickle.UnpicklingError:
			print 'something is wrong with your pkl file!'
		except:
			traceback.print_exc(file=sys.stdout)
			return None
	pkl_file.close()
	return data

def output_lines(lines, direc, finame = None, 
		overwrite = True, dont_ask = False):
	#if no finame is given, direc should contain the full path
	if finame is None: path = direc
	else: path = os.path.join(direc, finame)
	if os.path.isfile(path):
		if not overwrite:
			print 'cant output without overwriting; skipping!'
			return False

		else:
			if dont_ask: check = lambda: True
			#if dont_ask: True
			else:
				msg = '\n'.join(['Are you sure you want', 
					'to overwrite the module?:', path])
				check = lgd.message_dialog(None, msg, 'Overwrite', True)

			#if check(): print 'overwriting as instructed...'
			if check: print 'overwriting as instructed...'
			else:
				print 'wont output without your permission; skipping!'
				return False

	with open(path, 'w') as handle:
		[handle.write(line + '\n') for line in lines]

	return True

def parse_lines(file_path, parser, parser_args = ()):
	with open(file_path, 'r') as handle: lines = handle.readlines()
	parser(lines, *parser_args)

if __name__ == '__main__':
	print 'Hush - This is a library!'

if __name__ == 'libs.modular_core.libfiler':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb


