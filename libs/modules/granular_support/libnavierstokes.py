import libs.world3d_simulator.libopenglutilities as lgl
import libs.world3d_simulator.lib3dworld as l3d
import libs.modular_core.libmath as lm

import numpy as np
np.seterr(over='raise')

import pdb

if __name__ == 'libs.modules.granular_support.libnavierstokes':
	#if lfu.gui_pack is None: lfu.find_gui_pack()
	#lgm = lfu.gui_pack.lgm
	#lgb = lfu.gui_pack.lgb
	pass

if __name__ == '__main__': print 'this is a library!'

#need a class which accounts for all fluid regions
# need a fluid region class which handles a rectilinear 3-d region
#  each such region has 6 boundaries - some of which can be shared

class fluid_cell(l3d.cell):

	#a cell is a 3-d region scalar/vector fields can be calculated
	#it has a slice dictionary for accessing the proper sections 
	#	of the scalars/vectors for which it does calculation
	#each cell has 6 bounding planes, 
	#	each of which is open, closed, or periodic
	#the cell has methods for updating scalars/vectors

	def __init__(self, x, y, z, bbox1, bbox2):
		l3d.cell.__init__(self, x, y, z, 
			bbox1 = bbox1, bbox2 = bbox2)

	def _update_navier_stokes_vector(self): pass
	def _update_navier_stokes_scalar(self): pass

class bounding_plane(l3d.world_object):

	#a bounding plane is a 2-d region in 3-d space
	#it has a normal vector indicating to which basis vector
	#it has 2 2-d vectors indicating bbox relative to origin
	#	of 3-d space to which it is perpendicular
	#it is either open, closed, or periodic
	#	if its periodic, it contains a reference to another plane
	#	with which is is periodic - planes do NOT have to have the same normal even
	#bounding planes collect/maintain information about their flux
	#	both flux of fluid and particles

	def __init__(self, x, y, z, bbox1, bbox2):
		l3d.world_object.__init__(self, x, y, z, 
					bbox1 = bbox1, bbox2 = bbox2)

class the_medium(l3d.world_object):

	def __init__(self, x, y, z, bbox1, bbox2):
		l3d.world_object.__init__(self, x, y, z, 
					bbox1 = bbox1, bbox2 = bbox2)








class medium(object):

	#NEED TO SET 6 BOUNDARIES CONDITIONS
	# CREATE BOUNDARY PLANE OBJECTS AND APPEND TO SELF.BOUNDS
	# THIS SHOULD ALSO DETERMINE HOW BOUNDARIES ARE HANDLED
	#  AT RUNTIME
	# SPEC COMES IN AS:
	#	(periodic, periodic, closed, closed, closed, closed)
	##variable declarations

	def __init__(self, *args, **kwargs):
		self.space = kwargs['space']
		bbox1 = kwargs['bbox1']
		bbox2 = kwargs['bbox2']
		min_x,min_y,min_z = bbox1
		max_x,max_y,max_z = bbox2

		self.bounds = kwargs['bounds']
		self.bounds['x0'].append(min_x)
		self.bounds['x1'].append(max_x)
		self.bounds['y0'].append(min_y)
		self.bounds['y1'].append(max_y)
		self.bounds['z0'].append(min_z)
		self.bounds['z1'].append(max_z)

		self.nx  = kwargs['nx']
		self.ny  = kwargs['ny']
		self.nz  = kwargs['nz']
		self.nt  = kwargs['nt']
		self.nit = kwargs['nit']

		self.dx  = max_x/(self.nx-1)
		self.dy  = max_y/(self.ny-1)
		self.dz  = max_z/(self.nz-1)
		self.dt  = kwargs['dt']
		self.x   = np.linspace(min_x,max_x,self.nx)
		self.y   = np.linspace(min_y,max_y,self.ny)
		self.z   = np.linspace(min_z,max_z,self.nz)
		self.Y,self.X,self.Z = np.meshgrid(self.y,self.x,self.z)

		##physical variables
		self.rho = kwargs['rho']
		self.nu = kwargs['nu']
		self.F = kwargs['flow']

		#initial conditions
		self.u = np.zeros((self.nx,self.ny,self.nz),dtype=np.float16) ##create a XxY vector of 0's
		self.un = np.zeros((self.nx,self.ny,self.nz),dtype=np.float16) ##create a XxY vector of 0's

		self.v = np.zeros((self.nx,self.ny,self.nz),dtype=np.float16) ##create a XxY vector of 0's
		self.vn = np.zeros((self.nx,self.ny,self.nz),dtype=np.float16) ##create a XxY vector of 0's

		self.w = np.zeros((self.nx,self.ny,self.nz),dtype=np.float16) ##create a XxY vector of 0's
		self.wn = np.zeros((self.nx,self.ny,self.nz),dtype=np.float16) ##create a XxY vector of 0's

		self.p = np.ones((self.nx,self.ny,self.nz),dtype=np.float16) ##create a XxY vector of 0's
		self.pn = np.ones((self.nx,self.ny,self.nz),dtype=np.float16) ##create a XxY vector of 0's

		self.b = np.zeros((self.nx,self.ny,self.nz),dtype=np.float16)

		self.make_slices()
		self.make_boundaries()

	def make_slices(self):
		m_slice = slice(1,-1)
		b_slice = slice(0,-2)
		f_slice = slice(2,None)
		a_slice = slice(None,None)

		#0:-2,1:-1,1:-1

		mid_slice = (m_slice,m_slice,m_slice)
		back_slice_x = (b_slice,m_slice,m_slice)
		back_slice_y = (m_slice,b_slice,m_slice)
		back_slice_z = (m_slice,m_slice,b_slice)
		front_slice_x = (f_slice,m_slice,m_slice)
		front_slice_y = (m_slice,f_slice,m_slice)
		front_slice_z = (m_slice,m_slice,f_slice)

		mid_slice_x_fix0 = ( 0, m_slice, m_slice)
		mid_slice_x_fix1 = (-1, m_slice, m_slice)
		mid_slice_y_fix0 = (m_slice,  0, m_slice)
		mid_slice_y_fix1 = (m_slice, -1, m_slice)
		mid_slice_z_fix0 = (m_slice, m_slice,  0)
		mid_slice_z_fix1 = (m_slice, m_slice, -1)

		front_slice_x_fix0 = ( 0, f_slice, f_slice)
		front_slice_x_fix1 = (-1, f_slice, f_slice)
		front_slice_y_fix0 = (f_slice,  0, f_slice)
		front_slice_y_fix1 = (f_slice, -1, f_slice)
		front_slice_z_fix0 = (f_slice, f_slice,  0)
		front_slice_z_fix1 = (f_slice, f_slice, -1)

		back_slice_x_fix0 = ( 0, b_slice, b_slice)
		back_slice_x_fix1 = (-1, b_slice, b_slice)
		back_slice_y_fix0 = (b_slice,  0, b_slice)
		back_slice_y_fix1 = (b_slice, -1, b_slice)
		back_slice_z_fix0 = (b_slice, b_slice,  0)
		back_slice_z_fix1 = (b_slice, b_slice, -1)

		surf_slice_x_fix0 = ( 0, a_slice, a_slice)
		surf_slice_x_fix1 = (-1, a_slice, a_slice)
		surf_slice_y_fix0 = (a_slice,  0, a_slice)
		surf_slice_y_fix1 = (a_slice, -1, a_slice)
		surf_slice_z_fix0 = (a_slice, a_slice,  0)
		surf_slice_z_fix1 = (a_slice, a_slice, -1)

		self.slices3D = {
				'mid' : mid_slice, 
				'x' : (front_slice_x, back_slice_x, 
					front_slice_x_fix0, front_slice_x_fix1, 
					mid_slice_x_fix0, mid_slice_x_fix1, 
					back_slice_x_fix0, back_slice_x_fix1, 
					surf_slice_x_fix0, surf_slice_x_fix1, 
						self.dx), 
				'y' : (front_slice_y, back_slice_y, 
					front_slice_y_fix0, front_slice_y_fix1, 
					mid_slice_y_fix0, mid_slice_y_fix1, 
					back_slice_y_fix0, back_slice_y_fix1, 
					surf_slice_y_fix0, surf_slice_y_fix1, 
						self.dy), 
				'z' : (front_slice_z, back_slice_z, 
					front_slice_z_fix0, front_slice_z_fix1, 
					mid_slice_z_fix0, mid_slice_z_fix1, 
					back_slice_z_fix0, back_slice_z_fix1, 
					surf_slice_z_fix0, surf_slice_z_fix1, 
						self.dz), 
						}

	def make_boundaries(self):
		for c in ['x','y','z']:
			for n in ['0','1']:
				bnd = self.bounds[c+n]
				if bnd[0] == 'periodic':
					if int(n): bnd.append(self.per_bnd_R)
					else: self.bounds[c+n].append(self.per_bnd_L)

				elif bnd[0] == 'closed':
					if int(n): bnd.append(self.clo_bnd_R)
					else: self.bounds[c+n].append(self.clo_bnd_L)

				elif bnd[0] == 'open':
					if int(n): bnd.append(self.ope_bnd_R)
					else: self.bounds[c+n].append(self.ope_bnd_L)

	def average_velocity_over_granule(self, gran):
		pos = gran.body.getPosition()
		bb1, bb2 = self.get_bbox_corners()
		if not lm.in_bbox(bb1, bb2, pos):
			return np.array([0, 0, 0])

		#center_velocity = 
		#pdb.set_trace()
		return np.array([self.u.mean(), self.v.mean(), self.w.mean()])

	def get_bbox_corners(self):
		x0, y0, z0 = self.x[ 0], self.y[ 0], self.z[ 0]
		x1, y1, z1 = self.x[-1], self.y[-1], self.z[-1]
		return [x0, y0, z0], [x1, y1, z1]

	def get_center(self):
		mid_x = lm.mid(self.x)
		mid_y = lm.mid(self.y)
		mid_z = lm.mid(self.z)
		return [mid_x, mid_y, mid_z]

	def solve_vel_comp(self, c, cn, dt, comp, fc = 0.0):
		mid_ = self.slices3D['mid']
		front_ = self.slices3D[comp][0]
		back_ = self.slices3D[comp][1]
		dcomp_ = self.slices3D[comp][-1]
		front_x = self.slices3D['x'][0]
		back_x = self.slices3D['x'][1]
		front_y = self.slices3D['y'][0]
		back_y = self.slices3D['y'][1]
		front_z = self.slices3D['z'][0]
		back_z = self.slices3D['z'][1]
		dtdx, dtdy, dtdz = dt/self.dx, dt/self.dy, dt/self.dz
		p = self.p
		c[mid_] = cn[mid_]-\
			self.un[mid_]*dtdx*(cn[mid_]-cn[back_x])-\
			self.vn[mid_]*dtdy*(cn[mid_]-cn[back_y])-\
			self.wn[mid_]*dtdz*(cn[mid_]-cn[back_z])-\
			dt/(2*self.rho*dcomp_)*(p[front_]-p[back_])+\
			self.nu*\
			( dtdx**2*(cn[front_x]-2*cn[mid_]+cn[back_x])  +\
			  dtdy**2*(cn[front_y]-2*cn[mid_]+cn[back_y])  +\
			  dtdz**2*(cn[front_z]-2*cn[mid_]+cn[back_z]) )+\
			fc*dt

		'''
		all 3-d ranges used
		1:-1,1:-1,1:-1

		you can move an axis forward or backwards
		 you can do this with each of 3 axes
		0:-2,1:-1,1:-1
		2:  ,1:-1,1:-1

		1:-1,0:-2,1:-1
		1:-1,2:  ,1:-1

		1:-1,1:-1,0:-2
		1:-1,1:-1,2:  

		all other possibles are generated by 
		 picking one of the above 7 possible slices			what would have gone there
		 picking an axis									on which axis is the boundary being evaluated
		 fixing the axis at either upper or lower limit		on which side of the axis is the boundary being evaluated

		at this point every slice is either -2, -1, 0, 1, 2, None
		 surface slices fix any of 3 axes
		 at any of these values
		show this just for x
		-2,1:-1,1:-1
		-1,1:-1,1:-1
		 0,1:-1,1:-1
		 1,1:-1,1:-1
		 2,1:-1,1:-1
		'''
		'''
		computation of velocity for 3-d space - simplest
			u[1:-1,1:-1,1:-1] = un[1:-1,1:-1,1:-1]-\
				un[1:-1,1:-1,1:-1]*dt/dx*(un[1:-1,1:-1,1:-1]-un[0:-2,1:-1,1:-1])-\
				vn[1:-1,1:-1,1:-1]*dt/dy*(un[1:-1,1:-1,1:-1]-un[1:-1,0:-2,1:-1])-\
				wn[1:-1,1:-1,1:-1]*dt/dz*(un[1:-1,1:-1,1:-1]-un[1:-1,1:-1,0:-2])-\
				dt/(2*rho*dx)*(p[2:,1:-1,1:-1]-p[0:-2,1:-1,1:-1])+nu*\
				(dt/dx**2*(un[2:,1:-1,1:-1]-2*un[1:-1,1:-1,1:-1]+un[0:-2,1:-1,1:-1])+\
				dt/dy**2*(un[1:-1,2:,1:-1]-2*un[1:-1,1:-1,1:-1]+un[1:-1,0:-2,1:-1])+\
				dt/dz**2*(un[1:-1,1:-1,2:]-2*un[1:-1,1:-1,1:-1]+un[1:-1,1:-1,0:-2]))+\
				Fu*dt
		'''

	'''
		self.slices3D = {
				'mid' : mid_slice, 
				'x' : (front_slice_x, back_slice_x, 
					front_slice_x_fix0, front_slice_x_fix1, 
					mid_slice_x_fix0, mid_slice_x_fix1, 
					back_slice_x_fix0, back_slice_x_fix1, 
					surf_slice_x_fix0, surf_slice_x_fix1, 
						self.dx), 
				'y' : (front_slice_y, back_slice_y, 
					front_slice_y_fix0, front_slice_y_fix1, 
					mid_slice_y_fix0, mid_slice_y_fix1, 
					back_slice_y_fix0, back_slice_y_fix1, 
					surf_slice_y_fix0, surf_slice_y_fix1, 
						self.dy), 
				'z' : (front_slice_z, back_slice_z, 
					front_slice_z_fix0, front_slice_z_fix1, 
					mid_slice_z_fix0, mid_slice_z_fix1, 
					back_slice_z_fix0, back_slice_z_fix1, 
					surf_slice_z_fix0, surf_slice_z_fix1, 
						self.dz), 
						}
	'''

	def per_bnd_R(self, c, cn, dt, comp, fc):
		mid_ = self.slices3D[comp][5]
		dcomp_ = self.slices3D[comp][-1]
		dtdx, dtdy, dtdz = dt/self.dx, dt/self.dy, dt/self.dz
		p = self.p

		#c[mid_] = cn[mid_]-\
		#	self.un[1:-1,1:-1,1:-1]*dtdx*(cn[1:-1,1:-1,1:-1]-cn[0:-2,1:-1,1:-1])-\
		#	self.vn[1:-1,1:-1,1:-1]*dtdy*(cn[1:-1,1:-1,1:-1]-cn[1:-1,0:-2,1:-1])-\
		#	self.wn[1:-1,1:-1,1:-1]*dtdz*(cn[1:-1,1:-1,1:-1]-cn[1:-1,1:-1,0:-2])-\
		c[mid_] = cn[mid_]-\
			self.un[mid_]*dtdx*(cn[mid_]-cn[-2,1:-1,1:-1])-\
			self.vn[mid_]*dtdy*(cn[mid_]-cn[-1,0:-2,1:-1])-\
			self.wn[mid_]*dtdz*(cn[mid_]-cn[-1,1:-1,0:-2])-\
			dt/(2*self.rho*dcomp_)*(p[0,1:-1,1:-1]-p[-2,1:-1,1:-1])+\
			self.nu*\
			( dtdx**2*(cn[0,1:-1,1:-1]-2*cn[mid_]+cn[-2,1:-1,1:-1] )+\
			  dtdy**2*(cn[-1,2:,1:-1]-2*cn[mid_]+cn[-1,0:-2,1:-1]  )+\
			  dtdz**2*(cn[-1,1:-1,2:]-2*cn[mid_]+cn[-1,1:-1,0:-2] ))+\
			fc*dt

	def per_bnd_L(self, c, cn, dt, comp, fc):
		mid_ = self.slices3D[comp][4]
		dcomp_ = self.slices3D[comp][-1]
		dtdx, dtdy, dtdz = dt/self.dx, dt/self.dy, dt/self.dz
		p = self.p
		c[mid_] = cn[mid_]-\
			self.un[mid_]*dtdx*(cn[mid_]-cn[-1,1:-1,1:-1])-\
			self.vn[mid_]*dtdy*(cn[mid_]-cn[0,0:-2,1:-1])-\
			self.wn[mid_]*dtdz*(cn[mid_]-cn[0,1:-1,0:-2])-\
			dt/(2*self.rho*dcomp_)*(p[0,1:-1,1:-1]-p[-2,1:-1,1:-1])+\
			self.nu*\
			( dtdx**2*(cn[1,1:-1,1:-1]-2*cn[mid_]+cn[-1,1:-1,1:-1] )+\
			  dtdy**2*(cn[0,2:,1:-1]-2*cn[mid_]+cn[0,0:-2,1:-1]  )+\
			  dtdz**2*(cn[0,1:-1,2:]-2*cn[mid_]+cn[0,1:-1,0:-2] ))+\
			fc*dt

	def clo_bnd_R(self, c, cn, dt, comp, fc):
		sli = self.slices3D[comp][9]
		c[sli] = 0

	def clo_bnd_L(self, c, cn, dt, comp, fc):
		sli = self.slices3D[comp][8]
		c[sli] = 0

	def ope_bnd_L(self, c, cn, dt, comp, fc): print 'open boundary unimplemented'
	def ope_bnd_R(self, c, cn, dt, comp, fc): print 'open boundary unimplemented'

	def progress(self, *args, **kwargs):
		u, un = self.u, self.un
		v, vn = self.v, self.vn
		w, wn = self.w, self.wn
		dx, dy, dz, dt = self.dx, self.dy, self.dz, self.dt
		Fu, Fv, Fw = self.F

		udiff = 1
		stepcount = 0
		while udiff > 0.05:
			un = u.copy()
			vn = v.copy()
			wn = w.copy()
			self.b = self.build_b(dt, dx, dy, dz, u, v, w)
			self.p = self.pres_poiss(dx, dy, dz)

			self.solve_vel_comp(u, un, dt, 'x', Fu)
			self.solve_vel_comp(v, vn, dt, 'y', Fv)
			self.solve_vel_comp(w, wn, dt, 'z', Fw)

			self.bounds['x0'][2](u, un, dt, 'x', Fu)
			self.bounds['x0'][2](v, vn, dt, 'x', Fv)
			self.bounds['x0'][2](w, wn, dt, 'x', Fw)
			self.bounds['x1'][2](u, un, dt, 'x', Fu)
			self.bounds['x1'][2](v, vn, dt, 'x', Fv)
			self.bounds['x1'][2](w, wn, dt, 'x', Fw)

			self.bounds['y0'][2](u, un, dt, 'y', Fu)
			self.bounds['y0'][2](v, vn, dt, 'y', Fv)
			self.bounds['y0'][2](w, wn, dt, 'y', Fw)
			self.bounds['y1'][2](u, un, dt, 'y', Fu)
			self.bounds['y1'][2](v, vn, dt, 'y', Fv)
			self.bounds['y1'][2](w, wn, dt, 'y', Fw)

			self.bounds['z0'][2](u, un, dt, 'z', Fu)
			self.bounds['z0'][2](v, vn, dt, 'z', Fv)
			self.bounds['z0'][2](w, wn, dt, 'z', Fw)
			self.bounds['z1'][2](u, un, dt, 'z', Fu)
			self.bounds['z1'][2](v, vn, dt, 'z', Fv)
			self.bounds['z1'][2](w, wn, dt, 'z', Fw)

			'''
			u[1:-1,1:-1,1:-1] = un[1:-1,1:-1,1:-1]-\
				un[1:-1,1:-1,1:-1]*dt/dx*(un[1:-1,1:-1,1:-1]-un[0:-2,1:-1,1:-1])-\
				vn[1:-1,1:-1,1:-1]*dt/dy*(un[1:-1,1:-1,1:-1]-un[1:-1,0:-2,1:-1])-\
				wn[1:-1,1:-1,1:-1]*dt/dz*(un[1:-1,1:-1,1:-1]-un[1:-1,1:-1,0:-2])-\
				dt/(2*rho*dx)*(p[2:,1:-1,1:-1]-p[0:-2,1:-1,1:-1])+nu*\
				(dt/dx**2*(un[2:,1:-1,1:-1]-2*un[1:-1,1:-1,1:-1]+un[0:-2,1:-1,1:-1])+\
				dt/dy**2*(un[1:-1,2:,1:-1]-2*un[1:-1,1:-1,1:-1]+un[1:-1,0:-2,1:-1])+\
				dt/dz**2*(un[1:-1,1:-1,2:]-2*un[1:-1,1:-1,1:-1]+un[1:-1,1:-1,0:-2]))+\
				Fu*dt
			v[1:-1,1:-1,1:-1] = vn[1:-1,1:-1,1:-1]-\
				un[1:-1,1:-1,1:-1]*dt/dx*(vn[1:-1,1:-1,1:-1]-vn[0:-2,1:-1,1:-1])-\
				vn[1:-1,1:-1,1:-1]*dt/dy*(vn[1:-1,1:-1,1:-1]-vn[1:-1,0:-2,1:-1])-\
				wn[1:-1,1:-1,1:-1]*dt/dz*(vn[1:-1,1:-1,1:-1]-vn[1:-1,1:-1,0:-2])-\
				dt/(2*rho*dy)*(p[1:-1,2:,1:-1]-p[1:-1,0:-2,1:-1])+nu*\
				(dt/dx**2*(vn[2:,1:-1,1:-1]-2*vn[1:-1,1:-1,1:-1]+vn[0:-2,1:-1,1:-1])+\
				dt/dy**2*(vn[1:-1,2:,1:-1]-2*vn[1:-1,1:-1,1:-1]+vn[1:-1,0:-2,1:-1])+\
				dt/dz**2*(vn[1:-1,1:-1,2:]-2*vn[1:-1,1:-1,1:-1]+vn[1:-1,1:-1,0:-2]))+\
				Fv*dt
			w[1:-1,1:-1,1:-1] = wn[1:-1,1:-1,1:-1]-\
				un[1:-1,1:-1,1:-1]*dt/dx*(wn[1:-1,1:-1,1:-1]-wn[0:-2,1:-1,1:-1])-\
				vn[1:-1,1:-1,1:-1]*dt/dy*(wn[1:-1,1:-1,1:-1]-wn[1:-1,0:-2,1:-1])-\
				wn[1:-1,1:-1,1:-1]*dt/dz*(wn[1:-1,1:-1,1:-1]-wn[1:-1,1:-1,0:-2])-\
				dt/(2*rho*dz)*(p[1:-1,1:-1,2:]-p[1:-1,1:-1,0:-2])+nu*\
				(dt/dx**2*(wn[2:,1:-1,1:-1]-2*wn[1:-1,1:-1,1:-1]+wn[0:-2,1:-1,1:-1])+\
				dt/dy**2*(wn[1:-1,2:,1:-1]-2*wn[1:-1,1:-1,1:-1]+wn[1:-1,0:-2,1:-1])+\
				dt/dz**2*(wn[1:-1,1:-1,2:]-2*wn[1:-1,1:-1,1:-1]+wn[1:-1,1:-1,0:-2]))+\
				Fw*dt
			'''
			'''
			####Periodic BC u @ x = 2
			u[-1,1:-1,1:-1] = un[-1,1:-1,1:-1]-\
				un[-1,1:-1,1:-1]*dt/dx*(un[-1,1:-1,1:-1]-un[-2,1:-1,1:-1])-\
				vn[-1,1:-1,1:-1]*dt/dy*(un[-1,1:-1,1:-1]-un[-1,0:-2,1:-1])-\
				wn[-1,1:-1,1:-1]*dt/dz*(un[-1,1:-1,1:-1]-un[-1,1:-1,0:-2])-\
				dt/(2*rho*dx)*(p[0,1:-1,1:-1]-p[-2,1:-1,1:-1])+nu*\
				(dt/dx**2*(un[0,1:-1,1:-1]-2*un[-1,1:-1,1:-1]+un[-2,1:-1,1:-1])+\
				dt/dy**2*(un[-1,2:,1:-1]-2*un[-1,1:-1,1:-1]+un[-1,0:-2,1:-1])+\
				dt/dz**2*(un[-1,1:-1,2:]-2*un[-1,1:-1,1:-1]+un[-1,1:-1,0:-2]))+\
				Fu*dt
			####Periodic BC u @ x = 0
			u[0,1:-1,1:-1] = un[0,1:-1,1:-1]-\
				un[0,1:-1,1:-1]*dt/dx*(un[0,1:-1,1:-1]-un[-1,1:-1,1:-1])-\
				vn[0,1:-1,1:-1]*dt/dy*(un[0,1:-1,1:-1]-un[0,0:-2,1:-1])-\
				wn[0,1:-1,1:-1]*dt/dz*(un[0,1:-1,1:-1]-un[0,1:-1,0:-2])-\
				dt/(2*rho*dx)*(p[1,1:-1,1:-1]-p[-1,1:-1,1:-1])+nu*\
				(dt/dx**2*(un[1,1:-1,1:-1]-2*un[0,1:-1,1:-1]+un[-1,1:-1,1:-1])+\
				dt/dy**2*(un[0,2:,1:-1]-2*un[0,1:-1,1:-1]+un[0,0:-2,1:-1])+\
				dt/dz**2*(un[0,1:-1,2:]-2*un[0,1:-1,1:-1]+un[0,1:-1,0:-2]))+\
				Fu*dt
			####Periodic BC u @ x = 2
			v[-1,1:-1,1:-1] = vn[-1,1:-1,1:-1]-\
				un[-1,1:-1,1:-1]*dt/dx*(vn[-1,1:-1,1:-1]-vn[-2,1:-1,1:-1])-\
				vn[-1,1:-1,1:-1]*dt/dy*(vn[-1,1:-1,1:-1]-vn[-1,0:-2,1:-1])-\
				wn[-1,1:-1,1:-1]*dt/dz*(vn[-1,1:-1,1:-1]-vn[-1,1:-1,0:-2])-\
				dt/(2*rho*dy)*(p[0,1:-1,1:-1]-p[-2,1:-1,1:-1])+nu*\
				(dt/dx**2*(vn[0,1:-1,1:-1]-2*vn[-1,1:-1,1:-1]+vn[-2,1:-1,1:-1])+\
				dt/dy**2*(vn[-1,2:,1:-1]-2*vn[-1,1:-1,1:-1]+vn[-1,0:-2,1:-1])+\
				dt/dz**2*(vn[-1,1:-1,2:]-2*vn[-1,1:-1,1:-1]+vn[-1,1:-1,0:-2]))+\
				Fv*dt
			####Periodic BC u @ x = 0
			v[0,1:-1,1:-1] = vn[0,1:-1,1:-1]-\
				un[0,1:-1,1:-1]*dt/dx*(vn[0,1:-1,1:-1]-vn[-1,1:-1,1:-1])-\
				vn[0,1:-1,1:-1]*dt/dy*(vn[0,1:-1,1:-1]-vn[0,0:-2,1:-1])-\
				wn[0,1:-1,1:-1]*dt/dz*(vn[0,1:-1,1:-1]-vn[0,1:-1,0:-2])-\
				dt/(2*rho*dy)*(p[1,1:-1,1:-1]-p[-1,1:-1,1:-1])+nu*\
				(dt/dx**2*(vn[1,1:-1,1:-1]-2*vn[0,1:-1,1:-1]+vn[-1,1:-1,1:-1])+\
				dt/dy**2*(vn[0,2:,1:-1]-2*vn[0,1:-1,1:-1]+vn[0,0:-2,1:-1])+\
				dt/dz**2*(vn[0,1:-1,2:]-2*vn[0,1:-1,1:-1]+vn[0,1:-1,0:-2]))+\
				Fv*dt
			####Periodic BC u @ x = 2
			w[-1,1:-1,1:-1] = wn[-1,1:-1,1:-1]-\
				un[-1,1:-1,1:-1]*dt/dx*(wn[-1,1:-1,1:-1]-wn[-2,1:-1,1:-1])-\
				vn[-1,1:-1,1:-1]*dt/dy*(wn[-1,1:-1,1:-1]-wn[-1,0:-2,1:-1])-\
				wn[-1,1:-1,1:-1]*dt/dz*(wn[-1,1:-1,1:-1]-wn[-1,1:-1,0:-2])-\
				dt/(2*rho*dz)*(p[0,1:-1,1:-1]-p[-2,1:-1,1:-1])+nu*\
				(dt/dx**2*(wn[0,1:-1,1:-1]-2*wn[-1,1:-1,1:-1]+wn[-2,1:-1,1:-1])+\
				dt/dy**2*(wn[-1,2:,1:-1]-2*wn[-1,1:-1,1:-1]+wn[-1,0:-2,1:-1])+\
				dt/dz**2*(wn[-1,1:-1,2:]-2*wn[-1,1:-1,1:-1]+wn[-1,1:-1,0:-2]))+\
				Fw*dt
			####Periodic BC u @ x = 0
			w[0,1:-1,1:-1] = wn[0,1:-1,1:-1]-\
				un[0,1:-1,1:-1]*dt/dx*(wn[0,1:-1,1:-1]-wn[-1,1:-1,1:-1])-\
				vn[0,1:-1,1:-1]*dt/dy*(wn[0,1:-1,1:-1]-wn[0,0:-2,1:-1])-\
				wn[0,1:-1,1:-1]*dt/dz*(wn[0,1:-1,1:-1]-wn[0,1:-1,0:-2])-\
				dt/(2*rho*dz)*(p[1,1:-1,1:-1]-p[-1,1:-1,1:-1])+nu*\
				(dt/dx**2*(wn[1,1:-1,1:-1]-2*wn[0,1:-1,1:-1]+wn[-1,1:-1,1:-1])+\
				dt/dy**2*(wn[0,2:,1:-1]-2*wn[0,1:-1,1:-1]+wn[0,0:-2,1:-1])+\
				dt/dz**2*(wn[0,1:-1,2:]-2*wn[0,1:-1,1:-1]+wn[0,1:-1,0:-2]))+\
				Fw*dt
			'''
			'''
			####Wall BC: u,v = 0 @ y = 0,2
			u[:,0,:] = 0
			u[:,-1,:] = 0
			v[:,0,:] = 0
			v[:,-1,:] = 0
			w[:,0,:] = 0
			w[:,-1,:] = 0

			####Wall BC: u,v = 0 @ z = 0,2
			u[:,:,0] = 0
			u[:,:,-1] = 0
			v[:,:,0] = 0
			v[:,:,-1] = 0
			w[:,:,0] = 0
			w[:,:,-1] = 0
			'''

			udiff = (np.sum(u)-np.sum(un))/np.sum(u)
			stepcount += 1

		if stepcount > 1: print 'progress steps', stepcount

	def build_b(self, dt, dx, dy, dz, u, v, w):
		b = np.zeros_like(u)

		poweredx = ((u[2:,1:-1,1:-1]-u[0:-2,1:-1,1:-1])/(2*dx))**2
		poweredy = ((v[1:-1,2:,1:-1]-v[1:-1,0:-2,1:-1])/(2*dy))**2
		poweredz = ((w[1:-1,1:-1,2:]-w[1:-1,1:-1,0:-2])/(2*dz))**2
		powered = poweredx + poweredy + poweredz
		b[1:-1,1:-1,1:-1]=\
			self.rho*(1/dt*\
					((u[2:,1:-1,1:-1]-u[0:-2,1:-1,1:-1])/(2*dx) +\
					( v[1:-1,2:,1:-1]-v[1:-1,0:-2,1:-1])/(2*dy) +\
					( w[1:-1,1:-1,2:]-w[1:-1,1:-1,0:-2])/(2*dz))-\
				powered-\
				2*((u[1:-1,2:,1:-1]-u[1:-1,0:-2,1:-1])/(2*dy))*\
					((v[2:,1:-1,1:-1]-v[0:-2,1:-1,1:-1])/(2*dx))-\
				2*((v[1:-1,1:-1,2:]-v[1:-1,1:-1,0:-2])/(2*dz))*\
					((w[1:-1,2:,1:-1]-w[1:-1,0:-2,1:-1])/(2*dy))-\
				2*((w[2:,1:-1,1:-1]-w[0:-2,1:-1,1:-1])/(2*dx))*\
					((u[1:-1,1:-1,2:]-u[1:-1,1:-1,0:-2])/(2*dz)))

		####Periodic BC Pressure @ x = 2
		b[-1,1:-1,1:-1]=self.rho*(1/dt*(
			(u[0,1:-1,1:-1]-u[-2,1:-1,1:-1])/(2*dx)+\
			(v[-1,2:,1:-1]-v[-1,0:-2,1:-1])/(2*dy)+\
			(w[-1,1:-1,2:]-w[-1,1:-1,0:-2])/(2*dz))-\
				((u[0,1:-1,1:-1]-u[-2,1:-1,1:-1])/(2*dx))**2-\
				((v[-1,2:,1:-1]-v[-1,0:-2,1:-1])/(2*dy))**2-\
				((w[-1,1:-1,2:]-w[-1,1:-1,0:-2])/(2*dz))**2-\
				2*((u[-1,2:,1:-1]-u[-1,0:-2,1:-1])/(2*dy))*((v[0,1:-1,1:-1]-v[-2,1:-1,1:-1])/(2*dx))-\
				2*((v[-1,1:-1,2:]-v[-1,1:-1,0:-2])/(2*dz))*((w[-1,2:,1:-1]-w[-1,0:-2,1:-1])/(2*dy))-\
				2*((w[0,1:-1,1:-1]-w[-2,1:-1,1:-1])/(2*dx))*((u[-1,1:-1,2:]-u[-1,1:-1,0:-2])/(2*dz)))	

		####Periodic BC Pressure @ x = 0
		b[0,1:-1,1:-1]=self.rho*(1/dt*(
			(u[1,1:-1,1:-1]-u[-1,1:-1,1:-1])/(2*dx)+\
			(v[0,2:,1:-1]-v[0,0:-2,1:-1])/(2*dy)+\
			(w[0,1:-1,2:]-w[0,1:-1,0:-2])/(2*dz))-\
				((u[1,1:-1,1:-1]-u[-1,1:-1,1:-1])/(2*dx))**2-\
				((v[0,2:,1:-1]-v[0,0:-2,1:-1])/(2*dy))**2-\
				((w[0,1:-1,2:]-w[0,1:-1,0:-2])/(2*dz))**2-\
				2*((u[0,2:,1:-1]-u[0,0:-2,1:-1])/(2*dy))*((v[1,1:-1,1:-1]-v[-1,1:-1,1:-1])/(2*dx))-\
				2*((v[0,1:-1,2:]-v[0,1:-1,0:-2])/(2*dz))*((w[0,2:,1:-1]-w[0,0:-2,1:-1])/(2*dy))-\
				2*((w[1,1:-1,1:-1]-w[-1,1:-1,1:-1])/(2*dx))*((u[0,1:-1,2:]-w[0,1:-1,0:-2])/(2*dz)))

		return b

	def pres_poiss(self, dx, dy, dz):
		p = self.p
		pn = np.empty_like(p)

		for q in range(self.nit):
			pn[:]=p[:]
			p[1:-1,1:-1,1:-1] = (
				(pn[2:,1:-1,1:-1]+pn[0:-2,1:-1,1:-1])*(dy**2)*(dz**2)+\
				(pn[1:-1,2:,1:-1]+pn[1:-1,0:-2,1:-1])*(dx**2)*(dz**2)+\
				(pn[1:-1,1:-1,2:]+pn[1:-1,1:-1,0:-2])*(dy**2)*(dx**2)-\
					(dx**2)*(dy**2)*(dz**2)*self.b[1:-1,1:-1,1:-1])/\
						(2*(dx**2+dy**2+dz**2))

			####Periodic BC Pressure @ x = 2
			p[-1,1:-1,1:-1] = (
				(pn[0,1:-1,1:-1]+pn[-2,1:-1,1:-1])*(dy**2)*(dz**2)+\
				(pn[-1,2:,1:-1]+pn[-1,0:-2,1:-1])*(dx**2)*(dz**2)+\
				(pn[-1,1:-1,2:]+pn[-1,1:-1,0:-2])*(dy**2)*(dx**2)-\
					(dx**2)*(dy**2)*(dz**2)*self.b[-1,1:-1,1:-1])/\
						(2*(dx**2+dy**2+dz**2))

			####Periodic BC Pressure @ x = 0
			p[0,1:-1,1:-1] = (
				(pn[1,1:-1,1:-1]+pn[-1,1:-1,1:-1])*(dy**2)*(dz**2)+\
				(pn[0,2:,1:-1]+pn[0,0:-2,1:-1])*(dx**2)*(dz**2)+\
				(pn[0,1:-1,2:]+pn[0,1:-1,0:-2])*(dy**2)*(dx**2)-\
					(dx**2)*(dy**2)*(dz**2)*self.b[0,1:-1,1:-1])/\
						(2*(dx**2+dy**2+dz**2))

			####Wall boundary conditions, pressure

			####Closed BC Pressure @ y = 0 & y = 2
			p[:, 0,:] = p[:, 1,:]	##dp/dy = 0 at y = 0
			p[:,-1,:] = p[:,-2,:]	##dp/dy = 0 at y = 2

			####Closed BC Pressure @ z = 0 & z = 2
			p[:,:, 0] = p[:,:, 1]	##dp/dz = 0 at z = 0
			p[:,:,-1] = p[:,:,-2]	##dp/dz = 0 at z = 2

		return p

	def draw_gl(self, every_other = 2):
		x, y, z = (
			self.x[::every_other], 
			self.y[::every_other], 
			self.z[::every_other])
		u, v, w = (
			self.u[::every_other,::every_other,::every_other], 
			self.v[::every_other,::every_other,::every_other], 
			self.w[::every_other,::every_other,::every_other])
		lgl.draw_arrow_field(x, y, z, u, v, w)

class plane_boundary(object):

	#NEED A CLASS WHICH REPRESENTS A BOUNDARY
	# CAN BE OPEN, CLOSED, OR PERIODIC
	#  SHOULD RECORD FLUX THROUGH SURFACE IF NOT CLOSED
	#  SHOULD DRAW RECTANGLE IF CLOSED

	def __init__(self, *args, **kwargs):
		self.space = kwargs['space']
		self.n, self.d = kwargs['n'], kwargs['d']
		self.v1, self.v2 = (0, 0), (5, 5)
		self.geom = ode.GeomPlane(self.space, self.n, self.d)
		self.geom.bound = self

	def draw_gl(self):
		lgl.draw_rectangle(self.v1, self.v2, 
			self.d, self.n, color = (0.1, 0.1, 0.1))












