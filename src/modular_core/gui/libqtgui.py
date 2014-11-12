import modular_core.libfundamental as lfu
import modular_core.gui.libqtgui_masons as lgm
import modular_core.gui.libqtgui_bricks as lgb
import modular_core.gui.libqtgui_dialogs as lgd

#from PyQt4 import QtGui, QtCore
from PySide import QtGui, QtCore
import PySide

try:
    import matplotlib
    matplotlib.rcParams['backend.qt4'] = 'PySide'
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as figure_canvas
    #from matplotlib.backend_bases import NavigationToolbar2 as plt_toolbar
    import matplotlib.pyplot as plt
    #import matplotlib.patches as patches
    #import matplotlib.path as path
    #from mpl_toolkits.mplot3d import axes3d, Axes3D
except ImportError:
    traceback.print_exc(file=sys.stdout)
    print 'matplotlib could not be imported! - dialogs'

import types
import sys
import os
import time

import pdb

_window_ = None

def initialize_gui(params):
    app = application(params, sys.argv)
    sys.exit(app.exec_())

class application(QtGui.QApplication):

    _content_ = []
    _standards_ = {}
    def __init__(self, params, argv):
        self.params = params
        QtGui.QApplication.__init__(self, argv)
        self.initialize(content = self._content_,
                    standards = self._standards_)

    def initialize(self, *args, **kwargs):
        self.main_window = gui_window(*args, **kwargs)

class gui_window(QtGui.QMainWindow):
    #gui_window can hold any number of mobjs, and upon
    # request, can calculate the widgets of any of those
    # mobjs individually, and update its display
    def __init__(self, *args, **kwargs):
        global _window_
        _window_ = self
        super(gui_window, self).__init__()
        self.initialize(*args, **kwargs)

    def initialize(self, *args, **kwargs):
        self.mason = lgm.standard_mason(self)
        self.settables_infos = (self, )
        try: standards = kwargs['standards']
        except KeyError: standards = {}
        self.apply_standards(standards)
        self.statusBar().showMessage('Ready')
        try: self.content = kwargs['content']
        except KeyError: self.content = None
        self.set_up_widgets(*args, **kwargs)
        self.show()

    def apply_standards(self, standards):
        try: title = standards['title']
        except KeyError: title = '--'
        try: geometry = standards['geometry']
        except KeyError:
            x, y = lfu.convert_pixel_space(300, 300)
            x_size, y_size = lfu.convert_pixel_space(512, 512)
            geometry = (x, y, x_size, y_size)

        try: self.setWindowIcon(lgb.create_icon(
                    standards['window_icon']))
        except KeyError: pass
        self.setWindowTitle(title)
        self.setGeometry(*geometry)

    def set_up_widg_templates(self, *args, **kwargs):
        if type(self.content) is types.ListType:
            #obliges if mobj needs widgets recalculated
            #uses the mobjs' widgets for the current widget set
            [content.set_settables(*self.settables_infos) for 
                content in self.content if content.rewidget(
                        infos = self.settables_infos)]
            self.widg_templates = lfu.flatten([content.widg_templates 
                        for content in self.content])
            self.menu_templates = lfu.flatten([content.menu_templates
                        for content in self.content])
            self.tool_templates = lfu.flatten([content.tool_templates
                        for content in self.content])

        else:
            print 'window content unrecognized; window will be empty'
            self.content = []

    def set_up_widgets(self, *args, **kwargs):
        self.set_up_widg_templates(*args, **kwargs)
        self.set_up_menubars(*args, **kwargs)
        self.set_up_toolbars(*args, **kwargs)
        layout = QtGui.QVBoxLayout()
        for template in self.widg_templates:
            if hasattr(template, 'mason'): mason = template.mason
            else: mason = self.mason
            layout.addLayout(mason.interpret_template(template))

        central_wrap = lgb.central_widget_wrapper(content = layout)
        self.setCentralWidget(central_wrap)

    def set_up_menubars(self, *args, **kwargs):
        menubar = self.menuBar()
        menubar.clear()
        self.menus = []
        added_menus = []
        for template in self.menu_templates:
            for label, action in zip(template.menu_labels, 
                                    template.menu_actions):
                if not label in added_menus:
                    menu = menubar.addMenu(label)
                    self.menus.append(menu)
                    added_menus.append(label)
                
                else: menu = self.menus[added_menus.index(label)]
                menu.addAction(action)

    def set_up_toolbars(self, *args, **kwargs):
        try: [self.removeToolBar(bar) for bar in self.toolbars]
        except AttributeError: pass
        self.toolbars = []
        added_bars = []
        for template in self.tool_templates:
            for label, action in zip(template.tool_labels, 
                        template.tool_actions):
                if not label in added_bars:
                    toolbar = self.addToolBar(label)
                    self.toolbars.append(toolbar)
                    added_bars.append(label)

                else: toolbar = self.toolbars[added_bars.index(label)]
                toolbar.addAction(action)

    def on_close(self):
        lgd.message_dialog(self, 'Are you sure to quit?', 'Message', 
            if_yes = QtCore.QCoreApplication.instance().quit)

    def closeEvent(self, event):
        reply = QtGui.QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QtGui.QMessageBox.Yes | 
                QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes: event.accept()
        else: event.ignore()

    def on_center(self):
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def on_resize(self):
        x, y = lfu.convert_pixel_space(256, 256)
        x_size, y_size = lfu.convert_pixel_space(1280, 768)
        geometry = (x, y, x_size, y_size)
        self.setGeometry(*geometry)

class plot_page(lfu.modular_object_qt):

    _inspector_is_mobj_panel_ = True

    def __init__(self, parent, pagenum, data, targs, 
            title, xtitle, ytitle, filename, **kwargs):
        #self.impose_default('targets', [], **kwargs)
        #ptypes = ['lines', 'color', 'surface', 'bars']
        #self.impose_default('plot_type', 'lines', **kwargs)
        #self.impose_default('plot_types', ptypes, **kwargs)
        self.pagenum = pagenum
        self.title = title
        self.xtitle = xtitle
        self.ytitle = ytitle
        self.x_log = parent.x_log
        self.y_log = parent.y_log
        self.max_line_count = 20
        self.colors = []
        self.cplot_interpolation = parent.cplot_interpolation
        #Acceptable interpolations are:
        # 'none', 'nearest', 'bilinear', 'bicubic', 'spline16', 'spline36', 
        # 'hanning', 'hamming', 'hermite', 'kaiser', 'quadric', 'catrom', 
        # 'gaussian', 'bessel', 'mitchell', 'sinc', 'lanczos'
        self.fullfilename = filename
        self.filename = filename.split(os.path.sep)[-1]
        self.targs = targs[:]
        self.active_targs = targs[:]
        if data.data: self.xdomain = data.data[0].label
        else: self.xdomain = xtitle
        if data.data: self.ydomain = data.data[0].label
        else: self.ydomain = ytitle
        if data.data: self.zdomain = data.data[0].label
        else: self.zdomain = title
        if hasattr(data, 'plt_callbacks'):
            ucbs = data.plt_callbacks
        else: ucbs = {}
        self.user_callbacks = ucbs
        label = ' : '.join([str(pagenum), self.filename])
        lfu.modular_object_qt.__init__(self, 
            label = label, data = data, parent = parent)

    def get_targets(self):
        return self.targs

    def get_title(self):
        return self.title
    def set_title(self, new):
        self.title = new
        qplot = self.qplot[0]
        qplot.user_title = new

    def get_xtitle(self):
        return self.xtitle
    def set_xtitle(self, new):
        self.xtitle = new
        qplot = self.qplot[0]
        qplot.user_xtitle = new

    def get_ytitle(self):
        return self.ytitle
    def set_ytitle(self, new):
        self.ytitle = new
        qplot = self.qplot[0]
        qplot.user_ytitle = new

    def get_newest_ax(self):
        ax = self.qplot[0].newest_ax
        return ax

    def get_plot_info(self, data):
        data.xdomain = self.parent.xdomain
        data.ydomain = self.parent.ydomain
        data.zdomain = self.parent.zdomain
        data.active_targs = self.parent.active_targs
        data.cplot_interpolation = self.parent.cplot_interpolation
        data.x_log = self.parent.x_log
        data.y_log = self.parent.y_log
        return data

    def redraw_plot(self, xlab = None, ylab = None, title = None):
        qplot = self.qplot[0]
        data = self.get_plot_info(self.data)
        ptype = self.parent.plot_type
        qplot.plot(data, xlab, ylab, title, ptype = ptype)

    def show_plot(self):
        self.redraw_plot(self.get_xtitle(), 
            self.get_ytitle(), self.get_title())

    def roll_data(self):
        qplot = self.qplot[0]
        data = self.get_plot_info(self.data)
        #if self.plot_type == 'lines':
        #    print 'no plot roll for line data!'
        #elif self.plot_type == 'color':
        if self.parent.plot_type in ['color','voxels','bars']:
            slsels = data.sliceselectors
            slicekeys = slsels.__dict__.keys()
            selkeys = [ke for ke in slicekeys if
                ke.startswith('_sliceselector_')]
            sels = [slsels.__dict__[ke][0] for ke in selkeys]
            sels = [sl.children()[1] for sl in sels]
            rolsel = sels[0]#select the 0th axis only for now!
            max_rdex = rolsel.count() - 1
            data.slice_panel = self.parent.slice_panel[0]
            data.roll_delay = self.parent.get_roll_delay(max_rdex)
        #elif self.plot_type == 'surface':
        #    print 'no plot roll for surface data'
        #elif self.plot_type == 'bars':
        #    print 'no plot roll for bar data'
        #data.roll_delay = self.parent.roll_delay

        qplot.roll_data(data, self.get_xtitle(), self.get_ytitle())

    def set_settables(self, *args, **kwargs):
        window = args[0]
        toolbar_funcs = [window.get_current_page]
        data = self.data
        self.handle_widget_inheritance(*args, **kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['plot'], 
                keep_frame = [True], 
                instances = [[
                    self.parent.figure, 
                    self.parent.canvas]], 
                handles = [(self, 'qplot')], 
                callbacks = [toolbar_funcs], 
                datas = [data]))
        lfu.modular_object_qt.set_settables(
            self, *args, from_sub = True)

class plot_window(lfu.modular_object_qt):

    def __init__(self, *args, **kwargs):
        self.impose_default('selected_page_label', None, **kwargs)
        self.impose_default('page_labels', [], **kwargs)
        self.impose_default('pages', [], **kwargs)
        self.impose_default('title', 'Plot Window', **kwargs)
        self.impose_default('targs', [], **kwargs)
        self.impose_default('slice_widgets', [], **kwargs)
        self.impose_default('x_log', False, **kwargs)
        self.impose_default('y_log', False, **kwargs)
        ptypes = ['lines', 'color', 'surface', 'bars', 'voxels', 'tables']
        #ptypes = ['lines', 'color', 'surface', 'bars']
        self.impose_default('cplot_interpolation', 'bicubic', **kwargs)
        self.impose_default('plot_type', 'lines', **kwargs)
        self.impose_default('plot_types', ptypes, **kwargs)
        #self.impose_default('roll_dex', None, **kwargs)
        #self.impose_default('max_roll_dex', None, **kwargs)
        self.impose_default('roll_delay', 0.001, **kwargs)
        self.impose_default('roll_time_span', 1.0, **kwargs)
        self.impose_default('roll_methods', 
            ['time_span', 'preset'], **kwargs)
        self.impose_default('roll_method', 'time_span', **kwargs)
        self.bin_data_types = ['bin_vector']
        self.surf_data_types = ['surface_vector', 'surface_reducing']
        self.vox_data_types = ['voxel_vector']
        x, y = lfu.convert_pixel_space(256, 256)
        x_size, y_size = lfu.convert_pixel_space(1024, 768)
        self._geometry_ = (x, y, x_size, y_size)

        self.mason = lgm.standard_mason()
        self.figure = plt.figure()
        self.canvas = figure_canvas(self.figure)
        lfu.modular_object_qt.__init__(self, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        page = self.get_current_page()
        self.active_targs = page.active_targs
        self.xdomain = page.xdomain
        self.ydomain = page.ydomain
        self.zdomain = page.zdomain
        self.user_callbacks = page.user_callbacks
        self._display_interface_(self.mason)

    def get_current_page(self):
        if self.selected_page_label == 'None': return None
        pdex = self.page_labels.index(self.selected_page_label)
        return self.pages[pdex]

    def using_bars(self):
        return self.plot_type in ['bars']

    def using_surfaces(self):
        return self.plot_type in ['surface', 'color']

    def using_voxels(self):
        return self.plot_type in ['voxels']

    def set_up_widgets(self):
        current_page = self.get_current_page()
        if self.using_surfaces() or self.using_voxels() or self.using_bars():
            could = self.update_slice_panel() 
            if could: self.slice_panel[0].show()
            else: self.slice_panel[0].hide()
        else: self.slice_panel[0].hide()
        if not current_page is None: current_page.redraw_plot()

    def set_plot_info(self, dcontainer, filename, specs, title = 'title', 
            x_ax_title = 'xtitle', y_ax_title = 'ytitle'):
        pagenum = len(self.pages) + 1
        self.pages.append(plot_page(self,pagenum,dcontainer,specs,
                title,x_ax_title,y_ax_title,filename))
        self.page_labels.append(self.pages[-1].label)
        self.targs += self.pages[-1].targs
        self.targs = lfu.uniqfy(self.targs)
        if not self.selected_page_label:
            self.selected_page_label = self.pages[-1].label

    def get_roll_delay(self, max_r_dex):
        if self.roll_method == 'time_span':
            rdelay = self.roll_time_span/float(max_r_dex)
        elif self.roll_method == 'preset': rdelay = self.roll_delay
        else:
            print 'roll method is invalid!'
            return
        return rdelay

    def roll_pages(self):
        cata = self._catalog_[0].children()[0]
        sele = cata.selector
        rdex = 1
        max_rdex = len(cata.pages) - 1
        rdelay = self.get_roll_delay(max_rdex)
        while rdex <= max_rdex:
            sele.setCurrentIndex(rdex)
            cata.pages[rdex].repaint()
            rdex += 1
            time.sleep(rdelay)

    def update_slice_panel(self):
        slice_temps = self.make_slice_templates()
        if not slice_temps: return False
        pan = self.slice_panel[0]
        lay = pan.children()[0]
        cent = pan.children()[1]
        lay.removeWidget(cent)
        cent.deleteLater()
        new_pan = lgb.create_panel(slice_temps, 
            self.mason, False, 'vertical', True)
        lay.addWidget(new_pan)
        return True

    def make_slice_templates(self):
        def generate_slice_func(vals,dex):
            def slice_func(new):
		new = new.currentIndex()
                ax_defs[dex] = float(vals[new])
            return slice_func

        page = self.get_current_page()
        data = page.data
        data.sliceselectors = lfu.data_container()
        #if self.using_surfaces():
        #    reledata = [d for d in data.data if 
        #        d.tag in self.surf_data_types and 
        #        d.label in self.active_targs]
        #elif self.using_voxels():
        #    reledata = [d for d in data.data if 
        #        d.tag in self.vox_data_types and
        #        d.label in self.active_targs]
        #else:
        slice_types =\
            self.bin_data_types +\
            self.surf_data_types +\
            self.vox_data_types
        reledata = [d for d in data.data if 
            d.tag in slice_types and d.label 
            in self.active_targs]
        if reledata:
            dlabs = [d.label for d in reledata]
            if self.zdomain in dlabs:
                ddex = dlabs.index(self.zdomain)
            else: ddex = 0
            surf = reledata[ddex]
        else:
            return []
        ax_labs = surf.axis_labels
        ax_vals = surf.axis_values
        ax_defs = surf.axis_defaults
        rng = range(len(ax_defs))
        slice_templates = []      
        for dex, lab, sca, def_ in zip(rng, ax_labs, ax_vals, ax_defs):
            #pdb.set_trace()
            scastr = sca.as_string_list()
            slice_templates.append(
                lgm.interface_template_gui(
                    widgets = ['selector'], 
                    handles = [(data.sliceselectors, 
                        '_sliceselector_'+str(dex))], 
                    labels = [scastr], 
                    initials = [[str(def_)]], 
                    bindings = [[generate_slice_func(scastr,dex)]], 
                    refresh = [[True]], 
                    window = [[self]], 
                    box_labels = [lab]))
        return slice_templates

    def set_settables(self, *args, **kwargs):
        self.handle_widget_inheritance(*args, **kwargs)
        [pg.set_settables(self, **kwargs) for pg in self.pages]
        self.widg_templates.append(
                lgm.interface_template_gui(
                    layout = 'grid', 
                panel_position = (0,3), 
                widgets = ['mobj_catalog'], 
                instances = [[self.pages,self]], 
                keys = [['selected_page_label']], 
                handles = [(self, '_catalog_')], 
                callbacks = [[(self.set_up_widgets,), 
                        self.roll_pages]], 
                minimum_sizes = [[(1024, 768)]], 
                initials = [[self.selected_page_label]]))
        ucbs = self.user_callbacks
        cblab = 'change_x_domain'
        cb = ucbs[cblab] if cblab in ucbs.keys() else None
        self.widg_templates.append(
            lgm.interface_template_gui(
                panel_position = (0,0), 
                widgets = ['selector'], 
                layout = 'vertical', 
                labels = [self.targs], 
                initials = [[self.xdomain]], 
                instances = [[self]], 
                keys = [['xdomain']], 
                bindings = [[cb] if cb else None], 
                refresh = [[True]], 
                window = [[self]], 
                box_labels = ['X-Domain']))
        ucbs = self.user_callbacks
        cblab = 'change_y_domain'
        cb = ucbs[cblab] if cblab in ucbs.keys() else None
        self.widg_templates[-1] +=\
            lgm.interface_template_gui(
                widgets = ['selector'], 
                labels = [self.targs], 
                initials = [[self.ydomain]], 
                instances = [[self]], 
                keys = [['ydomain']], 
                bindings = [[cb] if cb else None], 
                refresh = [[True]], 
                window = [[self]], 
                box_labels = ['Y-Domain'])
        ucbs = self.user_callbacks
        cblab = 'change_z_domain'
        cb = ucbs[cblab] if cblab in ucbs.keys() else None
        self.widg_templates[-1] +=\
            lgm.interface_template_gui(
                widgets = ['selector'], 
                labels = [self.targs], 
                initials = [[self.zdomain]], 
                instances = [[self]], 
                keys = [['zdomain']], 
                bindings = [[cb] if cb else None], 
                refresh = [[True]], 
                window = [[self]], 
                box_labels = ['Surface Target'])
        self.widg_templates[-1] +=\
            lgm.interface_template_gui(
                widgets = ['radio'], 
                instances = [[self]], 
                keys = [['plot_type']], 
                initials = [[self.plot_type]], 
                labels = [self.plot_types], 
                refresh = [[True]], 
                window = [[self]], 
                box_labels = ['Plot Type'])
        targ_template =\
            lgm.interface_template_gui(
                panel_position = (0,1), 
                widgets = ['check_set'], 
                callbacks = [[self.set_up_widgets]], 
                instances = [[self]], 
                keys = [['active_targs']], 
                labels = [self.targs], 
                append_instead = [True])
        self.widg_templates.append(
            lgm.interface_template_gui(
                panel_position = (0,1),
                widgets = ['panel'], 
                scrollable = [True], 
                templates = [[targ_template]], 
                box_labels = ['Targets']))
        slice_templates = self.make_slice_templates()
        if slice_templates: slice_verb = 1
        else: slice_verb = 10
        self.widg_templates.append(
            lgm.interface_template_gui(
                panel_position = (0,2), 
                widgets = ['panel'], 
                layouts = ['vertical'], 
                scrollable = [True], 
                verbosities = [slice_verb], 
                handles = [(self, 'slice_panel')], 
                box_labels = ['Additional Axis Handling'], 
                templates = [slice_templates]))
        lfu.modular_object_qt.set_settables(
            self, *args, from_sub = True)

if __name__ == '__main__': 'this is a library!'





