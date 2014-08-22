import modular_core.libfundamental as lfu
import modular_core.gui.libqtgui as lqg
lgm = lqg.lgm
lgd = lqg.lgd
lgb = lqg.lgb
import modular_core.libsimcomponents as lsc

import os
import sys

import pdb

class modular(lqg.application):
    #gear_icon = os.path.join(os.getcwd(), 'resources', 'gear.png')
    gear_icon = lfu.get_resource_path('gear.png')
    _content_ = [lsc.ensemble_manager()]
    lsc.manager = _content_[0]

    def __init__(self, *args, **kwargs):
        lqg.application.__init__(self, *args, **kwargs)
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

_application_ = modular
_application_locked_ = True






