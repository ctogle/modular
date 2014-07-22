#!/usr/bin/python
from os.path import isfile, join
import glob
import os
import re

from setuptools import setup#, Extension

if isfile("MANIFEST"):
    os.unlink("MANIFEST")

TOPDIR = os.path.dirname(__file__) or "."
#VERSION = re.search('__version__ = "([^"]+)"',
#	open(TOPDIR + "/src/pkg1/__init__.py").read()).group(1)
VERSION = '1.0'

core_modules = [
	'modular_core.libfundamental', 
	'modular_core.libfiler', 
	'modular_core.libsimcomponents', 
	'modular_core.libmodcomponents', 
	'modular_core.libmultiprocess', 
	'modular_core.libpostprocess', 
	'modular_core.liboutput', 
	'modular_core.libmath', 
	'modular_core.gui.libqtgui', 
	'modular_core.gui.libqtgui_bricks', 
	'modular_core.gui.libqtgui_masons', 
	'modular_core.gui.libqtgui_dialogs', 

	'modular_core.gpu.lib_gpu', 

	#'modular_core.modules.libchemicallite', 
				]

def ignore_res(f):
	#if f.startswith('__') or f.startswith('_.'): return True
	#else: return False
	return False

res_dir = 'modular_core/resources/'
res_fis = [f for f in os.listdir(os.path.join(
	os.getcwd(), 'modular_core', 'resources')) if not ignore_res(f)]
res_files = [res_dir + f for f in res_fis]

data_pools_files = ['modular_core/data_pools/__init__.py']

requirements = [
	'numpy >= 1.8.1', 
	'scipy >= 0.14.0', 
	'PySide >= 1.2.2', 
	'matplotlib >= 1.1.1', 
	'six >= 1.7.3', 
	'PyOpenGL >= 3.0.0', 
	'python-dateutil >= 2.2', 
			]

setup(
	name="modular_core-pkg",
	version = VERSION,
	description = "modular core pkg",
	author = "ctogle",
	author_email = "cogle@vt.edu",
	url = "http://github.com/ctogle/modular",
	license = "MIT License",
	long_description =
"""\
This is the core package of modular
""",
	install_requires = requirements, 
	scripts = ['modular.py', 'modular.bat'], 
	packages = ['modular_core', 'modular_core.gui', 
			'modular_core.gpu', 'modular_core.modules'], 
			#'modular_core.modules.chemicallite_support'],
	#package_dir = {'':'pkg1'}, 
	py_modules = core_modules, 
	#package_data={"": ["*.tar.gz"]},
	#include_package_data=True,
	zip_safe = False,
	data_files=[('modular_core/resources', res_files), 
					('modular_core/data_pools', data_pools_files)], 
	#ext_package = 'modular_core.modules.chemicallite_support',
	#ext_modules = [Extension('stringchemical', 
	#		['modular_core/modules/chemicallite_support/libchemicalstring_6.c']),
	#					Extension('stringchemical_timeout', 
	#		['modular_core/modules/chemicallite_support/libchemicalstring_6_timeout.c'])],
	)

