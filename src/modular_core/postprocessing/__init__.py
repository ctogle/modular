#!/usr/bin/python2.7

__doc__ = '''
Provides analytic methods for any modular data.

A post process is a term for any analytic method to run.
Every post process has a distinct output plan for its output.
A post process can receive as input the data from simulations, the result 
of a fitting routine, or the result of another post process.
A post process can only receive input from processes which were run before it.
Any post process can therefore receive simulation data as input.
Any post process using simulation data as input is referred to as a "zeroth post process."
Non-zeroth post processes are always run on the root node for clustering.
Post processes are run in the order they are specified.



'''


