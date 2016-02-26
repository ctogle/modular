#!/usr/bin/python

from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext

import numpy,appdirs,os,pdb

def run_setup(*ags):
    pkgs = [
        'dstoolm4'
            ]
    exts = []
    setup(script_args = ags,name = 'dstoolm4',version = '4.0',description = 'dstoolm simulator',
        author = 'ctogle',author_email = 'cogle@vt.edu',url = 'http://github.com/ctogle/dstoolm',
        license = 'MIT License',long_description = '''dstoolm simulator''',
        cmdclass = {'build_ext': build_ext},include_dirs = [numpy.get_include()], 
        scripts = [],packages = pkgs,ext_modules = exts,py_modules = [])

if __name__ == '__main__':run_setup('build','install','--user')








