
modular:
========
modular_core is a python package that provides a framework for 
running arbitrary simulations and analyzing their results. 

installation:
=============
modular_core has been written for python 2.7; no attempts to use python 3+ have been made.
modular_core requires the following python packages: appdirs, setuptools, numpy, scipy, matplotlib, pyside, h5py, and mpi4py.

It is very likely that cython will be needed for most simulators written for modular.
Most users will also want the gillespie simulator written for use with modular_core which requires cython.
This is found at: http://github.com/ctogle/gillespiem

The 'src' folder contains everything necessary to install modular_core.
Use the following command to run the setup script:

python setup.py build install --user

testing:
========
In the 'tests' folder is a script to verify that typical run cases execute successfully.

python test_ensemble.py

running modular simulator:
==========================
modular_core is typically used via the modular.py script.

modular.py                                  -- starts the main gui

modular.py --plt                            -- starts the simple gui for opening pkl data

modular.py --modules                        -- simple terminal interface for loading/unloading simulation modules

modular.py somefile.mcfg somemodule         -- run the mcfg "somefile" using the simulation module "somemodule"

If no module is specified in the last usage case, modular.py will attempt to the simulation module "gillespiem"

Using the main gui to run an mcfg:

Make an ensemble (Ctrl+E)

Parse an mcfg file by using the "Parse mcfg File" button. (Ctrl+M)
There are some mcfgs used for testing in ./tests/gillespiemmcfgs

Run the ensemble using the "Run Ensemble" button. (Alt+R)

If output is specified in the chosen mcfg, it will be generated upon run completion.





