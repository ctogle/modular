import modular_core.libfundamental as lfu
import modular_core.libgeometry as lgeo
import modular_core.libsettings as lset

import modular_core.io.libfiler as lf
import modular_core.io.libvtkoutput as lvtk
import modular_core.io.libtxtoutput as ltxt

#from cStringIO import StringIO
import pdb,os,sys,time
import matplotlib.pyplot as plt
import numpy as np

if __name__ == 'modular_core.io.liboutput':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'liboutput of modular_core'

###############################################################################
### a writer handles one format of output for an output plan
###  it operates orthongonally to other writers - each format can have
###  different plot_targets / file paths
###############################################################################

class writer_abstract(lfu.mobject):

    #ABSTRACT
    def __init__(self,*args,**kwargs):
        self._default('name','output writer',**kwargs)
        self._default('default_targets',True,**kwargs)
        self._default('default_paths',True,**kwargs)
        self._default('save_directory',lfu.get_output_path(),**kwargs)
        self._default('save_filename','',**kwargs)
        self._default('targeted',[],**kwargs)
        self._default('tag','abstract',**kwargs)
        lfu.mobject.__init__(self,*args,**kwargs)

    def __call__(self,*args):
        self._write(*args)

    def _write(self,*args):pass

    def _widget(self,*args,**kwargs):
        tag = self.tag
        target_labels = self.parent._target_labels(*args,**kwargs)
        self._sanitize(*args,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                panel_label = tag + ' Writer Options', 
                panel_scrollable = True, 
                panel_position = (1, 3), 
                widgets = ['check_set'],
                box_labels = [tag + ' Plot Targets'],
                append_instead = [True],
                provide_master = [True],
                instances = [[self]],
                keys = [['targeted']], 
                labels = [target_labels]))
        self.widg_templates[-1] +=\
            lgm.interface_template_gui(
                widgets = ['check_set'],
                box_labels = [tag + ' Save Directory'], 
                append_instead = [False], 
                provide_master = [False], 
                instances = [[self]],
                keys = [['default_targets']],
                labels = [['Use Default Plot Targets']])
        self.widg_templates[-1] +=\
            lgm.interface_template_gui(
                widgets = ['directory_name_box'],
                box_labels = [tag + ' Save Directory'], 
                instances = [[self]],
                keys = [['save_directory']],
                initials = [[self.save_directory]],
                labels = [['Choose Directory']])
        self.widg_templates[-1] +=\
            lgm.interface_template_gui(
                widgets = ['file_name_box'],
                box_labels = [tag + ' Base Filename'], 
                instances = [[self]],
                keys = [['save_filename']],
                initials = [[self.save_filename]],
                labels = [['Choose Filename']])
        lfu.mobject._widget(self,*args,from_sub = True)

class writer_vtk(writer_abstract):

    def __init__(self,*args,**kwargs):
        self._default('name','vtk writer',**kwargs)
        op_vtk = lset.get_setting('output_vtk')
        self._default('use',op_vtk,**kwargs)
        self._default('tag','vtk',**kwargs)
        writer_abstract.__init__(self,*args,**kwargs)

    def _write(self,*args):
        lvtk.write_unstructured(*args)

class writer_pkl(writer_abstract):

    def __init__(self,*args,**kwargs):
        self._default('name','pkl writer',**kwargs)
        op_pkl = lset.get_setting('output_pkl')
        self._default('use',op_pkl,**kwargs)
        self._default('tag','pkl',**kwargs)
        writer_abstract.__init__(self,*args,**kwargs)

    def _write(self,*args):
        lf.save_pkl_object(*args[:2])

class writer_txt(writer_abstract):

    def __init__(self,*args,**kwargs):
        self._default('name','txt writer',**kwargs)
        op_txt = lset.get_setting('output_txt')
        self._default('use',op_txt,**kwargs)
        self._default('tag','txt',**kwargs)
        writer_abstract.__init__(self,*args,**kwargs)

    def _write(self,*args):
        ltxt.write_csv(*args)

qapp_started_flag = False
class writer_plt(writer_abstract):

    def __init__(self,*args,**kwargs):
        self._default('name','plt writer',**kwargs)
        op_plt = lset.get_setting('output_plt')
        self._default('use',op_plt,**kwargs)
        self._default('tag','plt',**kwargs)
        self._plt_window = None
        writer_abstract.__init__(self,*args,**kwargs)

    def _check_qt_application(self):
        qapp = lgb.QtGui.QApplication
        if qapp.instance() is None:
            app = qapp(sys.argv)
            app.setStyle(lgb.create_style('plastique'))

    def _window_title(self):
        titl = self.parent.parent.name
        if titl == 'mobj__':titl = self.parent.name
        return titl

    def _guilib(self):
        if hasattr(lfu.gui_pack,'lqg'):glib = lfu.gui_pack.lqg
        elif hasattr(lfu.gui_pack,'plot_window'):glib = lfu.gui_pack
        return glib

    def _get_plt_window(self):
        plot_types = ['color','surface','lines','bars','voxels']
        if lfu.using_gui and not self._plt_window:
            title = self._window_title()
            cplot_interp_def = lset.get_setting('cplot_interpolation')
            self._check_qt_application()
            glib = self._guilib()
            self._plt_window = glib.plot_window(
                title = title,plot_types = plot_types,
                cplot_interpolation = cplot_interp_def)

    def _write(self,*args):
        if self._plt_window is None:self._get_plt_window()
        self._plt_window.set_plot_info(*args)

###############################################################################
###############################################################################

###############################################################################
### an output_plan handles all formats of output for a set of data
###  the simulation, each post process, and each fitting routine get
###  their own output_plans which operate orthogonally
###############################################################################

class output_plan(lfu.plan):

    #any mobj which owns this mobj needs to have .capture_targets
    def __init__(self,*args,**kwargs):
        self._default('name','output plan',**kwargs)
        self._default('use_plan',True,**kwargs)
        self._default('flat_data',True,**kwargs)
        self._default('save_directory',lfu.get_output_path(),**kwargs)
        self._default('save_filename','',**kwargs)
        self._default('targeted',[],**kwargs)
        lfu.plan.__init__(self,*args,**kwargs)
        self.writers = [
            writer_vtk(parent = self),writer_pkl(parent = self), 
            writer_txt(parent = self),writer_plt(parent = self)]
        self.children = self.writers

    def _string(self):
        if self.label.startswith('Simulation'): numb = '0'
        else:
            # this needs to include fit routines too?
            procs = lfu.grab_mobj_names(self.parent.parent.post_processes)
            numb = str(procs.index(self.parent.label) + 1)

        plot_types = [item for item,out in zip(
            ['vtk','pkl','txt','plt'],
            [w.use for w in self.writers]) if out]
        if not plot_types:plots = 'none'
        else: plots = ', '.join(plot_types)

        if not self.targeted:targs = 'none'
        elif self.targeted == self._target_labels():targs = 'all'
        else:targs = ', '.join(self.targeted)

        return '\t' + ' : '.join([numb, self.save_directory, 
                        self.save_filename, plots, targs])

    # return whether or not any writers are enabled
    def _must_output(self):
        must = True in [w.use for w in self.writers]
        return must

    # increment all filenames to maintain uniqueness
    def _update_filenames(self,*args,**kwargs):
        self.save_filename = increment_filename(self.save_filename)
        for w in self.writers:
            w.save_filename = increment_filename(w.save_filename)

    # return the proper set of paths for each writer
    #  each writer can inherit the default paths or set its own
    def _proper_paths(self):
        propers = {}
        output_types = ['vtk','pkl','txt','plt']
        for typ,w in zip(output_types,self.writers):
            if w.default_paths:
                dfil = self.save_filename + '.' + typ
                ddir = self.save_directory
            else:
                ddir = w.save_directory
                dfil = w.save_filename
            dpath = os.path.join(ddir,dfil)
            propers[typ] = dpath
        self._validate_paths(propers)
        return propers

    # if any paths are not valid, reset to cwd
    def _validate_paths(self,paths):
        for typ,prop in paths.items():
            fil = prop.split(os.path.sep)[-1]
            for w in self.writers:w.save_filename = fil
            if not os.path.exists(prop):
                prope = os.getcwd()
                self.save_directory = prope
                for w in self.writers:w.save_directory = prope
            paths[typ] = os.path.join(prope,fil)

    # return the proper set of targets for each writer
    #  each writer can inherit the default targets or set its own
    def _proper_targets(self,data = None):
        if hasattr(data,'override_targets') and data.override_targets:
            propers = [data.override_targets]*4
        else:
            propers = []
            output_type_bool = [w.default_targets for w in self.writers]
            for dex,val in enumerate(output_type_bool):
                if val:propers.append(self.targeted)
                else:propers.append(self.writers[dex].targeted)
        return propers
    
    # return the set of valid targets based on owner mobject
    def _target_labels(self,*args,**kwargs):
        target_labels = lfu.uniqfy(self.parent.capture_targets)
        return target_labels

    # make chosen targets consistent with allowed targets
    def _target_settables(self,*args,**kwargs):
        target_labels = self._target_labels(*args,**kwargs)
        self.targeted = lfu.intersect_lists(self.targeted,target_labels)
        for dex in range(len(self.writers)):
            self.writers[dex].targeted = lfu.intersect_lists(
                    self.writers[dex].targeted,target_labels)

    # set the default save_directory if needed
    def _default_save_directory(self):
        if not self.save_directory:
            self.save_directory = lfu.get_output_path()

    # set the default save_filename if needed
    def _default_save_filename(self):
        if not self.save_filename:
            self.save_filename = self.parent.name + '.output'

    def _output_nonflat(self,data):
        types = ['vtk','pkl','txt','plt']
        proper_paths = self._proper_paths()
        proper_targets = self._proper_targets(data)
        pltflag = False
        for dchild in data.data.children:
            traj = dchild.data
            data_container = lfu.data_container(
                data = traj,plt_callbacks = data.plt_callbacks)
            self._update_filenames()
            for dx in range(len(self.writers)):
                if self.writers[dx].use:
                    plt = types[dx] == 'plt' and lfu.using_gui
                    if plt:
                        self.writers[dx]._get_plt_window()
                        pltflag = True
                    self.writers[dx](data_container,
                        proper_paths[types[dx]],proper_targets[dx])
        if pltflag:self.writers[dx]._plt_window()

    def _output_flat(self,data):
        types = ['vtk','pkl','txt','plt']
        proper_paths = self._proper_paths()
        proper_targets = self._proper_targets(data)
        self._update_filenames()
        for dx in range(len(self.writers)):
            if self.writers[dx].use:
                plt = types[dx] == 'plt' and lfu.using_gui
                if plt:self.writers[dx]._get_plt_window()
                self.writers[dx](data,
                    proper_paths[types[dx]],proper_targets[dx])
                if plt:self.writers[dx]._plt_window()

    # perform the output of all enabled writers
    def _enact(self,*args,**kwargs):
        data = args[0]
        if not hasattr(data,'plt_callbacks'):data.plt_callbacks = {}

        if self.flat_data:self._output_flat(data)
        else:self._output_nonflat(data)

    def _widget(self,*args,**kwargs):
        self._target_settables(*args,**kwargs)
        target_labels = self._target_labels(*args,**kwargs)
        self._sanitize(*args,**kwargs)
        [w._widget(*args,**kwargs) for w in self.writers]
        writer_templates = []
        [writer_templates.extend(w.widg_templates) for w in self.writers]
        writers_splitter_template = lgm.interface_template_gui(
            widgets = ['splitter'], 
            verbosities = [2], 
            orientations = [['horizontal']], 
            templates = [writer_templates])
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
        self._default_save_filename()
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
        self._default_save_directory()
        top_templates.append(
            lgm.interface_template_gui(
                panel_position = (0, 0), 
                widgets = ['directory_name_box'], 
                keys = [['save_directory']], 
                instances = [[self]], 
                initials = [[self.save_directory,None, 
                    os.path.join(os.getcwd(),'resources')]], 
                labels = [['Choose Directory']], 
                box_labels = ['Default Save Directory']))
        top_templates.append(
            lgm.interface_template_gui(
                panel_position = (0, 2), 
                widgets = ['check_set'], 
                append_instead = [False], 
                instances = [self.writers],
                keys = [['use']*4],
                labels = [[
                    'Output .vtk files','Output .pkl files', 
                    'Output .csv files','Output .plt files']], 
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
        lfu.mobject._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

# parse the output_plan specified on one line of an mcfg
#  the output_plan instance is assumed to exist
# owner index : path : filename : output types : output targets
def parse_output_plan_line(*args):
    line,ensem,parser,procs,routs,targs = args
    spl = [l.strip() for l in line.split(' : ')]

    odex = int(spl[0])
    if odex == 0: output = ensem.output_plan
    elif odex <= len(procs): output = procs[odex - 1].output
    else: output = routs[odex - len(procs) - 1].output

    output.save_directory = spl[1]
    output.save_filename = spl[2]

    ptypes = spl[3]
    possible_ptypes = [w.tag for w in output.writers]
    for dx in range(len(output.writers)):
        if possible_ptypes[dx] in ptypes:output.writers[dx].use = True
        else:output.writers[dx].use = False

    relevant = [l.strip() for l in spl[4].split(',')]
    if 'all' in relevant:
        if lfu.using_gui: output._widget(0,ensem)
        else: output._target_settables(0,ensem)
        output.targeted = output._target_labels()
    else: output.targeted = relevant

# CLEAN THIS FUNCTION UP!!!
# CLEAN THIS FUNCTION UP!!!
# CLEAN THIS FUNCTION UP!!!
# CLEAN THIS FUNCTION UP!!!
# CLEAN THIS FUNCTION UP!!!
# return modified filename to maintain uniqueness
def increment_filename(fi):
    print 'increment filename',fi
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

###############################################################################
###############################################################################









