#!/usr/bin/env python
import modular4.base as mb
import modular4.ensemble as me
import modular4.output as mo

import sim_anneal.pspace as spsp

import matplotlib
import matplotlib.pyplot as plt
matplotlib.rcParams['pdf.fonttype'] = 42

import argparse,sys,os,time,numpy,cPickle

import pdb

# mplot is a representation of a "figure", which 
# contains some number of subplots, and some arrangement
# of modular data objects with those plots
class mplot(mb.mobject):

    # use load_data to associate modular data objects with the mplot
    # specify general info about the final figure to help 
    # lay out the axes
    #   how many subplots?
    #   line and/or color and/or anything else?
    #   each ax has xax,[yax,[zax]],targets at minimum
    #       this corresponds to extracting arrays from data objects
    #   theres polish information for each subplot thats also needed:
    #       xax_title,yax_title,plot_title,color_bar_range
    #       colors of lines,legend labels per target
    #       line markers/styles/linewidths per target
    # 
    # presumeably the plot should be outputted pdf/png as the regular
    # plotting interface does
    #   requires filename/save directory
    #
    # paths is a list of full paths to data file from which modular
    #   data objects will be extracted

    # get a new axis to place in the figure
    def subplot(self,*args,**kwargs):
        sub = msubplot(self,*args,**kwargs)
        self.subplots.append(sub)
        return sub

    # destroy and data dep. information
    def clear(self):
        #for da in self.datas:self.datas[da] = None
        #self.datas['extras'] = lfu.data_container(data = [])
        #self.datas = {'extras':lfu.data_container(data = [])}
        self.datas = {'extras':{}}

    def __init__(self,*args,**kwargs):
        self._def('name','mplot',**kwargs)
        self._def('subplots',[],**kwargs)
        self._def('wspace',0.3,**kwargs)
        self._def('hspace',0.35,**kwargs)
        self._def('pipe',[],**kwargs)
        self.figure = plt.figure(figsize = (8,8))
        self.figure.subplots_adjust(wspace = self.wspace,hspace = self.hspace)
        #self.datas = {'extras':lfu.data_container(data = [])}
        self.datas = {'extras':{}}
        self.clear()
    
    # access specified data files and return data objects
    def open_data(self,*paths):
        self.clear()
        fpaths = []
        for pa in paths:
            if pa.endswith('.pkl'):
                #fpaths.extend(glob.glob(pa))
                fpaths.append(pa)
            else:
                pafis = os.listdir(pa)
                pfs = [p for p in pafis if p.endswith('.pkl')]
                fpaths.extend(pfs)
        for pa in fpaths:
            if not pa in self.datas:
                self.datas[pa] = None
        for fpa in self.datas:
            if fpa == 'extras':continue
            print '\nloading pkl data:',fpa
            with open(fpa,'rb') as h:dat = cPickle.load(h)['pages']
            self.datas[fpa] = dat

    # produce the actual plot axes objects with plotted data
    # axes are used from elsewhere (including plt.show())
    def render(self):
        for subp in self.subplots:
            subp.clear()
            #subp.extract()
            subp.render()
        #self.figure.tight_layout()
        self.figure.subplots_adjust(left = 0.05,right = 0.95,top = 0.96,bottom = 0.08)

# this represents a subplot in the figure, with one axis, and all
# other data associated with the plot
class msubplot(mb.mobject):

    # destroy any plot/data dep. information
    def clear(self):self.ax = None

    def __init__(self,mplot,subloc,*args,**kwargs):
        self.mplot = mplot
        self.loc = subloc
        self._def('reqorder',[],**kwargs)
        self._def('requests',[],**kwargs)
        self._def('name','msubplot',**kwargs)
        self._def('ptype','lines',**kwargs)
        self._def('plab',None,**kwargs)
        self._def('xlab',None,**kwargs)
        self._def('ylab',None,**kwargs)
        self._def('zlab',None,**kwargs)
        self._def('plabsize',18,**kwargs)
        self._def('xlabsize',20,**kwargs)
        self._def('ylabsize',20,**kwargs)
        self._def('zlabsize',20,**kwargs)
        self._def('xticksize',20,**kwargs)
        self._def('yticksize',20,**kwargs)
        self._def('xlog',False,**kwargs)
        self._def('ylog',False,**kwargs)
        self._def('zlog',False,**kwargs)
        self._def('xmin',None,**kwargs)
        self._def('xmax',None,**kwargs)
        self._def('ymin',None,**kwargs)
        self._def('ymax',None,**kwargs)
        self._def('zmin',None,**kwargs)
        self._def('zmax',None,**kwargs)
        self._def('legend',True,**kwargs)
        self._def('legendloc',1,**kwargs)

    # given x and y (strings), add a request for this target
    # requests are considered based on input data in self.extract
    def add_line(self,x,y,**kwargs):
        if type(x) is type(''):print 'expecting domain',x,'in input files'
        #elif issubclass(x.__class__,mst.scalars):
        #    self.mplot.datas['extras'].data.append(x)
        else:
            xnam = 'extrax-'+str(len(self.mplot.datas['extras']))
            xdat = numpy.array(x)
            self.mplot.datas['extras'][xnam] = xdat
            x = xnam
        if type(y) is type(''):print 'expecting codomain',y,'in input files'
        #elif issubclass(y.__class__,mst.scalars):
        #    self.mplot.datas['extras'].data.append(y)
        else:
            ynam = 'extray-'+str(len(self.mplot.datas['extras']))
            ydat = numpy.array(y)
            self.mplot.datas['extras'][ynam] = ydat
            y = ynam
        self.requests.append(kwargs)
        self.reqorder.append((x,y))
        self.ptype = 'lines'

    # given x,y, and z (strings), add a request for this target
    # requests are considered based on input data in self.extract
    def add_heat(self,x,y,z,**kwargs):
        if type(x) is type(''):print 'expecting xdomain',x,'in input files'
        #elif issubclass(x.__class__,mst.scalars):
        #    self.mplot.datas['extras'].data.append(x)
        else:
            xnam = 'extrax-'+str(len(self.mplot.datas['extras']))
            xdat = numpy.array(x)
            self.mplot.datas['extras'][xnam] = xdat
            x = xnam
            #xnam = 'extrax-'+str(len(self.mplot.datas['extras'].data))
            #xdat = mst.scalars(name = xnam,data = numpy.array(x))
            #self.mplot.datas['extras'].data.append(xdat)
            #x = xnam
        if type(y) is type(''):print 'expecting ydomain',y,'in input files'
        #elif issubclass(y.__class__,mst.scalars):
        #    self.mplot.datas['extras'].data.append(y)
        else:
            ynam = 'extray-'+str(len(self.mplot.datas['extras']))
            ydat = numpy.array(y)
            self.mplot.datas['extras'][ynam] = ydat
            y = ynam
            #ynam = 'extray-'+str(len(self.mplot.datas['extras'].data))
            #ydat = mst.scalars(name = ynam,data = numpy.array(y))
            #self.mplot.datas['extras'].data.append(ydat)
            #y = ynam
        if type(z) is type(''):print 'expecting surface',z,'in input files'
        #elif issubclass(z.__class__,mst.scalars):
        #    self.mplot.datas['extras'].data.append(z)
        else:
            znam = 'extraz-'+str(len(self.mplot.datas['extras']))
            zdat = numpy.array(z)
            self.mplot.datas['extras'][znam] = zdat
            z = znam
            #znam = 'extray-'+str(len(self.mplot.datas['extras'].data))
            #zdat = mst.scalars(name = znam,data = numpy.array(z))
            #self.mplot.datas['extras'].data.append(zdat)
            #z = znam
        self.requests.append(kwargs)
        self.reqorder.append((x,y,z))
        self.ptype = 'color'
    
    # given the data objects of the parent mplot
    # create and store a set of mplottarget objects 
    def extract(self):
        datas = self.mplot.datas
        if   self.ptype == 'lines':ptargets = self.lines(datas)
        elif self.ptype == 'color':ptargets = self.color(datas)
        else:raise ValueError
        self.plottargets = ptargets
        self.targetcount = len(ptargets)
            
    # generate mplottarget line objects for this subplot
    def lines(self,datas):
        exs = self.mplot.datas['extras']
        lines = []
        for reqx in range(len(self.reqorder)):
            rkws = self.requests[reqx]
            req = self.reqorder[reqx]
            xdom,ycod = req
            print '\nextracting request:',xdom,ycod,'\n','-'*40
            if xdom in exs:x = exs[xdom]
            else:x = self.locate(datas,xdom)
            if ycod in exs:y = exs[ycod]
            else:y = self.locate(datas,ycod)
            if   x is None:print 'failed to locate x for request:',req
            elif y is None:print 'failed to locate y for request:',req
            else:
                line = mplotline(self,x,y,req,**rkws)
                lines.append(line)
                print 'made line:',line
        return lines

    # generate color mesh objects for this subplot
    def color(self,datas):
        heats = []
        for reqx in range(len(self.reqorder)):
            rkws = self.requests[reqx]
            req = self.reqorder[reqx]
            xdom,ydom,zcod = req
            print '\nextracting request:',req,'\n','-'*40
            z = self.locate(datas,zcod)
            x = self.locate(datas,xdom)
            y = self.locate(datas,ydom)
            #if issubclass(z.__class__,mst.reducer):
            #    x = z
            #    y = z
            #else:
            #    x = self.locate(datas,xdom)
            #    y = self.locate(datas,ydom)
            if   x is None:print 'failed to locate x for request:',req
            elif y is None:print 'failed to locate y for request:',req
            elif z is None:print 'failed to locate z for request:',req
            else:
                heat = mplotheat(self,x,y,z,req,**rkws)
                heats.append(heat)
                print 'made heat map:',heat
        return heats

    # given a list of possibly redundant data objects
    # return the subset whose names match the target
    def locate(self,datas,target):
        located = []
        dfs = sorted(datas.keys())
        for df in dfs:
            if df == 'extras':continue
            data = datas[df]
            for pg in data:
                ds,ts,ps = pg
                if target in ts:
                    located.append((pg,df))
                elif target in pg[2].keys():
                    located.append((pg[2],df))
        lcnt = len(located)
        if lcnt == 0:
            print '\n','-'*40,'\ntarget:',target
            print '\tcould not be located!!\n','-'*40,'\n'
            return
        elif lcnt == 1:return located[0][0]
        elif self.mplot.pipe:return located[self.mplot.pipe.pop(0)][0]
        else:
            print 'more than one data object was found for:',target
            for lx in range(lcnt):
                lc,lf = located[lx]
                #print '\n',lx,'\tfrom file:',lf,'\n\t\tof class:',lc
                print '\n',lx,'\tfrom file:',lf
            which = int(raw_input('\n\tlocated index please:\n\t\t'))
            return located[which][0]
        '''#
        elif lcnt == 2 and located[0][1] == located[1][1]:
            if issubclass(located[0][0].__class__,mst.reducer):
                return located[0][0]
            else:return located[1][0]
        else:
            print 'more than one data object was found for:',target
            for lx in range(lcnt):
                lf,lc = located[lx]
                print '\n',lx,'\tfrom file:',lf,'\n\t\tof class:',lc
            which = int(raw_input('\n\tlocated index please:\n\t\t'))
            return located[which][0]
        '''#

    # determine the min/max of x/y based on current plottargets
    def minmaxes(self):
        tcnt = self.targetcount
        if tcnt == 0:mms = (0,1,0,1,0,1)
        elif tcnt == 1:mms = self.plottargets[0].minmax()
        else:
            mms = self.plottargets[0].minmax()
            for tx in range(1,tcnt):
                omms = self.plottargets[tx].minmax()
                mms = (
                    min(mms[0],omms[0]),max(mms[1],omms[1]),
                    min(mms[2],omms[2]),max(mms[3],omms[3]),
                    min(mms[4],omms[4]),max(mms[5],omms[5]))
        mms = (
            mms[0] if self.xmin is None else self.xmin,
            mms[1] if self.xmax is None else self.xmax,
            mms[2] if self.ymin is None else self.ymin,
            mms[3] if self.ymax is None else self.ymax,
            mms[4] if self.zmin is None else self.zmin,
            mms[5] if self.zmax is None else self.zmax)
        return mms

    # reset the axis and replot all mplottarget objects
    def render(self):
        self.clear()
        self.extract()

        self.ax = self.mplot.figure.add_subplot(self.loc)
        for ptarg in self.plottargets:ptarg.render(self.ax)
        xb,xt,yb,yt,zb,zt = self.minmaxes()
        self.ax.set_xlim([xb,xt])
        self.ax.set_ylim([yb,yt])
        #self.ax.set_zlim([zb,zt])
        if self.ptype == 'lines' and self.legend:
            leg = self.ax.legend(loc = self.legendloc)
            #leg.draggable()
        if self.xlog:self.ax.set_xscale('log')
        if self.ylog:self.ax.set_yscale('log')
        if self.xlab:self.ax.set_xlabel(self.xlab,fontsize = self.xlabsize)
        if self.ylab:self.ax.set_ylabel(self.ylab,fontsize = self.ylabsize)
        if self.zlab:
            if hasattr(self.ax,'set_zlabel'):
                self.ax.set_zlabel(self.zlab,fontsize = self.zlabsize)
        if self.plab:self.ax.set_title(self.plab,fontsize = self.plabsize)
        for tick in self.ax.xaxis.get_major_ticks():
            tick.label.set_fontsize(self.xticksize)
        for tick in self.ax.yaxis.get_major_ticks():
            tick.label.set_fontsize(self.yticksize)

# represents one plot target in a plot
class mplottarg(mb.mobject):

    # describe this line in a string
    def __str__(self):
        minx,maxx,miny,maxy,minz,maxz = self.minmax()
        s =  ''.join((' "',str(self.name),'" - ',str(self.__class__)))
        s += ''.join(('\n\tresulting from request: "',str(self.req),'"'))
        s += ''.join(('\n\tx-data:\n\t\ton range:',str(minx),' - ',str(maxx)))
        s += ''.join(('\n\ty-data:\n\t\ton range:',str(miny),' - ',str(maxy)))
        s += ''.join(('\n\tz-data:\n\t\ton range:',str(minz),' - ',str(maxz)))
        return s

    def __init__(self,msubplot,req,*args,**kwargs):
        self.msub = msubplot
        self._def('name',req[-1],**kwargs)

# represents one colormesh in a plot
class mplotheat(mplottarg):

    # given a data object for x,y, and z, store numpy arrays to plot
    def inp(self,x,y,z,req):
        if type(x) != type(()):
            self.x = x
            self.y = y
            self.z = z
        else:
            aux = x[2]
            if 'pspaceaxes' in aux and req[0] in aux['pspaceaxes']:
                axisnames = aux['pspaceaxes']
                axxs = tuple(z[1].index(a) for a in axisnames)
                axvs = [z[0][a] for a in axxs]
                axds = [None for a in axisnames]
                axcnt = len(axisnames)
                if axcnt > 1:
                    print '\nneed to set axis defaults on a reducer...'
                    for axx in range(axcnt):
                        nv,ax = '',axisnames[axx]
                        axval = numpy.unique(z[0][z[1].index(ax)])
                        if ax == req[0] or ax == req[1]:continue
                        if len(axval) > 1:
                            if ax in self.name:
                                nmsp = tuple(x.strip() for x in self.name.split('='))
                                nv = nmsp[nmsp.index(ax)+1]
                                try:nv = float(nv)
                                except:nv = ''
                            if nv == '':
                                axdef = numpy.unique(axvs[axx])
                                print 'reducer axis default:','"'+ax+'"',':',axdef
                                print '\twith potential values:',axval
                                nv = raw_input('\n\tnew value?:\t')
                        if nv == '':nv = axval[0]
                        try:
                            nv = float(nv)
                            nv = axval[spsp.locate(axval,nv)]
                            axds[axx] = nv
                        except:print 'axis default input ignored:',nv
                axss,inss = axds[:],[]
                axss[axisnames.index(req[0])] = None
                axss[axisnames.index(req[1])] = None
                for axx in range(len(axisnames)):
                    if axss[axx] is None:inss.append([1 for v in axvs[axx]])
                    else:inss.append([1 if v == axds[axx] else 0 for v in axvs[axx]])
                in_every = [(0 not in row) for row in zip(*inss)]   
                surf = [sur for sur,ie in zip(z[0][z[1].index(req[2])],in_every) if ie]
                xzip = zip(x[0][x[1].index(req[0])],in_every)
                yzip = zip(y[0][y[1].index(req[1])],in_every)
                dx = numpy.unique(numpy.array([j for j,ie in xzip if ie]))
                dy = numpy.unique(numpy.array([j for j,ie in yzip if ie]))
                ds = numpy.array(surf,dtype = numpy.float)

                ddx,ddy = dx[1]-dx[0],dy[1]-dy[0]
                dx = numpy.linspace(dx[0]-ddx/2.0,dx[-1]+ddx/2.0,dx.size+1)
                dy = numpy.linspace(dy[0]-ddy/2.0,dy[-1]+ddy/2.0,dy.size+1)

                #dx = numpy.linspace(dx[0],dx[-1]+ddx,dx.size+1)
                #dy = numpy.linspace(dy[0],dy[-1]+ddy,dy.size+1)

                #dx = numpy.linspace(dx[0],dx[-1],dx.size+1)
                #dy = numpy.linspace(dy[0],dy[-1],dy.size+1)

                ds = ds.reshape(dx.size-1,dy.size-1)
                #ds = ds.reshape(dx.size,dy.size)

                if axisnames.index(req[0]) < axisnames.index(req[1]):ds = ds.transpose()
                self.x = dx
                self.y = dy
                self.z = ds

            elif req[0] in x[1]:
                print 'simple!'

                pdb.set_trace()

            else:raise ValueError

        self.req = req

        #if   issubclass(x.__class__,mst.scalars):self.x = x.data
        #elif issubclass(x.__class__,mst.reducer):
        #    self.x = x.axis_values[x.axes.index(req[0])].data
        #if   issubclass(y.__class__,mst.scalars):self.y = y.data
        #elif issubclass(x.__class__,mst.reducer):
        #    self.x = x.axis_values[x.axes.index(req[0])]
        '''#
        if   issubclass(z.__class__,mst.scalars):self.z = z.data
        elif issubclass(z.__class__,mst.reducer):
            axcnt = len(z.axes)
            if axcnt > 1:
                print '\nneed to set axis defaults on a reducer...'
                for axx in range(axcnt):
                    nv,ax,axdef = '',z.axes[axx],z.axis_defaults[axx]
                    if ax == req[0] or ax == req[1]:continue
                    if len(z.axis_values[axx].data) > 1:
                        bax = ax.replace(' : value','')
                        if bax in self.name:
                            nmsp = lfu.msplit(self.name,'=')
                            nv = nmsp[nmsp.index(bax)+1]
                            try:nv = float(nv)
                            except:nv = ''
                        if nv == '':
                            print 'reducer axis default:','"'+ax+'"',':',axdef
                            print '\twith potential values:',y.axis_values[axx].data
                            nv = raw_input('\n\tnew value?:\t')
                    if nv == '':z.axis_values[axx].data[0]
                    try:
                        nv = float(nv)
                        nv = lfu.nearest(nv,z.axis_values[axx].data)
                        z.axis_defaults[axx] = nv
                    except:print 'axis default input ignored:',nv
            surf = z._surface(req[0],req[1],req[2])
            if not surf:raise ValueError
            self.x,self.y,self.z = surf
        '''#

    def __init__(self,msubplot,x,y,z,req,*args,**kwargs):
        mplottarg.__init__(self,msubplot,req,*args,**kwargs)
        self.inp(x,y,z,req)

    # get the min/max of the x/y data of this plot target
    def minmax(self):
        minx,maxx = self.x.min(),self.x.max()
        miny,maxy = self.y.min(),self.y.max()
        minz,maxz = self.z.min(),self.z.max()
        return minx,maxx,miny,maxy,minz,maxz

    # add a matplotlib color object to an axis for this target
    def render(self,ax):
        minx,maxx,miny,maxy,minz,maxz = self.msub.minmaxes()

        cmesh = ax.pcolor(self.x,self.y,self.z,vmin = minz,vmax = maxz)

        #xticks = self.x
        #yticks = self.y
        #xticks = numpy.linspace(self.x[0],self.x[-1],10)
        #yticks = numpy.linspace(self.y[0],self.y[-1],10)

        # ticks should optionally come directly from the mplt script!!
        xticks = numpy.linspace(100,200,6)
        yticks = numpy.linspace(100,1000,6)
        ax.set_xticks(xticks,minor = False)
        ax.set_yticks(yticks,minor = False)

        #cmesh = ax.imshow(self.z,vmin = minz,vmax = maxz,
        #    interpolation = 'nearest',extent = (minx,maxx,miny,maxy),
        #    aspect = 'auto')

        #    #cmap = cmap,shading = 'gouraud',vmin = z_min,vmax = z_max)
        #####
        #####
        #cmesh = ax.imshow(self.z,vmin = minz,vmax = maxz,
        #    interpolation = 'nearest',extent = (minx,maxx,miny,maxy))

        #    aspect = 'auto',interpolation = self.cplot_interpolation, 
        #    cmap = cmap,vmin = z_min,vmax = z_max,origin = 'lower',
        #    extent = self.minmax())
        #####

        #ax.set_yticks(numpy.arange(self.z.shape[0])+0.5,minor = False)
        #ax.set_xticks(numpy.arange(self.z.shape[1])+0.5,minor = False)

        if not minz == maxz:
            cb = self.msub.mplot.figure.colorbar(cmesh)
            cb.set_label('',fontsize = 20)
            for tick in cb.ax.xaxis.get_major_ticks():
                tick.label.set_fontsize(20)
        if False:
            curves = 10
            levels = numpy.arange(self.z.min(),self.z.max(),
                (1/float(curves))*(self.z.max()-self.z.min()))
            #ax.contour(surf,colors = 'white',levels = levels)
            contour = ax.contour(self.x,self.y,self.z,
                colors = 'white',levels = levels)
            ax.clabel(contour,inline=1,fontsize = 10)

# represents one line in a plot
class mplotline(mplottarg):

    # given a data object for x and y, store numpy arrays to plot
    def inp(self,x,y,req):
        if type(x) != type(()):
            self.x = x
            self.y = y
        else:
            aux = x[2]
            if 'pspaceaxes' in aux and req[0] in aux['pspaceaxes']:
                axisnames = aux['pspaceaxes']
                axxs = tuple(y[1].index(a) for a in axisnames)
                axvs = [y[0][a] for a in axxs]
                axds = [None for a in axisnames]
                axcnt = len(axisnames)
                if axcnt > 1:
                    print '\nneed to set axis defaults on a reducer...'
                    for axx in range(axcnt):
                        nv,ax = '',axisnames[axx]
                        axval = numpy.unique(y[0][y[1].index(ax)])
                        if ax == req[0]:continue
                        if len(axval) > 1:
                            if ax in self.name:
                                nmsp = tuple(x.strip() for x in self.name.split('='))
                                nv = nmsp[nmsp.index(ax)+1]
                                try:nv = float(nv)
                                except:nv = ''
                            if nv == '':
                                axdef = numpy.unique(axvs[axx])
                                print 'reducer axis default:','"'+ax+'"',':',axdef
                                print '\twith potential values:',axval
                                nv = raw_input('\n\tnew value?:\t')
                        if nv == '':nv = axval[0]
                        try:
                            nv = float(nv)
                            nv = axval[spsp.locate(axval,nv)]
                            axds[axx] = nv
                        except:print 'axis default input ignored:',nv
                axss,inss = axds[:],[]
                axss[axisnames.index(req[0])] = None
                for axx in range(len(axisnames)):
                    if axss[axx] is None:inss.append([1 for v in axvs[axx]])
                    else:inss.append([1 if v == axds[axx] else 0 for v in axvs[axx]])
                in_every = [(0 not in row) for row in zip(*inss)]   
                xzip = zip(x[0][x[1].index(req[0])],in_every)
                yzip = zip(y[0][y[1].index(req[1])],in_every)
                dx = numpy.array([j for j,ie in xzip if ie])
                dy = numpy.array([j for j,ie in yzip if ie])
                self.x = dx
                self.y = dy
            elif req[0] in x[1]:
                self.x = x[0][x[1].index(req[0])]
                self.y = y[0][y[1].index(req[1])]
            else:

                pdb.set_trace()

                raise ValueError

        if not len(self.x) == len(self.y):
            print 'unequal data lengths for request:',req
            raise ValueError
        self.req = req

    def __init__(self,msubplot,x,y,req,*args,**kwargs):
        mplottarg.__init__(self,msubplot,req,*args,**kwargs)
        self._def('color','black',**kwargs)
        self._def('style','-',**kwargs)
        self._def('width',2.0,**kwargs)
        self._def('mark','',**kwargs)
        self.inp(x,y,req)

    # get the min/max of the x/y data of this plot target
    def minmax(self):
        if type(self.x) == type({}):
            minx,maxx = 0,1
            miny,maxy = 0,1
            minz,maxz = 0,1
        else:
            minx,maxx = self.x.min(),self.x.max()
            miny,maxy = self.y.min(),self.y.max()
            minz,maxz = 0,1
        return minx,maxx,miny,maxy,minz,maxz

    # add a matplotlib line object to an axis for this target
    def render(self,ax):
        largs = {
            'color':self.color,'linestyle':self.style,
            'linewidth':self.width,'marker':self.mark}
        if type(self.x) == type({}):
            for le in self.x['extra_trajectory']:
                ln,gs = le
                line = matplotlib.lines.Line2D(*ln,**gs)
                #if self.name:line.set_label(self.name)
                ax.add_line(line)
        else:
            line = matplotlib.lines.Line2D(self.x,self.y,**largs)
            if self.name:line.set_label(self.name)
            ax.add_line(line)





def makeit():
    #reorgfile = '/srv/4.0/latitude/corrdemo/ensemble/bypsp_output.pkl'
    reorgfile = '/srv/4.0/enterprise/bypsp_output.pkl'
    x,y = 'lambda1','x1,x2-correlation'

    mp = mplot(wspace = 0.2,hspace = 0.2)
    mp.open_data(reorgfile)
    
    msub1 = mp.subplot('111',
        xlab = 'lambda1',ylab = 'correlation coefficient',ymin = 0,ymax = 1,
        plab = 'Correlation Resonance',legendloc = 'lower right')
    msub1.add_line(x,y,color = 'red',name = 'lambda2 = 10',width = 2)
    msub1.add_line(x,y,color = 'blue',name = 'lambda2 = 25',width = 2)
    msub1.add_line(x,y,color = 'green',name = 'lambda2 = 40',width = 2)
    msub1.add_line([10,10],[-1,1],name = '',color = 'black',width = 2,style = '--')
    msub1.add_line([25,25],[-1,1],name = '',color = 'black',width = 2,style = '--')
    msub1.add_line([40,40],[-1,1],name = '',color = 'black',width = 2,style = '--')

    mp.render()

if __name__ == '__main__':
    makeit()
    plt.show()





