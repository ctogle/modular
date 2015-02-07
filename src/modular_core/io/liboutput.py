import modular_core.libfundamental as lfu
import modular_core.libgeometry as lgeo
import modular_core.libsettings as lset

import modular_core.io.libfiler as lf
import modular_core.io.libvtkoutput as lvtk
import modular_core.io.libtxtoutput as ltxt

#from cStringIO import StringIO
import os, sys
import time
try: import matplotlib.pyplot as plt
except ImportError: print 'matplotlib could not be imported! - output'
import numpy as np

import pdb

if __name__ == 'modular_core.liboutput':
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'

def parse_output_plan_line(*args):
    data = args[0]
    ensem = args[1]
    parser = args[2]
    procs = args[3]
    routs = args[4]
    spl = [item.strip() for item in data.split(' : ')]
    dex = int(spl[0])
    if dex == 0: output = ensem.output_plan
    #else: output = procs[dex - 1].output
    elif dex <= len(procs): output = procs[dex - 1].output
    else: output = routs[dex - len(procs) - 1].output
    output.save_directory = spl[1]
    output.save_filename = spl[2]
    if 'plt' in spl[3]: output.output_plt = True
    else: output.output_plt = False
    if 'vtk' in spl[3]: output.output_vtk = True
    else: output.output_vtk = False
    if 'pkl' in spl[3]: output.output_pkl = True
    else: output.output_pkl = False
    if 'txt' in spl[3]: output.output_txt = True
    else: output.output_txt = False
    relevant = [item.strip() for item in spl[4].split(',')]
    if 'all' in relevant:
        if lfu.using_gui(): output.set_settables(0, ensem)
        else: output.set_target_settables(0, ensem)
        output.targeted = output.get_target_labels()
    else: output.targeted = relevant

class writer(lfu.mobject):

    def __init__(self, parent = None, filenames = [], 
            label = 'another output writer',
            visible_attributes = ['label','filenames']):

        self.filenames = filenames
        #lfu.mobject.__init__(self, label = label, 
        lfu.mobject.__init__(self, 
                visible_attributes = visible_attributes, 
                parent = parent)
        self.axes_manager = plot_axes_manager(parent = self)
        self._children_ = [self.axes_manager]

    def __call__(self, *args): pass
    def set_uninheritable_settables(self, *args, **kwargs):
        self.visible_attributes = ['label', 'base_class', 'filenames']

    def set_settables(self, *args, **kwargs):
        self.handle_widget_inheritance(*args, **kwargs)
        '''#this has never actually been implemeneted
        classes = [template._class for template 
                    in self.valid_base_classes]
        tags = [template._tag for template 
                in self.valid_base_classes]
        self.widg_templates.append(
            lgm.interface_template_gui(
                widget_mason = recaster, 
                widget_layout = 'vert', 
                key = ['_class'], 
                instance = [[self.base_class, self]], 
                widget = ['rad'], 
                hide_none = [True], 
                box_label = 'Write Method', 
                initial = [self.base_class._tag], 
                possibles = [tags], 
                possible_objs = [classes], 
                sizer_position = (1, 0)))
        '''
        super(writer, self).set_settables(*args, from_sub = True)

class writer_vtk(writer):

    def __init__(self,parent = None,filenames = [],label = 'vtk output writer'):
        self.filenames = filenames
        writer.__init__(self,label = label,parent = parent)

    def __call__(self, system, vtk_filename, specifics):
        lvtk.write_unstructured(system, vtk_filename, specifics)

    def set_uninheritable_settables(self, *args, **kwargs):
        self.visible_attributes = ['label','filenames']

class writer_pkl(writer):

    def __init__(self,parent = None,filenames = [],label = 'pkl output writer'):
        self.filenames = filenames
        writer.__init__(self,label = label,parent = parent)

    def __call__(self, *args):
        system = args[0]
        filename = args[1]
        try:
            lf.save_pkl_object(system, filename)

        except IOError:
            print 'failed to output .pkl file'

    def set_uninheritable_settables(self, *args, **kwargs):
        self.visible_attributes = ['label','filenames']

class writer_txt(writer):

    def __init__(self,parent = None,filenames = [],label = 'csv output writer'):
        self.filenames = filenames
        writer.__init__(self,label = label,parent = parent)

    def __call__(self, *args):
        system = args[0]
        filename = args[1]
        specifics = args[2]
        ltxt.write_csv(system, filename, specifics)

    def set_uninheritable_settables(self, *args, **kwargs):
        self.visible_attributes = ['label','filenames']

class plot_axes_manager(lfu.mobject):

    _children_ = []

    def grab_info_from_output_plan_parent(self):
        try: self.x_title = self.parent.parent.parent.x_title
        except: self.x_title = 'x-title'
        try: self.y_title = self.parent.parent.parent.y_title
        except: self.y_title = 'y-title'
        try: self.title = self.parent.parent.parent.title
        except: self.title = 'title'

    def use_line_plot(self):
        if self.parent.parent.parent.use_line_plot:
            return True
        else: return False

    def use_color_plot(self):
        if self.parent.parent.parent.use_color_plot:
            return True
        else: return False

    def use_bar_plot(self):
        if self.parent.parent.parent.use_bar_plot:
            return True
        else: return False

    def use_voxel_plot(self):
        if self.parent.parent.parent.use_voxel_plot:
            return True
        else: return False

    def set_settables(self, *args, **kwargs):
        self.handle_widget_inheritance(*args, **kwargs)
        super(plot_axes_manager, self).set_settables(
                            *args, from_sub = True)

class writer_plt(writer):

    def __init__(self,parent = None,filenames = [],label = 'plt output writer'):
        self.plt_window = None
        self.filenames = filenames
        writer.__init__(self,label = label,parent = parent)

    def get_plt_window(self):
        plot_types = []
        if self.axes_manager.use_color_plot():
            plot_types.append('color')
        if self.axes_manager.use_color_plot():
            plot_types.append('surface')
        if self.axes_manager.use_line_plot():
            plot_types.append('lines')
        if self.axes_manager.use_bar_plot():
            plot_types.append('bars')
        if self.axes_manager.use_voxel_plot():
            plot_types.append('voxels')
        self.axes_manager.grab_info_from_output_plan_parent()
        if lfu.using_gui():
            titl = self.parent.parent.label
            if titl == 'mobj__': titl = self.parent.label
            if hasattr(lfu.gui_pack, 'lqg'): glib = lfu.gui_pack.lqg
            elif hasattr(lfu.gui_pack, 'plot_window'): glib = lfu.gui_pack
            else: print 'serious gui problem...'; return
            qapp = lgb.QtGui.QApplication
            if qapp.instance() is None:
                app = qapp(sys.argv)
                app.setStyle(lgb.create_style('plastique'))
            cplot_interp_def = lset.get_setting('cplot_interpolation')
            self.plt_window = glib.plot_window(
                title = titl, plot_types = plot_types, 
                    cplot_interpolation = cplot_interp_def)

    def sanitize(self, *args, **kwargs):
        self.plt_window = None
        writer.sanitize(self, *args, **kwargs)

    def __call__(self, data_container, plt_filename, specifics):
        self.plotter(data_container, plt_filename, specifics)

    def plotter(self, data_container, plt_filename, specifics):
        if self.plt_window is None:
            print 'no plot window to post data to'
            print '\ttargets:', specifics
        else:
            self.plt_window.set_plot_info(
                data_container, plt_filename, 
                specifics, title = self.axes_manager.title, 
                x_ax_title = self.axes_manager.x_title, 
                y_ax_title = self.axes_manager.y_title)

    def set_uninheritable_settables(self, *args, **kwargs):
        self.visible_attributes = ['label', 'base_class', 'filenames']

qapp_started_flag = False
class output_plan(lfu.plan):

    #any mobj which owns this mobj needs to have .capture_targets
    def __init__(self,name = 'an output plan',use_plan = True, 
            visible_attributes = [
                'label', 'use_plan', 'output_vtk', 
                'output_pkl', 'output_txt', 'output_plt', 
                'save_directory', 'save_filename', 
                'filenames', 'directories', 'targeted'], 
            parent = None):
        self.writers = [    writer_vtk(parent = self), 
                            writer_pkl(parent = self), 
                            writer_txt(parent = self), 
                            writer_plt(parent = self)   ]
        self.flat_data = True
        #if label is not 'another output plan': one_of_a_kind = True
        self.targeted = []  #lists of strings to list of scalars
        self.outputs = [[], [], [], []] #strings pointing to targeted scalars
        #self.save_directory = save_directory
        self.save_directory = lfu.get_output_path()
        self.save_filename = ''
        self.filenames = {'vtk filename': '', 'pkl filename': '', 
                'txt filename': '', 'plt filename': ''}
        self.directories = {'vtk directory': '', 'pkl directory': '', 
                'txt directory': '', 'plt directory': ''}
        op_vtk = lset.get_setting('output_vtk')
        op_pkl = lset.get_setting('output_pkl')
        op_txt = lset.get_setting('output_txt')
        op_plt = lset.get_setting('output_plt')
        if not op_vtk is None: self.output_vtk = op_vtk
        else: self.output_vtk = False
        if not op_pkl is None: self.output_pkl = op_pkl
        else: self.output_pkl = False
        if not op_txt is None: self.output_txt = op_txt
        else: self.output_txt = False
        if not op_plt is None: self.output_plt = op_plt
        else: self.output_plt = False
        self.default_targets_vtk = True
        self.default_targets_pkl = True
        self.default_targets_txt = True
        self.default_targets_plt = True
        self.default_paths_vtk = True
        self.default_paths_pkl = True
        self.default_paths_txt = True
        self.default_paths_plt = True
        lfu.plan.__init__(self,name = name,use_plan = True,parent = parent,
            children = self.writers,visible_attributes = visible_attributes)

    def to_string(self):
        #0 : C:\Users\bartl_000\Desktop\Work\output : ensemble_output : none : all
        if self.label.startswith('Simulation'): numb = '0'
        else:
            procs = lfu.grab_mobj_names(
                self.parent.parent.post_processes)
            numb = str(procs.index(self.parent.label) + 1)

        plot_types = [item for item, out_item in 
            zip(['vtk', 'pkl', 'txt', 'plt'], 
            [self.output_vtk, self.output_pkl, 
            self.output_txt, self.output_plt]) if out_item]
        if not plot_types: plots = 'none'
        else: plots = ', '.join(plot_types)
        targs = self.get_target_labels()
        if not self.targeted: targs = 'none'
        elif self.targeted == targs: targs = 'all'
        else: targs = ', '.join(self.targeted)
        return '\t' + ' : '.join([numb, self.save_directory, 
                        self.save_filename, plots, targs])

    def must_output(self, *args, **kwargs):
        return True in [self.output_vtk, self.output_pkl, 
                        self.output_txt, self.output_plt]

    def update_filenames(self, *args, **kwargs):
        self.save_filename = increment_filename(self.save_filename)
        files = self.filenames
        for key in files.keys():
                files[key] = increment_filename(files[key])

    def find_proper_paths(self):
        propers = {}
        output_type_id = ['vtk', 'pkl', 'txt', 'plt']
        output_type_bool = [self.default_paths_vtk, 
                            self.default_paths_pkl, 
                            self.default_paths_txt, 
                            self.default_paths_plt]
        for _id, _bool in zip(output_type_id, output_type_bool):
            if _bool:
                propers[_id] = os.path.join(self.save_directory, 
                                self.save_filename + '.' + _id)

            else:
                propers[_id] = os.path.join(
                            self.directories[_id + ' directory'],
                            self.filenames[_id + ' filename'], '.' + _id)

        for _id, prop in propers.items():
            if not os.path.exists(prop):
                fil = prop.split(os.path.sep)[-1]
                #prope = os.getcwd()
                prope = lfu.get_output_path()
                self.save_directory = prope
                propers[_id] = os.path.join(prope, fil)
                for key in self.directories.keys():
                    if key.startswith(_id):self.directories[key] = prope
                for key in self.filenames.keys():
                    if key.startswith(_id):self.filenames[key] = fil

        return propers

    def find_proper_targets(self):
        propers = []
        output_type_bool = [self.default_targets_vtk, 
                            self.default_targets_pkl, 
                            self.default_targets_txt, 
                            self.default_targets_plt]
        for dex, _bool in enumerate(output_type_bool):
            if _bool: propers.append(self.targeted)
            else: propers.append(self.outputs[dex])
        return propers

    def enact_plan(self, *args):
        system = args[0]
        if hasattr(system, 'override_targets'):
            if system.override_targets:
                proper_targets = [system.override_targets]*4
            else: proper_targets = self.find_proper_targets()
        else: proper_targets = self.find_proper_targets()
        if not hasattr(system, 'plt_callbacks'):
            system.plt_callbacks = {}
        to_be_outted = []
        if not self.flat_data:  #if the list of data objects is not flat (system.data is the list)
            #self.to_be_outted has a 3rd element pointing to system within non-flat pool
            #system will be an object with attribute .data but .data is a non-flat list!
            #put each data list into a flat list of objects with flat lists for data attributes

            #targs = self.get_target_labels()
            for traj in system.data:
                #pdb.set_trace()
                #traj = lfu.flatten(traj)
                data_container = lfu.data_container(data = traj, 
                    plt_callbacks = system.plt_callbacks)
                try: self.update_filenames()
                except TypeError: print 'terror'
                proper_paths = self.find_proper_paths()
                if self.output_vtk:
                    to_be_outted.append((proper_paths['vtk'], 
                            0, data_container))

                if self.output_pkl:
                    to_be_outted.append((proper_paths['pkl'], 
                            1, data_container))

                if self.output_txt:
                    to_be_outted.append((proper_paths['txt'], 
                            2, data_container))

                if self.output_plt:
                    to_be_outted.append((proper_paths['plt'], 
                            3, data_container))

            using_plt = 3 in [out[1] for out in to_be_outted]
            if using_plt and lfu.using_gui():
            #if using_plt:
                #if not lfu.using_gui():
                #   import modular_core.gui.libqtgui_bricks as lgb
                #   app = lgb.QtGui.QApplication(sys.argv)
                self.writers[3].get_plt_window()
                plt_flag = True
            else: plt_flag = False

            [self.writers[out[1]](out[2], out[0], 
                proper_targets[out[1]]) for out in to_be_outted]

            if plt_flag: self.writers[3].plt_window()

        else:
            try: self.update_filenames()
            except TypeError: print 'terror'
            proper_paths = self.find_proper_paths()
            #if the list of data objects is flat (system.data is the list)
            #self.to_be_outted has only 2 elements since data is already flat
            if self.output_vtk:
                to_be_outted.append((proper_paths['vtk'], 0))

            if self.output_pkl:
                to_be_outted.append((proper_paths['pkl'], 1))

            if self.output_txt:
                to_be_outted.append((proper_paths['txt'], 2))

            if self.output_plt:
                to_be_outted.append((proper_paths['plt'], 3))

            using_plt = 3 in [out[1] for out in to_be_outted]
            if using_plt and lfu.using_gui():
                self.writers[3].get_plt_window()
                plt_flag = True
            else: plt_flag = False

            [self.writers[out[1]](system, out[0], 
                proper_targets[out[1]]) for out in to_be_outted]

            if plt_flag: self.writers[3].plt_window()

        self.plt_flag = plt_flag
        '''
        if plt_flag:
            app = lgb.QtGui.QApplication.instance()
            global qapp_started_flag
            if not qapp_started_flag:
                app.exec_()
                qapp_started_flag = True
        '''

    def verify_nonempty_save_directory(self):
        if not self.save_directory:
            #if not self.parent is None:
            self.save_directory = os.getcwd()

    def verify_nonempty_save_filename(self):
        if self.save_filename == None or self.save_filename == '':
            self.save_filename = '_'.join(
                ['_'.join(self.parent.label.split()), 'output'])

    def get_target_labels(self, *args, **kwargs):
        if args: ensem = args[0]
        if self.parent is None:
            target_labels = ensem.run_params['plot_targets']
        else:
            try:
                self.parent.run_params['plot_targets'] = lfu.uniqfy(
                        self.parent.run_params['plot_targets'])#hack
                target_labels = self.parent.run_params['plot_targets']
            except AttributeError:
                target_labels = self.parent.capture_targets
        return target_labels

    def set_target_settables(self, *args, **kwargs):
        target_labels = self.get_target_labels(*args, **kwargs)
        self.targeted = lfu.intersect_lists(self.targeted, target_labels)
        for dex in range(len(self.outputs)):
            self.outputs[dex] = lfu.intersect_lists(
                    self.outputs[dex], target_labels)

    def set_settables(self, *args, **kwargs):
        self.set_target_settables(*args, **kwargs)
        target_labels = self.get_target_labels(*args, **kwargs)
        #self.targeted = lfu.intersect_lists(self.targeted, target_labels)
        #for dex in range(len(self.outputs)):
        #   self.outputs[dex] = lfu.intersect_lists(
        #           self.outputs[dex], target_labels)
        self.handle_widget_inheritance(*args, **kwargs)
        self.writers[0].set_settables(*args, **kwargs)
        self.writers[1].set_settables(*args, **kwargs)
        self.writers[2].set_settables(*args, **kwargs)
        self.writers[3].set_settables(*args, **kwargs)
        plt_page_template = lgm.interface_template_gui(
                panel_label = 'plt Writer Options', 
                panel_scrollable = True, 
                panel_position = (1, 3), 
                widgets = ['panel', 'check_set', 'check_set', 
                        'directory_name_box', 'file_name_box'], 
                box_labels = [None, 'plt Plot Targets', '', 
                    'plt Save Directory', 'plt Base Filename'], 
                append_instead = [None, True, False, None, None], 
                provide_master = [None, True, False, None, None], 
                instances = [None, [self], [self, self], 
                    [self.directories], [self.filenames]], 
                rewidget = [None, [True], [True], [True], [True]], 
                keys = [None, ['outputs'], 
                #there is likely a bug with the 'outputs' check set ->
                #   it likely screws up nesting
                #   doesnt handle inst_is_list = True correctly
                    ['default_targets_plt', 'default_paths_plt'], 
                            ['pkl directory'], ['pkl filename']], 
                instance_is_dict = [None, None, None, 
                        (True, self), (True, self)], 
                initials = [None, None, None, 
                    [self.directories['plt directory']], 
                    [self.filenames['plt filename']]], 
                labels = [None, target_labels, 
                        ['Use Default Plot Targets', 
                        'Use Default Output Path'], 
                        ['Choose Directory'], ['Choose Filename']], 
                templates = [self.writers[3].widg_templates, 
                                None, None, None, None])
        txt_page_template = lgm.interface_template_gui(
                panel_label = 'csv Writer Options', 
                panel_scrollable = True, 
                widgets = ['panel', 'check_set', 'check_set', 
                        'directory_name_box', 'file_name_box'], 
                box_labels = [None, 'csv Plot Targets', '', 
                    'csv Save Directory', 'csv Base Filename'], 
                append_instead = [None, True, False, None, None], 
                provide_master = [None, True, False, None, None], 
                instances = [None, [self], [self, self], 
                    [self.directories], [self.filenames]], 
                rewidget = [None, [True], [True], [True], [True]], 
                keys = [None, ['outputs'], 
                #there is likely a bug with the 'outputs' check set ->
                #   it likely screws up nesting
                #   doesnt handle inst_is_list = True correctly
                    ['default_targets_txt', 'default_paths_txt'], 
                            ['txt directory'], ['txt filename']], 
                instance_is_dict = [None, None, None, 
                        (True, self), (True, self)], 
                initials = [None, None, None, 
                    [self.directories['txt directory']], 
                    [self.filenames['txt filename']]], 
                labels = [None, target_labels, 
                        ['Use Default Plot Targets', 
                        'Use Default Output Path'], 
                        ['Choose Directory'], ['Choose Filename']], 
                templates = [self.writers[2].widg_templates, 
                                None, None, None, None])
        pkl_page_template = lgm.interface_template_gui(
                panel_label = 'pkl Writer Options', 
                panel_scrollable = True, 
                widgets = ['panel', 'check_set', 'check_set', 
                        'directory_name_box', 'file_name_box'], 
                box_labels = [None, 'pkl Plot Targets', '', 
                    'pkl Save Directory', 'pkl Base Filename'], 
                append_instead = [None, True, False, None, None], 
                provide_master = [None, True, False, None, None], 
                instances = [None, [self], [self, self], 
                    [self.directories], [self.filenames]], 
                rewidget = [None, [True], [True], [True], [True]], 
                keys = [None, ['outputs'], 
                    ['default_targets_pkl', 'default_paths_pkl'], 
                            ['pkl directory'], ['pkl filename']], 
                instance_is_dict = [None, None, None, 
                        (True, self), (True, self)], 
                instance_is_list = [None, (True, 1), None, None, None], 
                initials = [None, None, None, 
                    [self.directories['pkl directory']], 
                    [self.filenames['pkl filename']]], 
                labels = [None, target_labels, 
                        ['Use Default Plot Targets', 
                        'Use Default Output Path'], 
                        ['Choose Directory'], ['Choose Filename']], 
                templates = [self.writers[1].widg_templates, 
                            None, None, None, None])
        vtk_page_template = lgm.interface_template_gui(
                panel_label = 'vtk Writer Options', 
                panel_scrollable = True, 
                widgets = ['panel', 'check_set', 'check_set', 
                        'directory_name_box', 'file_name_box'], 
                box_labels = [None, 'vtk Plot Targets', '', 
                    'vtk Save Directory', 'vtk Base Filename'], 
                append_instead = [None, True, False, None, None], 
                provide_master = [None, True, False, None, None], 
                instances = [None, [self], [self, self], 
                    [self.directories], [self.filenames]], 
                rewidget = [None, [True], [True], [True], [True]], 
                keys = [None, ['outputs'], 
                    ['default_targets_vtk', 'default_paths_vtk'], 
                            ['vtk directory'], ['vtk filename']], 
                instance_is_dict = [None, None, None, 
                        (True, self), (True, self)], 
                initials = [None, None, None, 
                    [self.directories['vtk directory']], 
                    [self.filenames['vtk filename']]], 
                labels = [None, target_labels, 
                        ['Use Default Plot Targets', 
                        'Use Default Output Path'], 
                        ['Choose Directory'], ['Choose Filename']], 
                templates = [self.writers[0].widg_templates, 
                                None, None, None, None])
        writers_splitter_template = lgm.interface_template_gui(
                widgets = ['splitter'], 
                verbosities = [2], 
                orientations = [['horizontal']], 
                templates = [[plt_page_template, txt_page_template, 
                            pkl_page_template, vtk_page_template]])
        top_templates = []
        top_templates.append(
            lgm.interface_template_gui(
                panel_position = (0, 3), 
                widgets = ['check_set'], 
                append_instead = [True], 
                provide_master = [True], 
                instances = [[self]],
                keys = [['targeted']],
                labels = [target_labels], 
                box_labels = ['Default Plot Targets']))
        self.verify_nonempty_save_filename()
        top_templates.append(
            lgm.interface_template_gui(
                panel_position = (0, 1), 
                widgets = ['file_name_box'], 
                keys = [['save_filename']], 
                instances = [[self]], 
                initials = [[self.save_filename, 
                    'Possible Outputs (*.vtk *.csv)']], 
                labels = [['Choose Filename']], 
                box_labels = ['Default Base Filename']))
        self.verify_nonempty_save_directory()
        top_templates.append(
            lgm.interface_template_gui(
                panel_position = (0, 0), 
                widgets = ['directory_name_box'], 
                keys = [['save_directory']], 
                instances = [[self]], 
                initials = [[self.save_directory, None, 
                    os.path.join(os.getcwd(), 'resources')]], 
                labels = [['Choose Directory']], 
                box_labels = ['Default Save Directory']))
        top_templates.append(
            lgm.interface_template_gui(
                panel_position = (0, 2), 
                widgets = ['check_set'], 
                append_instead = [False], 
                instances = [[self]*4],
                keys = [['output_vtk', 'output_pkl', 
                        'output_txt', 'output_plt']],
                labels = [['Output .vtk files', 'Output .pkl files', 
                        'Output .csv files', 'Output .plt files']], 
                box_labels = ['Output Types']))
        top_template = lgm.interface_template_gui(
                widgets = ['panel'], 
                scrollable = [True], 
                templates = [top_templates])
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['splitter'], 
                orientations = [['vertical']], 
                templates = [[top_template, 
                    writers_splitter_template]]))
        lfu.mobject.set_settables(
                self, *args, from_sub = True)

def increment_filename(fi):
    if fi == '': return fi
    else:
        fi = fi.split('.')
        if len(fi) == 1:    #non-indexed filename without extension
            return '.'.join(fi + ['0'])

        else:
            try:    #no file extension but an index to increment
                dex = int(fi[-1])
                dex = str(dex + 1)
                return '.'.join(fi[:-1] + [dex])

            except ValueError:  #assume a file extension
                try:
                    dex = int(fi[-2])
                    dex = str(dex + 1)
                    return '.'.join(fi[:-1] + [dex] + fi[-1:])

                except ValueError:  #had file extension but no index
                    return '.'.join(fi[:-1] + ['0'] + fi[-1:])
                except TypeError: pdb.set_trace()




