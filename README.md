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

../mrun.sh ./correl_ensemble_test/ --plt
-------------------------------------------------------------------------------

-------------------------------------------------------------------------------
Three ways to run an mcfg using the mrun.sh script:

../mrun.sh mcfgs/correl_demo.mcfg

../mrun.sh mcfgs/correl_demo.mcfg --np #processes

../mrun.sh mcfgs/correl_demo.mcfg --mpi "path/to/a/hostfile"
-------------------------------------------------------------------------------
