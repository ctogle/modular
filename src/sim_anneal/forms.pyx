# cython: profile=True
# cython: wraparound=False
# cython: boundscheck=False
# cython: nonecheck=False

cimport numpy as np
import numpy as np



__doc__ = '''fast versions of some common functions to fit with'''



#
# make an exponential class to avoid some computations?
#

cpdef exponential(x,float a,float b):
    '''compute a*e**(b*x)'''
    e = a*np.exp(b*x)
    return e

cpdef exponential_buffered(int i,np.ndarray[double,ndim = 1] x,np.ndarray[double,ndim = 1] buff,float a,float b):
    '''set buff = a*e**(b*x) where buff is an input'''
    cdef int j
    cdef double e = np.e
    for j in range(i):
        buff[j] = a*e**(x[j]*b)

cpdef bell(x,float m1,float s1,float a1):
    '''compute a1*e**(-0.5*((x-m1)/s1)**2)'''
    g = a1*np.exp(-0.5*((x-m1)/s1)**2)
    return g

cpdef bell_buffered(int i,np.ndarray[double,ndim = 1] x,np.ndarray[double,ndim = 1] buff,float m1,float s1,float a1):
    '''set buff = a1*e**(-0.5*((x-m1)/s1)**2) where buff is an input'''
    cdef int j
    cdef double e = np.e
    for j in range(i):
        buff[j] = a1*e**(-0.5*((x[j]-m1)/s1)**2)





