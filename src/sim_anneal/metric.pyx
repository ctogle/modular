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

cdef double least_squares_2d_c(np.ndarray[double,ndim = 2] fofy,np.ndarray[double,ndim = 2] y):
    cdef int i
    cdef int j
    cdef int t
    cdef int l
    cdef double dm
    cdef double m = 0.0
    t = fofy.shape[0]
    l = fofy.shape[1]
    for i in range(t):
        for j in range(l):
            dm = fofy[i,j] - y[i,j]
            m = m + dm*dm
    return m

cpdef double least_squares_2d(np.ndarray[double,ndim = 2] fofy,np.ndarray[double,ndim = 2] y):
    '''
    return the sum of the squared residuals between fofy and y 
    where fofy and y are of dimension 2
    '''
    return least_squares_2d_c(fofy,y)





