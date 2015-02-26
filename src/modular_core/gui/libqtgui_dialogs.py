import modular_core.fundamental as lfu
#import modular_core.libmath as lm
import modular_core.gui.libqtgui_bricks as lgb
import modular_core.gui.libqtgui_masons as lgm
from PySide import QtGui, QtCore

import pdb,traceback,sys,os,types,time
import numpy as np
import itertools as it

import matplotlib
matplotlib.rcParams['backend.qt4'] = 'PySide'
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backend_bases import NavigationToolbar2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.path as path
from matplotlib import animation

from mpl_toolkits.mplot3d import axes3d, Axes3D

if __name__ == 'modular_core.gui.libqtgui_dialogs':pass
if __name__ == '__main__':print 'libqtgui_dialogs of modular_core'

def message_dialog(window, message, dialog_title, if_yes = None):
    if if_yes is not None:
        reply = QtGui.QMessageBox.question(window, dialog_title, 
                message, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, 
                                QtGui.QMessageBox.No)
        if hasattr(if_yes, '__call__'):
            if reply == QtGui.QMessageBox.Yes: if_yes()

        elif type(if_yes) is types.BooleanType:
            if reply == QtGui.QMessageBox.Yes: return True
            elif reply == QtGui.QMessageBox.No: return False

    else: reply = QtGui.QMessageBox.question(window, dialog_title, 
                                message, QtGui.QMessageBox.Ok)

def create_dialog(title = 'Dialog', message = '', variety = 'input', 
                    fi_exts = None, initial = None, parent = None, 
                    templates = None, mason = None, options = None):

    def show_dialog_input():
        text, ok = QtGui.QInputDialog.getText(parent, title, message)
        if ok: return text

    def show_dialog_color():
        col = QtGui.QColorDialog.getColor()
        if col.isValid():
            some_frame.setStyleSheet(
                "QWidget { background-color: %s }" % col.name())

    def show_dialog_font():
        font, ok = QtGui.QFontDialog.getFont()
        if ok: some_label.setFont(font)

    def show_dialog_file():
        fname, _ = QtGui.QFileDialog.getOpenFileName(
            parent, 'Open file', initial, fi_exts)
        return fname

    def show_dialog_file_save():
        fname, _ = QtGui.QFileDialog.getSaveFileName(
            parent, 'Choose filename', initial, fi_exts)
        return fname

    def show_dialog_dir():
        return QtGui.QFileDialog.getExistingDirectory(
                parent, 'Open file', initial)

    def show_dialog_templated():
        if templates is None: temps = []
        else: temps = templates
        if mason is None: mas = lgm.standard_mason()
        else: mas = mason
        diag = create_obj_dialog(templates = temps,mason = mas)
        return diag

    if fi_exts is None: fi_exts = ''
    if initial is None: initial = os.getcwd()
    if variety == 'input': return show_dialog_input
    elif variety == 'color': return show_dialog_color
    elif variety == 'font': return show_dialog_font
    elif variety == 'file': return show_dialog_file
    elif variety == 'file_save': return show_dialog_file_save
    elif variety == 'directory': return show_dialog_dir
    elif variety == 'radioinput':
        choice_container = lfu.data_container(data = options[0])
        options_templates = [lgm.interface_template_gui(
            layout = 'horizontal', 
            widgets = ['radio'], 
            verbosities = [0], 
            labels = [options], 
            initials = [[choice_container.data]], 
            instances = [[choice_container]], 
            keys = [['data']], 
            #box_labels = ['Ensemble Module'], 
            minimum_sizes = [[(250, 50)]])]
        mod_dlg = create_dialog(title = title, 
            templates = options_templates,variety = 'templated')
        module = mod_dlg()
        if module: module = choice_container.data
        return module
    elif variety == 'templated': return show_dialog_templated()
    else:
        print 'variety unrecognized; defaulting to "input"'
        return show_dialog_input

class create_obj_dialog(QtGui.QDialog):
    made = False

    def __call__(self, *args, **kwargs):
        self.dialoging = True
        self.exec_()
        if self.made: return True
        else: return False

    def __init__(self, *args, **kwargs):
        super(create_obj_dialog, self).__init__(None)
        self.dialoging = False
        try: self.mason = kwargs['mason']
        except KeyError: self.mason = lgm.standard_mason()
        try: self.widg_templates = kwargs['templates']
        except KeyError: self.widg_templates = []
        try: self.title = kwargs['title']
        except KeyError: self.title = 'Make MObject'
        self.setWindowTitle(self.title)
        self.button_icons =\
            [lfu.get_resource_path('make.png'), 
            lfu.get_resource_path('back.png')]
        if 'button_regime' in kwargs.keys():
            reg = kwargs['button_regime']
            if reg.startswith('apply'):
                self.button_icons[0]=lfu.get_resource_path('apply.png')

            if reg.endswith('cancel'):
                self.button_icons[1]=lfu.get_resource_path('cancel.png')

        self.setWindowIcon(lgb.create_icon(
            lfu.get_resource_path('gear.png')))
        if 'from_sub' not in kwargs.keys(): self.set_up_widgets()
        else:
            if not kwargs['from_sub']: self.set_up_widgets()

    def rewidget(self, *args, **kwargs):
        try:
            if type(args[0]) is types.BooleanType:
                self.rewidget_ = args[0]

            else: print 'unrecognized argument for rewidget; ignoring'

        except IndexError: return self.rewidget_

    def set_up_widgets(self, layout = None):
        panel = lgb.create_panel(self.widg_templates, self.mason)
        button_template = lgm.interface_template_gui(
                widgets = ['button_set'], 
                verbosities = [0], 
                layout = 'horizontal', 
                bindings = [[self.on_make, self.reject]], 
                #labels = [['make', 'cancel']], 
                icons = [self.button_icons], 
                minimum_sizes = [[(100, 50), (100, 50)]])
        buttons = self.mason.interpret_template(button_template)
        buttons.itemAt(0).widget().setFocus()
        if layout: layout.addWidget(panel)
        else: layout = lgb.create_vert_box([panel])
        layout.addLayout(buttons)
        self.delete_layout()
        self.setLayout(layout)
            
        #self.layout().addWidget(panel)
        #self.layout().addLayout(buttons)

    def delete_layout(self):
        try:
            old = self.layout()
            # this is probably the way to replace layout items, in lieu of deleting a layout...
            #child = layout.takeAt(0)
            #while child:
            #   ...
            #   del child
            old.deleteLater()

        except AttributeError: pass

    def on_make(self):
        self.made = True
        if self.dialoging: self.accept()

###################
#plotting business#
###################
class labels_dialog(create_obj_dialog):

    def __init__(self, *args, **kwargs):
        if 'newtitle' in kwargs.keys():
            self.newtitle = kwargs['newtitle']
        else: self.newtitle = 'new title'

        if 'newxtitle' in kwargs.keys():
            self.newxtitle = kwargs['newxtitle']
        else: self.newxtitle = 'new x-title'
        if 'x_log' in kwargs.keys():
            self.x_log = kwargs['x_log']
        else: self.x_log = False

        if 'newytitle' in kwargs.keys():
            self.newytitle = kwargs['newytitle']
        else: self.newytitle = 'new y-title'
        if 'y_log' in kwargs.keys():
            self.y_log = kwargs['y_log']
        else: self.y_log = False

        if 'max_line_count' in kwargs.keys():
            self.max_line_count = kwargs['max_line_count']

        else: self.max_line_count = 20
        if 'plot_targets' in kwargs.keys():
            self.plot_targets = kwargs['plot_targets']

        else: self.plot_targets = ['NO TARGETS']
        if 'domain' in kwargs.keys():
            self.domain = kwargs['domain']

        else: self.domain = None
        if 'cplot_interpolation' in kwargs.keys():
            self.cplot_interpolation = kwargs['cplot_interpolation']

        else: self.cplot_interpolation = None
        if self.plot_targets: self.target = self.plot_targets[0]
        else: self.target = None
        colormap = plt.get_cmap('jet')
        if 'colors' in kwargs.keys(): self.colors = kwargs['colors']
        else:
            self.colors = [colormap(i) for i in np.linspace(
                            0, 0.9, min([self.max_line_count, 
                            len(self.plot_targets) - 1]))]

        mason = lgm.standard_mason(parent = self.parent)
        if 'title' in kwargs.keys(): title = kwargs['title']
        else: title = 'Change Plot Labels'

        create_obj_dialog.__init__(self, None, mason = mason, 
                title = title, button_regime = 'apply-cancel', 
                from_sub = True)
        self.set_settables()

    def pick_color(self):
        col = QtGui.QColorDialog.getColor()
        if col.isValid():
            targ_dex = self.plot_targets.index(self.target) - 1
            self.colors[targ_dex] = col.getRgbF()

    def set_settables(self, *args, **kwargs):
        self.widg_templates = []
        title_box = lgm.interface_template_gui(
            widgets = ['text'], 
            keys = [['newtitle']], 
            instances = [[self]], 
            box_labels = ['New Title'])
        title_panel = lgm.interface_template_gui(
            widgets = ['panel'], 
            layout = 'vertical', 
            templates = [[title_box]], 
            box_labels = ['General Settings'])
        x_title_box = lgm.interface_template_gui(
            widgets = ['text'], 
            keys = [['newxtitle']], 
            instances = [[self]], 
            box_labels = ['New X-Title'])
        x_log_box = lgm.interface_template_gui(
            widgets = ['check_set'], 
            labels = [['Use Log Scale']], 
            append_instead = [False], 
            instances = [[self]], 
            keys = [['x_log']])
        x_panel = lgm.interface_template_gui(
            widgets = ['panel'], 
            layout = 'vertical', 
            templates = [[x_title_box, x_log_box]], 
            box_labels = ['X-Axis Settings'])
        y_title_box = lgm.interface_template_gui(
            widgets = ['text'], 
            keys = [['newytitle']], 
            instances = [[self]], 
            box_labels = ['New Y-Title'])
        y_log_box = lgm.interface_template_gui(
            widgets = ['check_set'], 
            labels = [['Use Log Scale']], 
            append_instead = [False], 
            instances = [[self]], 
            keys = [['y_log']])
        y_panel = lgm.interface_template_gui(
            widgets = ['panel'], 
            layout = 'vertical', 
            templates = [[y_title_box, y_log_box]], 
            box_labels = ['Y-Axis Settings'])
        left_panel = title_panel + x_panel + y_panel
        self.widg_templates.append(left_panel)
        codomains = [item for item in self.plot_targets 
                            if not item == self.domain]
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['radio', 'button_set'], 
                labels = [codomains, ['Change Line Color']], 
                initials = [[self.target], None], 
                instances = [[self], None], 
                keys = [['target'], None], 
                bindings = [None, [self.pick_color]], 
                panel_label = 'Line Colors', 
                box_labels = ['Plot Target', None]))
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['radio'], 
                instances = [[self]], 
                keys = [['cplot_interpolation']], 
                labels = [['bicubic', 'bilinear', 'nearest']], 
                initials = [[self.cplot_interpolation]], 
                box_labels = ['Color Plot Settings']))
        self.set_up_widgets()

def change_labels_dialog(title, x_ax, y_ax, max_lines, 
        colors, targets, domain, xlog, ylog, cintrp):
    dlg = labels_dialog(newtitle = title, newxtitle = x_ax, 
        newytitle = y_ax, max_line_count = max_lines, colors = colors, 
                    plot_targets = targets, domain = domain, 
            x_log = xlog, y_log = ylog, cplot_interpolation = cintrp)
    made = dlg()
    if made:
        return (dlg.newtitle, dlg.newxtitle, 
                dlg.newytitle, dlg.colors, 
                dlg.x_log, dlg.y_log, dlg.cplot_interpolation)

    else: return False

###################
#plotting business#
###################

##########################
#parameter space business#
##########################
class trajectory_dialog(create_obj_dialog):

    def __init__(self, *args, **kwargs):
        mason = lgm.standard_mason(parent = self.parent)
        if 'title' in kwargs.keys(): title = kwargs['title']
        else: title = 'Create Trajectory Window'
        #import modular_core.libgeometry as lgeo
        # LGEO AND PSPACEPROXY ARE DEPRECATED
        self.p_sp_proxy = lgeo.p_space_proxy(*args, **kwargs)
        if self.p_sp_proxy.NO_AXES_FLAG and lfu.using_gui():
            lgd.message_dialog(self.parent, 
                'Parameter Space has no axes!', 'Problem')
            self.reject()
        create_obj_dialog.__init__(self, None, mason = mason, 
                            title = title, from_sub = True)
        self.set_settables()

    def set_settables(self, *args, **kwargs):
        self.widg_templates = []
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['radio'], 
                labels = [self.p_sp_proxy.comp_methods], 
                instances = [[self.p_sp_proxy]], 
                keys = [['composition_method']], 
                initials = [[self.p_sp_proxy.composition_method]],  
                box_labels = ['Composition Method']))
        self.set_up_widgets()

    def set_up_widgets(self):
        range_makers, variations = create_ranger_makers(
                            self.p_sp_proxy, 'variations')
        axis_widgets = lgb.central_widget_wrapper(content =\
            lgb.create_vert_box([lgb.central_widget_wrapper(content =\
                lgb.create_vert_box([lgb.create_label(
                text = axis), range_maker])) for axis, range_maker 
                        in zip(self.axis_labels, range_makers)]))
        variations = lgb.central_widget_wrapper(content =\
                        lgb.create_vert_box(variations))
        panel = lgb.create_scroll_area(lgb.central_widget_wrapper(
            content = lgb.create_horz_box([axis_widgets, variations])))
        layout = lgb.create_vert_box([panel])
        create_obj_dialog.set_up_widgets(self, layout)

    def on_make(self):
        self.p_space_proxy.on_make()
        self.result = self.p_sp_proxy.constructed
        self.result_string = self.p_sp_proxy.result_string
        if self.dialoging: create_obj_dialog.on_make(self)
        else: self.made = True

def create_ranger_makers(inst, key):
    makers = []
    displays = []
    for dex in range(len(inst.__dict__[key])):
        displays.append(range_maker_display(inst, key, dex))
        makers.append(range_maker(displays[-1]))

    return makers, displays

class range_maker_display(QtGui.QLabel):

    def __init__(self, inst, key, dex, parent = None):
        super(range_maker_display, self).__init__(parent)
        self.inst = inst
        self.key = key
        self.dex = dex
        self._range_ = ''
        self.box = lgb.create_text_box(parent = self, 
            instance = self, key = '_range_', alignment = 'center', 
            initial = self._range_, multiline = True, rewidget = False)
        self.box.textChanged.connect(self.update_variation)
        self.setLayout(lgb.create_horz_box([self.box]))
        lgb.set_sizes_limits([[self]], [[(100, 80)]])

    def update_variation(self):
        valid = []
        for val in self._range_.split(','):
            try: valid.append(float(val))
            except: pass

        self.inst.__dict__[self.key][self.dex] = valid

class range_maker(QtGui.QLabel):

    def __init__(self, display, parent = None):
        super(range_maker, self).__init__(parent)
        self.display = display
        self._range_ = ''
        self.box = lgb.create_text_box(parent = self, 
            instance = self, key = '_range_', alignment = 'center', 
            initial = self._range_, multiline = False, rewidget = False)
        self.box.returnPressed.connect(self.update_display)
        self.setLayout(lgb.create_horz_box([self.box]))
        lgb.set_sizes_limits([[self]], [[(max([25*10, 100]), 40)]])
        #self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def update_display(self):
        rng, valid = self.make_range()
        if valid: self.display.box.setText(rng)

    def make_range(self):
        ranges, valid = lm.make_range(self._range_)
        return ranges, valid

    def handle_rewidget(self):
        if self.rewidget and issubclass(self.inst.__class__, 
            lfu.modular_object_qt): self.inst.rewidget(True)

##########################
#parameter space business#
##########################



