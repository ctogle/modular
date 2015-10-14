import modular_core.fundamental as lfu
import modular_core.io.mpkl as lpkl
import modular_core.data.single_target as mst

import matplotlib,os,numpy,glob
import matplotlib.pyplot as plt

import pdb





# issue a message and request an input
# continue to ask until the result is among entries in vals
# of until the returned value indicates a null response
# if vals has no elements, any response is valid
# if vals has 1 element, that element is assumed
def gather(msg,vals):
    print 'gathering input'
    vals = [str(v) for v in vals]
    vcnt = len(vals)
    if vcnt == 0:return raw_input(msg)
    elif vcnt == 1:return vals[0]
    else:
        res = None
        while not res in vals:
            if not res is None:
                print '\n\t\tinvalid response:\t',res
            print '\nenter one of the following:\n\t',vals
            res = raw_input(msg)
            if res == '':res = vals[0]
    return res

# mplot is a representation of a "figure", which 
# contains some number of subplots, and some arrangement
# of modular data objects with those plots
class mplot(lfu.mobject):

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
        self.datas = {'extras':lfu.data_container(data = [])}

    def __init__(self,*args,**kwargs):
        self._default('name','mplot',**kwargs)
        self._default('subplots',[],**kwargs)
        self._default('wspace',0.3,**kwargs)
        self._default('hspace',0.35,**kwargs)
        self.figure = plt.figure(figsize = (8,8))
        self.figure.subplots_adjust(wspace = self.wspace,hspace = self.hspace)
        self.datas = {'extras':lfu.data_container(data = [])}
        self.clear()
        lfu.mobject.__init__(self,*args,**kwargs)
    
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
            dat = lpkl.load_pkl_object(fpa)
            self.datas[fpa] = dat

    # produce the actual plot axes objects with plotted data
    # axes are used from elsewhere (including plt.show())
    def render(self):
        for subp in self.subplots:
            subp.clear()
            #subp.extract()
            subp.render()

# this represents a subplot in the figure, with one axis, and all
# other data associated with the plot
class msubplot(lfu.mobject):

    # destroy any plot/data dep. information
    def clear(self):self.ax = None

    def __init__(self,mplot,subloc,*args,**kwargs):
        self.mplot = mplot
        self.loc = subloc
        self._default('reqorder',[],**kwargs)
        self._default('requests',[],**kwargs)
        self._default('name','msubplot',**kwargs)
        self._default('ptype','lines',**kwargs)
        self._default('plab',None,**kwargs)
        self._default('xlab',None,**kwargs)
        self._default('ylab',None,**kwargs)
        self._default('zlab',None,**kwargs)
        self._default('plabsize',18,**kwargs)
        self._default('xlabsize',16,**kwargs)
        self._default('ylabsize',16,**kwargs)
        self._default('zlabsize',16,**kwargs)
        self._default('xticksize',16,**kwargs)
        self._default('yticksize',16,**kwargs)
        self._default('xlog',False,**kwargs)
        self._default('ylog',False,**kwargs)
        self._default('zlog',False,**kwargs)
        self._default('xmin',None,**kwargs)
        self._default('xmax',None,**kwargs)
        self._default('ymin',None,**kwargs)
        self._default('ymax',None,**kwargs)
        self._default('zmin',None,**kwargs)
        self._default('zmax',None,**kwargs)
        self._default('legend',True,**kwargs)
        self._default('legendloc',1,**kwargs)
        lfu.mobject.__init__(self,*args,**kwargs)

    # given x and y (strings), add a request for this target
    # requests are considered based on input data in self.extract
    def add_line(self,x,y,**kwargs):
        if type(x) is type(''):print 'expecting domain',x,'in input files'
        elif issubclass(x.__class__,mst.scalars):
            self.mplot.datas['extras'].data.append(x)
        else:
            xnam = 'extrax-'+str(len(self.mplot.datas['extras'].data))
            xdat = mst.scalars(name = xnam,data = numpy.array(x))
            self.mplot.datas['extras'].data.append(xdat)
            x = xnam
        if type(y) is type(''):print 'expecting codomain',y,'in input files'
        elif issubclass(y.__class__,mst.scalars):
            self.mplot.datas['extras'].data.append(y)
        else:
            ynam = 'extray-'+str(len(self.mplot.datas['extras'].data))
            ydat = mst.scalars(name = ynam,data = numpy.array(y))
            self.mplot.datas['extras'].data.append(ydat)
            y = ynam
        self.requests.append(kwargs)
        self.reqorder.append((x,y))
        self.ptype = 'lines'

    # given x,y, and z (strings), add a request for this target
    # requests are considered based on input data in self.extract
    def add_heat(self,x,y,z,**kwargs):
        if type(x) is type(''):print 'expecting xdomain',x,'in input files'
        elif issubclass(x.__class__,mst.scalars):
            self.mplot.datas['extras'].data.append(x)
        else:
            xnam = 'extrax-'+str(len(self.mplot.datas['extras'].data))
            xdat = mst.scalars(name = xnam,data = numpy.array(x))
            self.mplot.datas['extras'].data.append(xdat)
            x = xnam
        if type(y) is type(''):print 'expecting ydomain',y,'in input files'
        elif issubclass(y.__class__,mst.scalars):
            self.mplot.datas['extras'].data.append(y)
        else:
            ynam = 'extray-'+str(len(self.mplot.datas['extras'].data))
            ydat = mst.scalars(name = ynam,data = numpy.array(y))
            self.mplot.datas['extras'].data.append(ydat)
            y = ynam
        if type(z) is type(''):print 'expecting surface',z,'in input files'
        elif issubclass(z.__class__,mst.scalars):
            self.mplot.datas['extras'].data.append(z)
        else:
            znam = 'extray-'+str(len(self.mplot.datas['extras'].data))
            zdat = mst.scalars(name = znam,data = numpy.array(z))
            self.mplot.datas['extras'].data.append(zdat)
            z = znam
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
        lines = []
        for reqx in range(len(self.reqorder)):
            rkws = self.requests[reqx]
            req = self.reqorder[reqx]
            xdom,ycod = req
            print '\nextracting request:',req,'\n','-'*40
            y = self.locate(datas,ycod)
            if issubclass(y.__class__,mst.reducer):x = y
            else:x = self.locate(datas,xdom)
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
            if issubclass(z.__class__,mst.reducer):
                x = z
                y = z
            else:
                x = self.locate(datas,xdom)
                y = self.locate(datas,ydom)
            if   x is None:print 'failed to locate x for request:',req
            elif y is None:print 'failed to locate y for request:',req
            elif z is None:print 'failed to locate z for request:',req
            else:
                heat = mplotheat(self,x,y,z,req,**rkws)
                heats.append(heat)
                print 'made heat map:',heat
        return heats

    # given a list of possibly redundant data objects
    # return the subset whose names matchh the target
    def locate(self,datas,target):
        located = []
        for df in datas:
            data = datas[df].data
            for d in data:
                if issubclass(d.__class__,mst.scalars):
                    if d.name == target:located.append((d,df))
                elif issubclass(d.__class__,mst.reducer):
                    if target in d.surfs:located.append((d,df)) 
                    elif target in d.axes:located.append((d,df)) 
        lcnt = len(located)
        if lcnt == 0:
            print '\n','-'*40,'\ntarget:',target
            print '\tcould not be located!!\n','-'*40,'\n'
            return
        elif lcnt == 1:return located[0][0]
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
class mplottarg(lfu.mobject):

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
        self._default('name',req[-1],**kwargs)
        lfu.mobject.__init__(self,*args,**kwargs)

# represents one colormesh in a plot
class mplotheat(mplottarg):

    # given a data object for x,y, and z, store numpy arrays to plot
    def inp(self,x,y,z,req):
        if   issubclass(x.__class__,mst.scalars):self.x = x.data
        elif issubclass(x.__class__,mst.reducer):
            self.x = x.axis_values[x.axes.index(req[0])].data
        if   issubclass(y.__class__,mst.scalars):self.y = y.data
        elif issubclass(x.__class__,mst.reducer):
            self.x = x.axis_values[x.axes.index(req[0])]
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
        self.req = req

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

        #    #cmap = cmap,shading = 'gouraud',vmin = z_min,vmax = z_max)
        #####
        #####
        #cmesh = ax.imshow(self.z,vmin = minz,vmax = maxz,
        #    interpolation = 'nearest',extent = (minx,maxx,miny,maxy))

        #    aspect = 'auto',interpolation = self.cplot_interpolation, 
        #    cmap = cmap,vmin = z_min,vmax = z_max,origin = 'lower',
        #    extent = self.minmax())
        #####

        if not minz == maxz:self.msub.mplot.figure.colorbar(cmesh)

        curves = 10
        levels = numpy.arange(self.z.min(),self.z.max(),
            (1/float(curves))*(self.z.max()-self.z.min()))
        #ax.contour(surf,colors = 'white',levels = levels)
        contour = ax.contour(self.x,self.y,self.z,
            colors = 'white',levels = levels)
        ax.clabel(contour,inline=1,fontsize=10)

# represents one line in a plot
class mplotline(mplottarg):

    # given a data object for x and y, store numpy arrays to plot
    def inp(self,x,y,req):
        if   issubclass(x.__class__,mst.scalars):self.x = x.data
        elif issubclass(x.__class__,mst.reducer):
            self.x = x.axis_values[x.axes.index(req[0])].data
        if   issubclass(y.__class__,mst.scalars):self.y = y.data
        elif issubclass(y.__class__,mst.reducer):
            axcnt = len(y.axes)
            if axcnt > 1:
                print '\nneed to set axis defaults on a reducer...'
                for axx in range(axcnt):
                    nv,ax,axdef = '',y.axes[axx],y.axis_defaults[axx]
                    if ax == req[0]:continue
                    if len(y.axis_values[axx].data) > 1:
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
                    if nv == '':y.axis_values[axx].data[0]
                    try:
                        nv = float(nv)
                        nv = lfu.nearest(nv,y.axis_values[axx].data)
                        y.axis_defaults[axx] = nv
                    except:print 'axis default input ignored:',nv
            print '\n\tproducing curve for request',req
            print '\t\twith default values:',y.axis_defaults
            curv = y._curve(req[0],'',req[1])
            if not curv:raise ValueError
            self.y = curv.data
            self.x = curv.domain
        if not len(self.x) == len(self.y):
            print 'unequal data lengths for request:',req
            raise ValueError
        self.req = req

    '''#
    # describe this line in a string
    def __str__(self):
        minx,maxx,miny,maxy,minz,maxz = self.minmax()
        s = 'line "',self.name,'" resulting from request "',self.req,'"'
        s += '\n\tx-data:\n\t\ton range:',minx,' - ',maxx
        s += '\n\ty-data:\n\t\ton range:',miny,' - ',maxy
        s += '\n\tz-data:\n\t\ton range:',minz,' - ',maxz
        return s
    '''#

    def __init__(self,msubplot,x,y,req,*args,**kwargs):
        mplottarg.__init__(self,msubplot,req,*args,**kwargs)

        #self.msub = msubplot
        #self._default('name',req[1],**kwargs)
        self._default('color','black',**kwargs)
        self._default('style','-',**kwargs)
        self._default('width',2.0,**kwargs)
        self._default('mark','',**kwargs)
        #lfu.mobject.__init__(self,*args,**kwargs)
        self.inp(x,y,req)

    # get the min/max of the x/y data of this plot target
    def minmax(self):
        minx,maxx = self.x.min(),self.x.max()
        miny,maxy = self.y.min(),self.y.max()
        minz,maxz = 0,1
        return minx,maxx,miny,maxy,minz,maxz

    # add a matplotlib line object to an axis for this target
    def render(self,ax):
        line = matplotlib.lines.Line2D(self.x,self.y,
            color = self.color,linestyle = self.style,
            linewidth = self.width,marker = self.mark)
        if self.name:line.set_label(self.name)
        ax.add_line(line)









