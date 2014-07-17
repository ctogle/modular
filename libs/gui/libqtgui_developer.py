import libs.modular_core.libfundamental as lfu
import libs.gui.libqtgui as lqg
lgm = lqg.lgm
lgd = lqg.lgd
lgb = lqg.lgb
import libs.developer.libdeveloper as ldev

import os

class application_developer(lqg.application):
	_content_ = [ldev.modular_developer2()]
	gear_icon = os.path.join(os.getcwd(), 'resources', 'gear.png')

	def __init__(self, *args, **kwargs):
		lqg.application.__init__(self, *args, **kwargs)
		x, y = lfu.convert_pixel_space(64, 64)
		x_size, y_size = lfu.convert_pixel_space(256, 512)
		self._standards_ = {
			'title' : 'Modular Developer', 
			'geometry' : (x, y, x_size, y_size), 
			'window_icon' : self.gear_icon}
		lqg._window_.apply_standards(self._standards_)
		lqg.application.setStyle(lgb.create_style('plastique'))

_application_ = application_developer
_application_locked_ = True




