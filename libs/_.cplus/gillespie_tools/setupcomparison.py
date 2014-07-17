from distutils.core import setup
from Cython.Build import cythonize

import numpy

from distutils.extension import Extension
from Cython.Distutils import build_ext

import numpy

ext_modules = [Extension('comparison', ['comparison.pyx'])]

#setup(
#	name = 'chemstringapp', 
#	ext_modules = ext_modules, 
#	cmdclass = {'build_ext': build_ext}, 
#	include_dirs = [numpy.get_include()]
#)

extensions = cythonize(ext_modules, annotate = True)
setup(ext_modules = extensions, include_dirs = [numpy.get_include()])
