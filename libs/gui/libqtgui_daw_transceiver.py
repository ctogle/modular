import libs.modular_core.libfundamental as lfu
import libs.gui.libqtgui as lqg
lgm = lqg.lgm
lgd = lqg.lgd
lgb = lqg.lgb
import libs.daw_transceiver.libs.libdawcommander as ldco

import sys

class application_daw_trans(lqg.application):
	_content_ = [ldco.daw_commander()]

_application_ = application_daw_trans
_application_locked_ = True

#def initialize_gui(params):
#	app = application_daw_trans(params, sys.argv)
#	sys.exit(app.exec_())






