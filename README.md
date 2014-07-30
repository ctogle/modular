modular
=======
This is a walkthrough for acquiring, installing, testing, and running modular.

acquisition:
============
Download the latest version of modular_core as a .zip file from this link:
https://github.com/ctogle/modular
Using git:
git clone htttp://github.com/ctogle/modular

installation:
=============
You will need a build of python with the proper packages to run modular.
You can download python 2.7.8 (32-bit is recommended for now) from this link:
https://www.python.org/download/

The setup script mentioned below will attempt to install the necessary dependencies, but if this fails I recommend using pip to install dependencies.
The following packages are required to run modular:
Numpy 1.8.1
Scipy 0.13.0
PyOpenGL 3.1.0
PySide 1.2.2
matplotlib 1.3.1

*The versions you use most likely do not need to match these, but this combination has been tested.

On windows, every one of these can be installed very easily using this website:
http://www.lfd.uci.edu/~gohlke/pythonlibs/
Be sure to grab the proper version as it should indicate it's for python 2.7, 32 or 64 bit, whichever matches the python you installed.
For examples: "numpy‑MKL‑1.8.1.win32‑py2.7.exe" is for python 2.7, 32 bit version.

If you obtained modular by using git, you will have a folder called 'modular' in your working directory which contains two folders.
The 'src' folder contains everything necessary to install modular_core. Use the follow commands to run the setup script:
cd modular/src
sudo python setup.py build install

If all the dependencies are sorted out properly, then installation of the modular_core package is complete.

You must repeat this process for the 'stringchemical' module using the repository located at:
http://github.com/ctogle/stringchemical
(You may need a c compiler installed to build the stringchemical cython based python extension.)

It is recommended you follow the testing section to be sure everything is installed.

testing:
========
In the previously used terminal use the follow commands to run the test script:
cd ../tests
sudo python test_ensemble.py

Wait a long time while lots of things happen, until either a status of 'OK' or 'FAILED' is issued.
The output files associated with the testing process are found in the working directory (./tests) as .pkl files.

If all tests pass, you may delete the './src' folder and run the modular.py script from anywhere you wish (such as a directory in your PATH.)

running modular simulator:
==========================
Using the same terminal start modular with the following commands:
cd ../
sudo python modular.py

Make an ensemble (Ctrl+E)
Parse a .mcfg file by using the "Parse mcfg File" button. (Ctrl+M)
	- There are some mcfgs used for testing in ./tests/stringchemical_dep_mcfgs
Run the ensemble using the "Run Ensemble" button. (Alt+R)

Lots of things should be printed to your terminal as it runs the simulations (or crashes, in which case email me a screen shot of your terminal.)






