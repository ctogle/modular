#!/usr/bin/python

from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext

import numpy,appdirs,os,pdb

def resource_files(res_files = [],srsrc_dir = './resources/'):
    for rf in os.listdir(srsrc_dir):
        p = srsrc_dir + rf
        if os.path.isfile(p):
            res_files.append(p)
        elif os.path.isdir(p):
            resource_files(res_files,p+'/')
    return res_files

def run_setup(*ags):
    pkgs = [
        'gillespiem4'
            ]
    exts = []
    setup(script_args = ags,name = 'gillespiem4',version = '4.0',description = 'gillespiem4 simulator',
        author = 'ctogle',author_email = 'cogle@vt.edu',url = 'http://github.com/ctogle/gillespiem4',
        license = 'MIT License',long_description = '''gillespiem4 simulator''',
        cmdclass = {'build_ext': build_ext},include_dirs = [numpy.get_include()], 
        scripts = [],packages = pkgs,ext_modules = exts,py_modules = [])

if __name__ == '__main__':run_setup('build','install','--user')








