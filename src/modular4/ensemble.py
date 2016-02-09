import modular4.base as mb
import modular4.mcfg as mcfg
import modular4.pspacemap as pmp
import modular4.measurement as eme
import modular4.output as mo
import modular4.mpi as mmpi
import numpy,random,time,os

import pdb





class ensemble(mb.mobject):

    simmodules = {
        'gillespiem' : ('gillespiem4','simmodule'), 
            }

    def prepare(self):
        top,smod = self.simmodules[self.module]
        self.simmodule = __import__(top).__dict__[smod]
        self.home = os.path.join(os.getcwd(),self.name)
        if mmpi.root() and not os.path.exists(self.home):
            os.makedirs(self.home)

    def initialize_measurements(self):
        z,nz = [],[]
        for mx in range(len(self.measurements)):
            m = self.measurements[mx]
            m._eindex = mx
            if 0 in m.input_sources:
                m.set_targets(self.targets,self.pspace)
                z.append(m)
            else:
                m.set_targets(m.seek_targets(self.measurements),self.pspace)
                nz.append(m)
        self.zeroth,self.nonzeroth = z,nz
        self.zerothdata = [(z[x]._eindex,[],{}) for x in range(len(z))]
        self.nonzerothdata = [(nz[x]._eindex,[],{}) for x in range(len(nz))]

    def set_targets(self,targets):
        for x in range(len(self.targets)):self.targets.pop(x)
        for t in targets:self.targets.append(t)
        return self

    def __init__(self,*ags,**kws):
        self._def('name','ensemble',**kws)
        self._def('module','gillespiem',**kws)
        self._def('simmodule',None,**kws)
        self._def('pspacemap',[],**kws)
        self._def('targets',[],**kws)
        self._def('measurements',[],**kws)
        self._def('outputs',[],**kws)
        self._def('capture',None,**kws)
        self._def('end',None,**kws)
        self._def('perform_installation',mmpi.root(),**kws)
        self._def('rgen',random.Random(),**kws)
        self.rgen.seed(random.getrandbits(100))
        self.prepare()

    def parse_mcfg(self,mcfgfile,**minput):
        if hasattr(self.simmodule,'parsers'):
            module_parsers = self.simmodule.parsers
        else:module_parsers = {}
        mcfg.measurement_parsers = eme.parsers
        einput = mcfg.parse(mcfgfile,module_parsers,**minput)
        if 'targets' in einput:self.set_targets(einput['targets'])
        if 'measurements' in einput:self.measurements = einput['measurements']
        if 'outputs' in einput:self.outputs = einput['outputs']
        if 'capture' in einput:self.capture = einput['capture']
        if 'end' in einput:self.end = einput['end']
        if 'parameterspace' in einput:
            pspace,trajectory,trajcount = einput['parameterspace']
            captcount = int(self.end / self.capture) + 1
            self.pspace = pspace
            pmpags = (pspace,trajectory,trajcount,captcount,self.targets)
            self.pspacemap = pmp.pspacemap(*pmpags)
        self.initialize_measurements()
        self.simparameters = {}
        for mp in module_parsers:self.simparameters[mp] = einput[mp]
        return self

    def output(self):
        try:
            import modular4.qtgui as mg
            mg.init_figure()
        except ImportError:print('failed to import gui...')
        result = []
        for ox in range(len(self.outputs)):
            o = self.outputs[ox]
            if ox == 0:
                t,n = self.targets[:],None
                d = self.pspacemap.get_data(t,n)
            else:
                m = self.measurements[ox-1]
                t = m.targets[:]
                if m in self.zeroth:
                    for d in self.zerothdata:
                        if d[0] == m._eindex:break
                elif m in self.nonzeroth:
                    for d in self.nonzerothdata:
                        if d[0] == m._eindex:break
                else:raise ValueError
            result.append(mo.output(o,d,t,home = self.home))
        return result

    def measure_data_zeroth(self,goalindex,
            precalced = None,returnonly = False,locd = None):
        pmp = self.pspacemap
        if locd is None:locd = pmp.data[goalindex]
        locp,loct = pmp.goal[goalindex],self.targets
        nzds = []
        for mx in range(len(self.zeroth)):
            m = self.zeroth[mx]
            zd = self.zerothdata[mx][1]
            for x in range(goalindex+1-len(zd)):zd.append([])
            if precalced:nzd = precalced[mx]
            else:nzd = m(locd,loct,locp)
            if returnonly:nzds.append(nzd)
            else:zd[goalindex].append(nzd)
        return nzds

    def measure_data_nonzeroth(self,**kws):
        zero,goal,axes = self.zerothdata,self.pspacemap.goal,self.pspace.axes
        for mx in range(len(self.nonzeroth)):
            m = self.nonzeroth[mx]
            for ishp in m.input_shapes:
                if ishp == 'parameterspace':
                    nonzmeasurement = m(zero,axes,goal,**kws)
                    self.nonzerothdata[mx][1].append(nonzmeasurement)

    def run_location(self,px,simf):
        trajcnt,targcnt,captcnt,p = self.pspacemap.set_location(px)
        d = numpy.zeros((trajcnt,targcnt,captcnt),dtype = numpy.float)
        for x in range(trajcnt):
            r = self.rgen.getrandbits(100)
            d[x] = simf(r,*p)
        return d

    def run(self):
        if mmpi.root():
            if mmpi.size() == 1:r = self.run_basic()
            else:r = self.run_dispatch()
        else:r = self.run_listen()
        return r

    def run_basic(self):
        simf = self.simmodule.overrides['prepare'](self)
        for px in range(len(self.pspacemap.goal)):
            pdata = self.run_location(px,simf)
            self.pspacemap.add_data(pdata)
            self.measure_data_zeroth(px)
        self.measure_data_nonzeroth()
        return self.output()

    def run_dispatch(self):
        print('dispatch beginning: %i' % mmpi.rank())
        simf = self.simmodule.overrides['prepare'](self)
        hosts = mmpi.hosts()
        for h in hosts:
            print('hostlookup: %s : %s' % (h,str(hosts[h])))
            if not h == 'root' and not h == mmpi.host():
                mmpi.broadcast('prom',hosts[h][0])
        mmpi.broadcast('prep')
        todo,done = [x for x in range(len(self.pspacemap.goal))],[]
        free,occp = [x for x in range(mmpi.size())],[]
        free.remove(mmpi.rank())
        while len(done) < len(self.pspacemap.goal):
            time.sleep(0.01)
            if todo and free:
                p = free.pop(0);w = todo.pop(0)
                mmpi.broadcast(['exec',w],p)
                occp.append(p)
            if occp:
                r = mmpi.passrecv()
                if not r is None and int(r) in occp:
                    px,pdata = mmpi.pollrecv(r)
                    free.append(r);occp.remove(r);done.append(px)
                    print('result from worker: %i' % r)
                    self.pspacemap.set_location(px)
                    self.measure_data_zeroth(px,precalced = pdata)
        self.measure_data_nonzeroth()
        mmpi.broadcast('halt')
        print('dispatch halting: %i' % mmpi.rank())
        return self.output()

    def run_listen(self):
        print('listener beginning: %i' % mmpi.rank())
        m = mmpi.pollrecv()
        while True:
            if m == 'halt':break
            elif m == 'host':mmpi.broadcast(mmpi.host(),0)
            elif m == 'prom':self.perform_installation = True
            elif m == 'prep':
                simf = self.simmodule.overrides['prepare'](self)
            elif m == 'exec':
                j = mmpi.pollrecv()
                r = self.run_location(j,simf)
                r = (j,self.measure_data_zeroth(j,returnonly = True,locd = r))
                mmpi.broadcast(mmpi.rank(),0)
                mmpi.broadcast(r,0)
                print('listener sent result: %s' % str(j))
            else:print('listener received unknown message: %s' % m)
            m = mmpi.pollrecv()
        print('listener halting: %i' % mmpi.rank())





