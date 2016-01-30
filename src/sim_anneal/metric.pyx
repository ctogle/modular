# cython: profile=True

cimport numpy as np
import numpy as np



cpdef least_squares(fofy,y):
    #m = (fofy - y)**2
    m = np.zeros(fofy.shape,dtype = np.float)
    for x in range(fofy.size):
        m[x] = (fofy[x] - y[x])*(fofy[x] - y[x])       
    return m



