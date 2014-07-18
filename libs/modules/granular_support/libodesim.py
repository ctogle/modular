import libs.modular_core.libmath as lm
#import libs.modular_core.libopenglutilities as lgl
import libs.world3d_simulator.libopenglutilities as lgl
import libs.modules.granular_support.libnavierstokes as lns

import ode
import sys, os, random, time, math
#from OpenGL.GL import *
#from OpenGL.GLU import *
#from OpenGL.GLUT import *
#from OpenGL.GLUT.freeglut import *

import numpy as np

import pdb


###
#GEOMETRIC UTILITY FUNCTIONS
###
def scalp (vec, scal):
    vec[0] *= scal
    vec[1] *= scal
    vec[2] *= scal

def length (vec):
    return math.sqrt (vec[0]**2 + vec[1]**2 + vec[2]**2)


###
#FUNCTIONS TO ADD GRANULES TO THE SYSTEM
###
def drop_box(bucket, 
		loc = (-2.5+random.gauss(0,0.1),10.0,2.5+random.gauss(0,0.1)), 
					rot = [0, 0, 0, 0, 0, 0, 0, 0, 0], density = 0.1, 
										lengths = (2.0, 0.5, 0.5)):

	#theta = random.uniform(0,2*math.pi)
	#theta = math.pi/2.0
	theta = 0.0
	ct = math.cos (theta)
	st = math.sin (theta)
	rot = [ct, 0., -st, 0., 1., 0., st, 0., ct]

	new_granule = granule(gtype = 'box', boxlengths = lengths, 
		density = density, location = loc, rotation = rot, **bucket)
	bucket['counter']=0
	bucket['objcount']+=1

def drop_ecoli(bucket, 
		loc = (-2.5+random.gauss(0,0.1),10.0,2.5+random.gauss(0,0.1)), 
					rot = [0, 0, 0, 0, 0, 0, 0, 0, 0], density = 0.1):
	ecoli_rad = 0.25
	ecoli_len = 2.0 - 2*ecoli_rad

	#theta = random.uniform(0,2*math.pi)
	#theta = math.pi/2.0
	theta = 0.0
	ct = math.cos(theta)
	st = math.sin(theta)
	rot = [ct, 0., -st, 0., 1., 0., st, 0., ct]

	new_granule = granule(
		gtype = 'capsule', 
		radius = ecoli_rad, 
		length = ecoli_len, 
		density = density, 
		parameters = {'theta':theta}, 
		location = loc, rotation = rot, **bucket)
	bucket['counter']=0
	bucket['objcount']+=1

###
#NON-ESSENTIAL ODE SIMULATION FUNCTIONS
###
def explosion(bucket):
    """Simulate an explosion.

    Every object is pushed away from the origin.
    The force is dependent on the objects distance from the origin.
    """
    #global bodies
    bodies = bucket['bodies']

    for b in bodies:
        l=b.getPosition ()
        d = length (l)
        a = max(0, 40*(1.0-0.2*d*d))
        l = [l[0] / 4, l[1], l[2] /4]
        scalp (l, a / length (l))
        b.addForce(l)

def apply_media_flow(bucket):
	#this code should instead use the medium to apply drag tensor forces
	granules = bucket['granules']
	medium = bucket['medium']
	for gr in granules:
		b = gr.body
		f = gr.compute_drag_f(medium)
		t = gr.compute_drag_t(medium)
		b.addForce(f)
		b.addTorque(t)

def apply_media_buoyancy(bucket):
	granules = bucket['granules']
	medium = bucket['medium']
	for gr in granules:
		b = gr.body
		buo = gr.compute_buoyancy(medium)
		b.addForce(buo)

def pull(bucket):
    """Pull the objects back to the origin.

    Every object will be pulled back to the origin.
    Every couple of frames there'll be a thrust upwards so that
    the objects won't stick to the ground all the time.
    """
    #global bodies, counter
    bodies = bucket['bodies']
    counter = bucket['counter']

    for b in bodies:
        l=list (b.getPosition ())
        scalp (l, -5 / length (l))
        b.addForce(l)
        if counter%60==0:
            b.addForce((0,5,0))


###
#ESSENTIAL ODE SIMULATION FUNCTIONS
###
# Collision callback
def near_callback(args, geom1, geom2):
    """Callback function for the collide() method.

    This function checks if the given geoms do collide and
    creates contact joints if they do.
    """
	#COULD THIS FUNCTION ALLOW ANY GEOM TO ALTER COLLISION BEHAVIOR, FOR INSTANCE FOR AN OPEN BOUNDARY
    # Check if the objects do collide
    contacts = ode.collide(geom1, geom2)

    # Create contact joints
    world,contactgroup = args
    for c in contacts:
        c.setBounce(0.01)
        #c.setMu(5000)
        c.setMu(1.0)
        j = ode.ContactJoint(world, contactgroup, c)
        j.attach(geom1.getBody(), geom2.getBody())

# initialize ode world and body/geom/contactgroup containers
def make_world(grav = (0,-9.81,0)):
	world = ode.World()
	world.setGravity(grav)
	world.setERP(0.8)
	world.setCFM(1E-5)
	space = ode.Space()
	bodies = []
	geoms = []
	contactgroup = ode.JointGroup()
	return world, space, bodies, geoms, contactgroup


###
#CLASSES USED FOR GRANULAR SIMULATION
###
'''
class plane_boundary:

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
'''

class granule:

	#THIS IS A CLASS WHICH REPRESENTS A SINGLE PARTICLE
	# IT GETS A SHAPE (BOX, CAPSULE, ETC)
	# IT HAS METHODS FOR DRAWING AND COLLISION IF NECESSARY

	def __init__(self, *args, **kwargs):
		self.gtype = kwargs['gtype']
		self.world = kwargs['world']
		self.space = kwargs['space']
		if 'parameters' in kwargs.keys():
			self.parameters = kwargs['parameters']

		else: self.parameters = {}
		self.parameters['density'] = kwargs['density']
		self.make_gran(*args, **kwargs)
		kwargs['bodies'].append(self.body)
		kwargs['geoms'].append(self.geom)
		kwargs['granules'].append(self)

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

	def make_gran(self, *args, **kwargs):
		print 'made granule of type:', self.gtype
		if self.gtype == 'capsule':
			self.parameters['radius'] = kwargs['radius']
			self.parameters['length'] = kwargs['length']
			self.parameters['direction'] = 3
			self.body, self.geom =\
				self.make_capsule(self.world, self.space)

		elif self.gtype == 'box':
			self.parameters['boxlengths'] = kwargs['boxlengths']
			self.body, self.geom =\
				self.make_box(self.world, self.space)

		self.body.setPosition(kwargs['location'])
		self.body.setRotation(kwargs['rotation'])

	def make_capsule(self, world, space):
		direction, radius, length = (self.parameters['direction'], 
			self.parameters['radius'], self.parameters['length'])

		# Create body
		body = ode.Body(world)
		M = ode.Mass()
		M.setCapsule(
			self.parameters['density'], 
			direction, radius, length)
		body.setMass(M)

		# Create a box geom for collision detection
		geom = ode.GeomCapsule(space, radius = radius, length = length)
		geom.setBody(body)
		return body, geom

	def make_box(self, world, space):
		lx, ly, lz = self.parameters['boxlengths']

		# Create body
		body = ode.Body(world)
		M = ode.Mass()
		M.setBox(self.parameters['density'], lx, ly, lz)
		body.setMass(M)

		# Create a box geom for collision detection
		geom = ode.GeomBox(space, lengths = (lx, ly, lz))
		geom.setBody(body)
		return body, geom

	def draw_gl(self):
		body = self.body
		x,y,z = body.getPosition()
		R = body.getRotation()
		rot = [	R[0], R[3], R[6], 0.,
				R[1], R[4], R[7], 0.,
				R[2], R[5], R[8], 0.,
				x, y, z, 1.0]
		lgl.draw_primitive(self.gtype, rot, self.parameters)



# idle callback which performs rigid body simulation
def generate_idle_callback(use_glut, end_test, 
				capture_test, capture, bucket):

	# Simulate
	def _idlefunc ():
		dt = bucket['dt']
		space = bucket['space']
		world = bucket['world']
		med = bucket['medium']
		contactgroup = bucket['contactgroup']

		t = dt - (time.time() - bucket['lasttime'])
		if (t > 0): time.sleep(t)
		bucket['counter'] += 1
		if bucket['state']==0:
			if bucket['counter']==50:
				#if random.random() < 0.5: drop_ecoli(bucket)
				#else: drop_box(bucket)
				drop_ecoli(bucket)

			if bucket['objcount']==100:
				bucket['state']=1
				bucket['counter']=0

		elif bucket['state']==1:
			if bucket['counter']==100: explosion(bucket)
			if bucket['counter']>300: pull(bucket)
			if bucket['counter']==500: bucket['counter']=50

		postredisplay()
		n = 2
		for i in range(n):
			# Detect collisions and create contact joints
			space.collide((world,contactgroup), near_callback)
			world.step(dt/n) # Simulation step
			contactgroup.empty() # Remove all contact joints

		med.progress()
		apply_media_flow(bucket)
		apply_media_buoyancy(bucket)

		bucket['lasttime'] = time.time()
		if capt(): capture_()
		if end(): return leave()
		return False

	if use_glut:
		postredisplay, leave = lgl.redisp_leave_funcs()

	else:
		postredisplay = lambda : 'redisplay'
		leave = lambda : True

	end = end_test
	capt = capture_test
	capture_ = capture
	return _idlefunc
 
def generate_key_callback(bucket):

	def _keyfunc (c, x, y):
		frac = 0.5
		if c == '+' and bucket['zoom'] > 1:
			bucket['zoom'] -= bucket['zoom']*frac

		elif c == '-' and bucket['zoom'] < 100:
			bucket['zoom'] += bucket['zoom']*frac

		elif c == 'z': bucket['orbit_x'] -= 10
		elif c == 'x': bucket['orbit_x'] += 10
		elif c == 'r': bucket['orbit_y'] -= 10
		elif c == 'f': bucket['orbit_y'] += 10
		elif c == 'a':
			bucket['cam_location'][0] += 1
			bucket['cam_target'][0] += 1

		elif c == 'd':
			bucket['cam_location'][0] -= 1
			bucket['cam_target'][0] -= 1

		elif c == 'w':
			bucket['cam_location'][2] += 1
			bucket['cam_target'][2] += 1

		elif c == 's':
			bucket['cam_location'][2] -= 1
			bucket['cam_target'][2] -= 1

		elif c == 'e':
			loc, trg = camera_around_medium(bucket['medium'])
			bucket['cam_location'] = loc
			bucket['cam_target'] = trg
			bucket['orbit_x'] = 0
			bucket['orbit_x'] = 0
			bucket['orbit_y'] = 0
			bucket['orbit_y'] = 0
			bucket['zoom'] = 5

		elif c == 'q': sys.exit(0)

	return _keyfunc

def generate_draw_callback(bucket):

	def _drawfunc ():
		lgl.prepare_GL(bucket['zoom'], 
			bucket['orbit_x'], bucket['orbit_y'], 
			bucket['cam_location'], bucket['cam_target'])
		for gran in bucket['granules']: gran.draw_gl()
		bucket['medium'].draw_gl()
		lgl.draw_axes()
		lgl.post_draw()

	return _drawfunc

def camera_around_medium(medium):
	return medium.get_bbox_corners()[1], medium.get_center()

def run_simulation(use_glut = True):

	def end_test():
		return simulation_bucket['lasttime'] -\
			simulation_bucket['starttime'] > 900.0

	def capture_test(): return True
	def capture(): data.append(len(bodies))

	world, space, bodies, geoms, contactgroup = make_world()
	granules = []
	fps = 50
	dt = 1.0/fps
	state = 0
	counter = 0
	objcount = 0
	starttime = time.time()
	lasttime = starttime
	zoom = 5
	orbit_x = 0
	orbit_y = 0
	periodic, closed = 'periodic', 'closed'
	medium = lns.medium(space = space, bounds = {
			'x0' : [periodic], 	'x1' : [periodic], 
			'y0' : [closed], 	'y1' : [closed], 
			'z0' : [closed], 	'z1' : [closed]}, 
		bbox1 = (-5.0, 0.0, 0.0), bbox2 = (10.0, 5.0, 5.0), nx = 21, 
		ny = 11, nz = 11, nt = 10, dt = 0.01, rho = 1, nu = 0.1, 
								nit = 50, flow = (1.0, 0.0, 0.0))
	cam_location, cam_target = camera_around_medium(medium)
	simulation_bucket =\
		{
			'world' : world, 
			'space' : space, 
			'bodies' : bodies, 
			'geoms' : geoms, 
			'contactgroup' : contactgroup, 
			'fps' : fps, 
			'dt' : dt, 
			'state' : state, 
			'counter' : counter, 
			'objcount' : objcount, 
			'zoom' : zoom, 
			'orbit_x' : orbit_x, 
			'orbit_y' : orbit_y, 
			'cam_location' : cam_location, 
			'cam_target' : cam_target, 
			'lasttime' : lasttime, 
			'starttime' : starttime, 
			'granules' : granules, 
			'medium' : medium
		}

	targets = ['population']
	data = []

	_key = generate_key_callback(simulation_bucket)
	_draw = generate_draw_callback(simulation_bucket)

	if use_glut:
		_idle = generate_idle_callback(True, end_test, 
			capture_test, capture, simulation_bucket)
		lgl.use_glut_display(_idle, _key, _draw, 
			window_title = "Rigid Body Simulation")
		lgl.start_main()

	else:
		_idle = generate_idle_callback(False, end_test, 
			capture_test, capture, simulation_bucket)
		while not _idle(): pass

	return data, targets

def test(display = True):
	print 'running test ode simulation'
	result = run_simulation(use_glut = display)
	print 'result\n', result
	pdb.set_trace()

if __name__ == 'libs.modules.granular_support.libodesim':
	pass

if __name__ == '__main__': print 'this is a library!'




















