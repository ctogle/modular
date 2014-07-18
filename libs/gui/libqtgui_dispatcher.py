import libs.modular_core.libfundamental as lfu
import libs.gui.libqtgui as lqg
lgm = lqg.lgm
lgd = lqg.lgd
lgb = lqg.lgb
import libs.dispatcher.libdispatch as ldp

class application_dispatch(lqg.application):
	_content_ = [ldp.ensemble_dispatcher()]

_application_ = application_dispatch





