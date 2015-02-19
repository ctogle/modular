import modular_core.libfundamental as lfu

import pyopencl as cl
import pdb,sys,os
import numpy as np

class kernal(lfu.mobject):

    def __call__(self,*args,**kwargs):
        print 'enact kernal!'
        pdb.set_trace()

    def __init__(self,*args,**kwargs):
        self.kernal = lfu.get_resource_path('gillespie.cl')
        lfu.mobject.__init__(self,*args,**kwargs)



        plats = cl.get_platforms()
        card_dex = len(plats) - 1

        pdb.set_trace()

        props = [(cl.context_properties.PLATFORM,plats[card_dex])]

        self.ctx = cl.Context(properties = props)
        self.queue = cl.CommandQueue(self.ctx)



        self._load_kernal()

    def _load_kernal(self):
        with open(self.kernal,'r') as keh:fstr = keh.read()
        self.program = cl.Program(self.ctx,fstr).build()


    def load_data(self, pos_vbo, col_vbo, vel):
        mf = cl.mem_flags
        self.pos_vbo = pos_vbo
        self.col_vbo = col_vbo
        self.pos = pos_vbo.data
        self.col = col_vbo.data
        self.vel = vel

        #Setup vertex buffer objects and share them with OpenCL as GLBuffers
        self.pos_vbo.bind()
        self.pos_cl = cl.GLBuffer(self.ctx,mf.READ_WRITE, int(self.pos_vbo.buffers[0]))

        self.col_vbo.bind()
        self.col_cl = cl.GLBuffer(self.ctx,mf.READ_WRITE, int(self.col_vbo.buffers[0]))

        #pure OpenCL arrays
        self.vel_cl     = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf = vel)
        self.pos_gen_cl = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf = self.pos)
        self.vel_gen_cl = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf = self.vel)

        self.queue.finish()

    def execute(self):
        global_size = (self.num,)
        local_size = None

        result = np.array((tcnt,ccnt),dtype = np.float)

        kargs = (  self.pos_cl, self.col_cl, self.vel_cl,
                    self.pos_gen_cl, self.vel_gen_cl, dt)
        self.program.simulate(self.queue,global_size,local_size,*(kargs))

        self.queue.finish()


def test():
    ke = kernal()

test()










