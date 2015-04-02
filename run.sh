#!/usr/bin/env bash

echo "start running"

virtualenv venv
source venv/bin/activate


#pip install appdirs
#pip install cython
pip install numpy
#pip install scipy
pip install h5py
#pip install dispy
#pip install PySide
#pip install PyOpenGL

python ./modular.py

deactivate

echo "done running"



