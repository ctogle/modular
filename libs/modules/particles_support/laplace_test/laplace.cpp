#include <math.h>
#include <stdio.h>

double timestep(double *u,int nx,int ny,double dx,double dy)
{
  double tmp, err, diff,dx2,dy2,dnr_inv;
  dx2=dx*dx;
  dy2=dy*dy;
  dnr_inv=0.5/(dx2+dy2);
  err = 0.0;
  int i,j;

for (i=1; i<nx-1; ++i) {
  for (j=1; j<ny-1; ++j) {
    tmp = u[i*nx+j];
    u[i*nx+j] = ((u[(i-1)*nx+j] + u[(i+1)*nx+j])*dy2 +
          (u[i*nx+j-1] + u[i*nx+j+1])*dx2)*dnr_inv;
    diff = u[i*nx+j] - tmp;
    err += diff*diff;
  }
}

 return sqrt(err);
}

double solve_in_C(double *u,int nx,int ny,double dx,double dy)
{
  double err;
  int iter;
  iter = 0;
  err = 1;
    while(iter <10000 && err > 1e-6)
      {
    err=timestep(u,nx,ny,dx,dy);
    iter++;
      }

  return err;
}
