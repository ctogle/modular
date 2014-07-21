#!/usr/bin/python
from os.path import isfile, join
import glob
import os
import re

from setuptools import setup


if isfile("MANIFEST"):
    os.unlink("MANIFEST")


TOPDIR = os.path.dirname(__file__) or "."
#VERSION = re.search('__version__ = "([^"]+)"',
#	open(TOPDIR + "/src/pkg1/__init__.py").read()).group(1)
VERSION = '1.0'

setup(name="pkg1-test",
      version = VERSION,
      description = "test pkg",
      author = "ctogle",
      author_email = "nonsense@nonsense.com",
      url = "http://nonsense.org",
      license = "MIT License",
      long_description =
"""\
This is a test setup for a dummy package pkg1
""",
      packages = ['pkg1'],
      #package_dir = {'':'pkg1'}, 
      py_modules = ['pkg1.modu1'], 
      #package_data={"": ["*.tar.gz"]},
      #include_package_data=True,
      zip_safe=False,
      )

