-------------------------------------------------------------------------------
# modular4
Version 4 of modular simulator framework
-------------------------------------------------------------------------------

-------------------------------------------------------------------------------
Install modular, sim_anneal, and gillespiem with:

./setup.py

-------------------------------------------------------------------------------

-------------------------------------------------------------------------------
To run the tests and view the test results:


Change to the tests directory:

cd ./tests/

Run the test:

./test.py

View the test results:

../mrun.sh --dir ./correl_ensemble_test/ --plt

-------------------------------------------------------------------------------

-------------------------------------------------------------------------------
Three ways to run an mcfg using the mrun.sh script (with mrun.sh in the path):

mrun.sh --mcfg path/to/some/mcfgfile.mcfg

mrun.sh --np #processes --mcfg path/to/some/mcfgfile.mcfg 

mrun.sh --mpi path/to/some/hostfile --mcfg path/to/some/mcfgfile.mcfg 


You can also run mcfgs using mpiexec manually:

mpiexec [mpi-options] mrun.sh --mcfg path/to/some/mcfgfile.mcfg


Running an mcfg creates a directory in the current working directory containing
results among other files generated during the run. To view output data:

mrun.sh --dir /path/to/output/files/ --plt

-------------------------------------------------------------------------------
