#import libs.modular_core.libfundamental as lfu
import modular_core.libfundamental as lfu

#import pyopencl as cl; gpu_support = True
if lfu.using_os('mac'):
	gpu_support = False; print 'gpu', gpu_support
else:
	try:
		import pyopencl as cl
		from pyopencl.tools import get_gl_sharing_context_properties
		gpu_support = True#; print 'gpu', gpu_support
	except ImportError: cl = None; gpu_support = False; print 'gpu', gpu_support

import sys 
import numpy as np
import os

import pdb

lib_path = os.path.join(os.getcwd(), 'libs', 'modular_core', 'gpu')
gpu_cl_extensions = {
	'addition' : os.path.join(lib_path, 
				'lib_gpu1to1addition.cl'), 
	'subtraction' : os.path.join(lib_path, 
				'lib_gpu1to1subtraction.cl'), 
	'multiplication' : os.path.join(lib_path, 
				'lib_gpu1to1multiplication.cl'), 
	'division' : os.path.join(lib_path, 
				'lib_gpu1to1division.cl'), 
	'particlesim' : os.path.join(lib_path, 
				'lib_gpuParticleSim.cl')}

class CL(object):

	def __init__(self, *args, **kwargs):
		global gpu_cl_extensions
		self.gpu_cl_extensions = gpu_cl_extensions
		self.initialize(*args, **kwargs)

	def initialize(self, *args, **kwargs):
		plats = cl.get_platforms()
		card_dex = len(plats) - 1
		if sys.platform == "darwin":
			self.ctx = cl.Context(properties=\
				get_gl_sharing_context_properties(),
										devices=[])
		else:
			props = [(cl.context_properties.PLATFORM,plats[card_dex])]+\
									get_gl_sharing_context_properties()
			try: self.ctx = cl.Context(properties=props, devices=None)
			except TypeError:
				print 'no GPU contexts will work properly...'; return
		self.queue = cl.CommandQueue(self.ctx)
		self.verify_cl_extension(*args, **kwargs)
		print 'initialized gpu worker using:', self.gpu_cl_extension_key
		print 'using:', plats[card_dex], 'given:', plats, 'as options'

	def load_program(self, filename):
		f = open(filename, 'r')
		fstr = ''.join(f.readlines())
		self.program = cl.Program(self.ctx, fstr).build()

	def verify_cl_extension(self, *args, **kwargs):
		if 'gpu_cl_extension' in kwargs.keys():
			self.gpu_cl_extension_key = kwargs['gpu_cl_extension']
			self.gpu_cl_extension = self.gpu_cl_extensions[
								self.gpu_cl_extension_key]

		else:
			self.gpu_cl_extension = self.gpu_cl_extensions['addition']
			self.gpu_cl_extension_key = 'addition'

		self.load_program(self.gpu_cl_extension)

	def load_data_gl(self, pos_vbo, col_vbo, vel):
		mf = cl.mem_flags
		self.pos_vbo = pos_vbo
		self.col_vbo = col_vbo
		self.pos = pos_vbo.data
		self.col = col_vbo.data
		self.vel = vel

		#Setup vertex buffer objects and share them with OpenCL as GLBuffers
		self.pos_vbo.bind()
		self.pos_cl = cl.GLBuffer(self.ctx, 
			mf.READ_WRITE, int(self.pos_vbo.buffers[0]))
		self.col_vbo.bind()
		self.col_cl = cl.GLBuffer(self.ctx, 
			mf.READ_WRITE, int(self.col_vbo.buffers[0]))

		#pure OpenCL arrays
		self.vel_cl = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=vel)
		self.pos_gen_cl = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=self.pos)
		self.vel_gen_cl = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=self.vel)
		self.queue.finish()

		# set up the list of GL objects to share with opencl
		self.gl_objects = [self.pos_cl, self.col_cl]

	def execute_gl(self, sub_intervals, dt):
		cl.enqueue_acquire_gl_objects(self.queue, self.gl_objects)

		global_size = (self.num,)
		local_size = None

		kernelargs = (	self.pos_cl, self.col_cl, self.vel_cl,
						self.pos_gen_cl, self.vel_gen_cl, dt)

		for i in xrange(0, sub_intervals):
			self.program.program__(self.queue, 
				global_size, local_size, *(kernelargs))

		cl.enqueue_release_gl_objects(self.queue, self.gl_objects)
		self.queue.finish()

	###
	#these work for 1 - 1 binary operations
	###
	def load_data(self, *args, **kwargs):
		mf = cl.mem_flags
		#initialize client side (CPU) arrays
		self.a = np.array(args[0], dtype=np.float32)
		self.b = np.array(args[1], dtype=np.float32)

		#create OpenCL buffers
		self.a_buf = cl.Buffer(self.ctx, 
			mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf = self.a)
		self.b_buf = cl.Buffer(self.ctx, 
			mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf = self.b)
		self.dest_buf = cl.Buffer(self.ctx, 
			mf.WRITE_ONLY, self.b.nbytes)

	def execute(self, *args, **kwargs):
		self.load_data(*args, **kwargs)
		self.program.program__(self.queue, self.a.shape, None, 
						self.a_buf, self.b_buf, self.dest_buf)
		c = np.empty_like(self.a)
		cl.enqueue_read_buffer(self.queue, self.dest_buf, c).wait()
		return c

	###
	###
	###

if __name__ == '__main__': print 'this is an awesome library'





