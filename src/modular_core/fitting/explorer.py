import modular_core.fundamental as lfu
import modular_core.fitting.routine_abstract as fab
import modular_core.io.output as lo

import modular_core.gui.libqtgui as lqg

import pdb,os,sys
import numpy as np

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as figure_canvas
import matplotlib.pyplot as plt

###############################################################################
### explorer walks the parameter space asking user for input
###############################################################################

class explorer(fab.routine_abstract):

    def _iterate(self,ensem,pspace):
        if self.onebyone:
            it = fab.routine_abstract._iterate(self,ensem,pspace)
            self.best = True
            return it
        else:pdb.set_trace()
        # for visiting 2+ locations per iteration:
        #   call fab._iterate for each pspace location
        #   return dpool with each trajectory/data and success bool
        # visiting 1 location:
        #   perform a sim, query user to keep or throw away step
        #   this can use super._iterate
        #pdb.set_trace()

    # overloaded to prompt user in the single plot query case
    # consider a measurement, undo or keep step?
    def _accept_step(self,information,ran):
        if not ran:return False
        if self.onebyone:
            split = information._split()
            #for sch in range(self.simulations_per_iteration):
            #    schild = split.children[sch]
            #    sfriendly = schild._plot_friendly()
            sfriendly = split.children[0]._plot_friendly()
            self._style_friendly_data('--','1.0',' ',sfriendly)
            sfriendly.extend(self.input_friendly)
            acceptance = choose_plot(sfriendly)
            return acceptance
        else:return True

    def _alias_input_data(self):
        self._style_friendly_data('-','1.0',' ',self.input_friendly)

    def _style_friendly_data(self,s,w,m,fly):
        colormap = plt.get_cmap('jet')
        colors = [colormap(i) for i in np.linspace(0,0.9,len(fly))]
        for fx in range(len(fly)):
            fly[fx].color = colors[fx]
            fly[fx].linestyle = s
            fly[fx].linewidth = w
            fly[fx].marker = m

    # prompt the user to select from a collection of plots
    def _feedback(self,information,ran,pspace):
        if self.onebyone:
            fab.routine_abstract._feedback(self,information,ran,pspace)
        else:pdb.set_trace()
        #self._pspace_move(pspace,undo)

    def __init__(self,*args,**kwargs):
        self._default('name','an explorer',**kwargs)
        self._default('max_runtime',300.0,**kwargs)
        self._default('max_iteration',10000.0,**kwargs)
        self._default('onebyone',True,**kwargs)
        fab.routine_abstract.__init__(self,*args,**kwargs)
    
    def _initialize(self,*args,**kwargs):
        check_qt_application()
        fab.routine_abstract._initialize(self,*args,**kwargs)
        if self.input_data:
            self.input_data._stow(v = False)
            self.input_friendly = self.input_data._plot_friendly()
            self._alias_input_data()
        else:self.input_friendly = []

    def _target_settables(self,*args,**kwargs):
        capture_targetable = self._targetables(*args,**kwargs)
        self.target_list = capture_targetable[:]
        self.capture_targets = self.target_list 
        fab.routine_abstract._target_settables(self,*args,**kwargs)

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self._target_settables(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        fab.routine_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

# return valid **kwargs for explorer based on msplit(line)
def parse_line(split,ensem,procs,routs):
    dpath = lfu.resolve_filepath(split[3])
    eargs = {
        'name':split[0],
        'variety':split[1],
        'pspace_source':split[2],
        'input_data_path':dpath, 
        'metamapfile':split[4], 
            }
    return eargs

###############################################################################

if __name__ == 'modular_core.fitting.explorer':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    #lqg = lfu.gui_pack
    fab.routine_types['explorer'] = (explorer,parse_line)

###############################################################################

###############################################################################
### utility functions and the like
###############################################################################

#figure = plt.figure()
#canvas = figure_canvas(figure)
figure = None
canvas = None

class plot_dialog(lqg.plot_window):

    def __init__(self,*args,**kwargs):
        self._default('choice',True,**kwargs)
        kwargs['figure'] = figure
        kwargs['canvas'] = canvas
        lqg.plot_window.__init__(self,*args,**kwargs)

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        [pg._sanitize(self,**kwargs) for pg in self.pages]
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['check_set'], 
                append_instead = [False],
                instances = [[self]],
                keys = [['choice']],
                box_labels = ['Is this closer to the desired plot?'],
                labels = [['Accept last parameter space step?']]))
        lqg.plot_window._widget(self,*args,from_sub = True)

def check_qt_application():
    global figure
    global canvas
    figure = plt.figure()
    canvas = figure_canvas(figure)

    qapp = lgb.QtGui.QApplication
    if qapp.instance() is None:
        app = qapp(sys.argv)
        app.setStyle(lgb.create_style('plastique'))

#check_qt_application()
def choose_plot(data):
    targets = [d.name for d in data]
    dlg = plot_dialog(
        title = 'tITle',plot_types = ['lines'], 
        cplot_interpolation = 'nearest')
    dcontainer = lfu.data_container(data = data)
    dlg.set_plot_info(
        dcontainer,'fitplot',targets,title = 'title',
        x_ax_title = 'xtitle',y_ax_title = 'ytitle')
    dlg()
    check_qt_application_exec()
    lo.qapp_started_flag = False
    choice = dlg.choice
    #raw_input('JUST IN CASE!')
    return choice

def check_qt_application_exec():
    app = lgb.QtGui.QApplication.instance()
    if app is None:print 'app was none!!'
    elif not lo.qapp_started_flag:
        app.exec_()
        lo.qapp_started_flag = True

###############################################################################










