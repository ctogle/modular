import numpy as np
cimport cython


@cython.boundscheck(False)
@cython.wraparound(False)

cdef class EnzymeNew:
	cdef double value

	def __init__(self, double value):
		self.value = value

	cpdef int add_one(self):
		self.value += 1
		return 0

	def get_value(self):
		return self.value

cdef:
	int EMAX = 10
	int ii0 = 0
	int jj0 = 0
	int ijk = 0
	int kkk, ii1, ii2, aaa

def trial_1():
	print "Begin Trial 1"
	# 1: test speed of addition in cython (very fast)
	cdef double aaa = 0
	for kkk in range(10):
		for ii1 in range(10000):
			for ii2 in range(1000):
				for ijk in range(EMAX):
					aaa = aaa+1
		print "Value check. ", kkk, "Out of 9. Raw addition: ", aaa
	return None

def trial_11():
	print "Begin Trial 11."

	cdef:
		EnzymeNew addInstance
		double value

	addition_classes = np.array([None] * 10, dtype = EnzymeNew)
	#addition_classes = np.array([None] * 10)
	for i in range(len(addition_classes)):
		addition_classes[i] = EnzymeNew(value=0)

	cdef EnzymeNew[:] arrayview = addition_classes

	val = 0
	for kkk in range(10):
		for ii1 in range(10000):
			for ii2 in range(1000):
				for ijk in range(EMAX):
					addInstance = arrayview[ijk]
					addInstance.add_one()

		for i in range(10):
			val += addition_classes[i].get_value()

		print "Value check. ", kkk, " of 9. sum of array: ", val
		val = 0

	return None
