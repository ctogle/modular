 #!python
import modular_core.fundamental as lfu
import modular_core.gui.libqtgui as lqg
lgm = lqg.lgm
lgd = lqg.lgd
lgb = lqg.lgb

import modular_core.mclient as mcli

import pdb,os,sys

class mclientapp(lqg.application):
    gear_icon = lfu.get_resource_path('gear.png')
    _content_ = [mcli.mclient()]

    def __init__(self, *args, **kwargs):
        lqg.application.__init__(self, *args, **kwargs)
        x, y = lfu.convert_pixel_space(784, 256)
        x_size, y_size = lfu.convert_pixel_space(512, 512)
        self._standards_ = {
            'title' : 'Modular Data Client', 
            'geometry' : (x, y, x_size, y_size), 
            'window_icon' : self.gear_icon}
        lqg._window_.apply_standards(self._standards_)
        lqg.application.setStyle(lgb.create_style('plastique'))

def initialize():lqg.initialize_app(mclientapp)

if __name__ == '__main__':initialize()









 

