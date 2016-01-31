# cython: profile=True

cimport numpy as np
import numpy as np





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
    return least_squares_c(fofy,y)





