import modular4.base as mb
import modular4.qtgui as mg
import multiprocessing

import numpy,os,cPickle

import pdb





class moutput(mb.mobject):
    '''
    moutput is a result container class
    '''

    def loadpkl(self,fp,**kws):
        with open(fp,'rb') as h:data = cPickle.load(h)
        return data

    def savepkl(self,fp,**kws):
        with open(fp,'wb') as h:cPickle.dump(kws,h)

    def openplt(self,wt,**kws):
        kws['window_title'] = wt
        if self.plt_multiprocessed:
            proc = multiprocessing.Process
            pltprocess = proc(target = mg.runapp,args = (mg.pwindow,kws))
            pltprocess.start()
            self._processes.append(pltprocess)
        else:mg.runapp(mg.pwindow,kws)

    def join(self):
        for p in self._processes:
            p.join()

    def __init__(self,*ags,**kws):
        self._def('plt_multiprocessed',True,**kws)
        self._def('path',None,**kws)
        self._def('filename',None,**kws)
        self._def('modes',[],**kws)
        self._def('targets',[],**kws)
        self._def('pages',[],**kws)
        self._processes = []

    def __call__(self,**kws):
        if 'path' in kws:p = kws['path']
        elif os.path.exists(self.path):p = self.path
        else:p = os.getcwd()
        if 'filename' in kws:f = kws['filename']
        else:f = self.filename
        if 'modes' in kws:modes = kws['modes']
        else:modes = self.modes
        if 'pages' in kws:pgs = kws['pages']
        else:pgs = self.pages
        for md in modes:
            fp = os.path.join(p,f+'.'+md)
            if md == 'pkl':self.savepkl(fp,pages = pgs)
            elif md == 'plt':self.openplt(f,pages = pgs)
            else:
                print('unkown output mode: %s' % md)
                raise ValueError

def output(ol,data,targs,**mokws):
    olpath,olfile,olmodes,oltargs = ol
    if not oltargs == 'all':
        oltargs = [x.strip() for x in oltargs.split(',')]
        oltargs = [t for t in oltargs if t in targs]
    else:oltargs = targs[:]
    if not os.path.exists(olpath):
        if 'home' in mokws and os.path.exists(mokws['home']):
            olpath = mokws['home']
        else:olpath = os.getcwd()
    mokws['path'] = olpath
    mokws['filename'] = olfile
    mokws['modes'] = [x.strip() for x in olmodes.split(',')]
    mokws['targets'] = oltargs
    if type(data) == type(()):
        print 'by parameter space'
        mindex,mdata,mextra = data
        if len(mdata) == 1: #only one page (one location)
            mdat,mtgs,mloc = mdata[0]
            pages = [(mdat,mtgs,mloc)]
        else: #many pages (many locations)
            pgcnt = len(mdata)
            pages = [None for x in range(pgcnt)]
            for locx in range(pgcnt):
                locdata = mdata[locx]
                if len(locdata) != 1: #many traj per location
                    pages[locx] = locdata
                else: #one traj per location
                    pages[locx] = locdata[0]
        mokws['pages'] = pages
        moup = moutput(**mokws)
    elif hasattr(data,'shape'):
        mokws['pages'] = [(d,targs) for d in data]
        moup = moutput(**mokws)
    else:
        print 'unknown output request'
        raise ValueError
    return moup

                                                 



