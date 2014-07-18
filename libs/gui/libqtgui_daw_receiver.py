import libs.modular_core.libfundamental as lfu
import libs.gui.libqtgui as lqg
lgm = lqg.lgm
lgd = lqg.lgd
lgb = lqg.lgb
import libs.daw_receiver.libs.libdawcontrol as ldc

import os
import sys

class application_daw_rec(lqg.application):
	gear_icon = os.path.join(os.getcwd(), 'resources', 'gear.png')
	_content_ = [ldc.motor_manager()]

	def __init__(self, *args, **kwargs):
		lqg.application.__init__(self, *args, **kwargs)
		lqg.application.setStyle(lgb.create_style('plastique'))
		x, y = lfu.convert_pixel_space(1024, 256)
		x_size, y_size = lfu.convert_pixel_space(512, 768)
		self._standards_ = {
			'title' : 'DAW Receiver', 
			'geometry' : (x, y, x_size, y_size), 
			'window_icon' : self.gear_icon}
		lqg._window_.apply_standards(self._standards_)

_application_ = application_daw_rec
_application_locked_ = True







