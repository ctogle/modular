import libs.modular_core.libfundamental as lfu
import libs.modular_core.libmath as lm
import numpy as np
from ctypes import c_void_p
import cgkit.cgtypes as cgt

#from OpenGLContext.arrays import vbo
from OpenGL.GL.ARB.vertex_buffer_object import *
from OpenGL.arrays import ArrayDatatype as ADT

from OpenGL.arrays import vbo
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT.freeglut import *

import math

import pdb

#def preprepare_GL(zoom = 1):
#	glViewport(x,y,width,height)

def use_glut_display(_idlefunc, _keyfunc, _drawfunc, 
		window_title = 'Simulation', x = 50, y = 50, 
								w = 800, h = 640):
	glutInit([])
	glutInitDisplayMode(GLUT_DOUBLE|GLUT_RGBA|GLUT_DEPTH)
	glutInitWindowPosition(x, y)
	glutInitWindowSize(w, h)
	_lighting()
	glutCreateWindow(window_title)
	glutKeyboardFunc(_keyfunc)
	glutDisplayFunc(_drawfunc)
	glutIdleFunc(_idlefunc)
	glutSetOption(
		GLUT_ACTION_ON_WINDOW_CLOSE, 
		GLUT_ACTION_CONTINUE_EXECUTION)

def run_gl(_idle, _key, _draw, title = 'Simulation'):
	use_glut_display(_idle, _key, _draw, window_title = title)
	start_main()

def prepare_GL(zoom = 1, orbit_x = 0, orbit_y = 0, orbit_z = 0, 
		cam_loc = (5.0, 5.0, 5.0), cam_trg = (2.5, 2.5, 2.5), 
						x = 50, y = 50, w = 800, h = 640):
	glEnable(GL_DEPTH_TEST)
	glDepthFunc(GL_LESS)

	glClearColor(0.8,0.8,0.9,0)
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

	# Initialize ModelView matrix
	glMatrixMode(GL_MODELVIEW)
	glLoadIdentity()

	# Projection
	set_projection_matrix(x, y, w, h, zoom)

	#_hud(w, h)

	#glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, 1)
	#glEnable(GL_LIGHTING)
	_lighting()

	# View transformation
	x_hat = (1, 0, 0)
	y_hat = (0, 1, 0)
	z_hat = (0, 0, 1)
	gluLookAt (
		cam_loc[0], cam_loc[1], cam_loc[2], 
		cam_trg[0], cam_trg[1], cam_trg[2], 
		y_hat[0], y_hat[1], y_hat[2])
	glTranslatef(*cam_trg)
	glRotatef(orbit_x, *x_hat)
	glRotatef(orbit_y, *y_hat)
	glRotatef(orbit_z, *z_hat)
	glTranslatef(*(-1.0*val for val in cam_trg))

def _use_light(color = [0.1, 0.1, 0.75, 1.0], 
			position = [4.0, 4.0,  4.0, 0.0], 
			specular = [1.0, 1.0,  1.0, 1.0], 
			dex = 0):
	lights = [	GL_LIGHT0, GL_LIGHT1, GL_LIGHT2, GL_LIGHT3, 
				GL_LIGHT4, GL_LIGHT5, GL_LIGHT6, GL_LIGHT7	]
	glLightfv(lights[dex], GL_SPECULAR, specular)
	glLightfv(lights[dex], GL_POSITION, position)
	glLightfv(lights[dex], GL_DIFFUSE, color)
	glEnable(lights[dex])

def _lighting(shade = 'flat', lighting = False):
	ambientColor = [0.2, 0.2, 0.2, 1.0]
	glLightModelfv(GL_LIGHT_MODEL_AMBIENT, ambientColor)
	glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, 1)
	mat_shininess = [50.0]
	mat_specular = [1.0, 1.0, 1.0, 1.0]
	glMaterialfv(GL_FRONT, GL_SPECULAR, mat_specular)
	glMaterialfv(GL_FRONT, GL_SHININESS, mat_shininess)
	if shade == 'smooth': glShadeModel(GL_SMOOTH)
	elif shade == 'flat': glShadeModel(GL_FLAT)
	if lighting: glEnable(GL_LIGHTING)
	else: glDisable(GL_LIGHTING)
	_use_light()
	glEnable(GL_NORMALIZE)

def _culling():
	glEnable(GL_CULL_FACE)
	glCullFace(GL_BACK)
	glFrontFace(GL_CW)
	#glFrontFace(GL_CCW)

def _depth():
	glEnable(GL_DEPTH_TEST)
	glDepthMask(GL_TRUE)
	glDepthFunc(GL_LEQUAL)
	glDepthRange(0.0, 1.0)
	glClearDepth(1.0)

def set_projection_matrix(x, y, w, h, zoom, diam = 2, 
						c = (0, 0, 0), ortho = True):

	glViewport(x, y, w, h)
	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()

	if ortho:
		x0 = 1.5 + zoom
		if (w <= h): glOrtho(-x0, x0, -x0*h/w, x0*h/w, -10.0, 10.0)
		else: glOrtho(-x0*w/h, x0*w/h, -x0, x0, -10.0, 10.0)
		return

		diam += zoom
		zNear = 0.001
		zFar = zNear + 2*diam
		left = c[0] - diam
		right = c[0] + diam
		bottom = c[2] - diam
		top = c[2] + diam
		glOrtho(left, right, bottom, top, zNear, zFar)

	else:
		gluPerspective(50.0*zoom, 
			float(width)/float(height), zNear, zFar)

def post_draw():
	glutSwapBuffers()

def redisp_leave_funcs():
	return glutPostRedisplay, glutLeaveMainLoop

def start_main():
	glutMainLoop()

def prep_list():
	genList = glGenLists(1)
	glNewList(genList, GL_COMPILE)
	return genList

def post_list():
	glEndList()

def draw_line(start = (0, 0, 0), end = (1, 0, 0), 
		color = (1,0,0,1), width = 2.0, norm = None):
	#glPushMatrix()
	glLineWidth(width)
	glBegin(GL_LINES)
	glColor4fv(color)
	if not norm is None:
		glNormal3fv(norm)
	glVertex3fv(start)
	glVertex3fv(end)
	glEnd()
	#glPopMatrix()

def draw_axes():
	draw_line(start = (0, 0, 0), end = (1, 0, 0), 
				color = (1,0,0,1), width = 2.0)
	draw_line(start = (0, 0, 0), end = (0, 1, 0), 
				color = (0,1,0,1), width = 2.0)
	draw_line(start = (0, 0, 0), end = (0, 0, 1), 
				color = (0,0,1,1), width = 2.0)

def draw_dot_field(x_, y_, z_, p_, color = (1, 1, 1)):
	locations = [(x, y, z, (xdex, ydex, zdex)) 
					for xdex, x in enumerate(x_) 
					for ydex, y in enumerate(y_) 
					for zdex, z in enumerate(z_)]
	for dot in locations:
		coord = dot[3]
		p = p_[coord[0], coord[1], coord[2]]
		glPushMatrix()
		glTranslatef(dot[0], dot[1], dot[2])
		draw_dot(color = color)
		glPopMatrix()

def draw_arrow_field(x_, y_, z_, u_, v_, w_, s = 0.25, 
		color = (0,0,1), width = 1.5, head_angle = 90):
	magnitudes = [lm.length(vec) for vec in 
		[(u_[x,y,z],v_[x,y,z],w_[x,y,z]) for 
			x in x_ for y in y_ for z in z_]]
	#magnitudes = [val for val in magnitudes if not val == 0]
	print min(magnitudes), max(magnitudes)
	vel_max = max(magnitudes)
	for u_dex, x in enumerate(x_):
		for v_dex, y in enumerate(y_):
			for w_dex, z in enumerate(z_):
				u = u_[u_dex, v_dex, w_dex]
				v = v_[u_dex, v_dex, w_dex]
				w = w_[u_dex, v_dex, w_dex]
				glPushMatrix()
				glTranslatef(x, y, z)
				conv = lm.length((u, v, w))
				if conv:

					#pdb.set_trace()
					mag_scale = 2.0*conv/vel_max
					#print mag_scale, 1, 1, conv, vel_max

					conv = 1.0/conv
					dir_ = (u*conv, v*conv, w*conv)
					x_hat = (1, 0, 0)
					q_hat = np.cross(x_hat, dir_)
					if lm.length(q_hat):
						q_hat = q_hat/lm.length(q_hat)
						ang = lm.angle(x_hat, dir_, unit = 'degree')
						glScalef(mag_scale, 1, 1)
						glRotatef(ang, *q_hat)

					glScalef(s, s, s)
					draw_line(start = (0, 0, 0), end = x_hat, 
								color = color, width = width)
					glTranslatef(*x_hat)
					glRotatef(head_angle, *x_hat)
					draw_triangle(color = color)

				else: draw_dot(color = (1, 0, 0))
				glPopMatrix()

def draw_dot(x = 0, y = 0, z = 0, color = (1, 1, 1), size = 4):
	#glPushMatrix()
	glPointSize(size)
	glBegin(GL_POINTS)
	glColor3f(*color)
	glVertex3f(x, y, z)
	glEnd()
	#glPopMatrix()

def draw_triangle(color = (0, 1, 0)):
	#glPushMatrix()
	glBegin(GL_TRIANGLES)
	glColor3f(*color)
	glVertex3f(0, 0,  0.5)
	glVertex3f(1, 0, 0)
	glVertex3f(0, 0, -0.5)
	glEnd()
	#glPopMatrix()

def draw_rectangle(bbox1, bbox2, color = (0.1,0.1,0.1,1.0), 
		normal = None, border = True, border_width = 4.0, 
					border_color = (0.1,0.1,0.1,1.0)):

	def make_coord(x, y, d1, d2):
		tup = np.zeros(3)
		tup[d1] = x
		tup[d2] = y
		return tuple(tup.tolist())

	_is_ = [1 if x == y else 0 for x, y in zip(bbox1, bbox2)]
	n = _is_.index(1)
	ds = [d for d in range(3) if not d == n]
	d1, d2 = ds[0], ds[1]
	x0, x1 = bbox1[d1], bbox2[d1]
	y0, y1 = bbox1[d2], bbox2[d2]
	n_offset = bbox1[n]
	coord1 = [x0, x0 + x1, x0 + x1, x0]
	coord2 = [y0 + y1, y0 + y1, y0, y0]
	coords = [make_coord(x, y, d1, d2) 
		for x, y in zip(coord1, coord2)]

	#glPushMatrix()
	glTranslatef(*(n_offset if is_ else 0 for is_ in _is_))
	glColor4f(*color)
	glBegin(GL_QUADS)
	#print 'rnorm', normal, _is_
	if normal is None: glNormal3f(*_is_)
	else: glNormal3f(*normal)
	#glNormal3f(*_is_)
	[glVertex3f(*coord) for coord in coords]
	glEnd()
	#glPopMatrix()

	if border:
		coords.append(coords[0])
		for ve in range(4):
			coord1, coord2 = coords[ve], coords[ve+1]
			draw_line(coord1, coord2, border_color, border_width, normal)

def draw_primitive(type_, rot, params = {}):
	glPushMatrix()
	glMultMatrixd(rot)
	if type_ == 'capsule':
		draw_capsule(params['radius'], params['length'])

	elif type_ == 'box': draw_box(params['boxlengths'])
	glPopMatrix()

def draw_sphere(r, lats, longs):
	for i in range(lats + 1):
		lat0 = math.pi * (-0.5 + float(i - 1) / lats)
		z0 = math.sin(lat0)
		zr0 = math.cos(lat0)

		lat1 = math.pi * (-0.5 + float(i) / lats)
		z1 = math.sin(lat1)
		zr1 = math.cos(lat1)

		glBegin(GL_QUAD_STRIP)
		for j in range(longs + 1):
			lng = 2 * math.pi * float(j - 1) / longs
			x = math.cos(lng)
			y = math.sin(lng)

			glNormal3f(r * x * zr0, r * y * zr0, r * z0)
			glVertex3f(r * x * zr0, r * y * zr0, r * z0)
			glNormal3f(r * x * zr1, r * y * zr1, r * z1)
			glVertex3f(r * x * zr1, r * y * zr1, r * z1)

		glEnd()

def draw_cylinder(r, h, sectors, rings):
	for i in range(sectors):
		theta = float(i)*2.0*math.pi
		nextTheta = float(i+1)*2.0*math.pi
		glBegin(GL_TRIANGLE_STRIP)
		#/*vertex at middle of end */
		glVertex3f(0.0, h, 0.0)
		#/*vertices at edges of circle*/
		glVertex3f(r*math.cos(theta), h, r*math.sin(theta))
		glVertex3f(r*math.cos(nextTheta), h, r*math.sin(nextTheta))
		glEnd()
		glBegin(GL_QUADS)
		glVertex3f(r*math.cos(theta), h, r*math.sin(theta))
		glVertex3f(r*math.cos(nextTheta), h, r*math.sin(nextTheta))
		glVertex3f(r*math.cos(nextTheta), -h, r*math.sin(nextTheta))
		glVertex3f(r*math.cos(theta), -h, r*math.sin(theta))
		glEnd()
		glBegin(GL_TRIANGLE_STRIP)
		#/* the same vertices at the bottom of the cylinder*/
		glVertex3f(r*math.cos(nextTheta), -h, r*math.sin(nextTheta))
		glVertex3f(r*math.cos(theta), -h, r*math.sin(theta))
		glVertex3f(0.0, -h, 0.0)
		glEnd()

def draw_capsule(radius, length):
	h = length
	r = radius
	d_vec = (0, 0, 1)
	glColor3f(0.0,1.0,0.0)

	glPushMatrix()
	trans_ = (h*0.5*val for val in d_vec)
	glTranslatef(*trans_)
	draw_sphere(r, 16, 16)
	glPopMatrix()

	glPushMatrix()
	trans_ = (-h*0.5*val for val in d_vec)
	glTranslatef(*trans_)
	draw_sphere(r, 16, 16)
	glPopMatrix()

	#qobj = gluNewQuadric();
	#gluQuadricDrawStyle(qobj, GLU_FILL); 
	#gluQuadricNormals(qobj, GLU_SMOOTH);
	glPushMatrix()
	glTranslatef(0.0, 0.0, -h*0.5)
	#gluCylinder(qobj, r, r, h, 16, 4);
	draw_cylinder(r, h, 16, 4)
	glPopMatrix()

def draw_box(boxlengths):
	def invert(vec): return (-1*x for x in vec)

	glPushMatrix()

	sx,sy,sz = boxlengths
	glScalef(sx, sy, sz)
	d = 0.5
	x_hat = (1, 0, 0)
	y_hat = (0, 1, 0)
	z_hat = (0, 0, 1)
	x_hat_n = invert(x_hat)
	y_hat_n = invert(y_hat)
	z_hat_n = invert(z_hat)
	glColor3f(1.0,0.0,1.0)

	glBegin(GL_QUADS)# Start Drawing The Cube
	glColor3f(0.0,1.0,0.0)# Set The Color To Blue
	glNormal3f(*y_hat)
	glVertex3f( d, d,-d)# Top Right Of The Quad (Top)
	glVertex3f(-d, d,-d)# Top Left Of The Quad (Top)
	glVertex3f(-d, d, d)# Bottom Left Of The Quad (Top)
	glVertex3f( d, d, d)# Bottom Right Of The Quad (Top)

	glColor3f(1.0,0.5,0.0)# Set The Color To Orange
	glNormal3f(*y_hat_n)
	glVertex3f( d,-d, d)# Top Right Of The Quad (Bottom)
	glVertex3f(-d,-d, d)# Top Left Of The Quad (Bottom)
	glVertex3f(-d,-d,-d)# Bottom Left Of The Quad (Bottom)
	glVertex3f( d,-d,-d)# Bottom Right Of The Quad (Bottom)

	glColor3f(1.0,0.0,0.0)# Set The Color To Red
	glNormal3f(*z_hat)
	glVertex3f( d, d, d)# Top Right Of The Quad (Front)
	glVertex3f(-d, d, d)# Top Left Of The Quad (Front)
	glVertex3f(-d,-d, d)# Bottom Left Of The Quad (Front)
	glVertex3f( d,-d, d)# Bottom Right Of The Quad (Front)

	glColor3f(1.0,1.0,0.0)# Set The Color To Yellow
	glNormal3f(*z_hat_n)
	glVertex3f( d,-d,-d)# Bottom Left Of The Quad (Back)
	glVertex3f(-d,-d,-d)# Bottom Right Of The Quad (Back)
	glVertex3f(-d, d,-d)# Top Right Of The Quad (Back)
	glVertex3f( d, d,-d)# Top Left Of The Quad (Back)

	glColor3f(0.0,0.0,1.0)# Set The Color To Blue
	glNormal3f(*x_hat_n)
	glVertex3f(-d, d, d)# Top Right Of The Quad (Left)
	glVertex3f(-d, d,-d)# Top Left Of The Quad (Left)
	glVertex3f(-d,-d,-d)# Bottom Left Of The Quad (Left)
	glVertex3f(-d,-d, d)# Bottom Right Of The Quad (Left)

	glColor3f(1.0,0.0,1.0)# Set The Color To Violet
	glNormal3f(*x_hat)
	glVertex3f( d, d,-d)# Top Right Of The Quad (Right)
	glVertex3f( d, d, d)# Top Left Of The Quad (Right)
	glVertex3f( d,-d, d)# Bottom Left Of The Quad (Right)
	glVertex3f( d,-d,-d)# Bottom Right Of The Quad (Right)
	glEnd()# Done Drawing The Quad

	glPopMatrix()



def compile_vertex_shader(source):
	"""Compile a vertex shader from source."""
	vertex_shader = glCreateShader(GL_VERTEX_SHADER)
	glShaderSource(vertex_shader, source)
	glCompileShader(vertex_shader)
	# check compilation error
	result = glGetShaderiv(vertex_shader, GL_COMPILE_STATUS)
	if not(result):raise RuntimeError(glGetShaderInfoLog(vertex_shader))
	return vertex_shader
 
def compile_fragment_shader(source):
	"""Compile a fragment shader from source."""
	fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
	glShaderSource(fragment_shader, source)
	glCompileShader(fragment_shader)
	# check compilation error
	result = glGetShaderiv(fragment_shader, GL_COMPILE_STATUS)
	if not(result):raise RuntimeError(glGetShaderInfoLog(fragment_shader))
	return fragment_shader
 
def link_shader_program(vertex_shader, fragment_shader):
	program = glCreateProgram()
	glAttachShader(program, vertex_shader)
	glAttachShader(program, fragment_shader)
	glLinkProgram(program)
	# check linking error
	result = glGetProgramiv(program, GL_LINK_STATUS)
	if not(result): raise RuntimeError(glGetProgramInfoLog(program))
	return program

# Vertex shader
VS_phong = '''
	#version 400
	
	layout (location = 0) in vec4 VertexPosition;
	layout (location = 1) in vec4 VertexNormal;
	
	out vec3 LightIntensity;
	//flat out vec3 LightIntensity;
	
	struct LightInfo {
	  vec4 Position; // Light position in eye coords.
	  vec3 La; // Ambient light intensity
	  vec3 Ld; // Diffuse light intensity
	  vec3 Ls; // Specular light intensity
	};
	uniform LightInfo Light;
	
	struct MaterialInfo {
	  vec3 Ka; // Ambient reflectivity
	  vec3 Kd; // Diffuse reflectivity
	  vec3 Ks; // Specular reflectivity
	  float Shininess; // Specular shininess factor
	};
	uniform MaterialInfo Material;
	
	uniform mat4 ModelViewMatrix;
	uniform mat3 NormalMatrix;
	uniform mat4 ProjectionMatrix;
	uniform mat4 MVP;
	
	void getEyeSpace( out vec3 norm, out vec4 position )
	{
	  norm = normalize( NormalMatrix * VertexNormal.xyz);
	  position = ModelViewMatrix * VertexPosition;
	}
	
	vec3 phongModel( vec4 position, vec3 norm )
	{
	  //vec4 li_pos = ModelViewMatrix * Light.Position;
	  vec3 s = normalize(vec3(Light.Position - position));
	  //vec3 s = normalize(vec3(li_pos - position));
	  vec3 v = normalize(-position.xyz);
	  vec3 r = reflect( -s, norm );
	  vec3 ambient = Light.La * Material.Ka;
	  float sDotN = max( dot(s,norm), 0.0 );
	  vec3 diffuse = Light.Ld * Material.Kd * sDotN;
	  vec3 spec = vec3(0.0);
	  if( sDotN > 0.0 )
		  spec = Light.Ls * Material.Ks *
				 pow( max( dot(r,v), 0.0 ), Material.Shininess );
	  return ambient + diffuse + spec;
	}
	
	void main()
	{
	  vec3 eyeNorm;
	  vec4 eyePosition;
	  // Get the position and normal in eye space
	  getEyeSpace(eyeNorm, eyePosition);
	  // Evaluate the lighting equation.
	  LightIntensity = phongModel( eyePosition, eyeNorm );
	  gl_Position = MVP * VertexPosition;
	}	
'''

# Fragment shader
FS_ads = """
#version 400
	in vec3 LightIntensity;
	//flat in vec3 LightIntensity;
	layout( location = 0 ) out vec4 FragColor;
	void main() {
		FragColor = vec4(LightIntensity, 1.0);
	}
"""

FS_ads_dir_illum = '''
	#version 400
	in vec3 LightIntensity;
	//flat in vec3 LightIntensity;
	layout( location = 0 ) out vec4 FragColor;

	vec3 DirectIllumination(vec3 P, vec3 N, vec3 lightCentre, float lightRadius, vec3 lightColour, float cutoff)
	{
		// calculate normalized light vector and distance to sphere light surface
		float r = lightRadius;
		vec3 L = lightCentre - P;
		float distance = length(L);
		float d = max(distance - r, 0);
		L /= distance;
		 
		// calculate basic attenuation
		float denom = d/r + 1;
		float attenuation = 1 / (denom*denom);
		 
		// scale and bias attenuation such that:
		//   attenuation == 0 at extent of max influence
		//   attenuation == 1 when d == 0
		attenuation = (attenuation - cutoff) / (1 - cutoff);
		attenuation = max(attenuation, 0);
		 
		float dot = max(dot(L, N), 0);
		return lightColour * dot * attenuation;
	}

	void main() {
		FragColor = vec4(LightIntensity, 1.0);
	}
'''

def get_shader():
	vs = compile_vertex_shader(VS_phong)
	fs = compile_fragment_shader(FS_ads_dir_illum)
	shaders_program = link_shader_program(vs, fs)
	return shaders_program

class material(object):
	def __init__(self, shininess = 0.15, 
			dif_refl = cgt.vec3([0.8,0.8,0.8]), 
			amb_refl = cgt.vec3([0.8,0.8,0.8]), 
			spe_refl = cgt.vec3([0.8,0.8,0.8])):
		self.dif_refl = dif_refl
		self.amb_refl = amb_refl
		self.spe_refl = spe_refl
		self.shininess = shininess

	def _get_uniforms_callback_(self, shader):
		def _uniform_callback_():
			Ka_unif = glGetUniformLocation(shader, "Material.Ka")
			Kd_unif = glGetUniformLocation(shader, "Material.Kd")
			Ks_unif = glGetUniformLocation(shader, "Material.Ks")
			Shininess_unif = glGetUniformLocation(
					shader, "Material.Shininess")
			glUniform3fv(Ka_unif, 1, np.array(self.amb_refl))
			glUniform3fv(Kd_unif, 1, np.array(self.dif_refl))
			glUniform3fv(Ks_unif, 1, np.array(self.spe_refl))
			glUniform1f(Shininess_unif, self.shininess)
		return _uniform_callback_

def _get_uniforms_callback_transform_(self, shader):
	def _transform_unifs_():
		M_unif = glGetUniformLocation(shader, 'ModelViewMatrix')
		N_unif = glGetUniformLocation(shader, 'NormalMatrix')
		P_unif = glGetUniformLocation(shader, 'ProjectionMatrix')
		MVP_unif = glGetUniformLocation(shader, 'MVP')
		glUniformMatrix4fv(M_unif,1,GL_FALSE,self._mvp_matrix_)
		glUniformMatrix3fv(N_unif,1,GL_FALSE,self._normal_matrix_)
		glUniformMatrix4fv(P_unif,1,GL_FALSE,self._projection_matrix_)
		glUniformMatrix4fv(MVP_unif,1,GL_FALSE,self._mvp_matrix_)
	return _transform_unifs_

def _get_uniforms_callback_light_(self, shader):
	def _uniform_callback_():
		pos_unif = glGetUniformLocation(shader, "Light.Position")
		La_unif = glGetUniformLocation(shader, "Light.La")
		Ld_unif = glGetUniformLocation(shader, "Light.Ld")
		Ls_unif = glGetUniformLocation(shader, "Light.Ls")
		glUniform4fv(pos_unif, 1, np.array(self._get_position_()))
		glUniform3fv(La_unif, 1, np.array(self.amb_int))
		glUniform3fv(Ld_unif, 1, np.array(self.dif_int))
		glUniform3fv(Ls_unif, 1, np.array(self.spe_int))
	return _uniform_callback_

def set_shader(shader, uniform_callbacks):
	glUseProgram(shader)
	for set_unif in uniform_callbacks.keys():
		uniform_callbacks[set_unif]()

def get_vbo_(data):
	_vbo = vbo.VBO(data=data, 
		usage=GL_DYNAMIC_DRAW, 
		target=GL_ARRAY_BUFFER)
	_vbo.bind()
	return _vbo




def _handle_one_vbo_(one, adex, comps, offset = None):
	one.bind()
	glEnableVertexAttribArray(adex)
	glVertexAttribPointer(adex, comps, 
		GL_FLOAT, GL_FALSE, 0, offset)

def _unhandle_one_vbo_(one, adex):
	one.unbind()
	glDisableVertexAttribArray(adex)

def render_gl_points(pos_vbo, col_vbo, pt_count):
	glEnable(GL_POINT_SMOOTH)
	glPointSize(2)
	glEnable(GL_BLEND)
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

	_handle_one_vbo_(pos_vbo, 0, 4)
	_handle_one_vbo_(col_vbo, 1, 4)

	glDrawArrays(GL_POINTS, 0, pt_count)

	_unhandle_one_vbo_(pos_vbo, 0)
	_unhandle_one_vbo_(col_vbo, 1)

	glDisable(GL_BLEND)

def render_gl_primitive(ver_vbo, col_vbo, orgs):
	_handle_one_vbo_(ver_vbo, 0, 4)
	_handle_one_vbo_(col_vbo, 1, 4)

	o_count = 0
	for org_ in orgs:
		org = org_[0]
		count = org_[1]
		if org == 'lines':
			glDrawArrays(GL_LINES, o_count, count)
			#glDrawRangeElements(GL_LINES,start,end,count,type,indices)
		elif org == 'fan':
			glDrawArrays(GL_TRIANGLE_FAN, o_count, count)
		elif org == 'strip':
			glDrawArrays(GL_TRIANGLE_STRIP, o_count, count)
		elif org == 'free':
			glDrawArrays(GL_TRIANGLES, o_count, count)
		o_count += count

	#glDrawElementsBaseVertex( mode , count , type , indices , basevertex )

	_unhandle_one_vbo_(ver_vbo, 0)
	_unhandle_one_vbo_(col_vbo, 1)

def render_gl_elements(orgs):
	for org_ in orgs:
		org = org_[0]
		if org == 'lines':
			mode = GL_LINES

		glMultiDrawElementsIndirect( mode , type , indirect , drawcount , stride )

'''
it has become evident that everything should be represented as verts of triangles
 which get multiplied by model matrices to get to world space
all the vertices should be in one big global render targeted data set
and each object has a set of ranges of indices corresponding to its verts/colors
when you call render on an object, it attempts to render that object from the 
 large global vert set which is stored on the gpu
a 1-1 global indices data set can also remain bounds all the time
within that structure of points, an offset and a range can specify the verts
related to a particular object
so render calls are glDrawElementsBaseVertex calls, one per object
 with a call to set_shader updating the model matrix for that object as well


can the vbos be bound once with ~4mb of space and never bound/unbound again?
'''

def get_primitive(form = 'box'):
	if form == 'box': return get_primitive_box()
	if form == 'cone': return get_primitive_cone()
	if form == 'axes': return get_primitive_axes()

def get_primitive_axes():
	v00 = (0, 0, 0, 1)
	v01 = (1, 0, 0, 1)
	v10 = (0, 0, 0, 1)
	v11 = (0, 1, 0, 1)
	v20 = (0, 0, 0, 1)
	v21 = (0, 0, 1, 1)
	n00 = (1, 1, 1, 1)
	n01 = (1, 1, 1, 1)
	n10 = (1, 1, 1, 1)
	n11 = (1, 1, 1, 1)
	n20 = (1, 1, 1, 1)
	n21 = (1, 1, 1, 1)
	vrt = np.array([v00,v01,v10,v11,v20,v21], dtype=np.float32)
	nrm = np.array([n00,n01,n10,n11,n20,n21], dtype=np.float32)
	return vrt, nrm, [('lines', 3)]

def get_primitive_box():
	#return ver, col arrays representing a unit cube
	num = 8*2
	pos = np.ndarray((num, 4), dtype=np.float32)
	pos[0] = [0,0,0,1]
	pos[1] = [1,0,0,1]
	pos[2] = [1,1,0,1]
	pos[3] = [0,1,0,1]
	pos[4] = [0,1,1,1]
	pos[5] = [0,0,1,1]
	pos[6] = [1,0,1,1]
	pos[7] = [1,0,0,1]

	pos[8]  = [1,1,1,1]
	pos[9]  = [0,1,1,1]
	pos[10] = [0,0,1,1]
	pos[11] = [1,0,1,1]
	pos[12] = [1,0,0,1]
	pos[13] = [1,1,0,1]
	pos[14] = [0,1,0,1]
	pos[15] = [0,1,1,1]

	nrm = np.ndarray((num, 4), dtype=np.float32)
	nrm[0] = [-1,-1,-1,1]
	nrm[1] = [ 1,-1,-1,1]
	nrm[2] = [ 1, 1,-1,1]
	nrm[3] = [-1, 1,-1,1]
	nrm[4] = [-1, 1, 1,1]
	nrm[5] = [-1,-1, 1,1]
	nrm[6] = [ 1,-1, 1,1]
	nrm[7] = [ 1,-1,-1,1]

	nrm[8]  = [ 1, 1, 1,1]
	nrm[9]  = [-1, 1, 1,1]
	nrm[10] = [-1,-1, 1,1]
	nrm[11] = [ 1,-1, 1,1]
	nrm[12] = [ 1,-1,-1,1]
	nrm[13] = [ 1, 1,-1,1]
	nrm[14] = [-1, 1,-1,1]
	nrm[15] = [-1, 1, 1,1]
	# temporarily use this to provide normal information
	#nrm[:,0] = 0.0
	#nrm[:,1] = 0.5
	#nrm[:,2] = 1.0
	#nrm[:,3] = 1.0
	return pos, nrm, [('fan', 8), ('fan', 8)]

def get_primitive_cone(sections = 8):
	#return ver, nrm arrays representing a unit cone -> NOT DONE!!
	num = 8*2
	pos = np.ndarray((num, 4), dtype=np.float32)
	pos[0] = [0,0,0,1]
	pos[1] = [1,0,0,1]
	pos[2] = [1,1,0,1]
	pos[3] = [0,1,0,1]
	pos[4] = [0,1,1,1]
	pos[5] = [0,0,1,1]
	pos[6] = [1,0,1,1]
	pos[7] = [1,0,0,1]

	pos[8]  = [1,1,1,1]
	pos[9]  = [0,1,1,1]
	pos[10] = [0,0,1,1]
	pos[11] = [1,0,1,1]
	pos[12] = [1,0,0,1]
	pos[13] = [1,1,0,1]
	pos[14] = [0,1,0,1]
	pos[15] = [0,1,1,1]

	nrm = np.ndarray((num, 4), dtype=np.float32)
	nrm[0] = [-1,-1,-1,1]
	nrm[1] = [ 1,-1,-1,1]
	nrm[2] = [ 1, 1,-1,1]
	nrm[3] = [-1, 1,-1,1]
	nrm[4] = [-1, 1, 1,1]
	nrm[5] = [-1,-1, 1,1]
	nrm[6] = [ 1,-1, 1,1]
	nrm[7] = [ 1,-1,-1,1]

	nrm[8]  = [ 1, 1, 1,1]
	nrm[9]  = [-1, 1, 1,1]
	nrm[10] = [-1,-1, 1,1]
	nrm[11] = [ 1,-1, 1,1]
	nrm[12] = [ 1,-1,-1,1]
	nrm[13] = [ 1, 1,-1,1]
	nrm[14] = [-1, 1,-1,1]
	nrm[15] = [-1, 1, 1,1]
	return pos, nrm, [('fan', 8), ('fan', 8)]




#TRASH BELOW?
null = c_void_p(0)
def use_vbo(vbo_, shader, v_count = 3):
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	vbo_.bind()
	glEnableVertexAttribArray(0)
	glEnableVertexAttribArray(1)
	glVertexAttribPointer(0, 4, GL_FLOAT, GL_FALSE, 0, None)
	glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 0, c_void_p(v_count*16))
	glDrawArrays(GL_LINE_STRIP, 0, v_count)
	#glDrawArrays(GL_TRIANGLE_STRIP, 0, v_count)
	#glDrawArrays(GL_TRIANGLES, 0, v_count)
	glDisableVertexAttribArray(0)
	glDisableVertexAttribArray(1)




#old default object for gl window
#else: GL.glCallList(self.object_)
'''
	def make_default_object(self):
		genList = GL.glGenLists(1)
		GL.glNewList(genList, GL.GL_COMPILE)

		GL.glBegin(GL.GL_QUADS)

		x1 = +0.06
		y1 = -0.14
		x2 = +0.14
		y2 = -0.06
		x3 = +0.08
		y3 = +0.00
		x4 = +0.30
		y4 = +0.22

		self.quad(x1, y1, x2, y2, y2, x2, y1, x1)
		self.quad(x3, y3, x4, y4, y4, x4, y3, x3)

		self.extrude(x1, y1, x2, y2)
		self.extrude(x2, y2, y2, x2)
		self.extrude(y2, x2, y1, x1)
		self.extrude(y1, x1, x1, y1)
		self.extrude(x3, y3, x4, y4)
		self.extrude(x4, y4, y4, x4)
		self.extrude(y4, x4, y3, x3)

		Pi = 3.14159265358979323846
		NumSectors = 200

		for i in range(NumSectors):
			angle1 = (i * 2 * Pi) / NumSectors
			x5 = 0.30 * math.sin(angle1)
			y5 = 0.30 * math.cos(angle1)
			x6 = 0.20 * math.sin(angle1)
			y6 = 0.20 * math.cos(angle1)

			angle2 = ((i + 1) * 2 * Pi) / NumSectors
			x7 = 0.20 * math.sin(angle2)
			y7 = 0.20 * math.cos(angle2)
			x8 = 0.30 * math.sin(angle2)
			y8 = 0.30 * math.cos(angle2)

			self.quad(x5, y5, x6, y6, x7, y7, x8, y8)

			self.extrude(x6, y6, x7, y7)
			self.extrude(x8, y8, x5, y5)

		GL.glEnd()
		GL.glEndList()

		return genList

	def quad(self, x1, y1, x2, y2, x3, y3, x4, y4):
		self.qglColor(self.trolltechGreen)

		GL.glVertex3d(x1, y1, -0.05)
		GL.glVertex3d(x2, y2, -0.05)
		GL.glVertex3d(x3, y3, -0.05)
		GL.glVertex3d(x4, y4, -0.05)

		GL.glVertex3d(x4, y4, +0.05)
		GL.glVertex3d(x3, y3, +0.05)
		GL.glVertex3d(x2, y2, +0.05)
		GL.glVertex3d(x1, y1, +0.05)

	def extrude(self, x1, y1, x2, y2):
		self.qglColor(self.trolltechGreen.darker(250 + int(100 * x1)))

		GL.glVertex3d(x1, y1, +0.05)
		GL.glVertex3d(x2, y2, +0.05)
		GL.glVertex3d(x2, y2, -0.05)
		GL.glVertex3d(x1, y1, -0.05)


class scene_node:
    def __init__(self,children = None):
        if children:
            self.children = children
        else:
            self.children = []
        self.add = self.children.append
    def draw(self):
        for x in self.children:
            x.draw()

class translation_node(scene_node):
    def __init__(self,offset,children = None):
        scene_node.__init__(self,children)
        self.offset = offset
    def draw(self):
        glPushMatrix()
        if callable(self.offset): glTranslate(*self.offset())
        else: glTranslate(*self.offset)
        scene_node.draw(self)
        glPopMatrix()

class rotation_node(scene_node):
    def __init__(self,angle,children = None):
        scene_node.__init__(self,children)
        self.angle = angle
    def draw(self):
        glPushMatrix()
        if callable(self.angle):
            glRotate(self.angle(),0,0,1.0)
        else:
            glRotate(self.angle,0,0,1.0)
        scene_node.draw(self)
        glPopMatrix()

class scale_node(scene_node):
    def __init__(self,factor,children = None):
        scene_node.__init__(self,children)
        self.factor = factor
    def draw(self):
        glPushMatrix()
        if callable(self.factor):
            glScale(*self.factor())
        else:
            glScale(*self.factor)
        scene_node.draw(self)
        glPopMatrix()

class node(scene_node):

	def __init__(self,func):
		scene_node.__init__(self)
		self.func = func

	def _get_center_(self):
		return np.array([0,0,0])

	def _get_extents_(self):
		return np.array([0,0,0])

	def _get_scales_(self):
		return np.array([1,1,1])

	def _get_position_(self):
		return np.array([0,0,0])

	def _make_ode_(self, ode_bucket):
		try:
			for obj in self.children: obj._make_ode_(ode_bucket)
		except AttributeError: pass

	def _update_(self):
		pass

	def draw(self):
		glPushMatrix()
		self.func()
		glPopMatrix()

class scene_axes(node):
	def __init__(self):
		node.__init__(self, draw_axes)


'''




if __name__ == '__main__':
	print 'Hush - This is a library!'

if __name__ == 'libs.modular_core.libopenglutilities':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb


