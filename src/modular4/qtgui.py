import modular4.base as mb
import modular4.mpi as mmpi

import os,sys,numpy,matplotlib,six
matplotlib.rcParams['backend.qt4'] = 'PySide'
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as figure_canvas
from matplotlib.backend_bases import NavigationToolbar2

from PySide import QtGui,QtCore

import pdb





###############################################################################
### utility functions
###############################################################################

def runapp(windowclass,kws):
    print('opening window : %s' % windowclass)
    mapp(windowclass,**kws).exec_()
    print('closed window : %s' % windowclass)

def convert_pixel_space(w,h):
    good_w,good_h = 1920.0,1080.0
    screensize = QtGui.QApplication.desktop().availableGeometry()
    runtime_w,runtime_h = screensize.width(),screensize.height()
    w_conversion = runtime_w / good_w
    h_conversion = runtime_h / good_h
    w_size,h_size = w * w_conversion,h * h_conversion
    return w_size,h_size

def bound(label,lay):
    group = QtGui.QGroupBox(title = label)
    group.setLayout(lay)
    return layout((group,))

def sortto(l1,l2):
    new = []
    for l in l1:
        if not l in l2:continue
        else:new.append(l)
    for x in range(len(l2)):l2.pop(0)
    for n in new:l2.append(n)

###############################################################################
### functions to create layouts/widgets
###############################################################################

def layout(widgets = [],orientation = 'v'):
    if orientation == 'v':lay = QtGui.QVBoxLayout
    elif orientation == 'h':lay = QtGui.QHBoxLayout
    l = lay()
    for w in widgets:l.addWidget(w)
    return l

def splitter(widgets = [],orientation = 'v',label = 'mwidgetsplitter'):
    if orientation == 'v':o = QtCore.Qt.Vertical
    elif orientation == 'h':o = QtCore.Qt.Horizontal
    split = QtGui.QSplitter(o)
    for w in widgets:split.addWidget(w)
    return bound(label,layout((split,)))

def buttons(funcs,events,labels,label = 'mwidgetbuttons',ori = 'v'):
    bs = []
    for bx in range(len(funcs)):
        f,e,l = funcs[bx],events[bx],labels[bx]
        b = QtGui.QPushButton(l)
        b.__getattribute__(e).connect(f)
        bs.append(b)
    return mwidget(layout(bs,ori),label)

def checks(tlist,labels,master = True,callback = None,label = 'mwidgetchecks',ori = 'v'):
    qck,quck = QtCore.Qt.Checked,QtCore.Qt.Unchecked
    tlisto = tlist[:]
    def togg(c,t):
        def f(i):
            if t in tlist:
                tlist.remove(t)
                c.setCheckState(QtCore.Qt.Unchecked)
            else:
                tlist.append(t)
                c.setCheckState(QtCore.Qt.Checked)
            sortto(tlisto,tlist)
        return f
    cs = [QtGui.QCheckBox(l) for l in labels]
    for c,l in zip(cs,labels):c.setCheckState(qck if l in tlist else quck)
    for c,l in zip(cs,labels):c.stateChanged.connect(togg(c,l))
    if callback:
        for c,l in zip(cs,labels):c.stateChanged.connect(callback)
    #if master:cs.insert(0,create_master(cs))
    return mwidget(layout(cs,ori),label)

'''
    def create_master(checks):

        def flip_all(integer):
            [check.stateChanged.emit(integer) for check in checks]
            if integer == 0:
                [check.setCheckState(QtCore.Qt.Unchecked) 
                                    for check in checks]

            if integer == 2:
                [check.setCheckState(QtCore.Qt.Checked) 
                                for check in checks]

        def find_initial_state():
            state_bool = not (False in [check.checkState() 
                                    for check in checks])
            if state_bool: return QtCore.Qt.Checked
            else: return QtCore.Qt.Unchecked

        master = QtGui.QCheckBox('All')
        master.setCheckState(find_initial_state())
        master.stateChanged.connect(flip_all)
        return master
'''

def selector(labels,initial,callback,label = 'mwidgetselector'):
    def pick():
        c = sel.currentIndex()
        callback(lcopy,c)
    lcopy = labels[:]
    sel = QtGui.QComboBox()
    for l in labels:sel.addItem(l)
    sel.currentIndexChanged.connect(pick)
    sel.setCurrentIndex(labels.index(initial))
    return mwidget(layout((sel,)),label)

def radios(labels,initial,callback,label = 'mwidgetradios',ori = 'v'):
    def pick(x):
        f = lambda : callback(lcopy,x)
        return f
    lcopy = labels[:]
    rads = [QtGui.QRadioButton(l) for l in labels]
    rads[labels.index(initial)].setChecked(True)
    for rx in range(len(rads)):rads[rx].clicked.connect(pick(rx))
    return mwidget(layout(rads,ori),label)

###############################################################################
### classes useful for making applications
###############################################################################

class mapp(QtGui.QApplication):

    def __init__(self,main_window_class = None,**kws):
        QtGui.QApplication.__init__(self,sys.argv)
        if main_window_class is None:main_window_class = mwindow
        self.main_window = main_window_class(**kws)

class mwindow(QtGui.QMainWindow):

    def _standards(self,**st):
        if 'title' in st:wt = st['title']
        else:wt = 'mwindow'
        if 'geometry' in st:geo = st['geometry']
        else:
            x,y = convert_pixel_space(300,300)
            x_size,y_size = convert_pixel_space(512,512)
            geo = (x,y,x_size,y_size)

        #try: self.setWindowIcon(lgb.create_icon(standards['window_icon']))
        #except KeyError: pass

        self.setWindowTitle(wt)
        self.setGeometry(*geo)

    def __init__(self,**kws):
        QtGui.QMainWindow.__init__(self)
        self._standards(**kws)
        w = QtGui.QWidget()
        w.setLayout(self.content(**kws))
        self.setCentralWidget(w)
        self.show()

    def content(self,**kws):
        content = QtGui.QVBoxLayout()
        return content

class pwindow(mwindow):

    def content(self,**kws):
        tree = tree_book(**kws)
        content = layout((tree,),'v')
        return content

###############################################################################
### custom widget classes
###############################################################################

class mwidget(QtGui.QWidget,mb.mobject):

    def __init__(self,lay = None,lab = '',**kws):
        QtGui.QWidget.__init__(self)
        if not lay is None:
            if lab:lay = bound(lab,lay)
            self.setLayout(lay)

class plttoolbar(NavigationToolbar2,QtGui.QToolBar):

    message = QtCore.Signal(str)
    if hasattr(NavigationToolbar2,'toolitems'):
        titems = NavigationToolbar2.toolitems 
        defitems = ('Pan','Zoom','Save')
        toolitems = [t for t in titems if t[0] in defitems]
    else:toolitems = []

    def pan(self,*ags):
        super(plttoolbar,self).pan(*ags)
        self._update_buttons_checked()

    def zoom(self,*ags):
        super(plttoolbar,self).zoom(*ags)
        self._update_buttons_checked()

    def _update_buttons_checked(self):
        self._actions['pan'].setChecked(self._active == 'PAN')
        self._actions['zoom'].setChecked(self._active == 'ZOOM')

    def _init_toolbar(self):
        for text,tooltip_text,image_file,callback in self.toolitems:
            if text is None:self.addSeparator()
            else:
                i = QtGui.QIcon()
                a = self.addAction(i,text,getattr(self,callback))
                self._actions[callback] = a
            if callback in ('zoom','pan'):a.setCheckable(True)
            if tooltip_text is not None:a.setToolTip(tooltip_text)
        self.locLabel = QtGui.QLabel("", self)
        self.locLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        self.locLabel.setSizePolicy(QtGui.QSizePolicy(
            QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Ignored))
        labelAction = self.addWidget(self.locLabel)
        labelAction.setVisible(True)

    def __init__(self,canvas):
        self.canvas = canvas
        self.img_extensions = 'Image (*.png,*.pdf)'
        self._actions = {}
        QtGui.QToolBar.__init__(self)
        NavigationToolbar2.__init__(self,canvas)

    #toolitems.append(('Labels','Change the title and axes labels','gear','labels'))
    def labels(self):
        print('need labels func!')
    '''#
        lgd = lfu.gui_pack.lgd
        domain = page.get_xtitle()
        labels_dlg = lgd.change_labels_dialog(page.get_title(),domain,
            page.get_ytitle(),page.max_line_count,page.parent.colors, 
            page.get_targets(),domain,page.x_log,page.y_log,
            page.parent.cplot_interpolation,
            page.parent.cplot_zmin,page.parent.cplot_zmax)
        if not labels_dlg: return
        new_title,new_x_label,new_y_label,colors,xlog,ylog,cinterp,czmin,czmax = labels_dlg
        
        #page.set_title(new_title)
        page.parent.plot_title = new_title
        page.set_title()

        #page.set_xtitle(new_x_label)
        page.parent.xtitle = new_x_label
        page.set_xtitle()

        #page.set_ytitle(new_y_label)
        page.parent.ytitle = new_y_label
        page.set_ytitle()

        #page.colors = colors
        try:czmin = float(czmin)
        except:czmin = None
        try:czmax = float(czmax)
        except:czmax = None
        page.parent.colors = colors
        page.parent.cplot_interpolation = cinterp
        page.parent.cplot_zmin = czmin
        page.parent.cplot_zmax = czmax

        page.parent.x_log = xlog
        page.parent.y_log = ylog
        page.x_log = xlog
        page.y_log = ylog

        #ax = page.newest_ax

        ax = page.get_newest_ax()
        ax.set_xlabel(new_x_label, fontsize = 18)
        ax.set_ylabel(new_y_label, fontsize = 18)
        if page.parent.y_log: ax.set_yscale('log')
        if self.parent.plot_type in ['surface']:
            ax.set_zlabel(new_title, fontsize = 18)
        ax.set_title(new_title)
        else: cpage = self.parent.current_page

        #self.parent.get_current_page().show_plot()

        cpage().show_plot()
    '''#

    def draw_rubberband(self,event,x0,y0,x1,y1):
        height = self.canvas.figure.bbox.height
        y1 = height - y1
        y0 = height - y0
        w = abs(x1 - x0)
        h = abs(y1 - y0)
        rect = [int(val)for val in (min(x0,x1),min(y0,y1),w,h)]
        self.canvas.drawRectangle(rect)

    def save_figure(self,*ags):
        fname = QtGui.QFileDialog.getSaveFileName(self,
            'Choose Filename','aplot.pdf',self.img_extensions) 
        if fname:
            try:
                self.canvas.print_figure(six.text_type(fname[0]))
                print('saved figure at: %s' % fname)
            except Exception as e:
                QtGui.QMessageBox.critical(
                    self,'error saving file',str(e),
                    QtGui.QMessageBox.Ok,QtGui.QMessageBox.NoButton)

plt_figure = None
def init_figure():
    global plt_figure
    if mmpi.size() == 1 and mmpi.root():
        plt_figure = plt.figure()

class mpltwidget(mwidget):
    
    def show(self):
        #print('mpltwidget show')
        mwidget.show(self.update())
        return self

    def hide(self):
        #print('mpltwidget hide')
        mwidget.hide(self)
        return self

    def update(self):
        print('mpltwidget should update its plot!')
        ax = self.clear_ax()
        x,y,z = self.xdomain,self.ydomain,self.zdomain
        d,t = self.kws['entry']
        if self.plottype == 'lines':
            ax = self.calc_lines_plot(ax,d,t,x,self._targets,z)
        elif self.plottype == 'color':
            ax = self.calc_color_plot(ax,d,t,x,y,z)
        else:
            print('unknown plottype: %s' % self.plottype)
            raise ValueError

        #if xlog:ax.set_xscale('log')
        #if ylog:ax.set_yscale('log')

        leg = ax.legend()
        if leg:leg.draggable()
        else:print('legend was None...')

        self.canvas.draw()
        return self

    def clear_ax(self,proj = None):
        self.fig.clf()
        ax = self.fig.gca(projection = proj)
        ax.cla()
        ax.grid(True)
        return ax

    def calc_lines_plot(self,ax,dt,ts,x,ys,z):
        def get(t):
            tx = ts.index(t)
            return dt[tx],ts[tx]
        ymin,ymax = sys.float_info.max,-sys.float_info.max
        dx,xt = get(x)
        for y in ys:
            if y in self._targets:
                dy,yt = get(y)
                if dy.min() < ymin:ymin = dy.min()
                if dy.max() > ymax:ymax = dy.max()
                ax.plot(dx,dy,label = yt)
        ax.axis((dx.min(),dx.max(),ymin,ymax))
        return ax

    def calc_color_plot(self,ax,dt,ts,x,y,z):
        def get(t):
            tx = ts.index(t)
            return dt[tx],ts[tx]

        dx,xt = get(x)
        dy,yt = get(y)
        dz,zt = get(z)

        print('should make a color plot instead!')
        ds = numpy.zeros((len(dx),len(dy)),dtype = numpy.float)
        ds[2,:] += 13
        ds[:,3] += 10
        
        minz,maxz = ds.min(),ds.max()
        pckws = {
            'shading':'gouraud',
            'cmap':self.colormap, 
            'vmin':minz, 
            'vmax':maxz, 
                }
        pc_mesh = ax.pcolor(dx,dy,ds,**pckws)
        self.fig.colorbar(pc_mesh)
        ax.axis((dx.min(),dx.max(),dy.min(),dy.max()))
        return ax

    def _defbind(self,k):
        def b(ls,c):
            self.__setattr__(k,ls[c])
            print('set pltwidget attribute: %s : %s' % (k,str(ls[c])))
            self.update()
        return b

    def __init__(self,**kws):
        self._def('xdomain',None,**kws)
        self._def('ydomain',None,**kws)
        self._def('zdomain',None,**kws)
        self._def('maxlinecount',20,**kws)
        self._def('colormap',plt.get_cmap('jet'),**kws)
        self._def('plottypes',('lines','color'),**kws)
        self._def('plottype','lines',**kws)
        mwidget.__init__(self)
        self.kws = kws
        self._targets = self.kws['entry'][1][:]

        self.fig = plt_figure
        self.canvas = figure_canvas(self.fig)
        self.toolbar = plttoolbar(self.canvas)

        tcs = checks(self._targets,self._targets,True,self.update,'Plot Targets')
        rds = radios(self.plottypes,self.plottype,self._defbind('plottype'),'Plot Type')
        bts = buttons((self.update,),('clicked',),('Update Plot',),'')
        xsel = selector(self._targets,self._targets[0],self._defbind('xdomain'),'X-Domain')
        ysel = selector(self._targets,self._targets[0],self._defbind('ydomain'),'Y-Domain')
        zsel = selector(self._targets,self._targets[0],self._defbind('zdomain'),'X-Domain')
        left = mwidget(layout((bts,xsel,ysel,zsel)),'')
        hsplit = mwidget(splitter((left,tcs,rds),'h',''),'')
        vsplit = splitter((hsplit,mwidget(layout((self.canvas,self.toolbar)),'')),'v','')

        self.setLayout(vsplit)
        self.setBackgroundRole(QtGui.QPalette.Window)
  
class tree_book(mwidget):

    def set_page(self,pgx):
        self.tree_pages[self.page].hide()
        self.tree_pages[pgx].show()
        self.page = pgx

    def _change_page(self,cpg,ppg):
        for ix in range(len(self.tree_items)):
            if self.tree_items[ix] is cpg:
                self.set_page(ix)
                return

    def _header(self,header):
        if not type(header) is type(''):header = ''
        self.tree.setHeaderLabel(header)

    def _pages(self,pages):
        self.tree.setColumnCount(1)
        self.tree.clear()
        titems,tpages,tops,bottoms = [],[],[],[]
        for x in range(len(pages)):
            pgd,pgt,pge = pages[x]
            top = QtGui.QTreeWidgetItem(None,[pge['header']])
            tops.append(top)
            main_page = mwidget()
            titems.append(top)
            tpages.append(main_page)
            if len(pgd.shape) == 2:
                subs = (((pgd,pgt),'single'),)
            elif len(pgd.shape) == 3:
                subs = tuple(((pgd[x],pgt),str(x)) for x in range(pgd.shape[0]))
            else:
                print('unknown tree widget scenario')
                raise ValueError
            for subpg,subh in subs:
                bottom = QtGui.QTreeWidgetItem(top,[subh])
                bottoms.append(bottom)
                titems.append(bottom)
                t1 = subpg[1][0]
                pkws = {
                    'xdomain':t1,'ydomain':t1,'zdomain':t1,
                    'entry':subpg,'header':subh,
                        }
                sub_page = mpltwidget(**pkws)
                tpages.append(sub_page)
            self.tree.addTopLevelItem(top)
        for page in tpages:
            self.split.addWidget(page)
            page.hide()
        self.tree_items = titems
        self.tree_pages = tpages
        self.tree_tops = tops
        self.tree_bottoms = bottoms
        self.set_page(self.page)

    def _widgets(self):
        self.split = QtGui.QSplitter(QtCore.Qt.Horizontal)
        self.tree = QtGui.QTreeWidget()
        self.split.addWidget(self.tree)

        #self.selector.currentIndexChanged.connect(self.change_page)
        #self.tree.itemCollapsed.connect(self.remember_collapsed)
        #self.tree.itemExpanded.connect(self.remember_expanded)

        self.tree.currentItemChanged.connect(self._change_page)
        self._header(self.header)
        self._pages(self.pages)
        return (self.split,)

    def __init__(self,**kws):
        mwidget.__init__(self,**kws)
        self._def('pages',[],**kws)
        self._def('page',0,**kws)
        self._def('header','treebookheader',**kws)

        wgs = self._widgets()
        self._layout = layout(wgs,'h')
        self.setLayout(self._layout)
        for top in self.tree_tops:self.tree.expandItem(top)





