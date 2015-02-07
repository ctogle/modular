import modular_core.libfundamental as lfu
import modular_core.gui.libqtgui as lqg
lgm = lqg.lgm
lgd = lqg.lgd
lgb = lqg.lgb
import modular_core.libensemble as lensem

import os
import sys

import pdb

class modular(lqg.application):
    gear_icon = lfu.get_resource_path('gear.png')

    def __init__(self, *args, **kwargs):
        self._content_ = [lensem.ensemble_manager()]
        lqg.application.__init__(self,*args,**kwargs)
        x, y = lfu.convert_pixel_space(784, 256)
        x_size, y_size = lfu.convert_pixel_space(512, 512)
        self._standards_ = {
            'title' : 'Modular', 
            'geometry' : (x, y, x_size, y_size), 
            'window_icon' : self.gear_icon}
        lqg._window_.apply_standards(self._standards_)
        #lqg.application.setStyle(lgb.create_style('windows'))
        #lqg.application.setStyle(lgb.create_style('xp'))
        #lqg.application.setStyle(lgb.create_style('vista'))
        #lqg.application.setStyle(lgb.create_style('motif'))
        #lqg.application.setStyle(lgb.create_style('cde'))
        lqg.application.setStyle(lgb.create_style('plastique'))
        #lqg.application.setStyle(lgb.create_style('clean'))

def initialize():lqg.initialize_app(modular)





