
from ctypes import *

import os
import numpy as np
import pdb

laplace=CDLL(os.path.join(os.getcwd(), 'laplace.so'))
laplace.timestep.restype=c_double
laplace.solve_in_C.restype=c_double
import numpy
u=numpy.zeros((51,51),dtype=float)
pi_c=float(np.pi)
x=numpy.arange(0,pi_c+pi_c/50,pi_c/50,dtype=float)
u[0,:]=numpy.sin(x)
u[50,:]=numpy.sin(x)

def solve(u):
  iter =0
  err = 2
  n=c_int(int(51))
  pi_c=float(np.pi/50)
  dx=c_double(pi_c)
  while(iter <5000 and err>1e-6):
     err=laplace.timestep(u.ctypes.data_as(c_void_p),n,n,dx,dx)
     iter+=1
     if(iter %50==0):
        print((err,iter))
  return (u,err,iter)

pdb.set_trace()
