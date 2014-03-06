import libs.modular_core.libfundamental as lfu
import libs.gui.libqtgui as lqg
lgm = lqg.lgm
lgd = lqg.lgd
lgb = lqg.lgb
import libs.daw_receiver.libs.libdawcontrol as ldc

import sys

class application_daw_rec(lqg.application):
	_content_ = [ldc.motor_manager()]

	def __init__(self, *args, **kwargs):
		lqg.application.__init__(self, *args, **kwargs)
		#lqg.application.setStyle(lgb.create_style('windows'))
		#lqg.application.setStyle(lgb.create_style('xp'))
		#lqg.application.setStyle(lgb.create_style('vista'))
		#lqg.application.setStyle(lgb.create_style('motif'))
		#lqg.application.setStyle(lgb.create_style('cde'))
		lqg.application.setStyle(lgb.create_style('plastique'))
		#lqg.application.setStyle(lgb.create_style('clean'))

_application_ = application_daw_rec
_application_locked_ = True

#def initialize_gui(params):
#	app = application_daw_rec(params, sys.argv)
#	sys.exit(app.exec_())






