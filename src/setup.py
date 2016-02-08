#!/usr/bin/python

from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext

import numpy

pkgs = [
    'modular4',
        ]
#exts = [Extension('sim_anneal.metric',['sim_anneal/metric.pyx'])]
exts = []
setup(name = 'modular4',version = '4.0',description = 'minimal modular simulator',
    author = 'ctogle',author_email = 'cogle@vt.edu',url = 'http://github.com/ctogle/modular4',
    license = 'MIT License',long_description = '''modular4: minimal modular simulator''',
    cmdclass = {'build_ext': build_ext},include_dirs = [numpy.get_include()], 
    scripts = ['../mrun.sh'],packages = pkgs,ext_modules = exts,py_modules = [])








