import modular4.base as mb
import modular4.mpi as mmpi

import sys,matplotlib
matplotlib.rcParams['backend.qt4'] = 'PySide'
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as figure_canvas

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

###############################################################################
### functions to create layouts/widgets
###############################################################################

def layout(widgets = [],orientation = 'v'):
    if orientation == 'v':lay = QtGui.QVBoxLayout
    elif orientation == 'h':lay = QtGui.QHBoxLayout
    l = lay()
    for w in widgets:l.addWidget(w)
    return l

def buttons(funcs,events,labels):
    bs = []
    for bx in range(len(funcs)):
        f,e,l = funcs[bx],events[bx],labels[bx]
        b = QtGui.QPushButton(l)
        b.__getattribute__(e).connect(f)
        bs.append(b)
    return bs

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
        def f():print('bindcalled')
        fs = ((f,),('clicked',),('BIND',))
        bs = buttons(*fs)
        tree = tree_book(**kws)
        ws = [tree]+bs
        content = layout(ws,'v')
        return content

###############################################################################
### custom widget classes
###############################################################################

class mwidget(QtGui.QWidget,mb.mobject):

    def __init__(self,**kws):
        QtGui.QWidget.__init__(self)

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

        #ax.axis(self.get_minmaxes(xs_, ys_))

        x,y,z = self.xdomain,self.ydomain,self.zdomain
        d,t = self.kws['entry']
        ax = self.calc_plot(ax,d,t,x,y,z)

        #if xlog:ax.set_xscale('log')
        #if ylog:ax.set_yscale('log')

        leg = ax.legend()
        leg.draggable()
        self.canvas.draw()
        return self

    def clear_ax(self,proj = None):
        self.fig.clf()
        ax = self.fig.gca(projection = proj)
        ax.cla()
        ax.grid(True)
        return ax

    def calc_plot(self,ax,dt,ts,x,ys,z):
        if ys is None:ys = ts
        def get(t):
            tx = ts.index(t)
            return dt[tx],ts[tx]
        dx,xt = get(x)
        for y in ys:
            dy,yt = get(y)
            ax.plot(dx,dy,label = yt)
        return ax

    def __init__(self,**kws):
        self._def('xdomain',None,**kws)
        self._def('ydomain',None,**kws)
        self._def('zdomain',None,**kws)
        self._def('maxlinecount',20,**kws)
        self._def('colormap',plt.get_cmap('jet'),**kws)
        mwidget.__init__(self)
        self.kws = kws

        self.fig = plt_figure
        self.canvas = figure_canvas(self.fig)
        self.toolbar = mwidget()

        #self.toolbar = plot_window_toolbar(self.canvas,self,self.callbacks)

        pl = layout((self.canvas,self.toolbar),'v')
        self.setLayout(pl)
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
        titems,tpages = [],[]
        for x in range(len(pages)):
            pgd,pgt,pge = pages[x]
            top = QtGui.QTreeWidgetItem(None,[str(pge)])
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
                titems.append(bottom)
                pkws = {
                    'xdomain' : 'time','ydomain' : None,'zdomain' : None,
                    'entry' : subpg,'header' : subh,
                        }
                sub_page = mpltwidget(**pkws)
                tpages.append(sub_page)
            self.tree.addTopLevelItem(top)
        for page in tpages:self.split.addWidget(page.hide())
        self.tree_items = titems
        self.tree_pages = tpages
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





