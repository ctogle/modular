
# cython:profile=False,boundscheck=False,nonecheck=False,wraparound=False,initializedcheck=False,cdivision=True
###################################
# imports:
from libc.math cimport log
from libc.math cimport sin
from libc.math cimport cos
#from libc.stdlib cimport rand
#cdef extern from "limits.h":
#	int INT_MAX
from numpy import cumprod as cumulative_product
cdef double pi = 3.14159265359
import random,numpy
import time as timemodule
from cython.view cimport array as cvarray

cdef inline double heaviside(double value):
	if value >= 0.0:return 1.0
	else:return 0.0


cdef inline double ext_signal(double [4] state):
	cdef double val = 10.0*(external_signal(/home/cogle/dev/modular/tests/data/extsignal1.txt,state[0]) + 1.0)
	state[3] = val
	return val










################################################################################

cpdef gillespie_run(rseed,k_cat):
	cdef double [:,:] data = numpy.zeros((3, 201),dtype = numpy.double)
	cdef double capture[3]
	cdef double state[4]
	state[0] = 0.0
	state[1] = 0
	state[2] = 1.0
	ext_signal(state)
	random.seed(rseed)
	cdef int totalcaptures = 201
	cdef int capturecount = 0
	cdef int rtabledex
	cdef int tdex
	cdef int cdex
	cdef double totalpropensity
	cdef double tpinv
	cdef double time = 0.0
	cdef double lasttime = 0.0
	cdef double realtime = 0.0
	cdef double del_t = 0.0
	cdef double randr
	cdef int whichrxn = 0
	cdef int rxncount = 2
	cdef double reactiontable[2]
	cdef double propensities[2]
	propensities[0] = ext_signal(state)
	propensities[1] = (state[1])*state[2]
	cdef int tdexes[3]
	tdexes[0] = 0
	tdexes[1] = 1
	tdexes[2] = 3

	while capturecount < totalcaptures:
		totalpropensity = 0.0
		totalpropensity = totalpropensity + propensities[0]
		reactiontable[0] = totalpropensity
		if state[1] >= 1:totalpropensity = totalpropensity + propensities[1]
		reactiontable[1] = totalpropensity

		if totalpropensity > 0.0:
			tpinv = 1.0/totalpropensity
			del_t = -1.0*log(random.random())*tpinv
			randr = random.random()*totalpropensity
			for rtabledex in range(rxncount):
				if randr < reactiontable[rtabledex]:
					whichrxn = rtabledex
					break


		else:
			del_t = 10.0
			whichrxn = -1

		state[0] += del_t
		realtime = state[0]
		while lasttime < realtime and capturecount < totalcaptures:
			state[0] = lasttime
			lasttime += 10.0

			ext_signal(state)

			for cdex in range(3):
				data[cdex,capturecount] = state[tdexes[cdex]]
			capturecount += 1
		state[0] = realtime

		if whichrxn == -1:
			propensities[0] = ext_signal(state)
			propensities[1] = (state[1])*state[2]
		elif whichrxn == 0:
			state[1] += 1

			propensities[0] = ext_signal(state)
			propensities[1] = (state[1])*state[2]
		elif whichrxn == 1:
			state[1] -= 1

			propensities[0] = ext_signal(state)
			propensities[1] = (state[1])*state[2]

	return numpy.array(data,dtype = numpy.float)

################################################################################









