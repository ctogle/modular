#!/usr/bin/env python2.7

import argparse

import shutil
import glob
import os
import os.path
import zipfile
import time

import pdb

_filter_endings_ = ['pyc', 'vtu', 'db', '.pkl', 
					'pvsm', 'sh', 'zip', 'xmind']

def ignore_filter_(fi):
	endings = _filter_endings_
	ended = [fi.endswith(ending) for ending in endings]
	return True in ended or fi.startswith('_.') or fi.startswith('.')

def ignore_paths():

	def ignoref(pa, files):
		if pa.startswith('_.') or pa.startswith('.'):
			return (f for f in files)

		else: fis = [f for f in files if ignore_filter_(f)]
		return fis

	return ignoref

def get_new_src_folder(base = '_.src.0', fi_ext = None):
	counts = range(100)
	counts.reverse()
	def get_is():
		if fi_ext:
			is_ = os.path.isfile(os.path.join(
				os.getcwd(), base + str(fi_ext)))

		else: is_ = os.path.isdir(os.path.join(os.getcwd(), base))
		return is_

	while get_is():
		try: base = base[:base.rfind('.')] + '.' + str(counts.pop())
		except: pdb.set_trace()

	return base

def copy_to_src(new = True):
	if new:
		which = get_new_src_folder()
		shutil.copytree(os.getcwd(), os.path.join(
			os.getcwd(), which), ignore = ignore_paths())
		return which

	else: return find_most_recent_build()

def find_most_recent_build():
	srcs = [int(sc.split('.')[-1]) for sc in 
		os.listdir(os.getcwd()) if sc.startswith('_.src')]
	max_dex = [val == max(srcs) for val in srcs].index(True)
	return '_.src.' + str(srcs[max_dex])

def get_build_zip_name(dst, src):
	lt = time.localtime(time.time())
	date = time.strftime('%m.%d.%Y', lt)
	src_dex = src[src.rfind('.') + 1:]
	zip_name = '.'.join([dst, date, src_dex, '0'])
	zip_name = get_new_src_folder(zip_name, fi_ext = '.zip')
	return zip_name

def zip_(src, dst):
	#src = find_most_recent_build(src)
	dst = get_build_zip_name(dst, src)
	zf = zipfile.ZipFile("%s.zip" % (dst), "w")
	abs_src = os.path.abspath(src)
	for dirname, subdirs, files in os.walk(src):
		if files:
			for filename in files:
				absname = os.path.abspath(os.path.join(dirname, filename))
				arcname = absname[len(abs_src) + 1:]
				#print 'zipping %s as %s' % (
				#	os.path.join(dirname, filename), arcname)
				zf.write(absname, arcname)

		else:
			absname = os.path.abspath(os.path.join(
							dirname, 'dummy.txt'))
			open(absname, 'a').close()
			arcname = absname[len(abs_src) + 1:]
			zf.write(absname, arcname)

	zf.close()
	return src, dst

if __name__ == '__main__':
	'''
	if a _.src.# folder is already present, 
		such a folder with the highest value of # is used
		to create the new build
	if none are present, one is generated with # = 0
	if --skip is provided, this new src 
		folder wont be automatically deleted
	if the same src folder is used more than once, the value of 
		& corresponds to which copy of that particular src folder
		the given build was generated from

	the resulting zip file name is in this format:
	modular.month.day.year.#.&

	thus, this utility will not overwrite a .zip build nor a
		_.src.# directory the user has chosen to keep; it will 
		instead generate a unique name by incrementing either
		# or & depending on the presence of _.src.# directories
		which have been kept via the --skip run option and on
		the number of .zip builds generated from that _.src.# 
		directory
	'''
	parser = argparse.ArgumentParser()
	reg = ['skipclean', 'prevent auto deletion of copied src build']
	parser.add_argument('--' + reg[0], action = "store_false", 
								default = True, help = reg[1])
	new_help = 'create a new src folder to \
		use even if one is already present'
	parser.add_argument('--new', action = "store_false", 
					default = False, help = new_help)
	#this is still buggy, but sufficient for now...
	options = parser.parse_args()
	new = get_new_src_folder().endswith('0') or options.__dict__['new']
	src_copied = copy_to_src(new)
	src_used, dst_used = zip_(src_copied, "modular")
	if options.__dict__[reg[0]]: shutil.rmtree(src_used)

