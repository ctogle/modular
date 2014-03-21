from distutils.core import setup
from Cython.Build import cythonize

import numpy

from distutils.extension import Extension
from Cython.Distutils import build_ext

import numpy

ext_modules = [Extension('stringchemical', ['libchemicalstring_4.pyx'])]
#ext_modules = cythonize('libchemicalstring.pyx', annotate = True) # accepts a glob pattern

setup(
	name = 'chemstringapp', 
	ext_modules = ext_modules, 
	cmdclass = {'build_ext': build_ext}, 
	include_dirs = [numpy.get_include()]
)

#python setup.py build_ext --inplace


