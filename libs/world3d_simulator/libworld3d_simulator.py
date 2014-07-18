import libs.modular_core.libfundamental as lfu
#import libs.modular_core.lib3dworld as l3d
import libs.world3d_simulator.lib3dworld as l3d
#import libs.modular_core.libopenglutilities as lgl
import libs.world3d_simulator.libopenglutilities as lgl
import libs.modular_core.libmath as lm
import libs.modular_core.libsettings as lset

import libs.gpu.lib_gpu as lgpu

import numpy as np
import traceback, sys, time

import pdb



if __name__ == 'libs.world3d_simulator.libworld3d_simulator':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'

def particle_fountain_np(num):
	pos = np.ndarray((num, 4), dtype=np.float32)
	col = np.ndarray((num, 4), dtype=np.float32)
	vel = np.ndarray((num, 4), dtype=np.float32)

	pos[:,0] = np.sin(np.arange(0., num) * 2.00 * np.pi / num) 
	pos[:,0] *= np.random.random_sample((num,)) / 3. + .2
	pos[:,2] = np.cos(np.arange(0., num) * 2.00 * np.pi / num) 
	pos[:,2] *= np.random.random_sample((num,)) / 3. + .2
	pos[:,1] = 0.
	pos[:,3] = 1.

	col[:,0] = 0.
	col[:,1] = 1.
	col[:,2] = 0.
	col[:,3] = 1.

	vel[:,0] = pos[:,0] * 2.
	vel[:,2] = pos[:,2] * 2.
	vel[:,1] = 3.
	vel[:,3] = np.random.random_sample((num, ))

	return pos, col, vel

class world3d_simulator(lfu.modular_object_qt):

	def __init__(self, *args, **kwargs):
		self.settings_manager = lset.settings_manager(
			parent = self, filename = 'world3d_simulator_settings.txt')
		self.settings = self.settings_manager.read_settings()
		lfu.modular_object_qt.__init__(self, *args, **kwargs)
		self._quit_ = True
		self.set_key_mapping(*args, **kwargs)

	def set_key_mapping(self, *args, **kwargs):

		def _keys_help():
			for key in mapping.keys():
				print 'key', key, '-', mapping[key][1]

		if 'key_mapping' in kwargs.keys():
			self.key_mapping = kwargs['key_mapping']
		else:
			self.key_mapping = {
				'q':(self.end_world, 'end simulation'), 
				'h':(_keys_help, 'display keys'), 
								}

	def start_world(self):
		if self._quit_:
			self._quit_ = False
			self.starttime_ = time.time()
			self.lasttime_ = self.starttime_
			gl_view_ = self.gl_view[0]
			#self.dt_ = 1.0/gl_view_.fps
			gl_view_.data_callback = self.opencl_data
			gl_view_.data_callback(gl_view_.camera.shader)
			gl_view_.draw_callback = self.opencl_draw
			gl_view_.idle_callback = self.opencl_idle
			gl_view_.key_callback = self.opencl_keys
			print 'the world has started...'
		else: print 'cant start the world twice!'

	def end_world(self):
		if not self._quit_:
			self._quit_ = True
			gl_view_ = self.gl_view[0]
			gl_view_.key_callback = None
			gl_view_.idle_callback = None
			gl_view_.draw_callback = None
			gl_view_.data_callback = None
			gl_view_.camera.reset()
			print 'the world has ended...'
		else: print 'cant end a nonexistent world!'

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['opengl_view'], 
				handles = [(self, 'gl_view')]))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['button_set'], 
				layout = 'horizontal', 
				labels = [['Start Simulation', 'End Simulation']], 
				bindings = [[self.start_world, self.end_world]]))
		lfu.modular_object_qt.set_settables(
			self, *args, from_sub = True)



	def opencl_keys(self, c, x, y):
		try: self.key_mapping[c][0]()
		except KeyError:
			if not c == '':
				traceback.print_exc(file=sys.stdout)
				print 'unrecognized key'

	def opencl_idle(self):
		#t = self.dt_ - (time.time() - self.lasttime_)
		#print 't', t
		#if t > 0: time.sleep(t)
		self.cle.execute_gl(self.sub_intervals, self.dt_)
		#for obj in bucket['objects']: obj._update_()
		#if self._ode_world_: los.ode_world_step(bucket['ode'])
		self.lasttime_ = time.time()
		return False

	def opencl_draw(self, shader = None):
		self.axes.draw_gl(shader)
		lgl.render_gl_points(self.cle.pos_vbo, 
			self.cle.col_vbo, self.cle.num)

	def opencl_data(self, shader = None):
		p_count = 500000
		dt = 0.01
		self.sub_intervals = 10
		self.dt_ = np.float32(dt/self.sub_intervals)
		(pos, col, vel) = particle_fountain_np(num = p_count)
		pos_vbo = lgl.get_vbo_(pos)
		col_vbo = lgl.get_vbo_(col)

		#create our OpenCL instance
		self.cle = lgpu.CL(gpu_cl_extension = 'particlesim')
		self.cle.num = p_count
		#self.cle.dt = np.float32(dt)
		self.cle.load_data_gl(pos_vbo, col_vbo, vel)

		self.axes = l3d.axes(shader = shader)





