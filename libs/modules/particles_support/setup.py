from distutils.core import setup, Extension
import numpy as np
import os

import pdb

module1 = Extension('generic_wrap', 
	include_dirs = ['.', np.get_include(), 
		os.path.join(np.get_include(), 'numpy')], 
	sources = ['generic_wrap.cpp'])

setup (name = 'ModuleWrap',
	version = '1.0',
	description = 'This is a generic simulation module', 
	ext_modules = [module1])







