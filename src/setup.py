#!/usr/bin/python

from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext

import numpy

pkgs = [
    'gillespiem4'
        ]
exts = []
setup(name = 'gillespiem4',version = '4.0',description = 'gillespiem4 simulator',
    author = 'ctogle',author_email = 'cogle@vt.edu',url = 'http://github.com/ctogle/gillespiem4',
    license = 'MIT License',long_description = '''gillespiem4 simulator''',
    cmdclass = {'build_ext': build_ext},include_dirs = [numpy.get_include()], 
    scripts = [],packages = pkgs,ext_modules = exts,py_modules = [])








