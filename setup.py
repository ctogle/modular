#!/usr/bin/python

from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext

import numpy,appdirs,os,pdb

def resource_files(res_files = [],srsrc_dir = './src/resources/'):
    for rf in os.listdir(srsrc_dir):
        p = srsrc_dir + rf
        if os.path.isfile(p):
            res_files.append(p)
        elif os.path.isdir(p):
            resource_files(res_files,p+'/')
    return res_files

def run_modular_setup(*ags):
    cwd = os.getcwd()
    os.chdir(os.path.join(cwd,'src'))
    pkgs = ['modular4']
    exts = []
    rsrc_dir = os.path.join(appdirs.user_config_dir(),'modular4_resources')
    rsrc_files = resource_files([],'./resources/')
    setup(script_args = ags,name = 'modular4',version = '4.0',description = 'minimal modular simulator',
        author = 'ctogle',author_email = 'cogle@vt.edu',url = 'http://github.com/ctogle/modular',
        license = 'MIT License',long_description = '''modular4: minimal modular simulator''',
        cmdclass = {'build_ext': build_ext},include_dirs = [numpy.get_include()], 
        data_files = [(rsrc_dir,rsrc_files)],
        scripts = ['../mrun.sh'],packages = pkgs,ext_modules = exts,py_modules = [])
    os.chdir(cwd)

def run_gillespiem_setup(*ags):
    cwd = os.getcwd()
    os.chdir(os.path.join(cwd,'src','gillespiem4','src'))
    pkgs = ['gillespiem4']
    exts = []
    setup(script_args = ags,name = 'gillespiem4',version = '4.0',description = 'gillespiem4 simulator',
        author = 'ctogle',author_email = 'cogle@vt.edu',url = 'http://github.com/ctogle/gillespiem',
        license = 'MIT License',long_description = '''gillespiem4 simulator''',
        cmdclass = {'build_ext': build_ext},include_dirs = [numpy.get_include()], 
        scripts = [],packages = pkgs,ext_modules = exts,py_modules = [])
    os.chdir(cwd)

def run_dstoolm_setup(*ags):
    cwd = os.getcwd()
    os.chdir(os.path.join(cwd,'src','dstoolm4','src'))
    pkgs = ['dstoolm4']
    exts = []
    setup(script_args = ags,name = 'dstoolm4',version = '4.0',description = 'dstoolm4 simulator',
        author = 'ctogle',author_email = 'cogle@vt.edu',url = 'http://github.com/ctogle/dstoolm',
        license = 'MIT License',long_description = '''dstoolm4 simulator''',
        cmdclass = {'build_ext': build_ext},include_dirs = [numpy.get_include()], 
        scripts = [],packages = pkgs,ext_modules = exts,py_modules = [])
    os.chdir(cwd)

def run_sim_anneal_setup(*ags):
    cwd = os.getcwd()
    os.chdir(os.path.join(cwd,'src','sim_anneal','src'))
    pkgs = ['sim_anneal']
    exts = [Extension('sim_anneal.metric',['sim_anneal/metric.pyx'])]
    setup(script_args = ags,name = 'sim_anneal',version = '1.0',description = 'simulated annealing implementation',
        author = 'ctogle',author_email = 'cogle@vt.edu',url = 'http://github.com/ctogle/sim_anneal',
        license = 'MIT License',long_description = '''simple simulated annealing implementation''',
        cmdclass = {'build_ext': build_ext},include_dirs = [numpy.get_include()], 
        scripts = [],packages = pkgs,ext_modules = exts,py_modules = [])
    os.chdir(cwd)

if __name__ == '__main__':
    run_modular_setup('build','install','--user')
    run_gillespiem_setup('build','install','--user')
    run_dstoolm_setup('build','install','--user')
    run_sim_anneal_setup('build','install','--user')





