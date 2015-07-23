 #!python
import modular_core.fundamental as lfu

import modular_core.io.output as lo
#import modular_core.io.libfiler as lf
import modular_core.io.mpkl as lpkl
import modular_core.settings as lset
import modular_core.data.batch_target as dba

import modular_core.gui.libqtgui as lqg
lgm = lqg.lgm
lgd = lqg.lgd
lgb = lqg.lgb

import pdb,os,sys

class pkl_handler(lfu.mobject):
    def __init__(self,*args,**kwargs):
        self.settings_manager = lset.settings_manager(
            parent = self,filename = 'plot_pkls_settings.txt')
        self.settings = self.settings_manager.read_settings()
        self._default('capture_targets',[],**kwargs)
        self._default('pkl_files_directory',os.getcwd(),**kwargs)
        lfu.mobject.__init__(self,*args,**kwargs)

    def load_data(self):
        pkl_files = [p for p in os.listdir(
            self.pkl_files_directory) if p.endswith('.pkl')]
        fronts = lfu.uniqfy([p[:p.find('.')] for p in pkl_files])
        outputs = []
        data_ = []
        for outp in fronts:
            newoutp = lo.output_plan(name = outp,parent = self,flat_data = False)
            newoutp.writers[3].use = True
            outputs.append(newoutp)
            data_.append(dba.batch_node())
            self.capture_targets = []
            #relev = [p for p in pkl_files if p[:p.find('.')] == outp]
            relev = sorted([p for p in pkl_files if p[:p.find('.')] == outp])
            for fi in relev:
                fipath = os.path.join(self.pkl_files_directory, fi)
                dat = lpkl.load_pkl_object(fipath)
                ptargets = [d.name for d in dat.data]
                data_[-1]._add_child(dba.batch_node(data = dat.data))
                self.capture_targets.extend(ptargets)
            targs = lfu.uniqfy(self.capture_targets)
            outputs[-1].targeted = targs
            outputs[-1].save_filename = outp
            self.capture_targets = targs
            outputs[-1]._target_settables()
        [outp(lfu.data_container(data = da)) for outp,da in zip(outputs,data_)]

    def _widget(self,*args,**kwargs):
        window = args[0]
        self._sanitize(*args,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['directory_name_box'], 
                layout = 'horizontal', 
                keys = [['pkl_files_directory']], 
                instances = [[self]], 
                initials = [[self.pkl_files_directory,None,os.getcwd()]],
                labels = [['Choose Directory With .pkl Data']], 
                box_labels = ['Data Directory']))
        self.widg_templates[-1] +=\
            lgm.interface_template_gui(
                widgets = ['button_set'], 
                bindings = [[self.load_data]], 
                labels = [['Load .pkl Data']])
        lfu.mobject._widget(self,*args,from_sub = True)

class pkl_plotter(lqg.application):
    gear_icon = lfu.get_resource_path('gear.png')
    _content_ = [pkl_handler()]

    def __init__(self, *args, **kwargs):
        lqg.application.__init__(self, *args, **kwargs)
        x, y = lfu.convert_pixel_space(784, 256)
        x_size, y_size = lfu.convert_pixel_space(512, 512)
        self._standards_ = {
            'title' : 'Pkl Plotter', 
            'geometry' : (x, y, x_size, y_size), 
            'window_icon' : self.gear_icon}
        lqg._window_.apply_standards(self._standards_)
        lqg.application.setStyle(lgb.create_style('plastique'))

def initialize():lqg.initialize_app(pkl_plotter)

if __name__ == '__main__':initialize()









 
