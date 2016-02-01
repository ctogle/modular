# cython: profile=True
# cython: wraparound=False
# cython: boundscheck=False
# cython: nonecheck=False

cimport numpy as np
import numpy as np



__doc__ = '''fast versions of some common metrics'''



cdef double least_squares_c(double[:] fofy,double[:] y):
    cdef int x
    cdef int l = fofy.size
    cdef double dm
    cdef double m = 0.0
    for x in range(l):
        dm = fofy[x] - y[x]
        m = m + dm*dm
    return m

cpdef double least_squares(double[:] fofy,double[:] y):
    '''return the sum of the squared residuals between fofy and y'''
    return least_squares_c(fofy,y)





