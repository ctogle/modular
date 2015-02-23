import modular_core.libfundamental as lfu

import pyopencl as cl
import pdb,sys,os
import numpy as np

class kernal(lfu.mobject):

    def _get_platform(self):
        plats = cl.get_platforms()
        return plats[0]

    def __init__(self,*args,**kwargs):
        gillespiek = lfu.get_resource_path('gillespie.cl')
        self._default('kernal',gillespiek,**kwargs)
        self._default('num_trajectories',100,**kwargs)
        self._default('num_targets',1,**kwargs)
        self._default('num_captures',200,**kwargs)
        lfu.mobject.__init__(self,*args,**kwargs)

        plat = self._get_platform()
        props = [(cl.context_properties.PLATFORM,plat)]

        self.ctx = cl.Context(properties = props)
        self.queue = cl.CommandQueue(self.ctx)

        self._load_kernal()

    def _load_kernal(self):
        with open(self.kernal,'r') as keh:fstr = keh.read()
        self.program = cl.Program(self.ctx,fstr).build()

        pdb.set_trace()

    def _bufferize(self):
        mf = cl.mem_flags
        bf = mf.READ_ONLY | mf.COPY_HOST_PTR

        self.result_buffers = []
        for rarr in self.results:
            buff = cl.Buffer(self.ctx,bf,hostbuf = rarr)
            self.result_buffers.append(buff)

        self.queue.finish()

    def _initialize(self):
        ntraj = self.num_trajectories
        ntarg = self.num_targets
        ncapt = self.num_captures
        results = []
        for n in range(ntarg):
            results.append(np.zeros((ntraj,ncapt),dtype = np.float32))
        self.results = results
        self._bufferize()

    def _execute(self):
        self._initialize()
        kargs = self.result_buffers
        global_size = (self.num_trajectories,)
        local_size = None

        kargs = self.results
        self.program.simulate(self.queue,global_size,local_size,*(kargs))

        pdb.set_trace()

        self.program.simulate(self.queue,global_size,local_size,*kargs)
        #self.program.simulate(self.queue,global_size,local_size,*(kargs))

        self.queue.finish()
        return self.results


def test():
    ke = kernal()
    results = ke._execute()
    pdb.set_trace()

test()










