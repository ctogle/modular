import modular4.base as mb

import numpy

import pdb





class pspacemap(mb.mobject):

    def __init__(self,psp,traj,tcnt,ccnt,targs,**kws):
        self.pspace = psp
        self.targets = targs
        self.trajcount = tcnt
        self.captcount = ccnt
        self.goal = traj
        self.dshape = (self.trajcount,len(self.targets),self.captcount)

        self.completed = {}

        # replace this with hdf5 file
        goaldshape = (len(self.goal),)+self.dshape
        self.data = numpy.zeros(goaldshape,dtype = numpy.float)

    def set_location(self,x):
        self.pspace.move(self.goal[x])
        self.goalindex = x
        pkey = self.pspace.current
        if not pkey in self.completed:self.completed[pkey] = 0
        return self.trajcount,len(self.targets),self.captcount,pkey

    def get_data(self,ts = None,tc = None):
        if tc is None:tc = self.trajcount
        if ts is None:ts = self.targets[:]
        d = []
        for x in range(len(self.goal)):
            dx = self.data[x,:tc,:,:]
            gx = self.goal[x]
            d.append((dx,ts,gx))
        return -1,d,{}

    def add_data(self,d):
        ddim = len(d.shape)
        pkey = self.pspace.current
        if ddim == 2:
            self.data[self.goalindex,self.completed[pkey],:,:] = d
            self.completed[pkey] += 1
        elif ddim == 3:
            if d.shape[0] == self.data[self.goalindex].shape[0]:
                self.data[self.goalindex,:,:,:] = d
            elif d.shape[0] < self.data[self.goalindex].shape[0]:
                print('must implement data assimilation...')
                raise ValueError
                #self.data[self.goalindex,self.completed[pkey],:,:] = d
            self.completed[pkey] += d.shape[0]
        else:
            print('must implement data assimilation...')
            raise ValueError
            





