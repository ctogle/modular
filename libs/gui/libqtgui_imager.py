import libs.modular_core.libfundamental as lfu
import libs.gui.libqtgui as lqg
lgm = lqg.lgm
lgd = lqg.lgd
lgb = lqg.lgb
import libs.imager.libimager as lprog

import os

class application_imager(lqg.application):
	_content_ = [lprog.imager()]
	gear_icon = os.path.join(os.getcwd(), 'resources', 'gear.png')

	def __init__(self, *args, **kwargs):
		lqg.application.__init__(self, *args, **kwargs)
		x, y = lfu.convert_pixel_space(1024, 256)
		x_size, y_size = lfu.convert_pixel_space(512, 512)
		self._standards_ = {
			'title' : 'Imager', 
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

_application_ = application_imager
_application_locked_ = False

