#!/usr/bin/python

from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext

import numpy

pkgs = ['sim_anneal']
exts = [
    Extension('sim_anneal.pspace',['sim_anneal/pspace.pyx','sim_anneal/pspace.pxd']),
    Extension('sim_anneal.metric',['sim_anneal/metric.pyx','sim_anneal/metric.pxd']),
    Extension('sim_anneal.forms',['sim_anneal/forms.pyx','sim_anneal/forms.pxd'])]
setup(name = 'sim_anneal',version = '1.0',description = 'simulated annealing implementation',
    author = 'ctogle',author_email = 'cogle@vt.edu',url = 'http://github.com/ctogle/sim_anneal',
    license = 'MIT License',long_description = '''simple simulated annealing implementation''',
    cmdclass = {'build_ext': build_ext},include_dirs = [numpy.get_include()], 
    scripts = [],packages = pkgs,ext_modules = exts,py_modules = [])








