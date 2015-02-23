#!/usr/bin/python
from os.path import isfile, join
import glob
import os
import re

import appdirs

from setuptools import setup#, Extension

import pdb

core_modules = []

res_dir = 'modular_core/resources/'
res_fis = [f for f in os.listdir(os.path.join(
    os.getcwd(),'modular_core','resources'))]
res_files = [res_dir + f for f in res_fis]

data_pools_files = ['modular_core/data_pools/__init__.py']

pkgs = [
    'modular_core',
    'modular_core.gui', 
    'modular_core.gpu',
    'modular_core.modules',
    'modular_core.io',
    'modular_core.fitting', 
    'modular_core.criteria',
    'modular_core.data', 
    'modular_core.postprocessing',
    'modular_core.cython']
setup(
    name="modular_core-pkg",
    version = '1.0',
    description = "modular core pkg",
    author = "ctogle",
    author_email = "cogle@vt.edu",
    url = "http://github.com/ctogle/modular",
    license = "MIT License",
    long_description = '''this is the core package of modular''',
    scripts = ['../modular.py'], 
    packages = pkgs, 
    py_modules = core_modules, 
    zip_safe = False,
    data_files=[(os.path.join(appdirs.user_config_dir(), 
                        'modular_resources'), res_files), 
                (os.path.join(appdirs.user_data_dir(), 
                    'modular_data_pools'), data_pools_files)], 
    )

