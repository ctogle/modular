# distutils: language = c++

########################################################################

import cython
import numpy as np
import pdb

mm_sys_string = '<species>Substrate:10000,Enzyme:5000,ES_Complex:0,Product:0<variables><functions><reactions>(1)ES_Complex->800.0->(1)Enzyme+(1)Product,(1)Substrate+(1)Enzyme->1.0->(1)ES_Complex,(1)ES_Complex->0.01->(1)Substrate+(1)Enzyme<end>time>=0.00098<capture>increment:time:0.00002<targets>ES_Complex,Product,iteration,time||'

########################################################################
'''
The gillespie toolset will aim to support many varieties of stochastic simulation

The interface will necessarily include:
simulate(system_string) : parse the system, run the system, return results
parse(system_string) : parse the system, return an object with methods for simulation
	step() : step the system forward by one iteration -> useful for branching
	run() : run step() until the system is over
	spill() : return the results of the simulation

** simulate should in principle just call parse(), run(), spill()

This should be accomplished in an object oriented fashion - extendable from python
necessary objects:
	species
		agent_based_species as a subclass
	reaction
		8 typical propensity cases as subclasses
		

as a starting point, i should attempt to implement MM sufficient toolset for speed test comparison

'''
########################################################################

cdef extern from "src/species.h":
	cdef cppclass species:
		species() except +
		#species(int) except +

		#int initial_count
		#int count

		double onee #############

		#int get_count()
		#void set_count(int)

		int add_onee() #############
		double get_onee() #############

@cython.boundscheck(False)
@cython.wraparound(False)
cdef class pySpecies:

	cdef species* thisptr

	def __cinit__(self, initial = 0):
		#self.thisptr = new species(initial)
		self.thisptr = new species()
	def __dealloc__(self): del self.thisptr
	#cpdef get_count(self): return self.thisptr.get_count()
	#cpdef set_count(self, val): self.thisptr.set_count(val)

	cpdef int add_onee(self):
		self.thisptr.add_onee()
		return 0
	def get_onee(self): return self.thisptr.get_onee()

########################################################################

cdef extern from "src/sim_system.h":
	cdef cppclass sim_system:
		sim_system() except +

		int total_captures
		int capture_count

		void parse()
		void step()
		void run()
		int spill()


		void run_test()####################

cdef class pySystem:

	cdef sim_system* thisptr
	cdef char* sys_string

	def __cinit__(self, sys_string = mm_sys_string):
		self.sys_string = sys_string
		self.thisptr = new sim_system()
		self.parse()
	def __dealloc__(self): del self.thisptr
	def __str__(self): return self.sys_string
	def __call__(self, *args, **kwargs):
		self.run()
	cpdef parse(self):
		print 'parse sys_string into reactions/species/etc'
		print self.sys_string
		self.thisptr.total_captures = 10
	cpdef step(self): self.thisptr.step()
	cpdef run(self): self.thisptr.run()
	cpdef spill(self): return self.thisptr.spill()

	cpdef run_test(self): self.thisptr.run_test()#######################

########################################################################
########################################################################
########################################################################



cdef extern from "src/sim_system.h":
	cdef int main()

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef int py_main():
	return main()

cdef extern from "src/sim_system.h":
	cdef int maintwo()

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef int py_main2():
	return maintwo()



def simulate(system_string = mm_sys_string):
	#cdef system = pySystem(system_string)
	print mm_sys_string
	#cdef pySpecies [:] species
	
	#create an object by parsing the system_string
	#	** this object will be a system object...
	#	this object should have parse(), step(), run(), spill()
	#	parse() is for subclasses and reparsing a system_string (bruteforce modification)
	#		the constructor MUST use the same pipeline
	#	step() takes one iterative step
	#	run() runs all iterative steps remaining
	#	spill() returns the resulting data set



@cython.boundscheck(False)
@cython.wraparound(False)
def add_test():
	print "Begin Trial 11."

	specs = np.array([pySpecies() for d in range(10)],dtype=object)

	cdef pySpecies[:] arrayview = specs

	cdef pySpecies sp
	cdef int EMAX = 10
	cdef int kkk, ii1, ii2

	cdef double val = 0
	for kkk in range(10):
		for ii1 in range(10000):
			for ii2 in range(1000):
				for ijk in range(EMAX):
					sp = arrayview[ijk]
					sp.add_onee()

		for i in range(10):
			val += arrayview[i].get_onee()

		print "Value check. ", kkk, " of 9. sum of array: ", val
		val = 0

@cython.boundscheck(False)
@cython.wraparound(False)
def add_test2():
	print "Begin Trial 111."

	cdef sys = pySystem()
	sys.run_test()









