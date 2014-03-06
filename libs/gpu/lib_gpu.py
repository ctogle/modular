#import pyopencl as cl; gpu_support = True
try: import pyopencl as cl; gpu_support = True; print 'gpu', gpu_support
except ImportError: cl = None; gpu_support = False; print 'gpu', gpu_support

import numpy
import os

lib_path = os.path.join(os.getcwd(), 'libs', 'gpu')
gpu_cl_extensions = {
	'addition' : os.path.join(lib_path, 
				'lib_gpu1to1addition.cl'), 
	'subtraction' : os.path.join(lib_path, 
				'lib_gpu1to1subtraction.cl'), 
	'multiplication' : os.path.join(lib_path, 
				'lib_gpu1to1multiplication.cl'), 
	'division' : os.path.join(lib_path, 
				'lib_gpu1to1division.cl')}

class CL:

	''' usage:
	example = CL()
	example.loadProgram('lib_gpu1to1addition.cl')
	example.popCorn()
	example.execute()
	'''
	def __init__(self, *args, **kwargs):
		global gpu_cl_extensions
		self.gpu_cl_extensions = gpu_cl_extensions
		#self.initialize(*args, **kwargs)

	def initialize(self, *args, **kwargs):
		platform = cl.get_platforms()
		gpu_devices = platform[1].get_devices(
			device_type = cl.device_type.GPU)
		self.ctx = cl.Context(devices = gpu_devices)
		#self.ctx = cl.create_some_context()
		self.queue = cl.CommandQueue(self.ctx)
		self.verify_cl_extension(*args, **kwargs)
		#print 'initialized gpu worker', self.gpu_cl_extension

	def loadProgram(self, filename):
		#read in the OpenCL source file as a string
		f = open(filename, 'r')
		fstr = ''.join(f.readlines())
		#create the program
		self.program = cl.Program(self.ctx, fstr).build()

	def verify_cl_extension(self, *args, **kwargs):
		if 'gpu_cl_extension' in kwargs.keys():
			self.gpu_cl_extension = self.gpu_cl_extensions[
								kwargs['gpu_cl_extension']]

		else: self.gpu_cl_extension = self.gpu_cl_extensions['addition']
		self.loadProgram(self.gpu_cl_extension)

	def popCorn(self, *args, **kwargs):
		mf = cl.mem_flags
		#initialize client side (CPU) arrays
		self.a = numpy.array(args[0], dtype=numpy.float32)
		self.b = numpy.array(args[1], dtype=numpy.float32)

		#create OpenCL buffers
		self.a_buf = cl.Buffer(self.ctx, 
			mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf = self.a)
		self.b_buf = cl.Buffer(self.ctx, 
			mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf = self.b)
		self.dest_buf = cl.Buffer(self.ctx, 
			mf.WRITE_ONLY, self.b.nbytes)

	def execute(self, *args, **kwargs):
		self.popCorn(*args, **kwargs)
		self.program.part1(self.queue, self.a.shape, None, 
					self.a_buf, self.b_buf, self.dest_buf)
		c = numpy.empty_like(self.a)
		cl.enqueue_read_buffer(self.queue, self.dest_buf, c).wait()
		return c

if __name__ == '__main__': print 'this is an awesome library'





