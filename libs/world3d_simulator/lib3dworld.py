import libs.modular_core.libfundamental as lfu
import libs.modular_core.libmath as lm

#import libs.world3d_simulator.libodesim as los
import libs.world3d_simulator.libopenglutilities as lgl

import cgkit.cgtypes as cgt
import numpy as np
import math, time, sys, traceback

import pdb

#class world_object(lgl.node):
class world_object(object):

	#a world object is to be used in simulation
	# to interface - a proxy class should be used
	# hence it inherits form object and lfu.modular_object

	#a world object has an origin and
	# methods relating to global position
	#it also has 2 3-d vectors indicating a bounding box
	#it has a world scale matrix
	#	this matrix relates its geometry to the world

	_draw_origin_ = True

	def __init__(self, x, y, z, sx = 1, sy = 1, sz = 1, 
				bbox1 = [0, 0, 0], bbox2 = [0, 0, 0], 
				children = None, shader = None, parent = None):
		self._set_position_(x, y, z)
		self._set_scales_(sx, sy, sz)
		self._set_bbox_local_(bbox1, bbox2)
		#lgl.node.__init__(self, self.draw_gl)
		self.parent = parent
		if children is None: self.children = []
		else: self.children = children
		if not shader is None:
			self._set_shader_callbacks_(shader)

	def _get_shader_callbacks_(self, shader): return {}
	def _set_shader_callbacks_(self, shader, callbacks = None):
		if not callbacks is None: self.shader_callbacks = callbacks
		else:
			self.shader_callbacks =\
				self._get_shader_callbacks_(shader)

	def _get_center_(self):
		x_ = np.mean([self.bbox1[0], self.bbox2[0]])
		y_ = np.mean([self.bbox1[1], self.bbox2[1]])
		z_ = np.mean([self.bbox1[2], self.bbox2[2]])
		#return np.array([x_, y_, z_])
		return cgt.vec3([x_, y_, z_])

	def _get_extents_(self):
		l = self.bbox2[0] - self.bbox1[0]
		w = self.bbox2[1] - self.bbox1[1]
		h = self.bbox2[2] - self.bbox1[2]
		#return np.array([l, w, h])
		return cgt.vec3([l, w, h])

	def _get_position_(self):
		#return np.array([self._x, self._y, self._z])
		return cgt.vec3([self._x, self._y, self._z])

	def _set_position_(self, x, y, z):
		self._x = x
		self._y = y
		self._z = z

	def _get_scales_(self):
		return np.array([self.sx, self.sy, self.sz])

	def _set_scales_(self, sx, sy, sz):
		self.sx = sx
		self.sy = sy
		self.sz = sz

	def _get_bbox_local_(self):
		return (self.bbox1, self.bbox2)

	def _set_bbox_local_(self, bbox1, bbox2):
		self.bbox1 = np.array(bbox1)
		self.bbox2 = np.array(bbox2)

	def _get_bbox_global_(self):
		pos = self._get_position_()
		bb1 = self.bbox1 + pos
		bb2 = self.bbox2 + pos
		return (bb1, bb2)

	def _hide_origin_(self):
		self._draw_origin_ = False

	def _show_origin_(self):
		self._draw_origin_ = True

	def _update_(self): pass
	def draw_gl(self, shader = None):
		[child.draw_gl(shader) for child in self.children]
		if self._draw_origin_:
			pos = self._get_position_()
			lgl.draw_dot(x = pos[0], y = pos[1], z = pos[2], 
										color = (0, 1, 0))

class axes(world_object):
	def __init__(self, x = 0, y = 0, z = 0, shader = None):
		world_object.__init__(self, x, y, z, shader = shader)
		self._set_geometry_()

	def _set_geometry_(self):
		vrt, nrm, orgs = lgl.get_primitive('axes')
		vrt_vbo = lgl.get_vbo_(vrt)
		nrm_vbo = lgl.get_vbo_(nrm)
		self._vertices_ = (vrt_vbo, nrm_vbo, orgs)

	def draw_gl(self, shader = None):
		lgl.set_shader(shader, self.shader_callbacks)
		lgl.render_gl_primitive(*self._vertices_)

class cube(world_object):
	def __init__(self, x = 0, y = 0, z = 0, shader = None):
		self.material = lgl.material(shininess = 0.01, 
					dif_refl = cgt.vec3([0.9,0.1,0.1]), 
					amb_refl = cgt.vec3([0.9,0.1,0.1]))
		world_object.__init__(self, x, y, z, shader = shader)
		self._set_geometry_()

	def _set_geometry_(self):
		vrt, nrm, orgs = lgl.get_primitive('box')
		vrt_vbo = lgl.get_vbo_(vrt)
		nrm_vbo = lgl.get_vbo_(nrm)
		self._vertices_ = (vrt_vbo, nrm_vbo, orgs)

	def _get_shader_callbacks_(self, shader):
		mat_callback = self.material._get_uniforms_callback_(shader)
		callbacks = {'material':mat_callback}
		return callbacks

	def draw_gl(self, shader = None):
		lgl.set_shader(shader, self.shader_callbacks)
		lgl.render_gl_primitive(*self._vertices_)

class cell(world_object):

	#a cell is a 3-d region scalar/vector fields can be calculated
	#it has a slice dictionary for accessing the proper sections 
	#	of the scalars/vectors for which it does calculation
	#each cell has 6 bounding planes, 
	#	each of which is open, closed, or periodic
	#the cell has methods for updating scalars/vectors

	def __init__(self, x = 0, y = 0, z = 0, dt = 0.01, nt = 10, 
			nx = 5, ny = 5, nz = 5, vfields = [], sfields = [], 
			l = 2, h = 2, w = 2, bounds = None, ode_bucket = None):
		if bounds is None:
			bounds = ('closed', 'closed', 'closed', 
					'closed', 'closed', 'closed')

		bbox1 = [0, 0, 0]
		bbox2 = [l, h, w]
		world_object.__init__(self, x, y, z, 
				bbox1 = bbox1, bbox2 = bbox2)
		self._set_grid_space_(bbox1, bbox2, dt, nt, nx, ny, nz)
		self._set_bounding_planes_(bbox1, bbox2, bounds, ode_bucket)
		sfields.append('FLOW')
		self._set_fields_(vfields, sfields)

	def _set_grid_space_(self, bbox1, bbox2, dt, nt, nx, ny, nz):
		min_x,min_y,min_z = bbox1
		max_x,max_y,max_z = bbox2

		self.nt = nt
		self.nx = nx
		self.ny = ny
		self.nz = nz

		self.dt = dt
		self.dx = max_x/(self.nx-1)
		self.dy = max_y/(self.ny-1)
		self.dz = max_z/(self.nz-1)

		self.x = np.linspace(min_x,max_x,self.nx)
		self.y = np.linspace(min_y,max_y,self.ny)
		self.z = np.linspace(min_z,max_z,self.nz)
		self.Y,self.X,self.Z = np.meshgrid(self.y,self.x,self.z)

	def _set_bounding_planes_(self, bbox1, bbox2, 
					bounds, ode_bucket = None):
		pos = self._get_position_()
		l = bbox2[0] - bbox1[0]
		h = bbox2[1] - bbox1[1]
		w = bbox2[2] - bbox1[2]
		bottom = (pos[0],   pos[1],   pos[2], l, w, 
				(0, -1, 0), bounds[0], ode_bucket)
		top	   = (pos[0],   pos[1]+h, pos[2], l, w, 
				(0,  1, 0), bounds[1], ode_bucket)
		front  = (pos[0],   pos[1],   pos[2], h, l, 
				(0, 0,  1), bounds[2], ode_bucket)
		back   = (pos[0],   pos[1],   pos[2]+w, h, l, 
				(0, 0, -1), bounds[3], ode_bucket)
		left   = (pos[0],   pos[1],   pos[2], w, h, 
				( 1, 0, 0), bounds[4], ode_bucket)
		right  = (pos[0]+l, pos[1],   pos[2], w, h, 
				(-1, 0, 0), bounds[5], ode_bucket)
		boundings = [
			bounding_plane(*bottom), 
			bounding_plane(*top), 
			bounding_plane(*front), 
			bounding_plane(*back), 
			bounding_plane(*left), 
			bounding_plane(*right)]
		self.bounds = boundings
		self.children.extend(self.bounds)

	def _set_fields_(self, vfields, sfields):
		self.fields = {'vector' : {}, 'scalar' : {}}
		for field in vfields:
			self.fields['vector'][field] =\
				field_vector(
					self.x,  self.y,  self.z, 
					self.nx, self.ny, self.nz)

		for field in sfields:
			self.fields['scalar'][field] =\
				field_scalar(
					self.x,  self.y,  self.z, 
					self.nx, self.ny, self.nz)

	def _update_(self):
		#med.progress()
		#apply_media_flow(bucket)
		#apply_media_buoyancy(bucket)
		[child._update_() for child in self.children]

	def draw_gl(self):
		for V in self.fields['vector'].keys():
			field = self.fields['vector'][V]
			if field._draw_field_: field.draw_gl()

		for P in self.fields['scalar'].keys():
			field = self.fields['scalar'][P]
			if field._draw_field_: field.draw_gl()

		world_object.draw_gl(self)

class field(object):

	#fields are meant to be used via cells
	#x, y, z are 1-d linspaces

	_draw_field_ = True

	def __init__(self, x, y, z):
		self.x = x
		self.y = y
		self.z = z

	def _hide_field_(self):
		self._draw_field_ = False

	def _show_field_(self):
		self._draw_field_ = True

	def draw_gl(self): pass

class field_vector(field):

	def __init__(self, x, y, z, nx, ny, nz):
		field.__init__(self, x, y, z)
		self.u = np.zeros((nx,ny,nz))
		self.v = np.zeros((nx,ny,nz))
		self.w = np.zeros((nx,ny,nz))

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

class field_scalar(field):

	def __init__(self, x, y, z, nx, ny, nz):
		field.__init__(self, x, y, z)
		self.p = np.zeros((nx,ny,nz))

	def draw_gl(self, every_other = 2):
		x, y, z = (
			self.x[::every_other], 
			self.y[::every_other], 
			self.z[::every_other])
		p = self.p[::every_other,::every_other,::every_other]
		lgl.draw_dot_field(x, y, z, p)

class bounding_plane(world_object):

	#a bounding plane is a 2-d region in 3-d space
	#it has a normal vector indicating to which basis vector
	#it has 2 2-d vectors indicating bbox relative to origin
	#	of 3-d space to which it is perpendicular
	#it is either open, closed, or periodic
	#	if its periodic, it contains a reference to another plane
	#	with which is is periodic - planes do NOT have to have the same normal even
	#bounding planes collect/maintain information about their flux
	#	both flux of fluid and particles

	#norm should be basis vector of R3

	def __init__(self, x, y, z, l, w, n = (0, 1, 0), 
			condition = 'closed', ode_bucket = None):
		if   n[0]: bbox1, bbox2 = (x, y, z), (x, l, w)
		elif n[1]: bbox1, bbox2 = (x, y, z), (l, y, w)
		elif n[2]: bbox1, bbox2 = (x, y, z), (l, w, z)
		self.n = n
		self.gtype = 'box'
		self.parameters = {'boxlengths':[2, 0.2, 2]}
		self.condition = condition
		world_object.__init__(self, x, y, z, 
				bbox1 = bbox1, bbox2 = bbox2)
		if ode_bucket: self._make_ode_(ode_bucket)

	def _make_ode_(self, ode_bucket):
		#self.body, self.geom =\
		#	los.make_box(ode_bucket['world'], 
		#		ode_bucket['space'], 1.8, 1.8, 1.8, 100, True)
			#rot = [1,0,-1,0,1,0,1,0,1]
		loc = self._get_center_()# + np.array([.1, .1, .1])
		#print 'make ode on bp', loc
		self.body, self.geom =\
			los.make_finite_plane(ode_bucket['world'], 
						ode_bucket['space'], self.n)
		self.body.setPosition(loc)
		norm = self.n
		if   norm == ( 1,0,0) or norm == (-1,0,0):
			rot = [1,-1,0,1,-1,0,0,0,1]
			#self.body.setRotation(rot)
		elif norm == (0, 1,0) or norm == (0,-1,0): pass
			#rot = [1,0,0,0,1,0,0,0,1]
		elif norm == (0,0, 1) or norm == (0,0,-1):
			rot = [1,0,0,0,1,-1,0,1,-1]
			#self.body.setRotation(rot)

	def _update_(self):
		pass

	def draw_gl(self):
		#lgl.draw_rectangle(self.bbox1, self.bbox2, 
		#	color = (0.2, 0.4, 0.6, 0.2), normal = self.n, 
		#				border = True, border_width = 2.0, 
		#				border_color = (0.1,0.1,0.1,1.0))
		world_object.draw_gl(self)
		los.draw_gl(self)

'''
class world3d(object):

	#world3d is a class for quickly running an open gl simulation
	# it just provides a callback for 
	# running a generic simulation quickly

	def __init__(self, idle = None, keys = None, draw = None, 
			run = True, display = True, title = 'Simulation', 
					objs = [], bucket = {}, end_check = None, 
						ode_world = True, qtembedded = False):
		self.bucket = bucket
		self.bucket['selected'] = None
		self.bucket['objects'] = []
		self.qtembedded = qtembedded
		self._ode_world_ = ode_world
		if ode_world:
			gravity = (0.0,-9.81,0.0)
			bucket['ode'] = {}
			(bucket['ode']['world'], 
				bucket['ode']['space'], 
				bucket['ode']['bodies'], 
				bucket['ode']['geoms'], 
				bucket['ode']['contactgroup']) =\
			los.make_world(gravity)

		#self.sg_root = lgl.scene_node()
		#self.obj_to_world(lgl.scene_axes())
		for obj in objs: self.obj_to_world(obj)
		if idle is None:
			self.idle = self.generate_idle(display, end_check)

		else: self.idle = idle
		if keys is None: self.keys = self.generate_keys()
		else: self.keys = keys
		if draw is None: self.draw = self.generate_draw()
		else: self.draw = draw
		if run: self.run_world(display = display, title = title)

	def run_world(self, display = True, title = 'Simulation'):
		bucket = self.bucket
		st_time = time.time()
		bucket['starttime'] = st_time
		bucket['lasttime'] = st_time
		if display:
			lgl.use_glut_display(
				self.idle, self.keys, self.draw, 
				window_title = title)
			lgl.start_main()

		else:
			_idle = self.idle
			while not _idle(): pass

	def generate_idle(self, display, end = None):

		def _idle():
			t = bucket['dt'] - (time.time() - bucket['lasttime'])
			if (t > 0): time.sleep(t)
			postredisplay()
			for obj in bucket['objects']: obj._update_()
			if self._ode_world_: los.ode_world_step(bucket['ode'])
			bucket['lasttime'] = time.time()
			if end(): return leave()
			return False

		bucket = self.bucket
		bucket['lasttime'] = time.time()
		fps = 50
		bucket['dt'] = 1.0/fps
		if self._ode_world_: bucket['ode']['dt'] = bucket['dt']
		if self.qtembedded:
			postredisplay = lambda : 'redisplay'
			leave = lambda : True

		elif display:
			postredisplay, leave = lgl.redisp_leave_funcs()

		else:
			postredisplay = lambda : 'redisplay'
			leave = lambda : True

		if end is None: end = lambda : False
		return _idle

	def generate_keys(self):

		def zoom_in(): bucket['zoom'] -= bucket['zoom']
		def zoom_out(): bucket['zoom'] += bucket['zoom']
		def orbit_x_left(): bucket['orbit_x'] -= 10
		def orbit_x_right(): bucket['orbit_x'] += 10
		def orbit_y_left(): bucket['orbit_y'] -= 10
		def orbit_y_right(): bucket['orbit_y'] += 10
		def orbit_z_left(): bucket['orbit_z'] -= 10
		def orbit_z_right(): bucket['orbit_z'] += 10
		def pan_cam_x_right():
			bucket['cam_location'][0] += 1
			bucket['cam_target'][0] += 1
		def pan_cam_x_left():
			bucket['cam_location'][0] -= 1
			bucket['cam_target'][0] -= 1
		def pan_cam_z_right():
			bucket['cam_location'][2] -= 1
			bucket['cam_target'][2] -= 1
		def pan_cam_z_left():
			bucket['cam_location'][2] += 1
			bucket['cam_target'][2] += 1
		def reset_camera():
			if bucket['selected']:
				sel_loc = bucket['selected']._get_center_()
				cam_loc, cam_trg = cam_loc_initial, sel_loc
			else: cam_loc, cam_trg = cam_loc_initial, cam_trg_initial
			bucket['cam_location'] = cam_loc
			bucket['cam_target'] = cam_trg
			bucket['orbit_x'] = 0
			bucket['orbit_y'] = 0
			bucket['orbit_z'] = 0
			bucket['zoom'] = 5
		def add_ecoli(): self.obj_to_world(new_ecoli(bucket['ode']))
		def add_box(): self.obj_to_world(new_box_granule(bucket['ode']))
		def quit_(): sys.exit(0)
		def _keys_help():
			for key in mapping.keys():
				print 'key', key, '-', mapping[key][1]
		def _keys(c, x, y):
			try: mapping[c][0]()
			except KeyError:
				traceback.print_exc(file=sys.stdout)
				print 'unrecognized key'

		mapping = {}
		mapping['+'] = (zoom_in, 'zoom in')
		mapping['-'] = (zoom_out, 'zoom out')
		mapping['q'] = (quit_, 'quit')
		mapping['z'] = (orbit_x_left, 'x orbit left')
		mapping['x'] = (orbit_x_right, 'x orbit right')
		mapping['r'] = (orbit_y_left, 'y orbit left')
		mapping['f'] = (orbit_y_right, 'y orbit right')
		mapping['t'] = (orbit_z_left, 'z orbit left')
		mapping['g'] = (orbit_z_right, 'z orbit right')
		mapping['a'] = (pan_cam_x_left, 'pan camera along x left')
		mapping['d'] = (pan_cam_x_right, 'pan camera along x right')
		mapping['s'] = (pan_cam_z_left, 'pan camera along z left')
		mapping['w'] = (pan_cam_z_right, 'pan camera along z right')
		mapping['e'] = (reset_camera, 'reset camera')
		mapping['h'] = (_keys_help, 'keys help')
		mapping['p'] = (add_ecoli, 'add ecoli')
		mapping['o'] = (add_box, 'add box')

		bucket = self.bucket
		bucket['mapping'] = mapping
		cam_loc_initial = [5, 5, 5]
		cam_trg_initial = [0, 0, 0]
		bucket['zoom'] = 5
		bucket['orbit_x'] = 0
		bucket['orbit_y'] = 0
		bucket['orbit_z'] = 0
		bucket['cam_location'] = cam_loc_initial
		bucket['cam_target'] = cam_trg_initial
		return _keys

	def generate_draw(self):

		def _draw_embedded():
			for obj in bucket['objects']: obj.draw_gl()
			#self.sg_root.draw()
			#lgl.draw_axes()

		def _draw():
			lgl.prepare_GL(bucket['zoom'], 
				bucket['orbit_x'], 
				bucket['orbit_y'], 
				bucket['orbit_z'], 
				bucket['cam_location'], bucket['cam_target'], 
				bucket['view_x'], bucket['view_y'], 
				bucket['view_w'], bucket['view_h'])
			for obj in bucket['objects']: obj.draw_gl()
			lgl.draw_axes()
			lgl.post_draw()

		bucket = self.bucket
		bucket['view_x'] = 50
		bucket['view_y'] = 50
		bucket['view_w'] = 800
		bucket['view_h'] = 640
		if self.qtembedded: return _draw_embedded
		else: return _draw

	def obj_to_world(self, obj):
		print 'obj to world', obj
		if self._ode_world_ and hasattr(obj, '_make_ode_'):
			obj._make_ode_(self.bucket['ode'])

		self.bucket['objects'].append(obj)
		if self.bucket['selected'] is None:
			self.bucket['selected'] = obj

'''

def in_bbox(bbox, v_):
	def in_bbox1d(rng, x): return x >= rng[0] and x <= rng[1]
	bbox1, bbox2 = bbox
	in_x = in_bbox1d((bbox1[0], bbox2[0]), v_[0])
	in_y = in_bbox1d((bbox1[1], bbox2[1]), v_[1])
	in_z = in_bbox1d((bbox1[2], bbox2[2]), v_[2])
	return in_x and in_y and in_z

def new_ecoli(bucket, loc=(1,10,1), 
		rot=[0,0,0,0,0,0,0,0,0], density=0.1):
	ecoli_rad = 0.25
	ecoli_len = 2.0 - 2*ecoli_rad
	theta = 0
	new_granule = granule(loc, rot, ode_bucket = bucket, 
		gtype = 'capsule', parameters = {
			'theta':theta, 'density':density, 
			'radius':ecoli_rad, 'length':ecoli_len})
	return new_granule

def new_box_granule(bucket, loc=(1,10,1), 
		rot=[0,0,0,0,0,0,0,0,0], density=0.1):
	new_granule = granule(loc, rot, ode_bucket = bucket, 
		gtype = 'box', parameters = {
			'density':density, 
			'boxlengths':(1,1,1)})
	return new_granule

class granule(world_object):

	#THIS IS A CLASS WHICH REPRESENTS A SINGLE PARTICLE
	# IT GETS A SHAPE (BOX, CAPSULE, ETC)
	# IT HAS METHODS FOR DRAWING AND COLLISION IF NECESSARY

	def __init__(self, loc, rot, ode_bucket, 
			gtype = 'capsule', parameters = {}):
		self.gtype = gtype
		self.parameters = parameters
		self.make_gran(loc, rot, ode_bucket)
		aabb = self.geom.getAABB()
		bbox1, bbox2 = np.array(aabb[::2]), np.array(aabb[1::2])
		loc = np.array(loc)
		world_object(self, loc[0], loc[1], loc[2], 
				bbox1=bbox1-loc, bbox2=bbox2-loc)

	def make_gran(self, loc, rot, bucket):
		print 'made granule of type:', self.gtype
		world = bucket['world']
		space = bucket['space']
		density = self.parameters['density']
		if self.gtype == 'capsule':
			dir_ = 3
			self.parameters['direction'] = dir_
			rad_ = self.parameters['radius']
			leng = self.parameters['length']
			self.body, self.geom =\
				los.make_capsule(world, space, 
					dir_, rad_, leng, density)

		elif self.gtype == 'box':
			lx, ly, lz = self.parameters['boxlengths']
			self.body, self.geom =\
				los.make_box(world, space, 
					lx, ly, lz, density)

		self.body.setPosition(loc)
		self.body.setRotation(rot)



	def compute_cross_section(self, n_):
		unit = np.array([0, 0, 1])
		rot = self.body.getRotation()
		rot = np.ndarray(shape = (3, 3,), dtype = np.float16, 
				buffer = np.array(rot, dtype = np.float16))
		unit = np.dot(rot, unit).round()
		alpha = lm.angle(unit, n_)
		r_ = self.parameters['radius']
		l_ = self.parameters['length']
		area = r_*(2*l_*math.sin(alpha) + math.pi*r_)
		return area

	def compute_drag_f(self, medium):
		bvel = np.array(self.body.getLinearVel())
		mvel = medium.average_velocity_over_granule(self)
		if not lm.length(mvel): return np.array([0, 0, 0])
		rvel = mvel - bvel
		if not lm.length(rvel): return np.array([0, 0, 0])
		rho_ = medium.rho
		c_drag = 1.0
		area = self.compute_cross_section(mvel/lm.length(mvel))
		f_x, f_y, f_z =\
			0.5*lm.dot_product(rvel, rvel)*rho_*\
				area*c_drag*rvel/lm.length(rvel)
		return [f_x, f_y, f_z]

	def compute_drag_t(self, medium):
		t_x, t_y, t_z = [0, 0, 0]
		return [t_x, t_y, t_z]

	def compute_buoyancy(self, medium):
		b_x, b_y, b_z = [0, 0, 0]
		return [b_x, b_y, b_z]



	def draw_gl(self):
		los.draw_gl(self)

class light(world_object):
	def __init__(self, x, y, z, shader = None):
		world_object.__init__(self, x, y, z, shader = shader)
		self.amb_int = cgt.vec3([0.4,0.4,0.4])
		self.dif_int = cgt.vec3([0.8,0.8,0.8])
		self.spe_int = cgt.vec3([0.0,0.0,0.0])
		self._set_geometry_()

	def _set_geometry_(self):
		vrt, nrm, orgs = lgl.get_primitive('cone')
		vrt_vbo = lgl.get_vbo_(vrt)
		nrm_vbo = lgl.get_vbo_(nrm)
		self._vertices_ = (vrt_vbo, nrm_vbo, orgs)

	def _get_shader_callbacks_(self, shader):
		return {'lights':self._get_uniforms_callback_(shader)}

	def _get_uniforms_callback_(self, shader):
		return lgl._get_uniforms_callback_light_(self, shader)

	def draw_gl(self, shader):
		lgl.set_shader(shader, self.shader_callbacks)
		#lgl.render_gl_primitive(*self._vertices_)

class camera(world_object):
	def draw_gl(self):
		world_object.draw_gl(self, self.shader)
		self.update_transforms()
		lgl.set_shader(self.shader, self.shader_callbacks)
	def toggle_ortho(self, to = None):
		if not to is None: self.ortho = to
		else: self.ortho = not self.ortho
		if self.ortho: print 'camera is orthographic'
		else: print 'camera is perspective'
		self.update_projection()
	def toggle_regime(self, to = None):
		if not to is None: self.view_regime = to
		else:
			v_dex = self.view_regimes.index(self.view_regime)+1
			if v_dex == len(self.view_regimes): v_dex = 0
			self.view_regime = self.view_regimes[v_dex]
		print 'view regime is', self.view_regime
		self.update_projection()
	def reset(self):
		self.location.x = self.location_initial.x
		self.location.y = self.location_initial.y
		self.location.z = self.location_initial.z
		if self.select_: self.select(self.select_)
		else:
			self.target.x = self.target_initial.x
			self.target.y = self.target_initial.y
			self.target.z = self.target_initial.z
		self.roll = 0
		self.pitch = 0
		self.yaw = 0
		self.zoom_ = self.zoom_initial
		self.update_transforms()
	def zoom(self, dz):
		self.zoom_ = lm.clamp(self.zoom_ + dz, 2, 100)
		self.update_projection()
	def pan(self, dx, dy):
		dx *=-0.2
		dy *= 0.2
		r_hat, u_hat, f_hat = self.get_basis(self.view_regime)
		delta = r_hat*dx + u_hat*dy
		self.location += delta
		self.target += delta
		self.update_view()
	def orbit(self, dx, dy):
		self.yaw += lm.normalize_angle(dx)
		self.pitch += lm.normalize_angle(dy)
		self.update_view()
	def toggle_select(self, dir_ = 'forward'):
		print 'toggle selected in direction', dir_
		if self.selectables:
			max_s_dex = len(self.selectables) - 1
			if self.select_:
				s_dex = self.selectables.index(self.select_)
				if dir_ == 'forward': s_dex += 1
				elif dir_ == 'backward': s_dex -= 1
				if s_dex < 0: s_dex = max_s_dex
				elif s_dex > max_s_dex: s_dex = 0
			else: s_dex = 0
			sobj = self.selectables[s_dex]
			self.select(sobj)
			print 'selected', sobj
	def select(self, obj):
		self.select_ = obj
		t_pos = self.select_._get_center_()
		self.target.x = t_pos[0]
		self.target.y = t_pos[1]
		self.target.z = t_pos[2]
	def __init__(self, x, y, z, parent = None, 
					target = cgt.vec3([.5,.5,.5]), 
					ortho = True, zoom = 30):
		#lgl._culling()
		self.shader = lgl.get_shader()
		self.light = light(x, y, z, shader = self.shader)
		self.material = lgl.material()
		world_object.__init__(self, x, y, z, parent = parent, 
			shader = self.shader, children = [self.light])
		self._draw_origin_ = False
		self.ortho = ortho
		self.zoom_initial = zoom
		self.zoom_ = self.zoom_initial

		self.znear = 0.001
		self.zfar = 1000.0

		self.location_initial = self._get_position_()
		self.target_initial = target
		self.location = cgt.vec3(self.location_initial)
		self.target = cgt.vec3(self.target_initial)

		self.select_ = None
		self.selectables = []

		self.roll = 0
		self.pitch = 0
		self.yaw = 0

		self.view_regimes = ['first person', 'arc ball']
		self.view_regime = self.view_regimes[1]
		self.view_callbacks = {
			'first person':self.get_basis_first_person, 
			'arc ball':self.get_basis_arc_ball, 
			}

		self._view_matrix_ = lm.identity_mat(4).flatten()
		self._projection_matrix_ = lm.identity_mat(4).flatten()
		self._normal_matrix_ = lm.identity_mat(3).flatten()
		self._mvp_matrix_ = lm.identity_mat(4).flatten()
		self.update_transforms()

	def _get_shader_callbacks_(self, shader):
		material_callback =\
			self.material._get_uniforms_callback_(shader)
		transform_callback =\
			lgl._get_uniforms_callback_transform_(self, shader)
		callbacks = {
			'material':material_callback, 
			'transforms':transform_callback}
		return callbacks

	def update_transforms(self):
		self.update_projection()
		self.update_view()
		self.update_mvp()

	def update_mvp(self, modl_ = None):
		if modl_: modl = modl_
		else: modl = cgt.mat4(1)
		proj = self.update_projection()
		view = self.update_view()
		mvp = proj*view*modl
		self._mvp_matrix_[:] = np.array(mvp).flatten()
		return mvp



	def projection_persp(self):
		near, far = self.znear, self.zfar
		#fFrustumScale = 1.0*self.zoom_
		aspectRatio = 0.75
		DEG2RAD = math.pi / 180.0
		fov = 60*DEG2RAD
		h = 10*math.cos(0.5*fov)/(math.sin(0.5*fov)*self.zoom_)
		w = h * aspectRatio
		a = (far + near)/(near - far)
		b = (2*near*far)/(near - far)
		proj = cgt.mat4([
			w, 0, 0, 0, 
			0, h, 0, 0, 
			0, 0, a, b, 
			0, 0,-1, 0])
		return proj

	def projection_ortho(self):
		near, far = self.znear, self.zfar
		corner = 0.1*self.zoom_
		left = -corner
		right = corner
		bottom = -corner
		top = corner
		s1 = 2.0 / (right - left)
		s2 = 2.0 / (top - bottom)
		s3 = -2.0 / (far - near)
		t1 = -(right+left)/(right-left)
		t2 = -(top+bottom)/(top-bottom)
		t3 = -(far+near)/(far-near)
		proj = cgt.mat4([
			s1, 0, 0,t1,
			 0,s2, 0,t2,
			 0, 0,s3,t3,
			 0, 0, 0, 1])
		return proj

	def update_projection(self, width = None, height = None):
		if not width is None: self.width = width
		if not height is None: self.height = height
		if self.ortho: proj = self.projection_ortho()
		else: proj = self.projection_persp()
		self._projection_matrix_[:] = np.array(proj).flatten()
		return proj



	def get_basis_look_at(self, y_hat):
		f_hat = (self.location - self.target).normalize()
		r_hat = y_hat.cross(f_hat).normalize()
		u_hat = f_hat.cross(r_hat).normalize()
		return r_hat, u_hat, f_hat

	def get_basis_first_person(self):
		DEG2RAD = math.pi / 180.0
		yaw, pitch = self.yaw*DEG2RAD, self.pitch*DEG2RAD
		cosPitch = math.cos(pitch)
		sinPitch = math.sin(pitch)
		cosYaw = math.cos(yaw)
		sinYaw = math.sin(yaw)
		r_hat = cgt.vec3([sinYaw*cosPitch,
				-sinPitch,cosPitch*cosYaw])
		f_hat = cgt.vec3([cosYaw,0,-sinYaw])
		#r_hat = cgt.vec3([cosYaw,0,-sinYaw])
		u_hat = cgt.vec3([sinYaw*sinPitch,
				cosPitch,cosYaw*sinPitch])
		return r_hat, u_hat, f_hat

	def get_basis_arc_ball(self):
		#pseudo code:
		#//some angle & some other angle = only the amount you want the camera to rotate since last frame.
		#//pitch
		#position = (Rotate(some angle, cameraRight) * (position - target)) + target;
		#//yaw, Y-up system
		#position = (rotate(some other angle, (0,1,0) * (position - target)) + target;
		#view = LookAt(position, target, up);
		DEG2RAD = math.pi / 180.0
		y_hat = cgt.vec3([0,1,0])

		cur_loc = self.location
		target = self.target

		forw = cur_loc - target
		R = forw.length()
		cosPitch = math.cos(self.pitch*DEG2RAD)
		cosYaw = math.cos(self.yaw*DEG2RAD)
		sinPitch = math.sin(self.pitch*DEG2RAD)
		sinYaw = math.sin(self.yaw*DEG2RAD)

		trg_relative_loc = cgt.vec3(R*cosPitch*cosYaw, 
						R*sinPitch, R*cosPitch*sinYaw)

		#f_hat = (cur_loc - target).normalize()
		#f_hat = (target - cur_loc).normalize()
		#r_hat = y_hat.cross(f_hat).normalize()
		#cur_pitch = 90 - math.asin(f_hat.cross(y_hat))/DEG2RAD
		#trg_pitch = self.pitch*DEG2RAD

		#if not cur_pitch == trg_pitch:

		#cur_loc = cgt.quat(self.pitch*DEG2RAD,r_hat).rotateVec(cur_loc-target)
		#cur_loc = cgt.quat(self.yaw*DEG2RAD,y_hat).rotateVec(cur_loc)+target

		self.location.x = target.x + trg_relative_loc.x
		self.location.y = target.y + trg_relative_loc.y
		self.location.z = target.z + trg_relative_loc.z

		r_hat, u_hat, f_hat = self.get_basis_look_at(y_hat)
		return r_hat, u_hat, f_hat

	def get_basis(self, regime):
		#get_basis is responsible for calculating the proper
		# camera location and target and calculating a set of
		# R3 basis vectors from these
		r_hat, u_hat, f_hat = self.view_callbacks[regime]()
		return r_hat, u_hat, f_hat

	def update_normal(self, regime):
		r_hat, u_hat, f_hat = self.get_basis(regime)
		norm = cgt.mat3([
			r_hat[0], r_hat[1], r_hat[2], 
			u_hat[0], u_hat[1], u_hat[2], 
			f_hat[0], f_hat[1], f_hat[2]])
		self._normal_matrix_[:] = np.array(norm).flatten()
		return norm

	def view(self, regime):
		r_hat, u_hat, f_hat = self.get_basis(regime)
		eye = self.location
		x, y, z = eye
		view = cgt.mat4([
			r_hat[0], r_hat[1], r_hat[2], -r_hat*eye, 
			u_hat[0], u_hat[1], u_hat[2], -u_hat*eye, 
			f_hat[0], f_hat[1], f_hat[2], -f_hat*eye, 
			0, 0, 0, 1])
		return view

	def update_view(self):
		self.update_normal(self.view_regime)
		view = self.view(self.view_regime)
		self._view_matrix_[:] = np.array(view).flatten()
		return view



if __name__ == '__main__':
	print 'Hush - This is a library!'

if __name__ == 'libs.modular_core.lib3dworld':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb




