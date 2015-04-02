#!/usr/bin/python
import pdb,os,appdirs

from setuptools import setup

res_dir = 'modular_core/resources/'
res_fis = [f for f in os.listdir(os.path.join(
    os.getcwd(),'modular_core','resources'))]
res_files = [res_dir + f for f in res_fis]

#data_pools_files = ['modular_core/data_pools/__init__.py']
initfile = ['modular_core/resources/__init__.py']

mdatapooldir = os.path.join(appdirs.user_data_dir(),'modular_data_pools')
mdatamappooldir = os.path.join(mdatapooldir,'mapdata')
mresourcesdir = os.path.join(appdirs.user_config_dir(),'modular_resources')
mcachedir = os.path.join(appdirs.user_cache_dir(),'modular_cache')

pkgs = [
    'modular_core',
    'modular_core.gui', 
    'modular_core.modules',
    'modular_core.io',
    'modular_core.fitting', 
    'modular_core.criteria',
    'modular_core.data', 
    'modular_core.postprocessing',
    'modular_core.parameterspace',
    'modular_core.parallel',
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
    #py_modules = ['../modular.py'], 
    zip_safe = False,
    data_files=[(mresourcesdir,res_files), 
                (mcachedir,initfile),
                (mdatapooldir,initfile),
                (mdatamappooldir,initfile)]
    )









