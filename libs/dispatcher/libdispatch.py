import libs.modular_core.libfundamental as lfu
import libs.modular_core.libudp as ludp

import types

import pdb

class ensemble_dispatcher(lfu.modular_object_qt):
	udp_receiver = ludp.receiver()
	udp_transceiver = ludp.transceiver()

	def __init__(self, *args, **kwargs):
		self.udp_receiver.parent = self
		self.udp_transceiver.parent = self
		lfu.modular_object_qt.__init__(self, *args, **kwargs)

	def interpret_udp(self, data):
		print 'instructed to ', data
		if data == 'left': self.on_go_left()
		elif data == 'right': self.on_go_right()
		elif data == 'zero': self.on_go_zero()
		else:
			try:
				data = int(data)
				self.follow_state.set_in_state(data)
			except: print 'received a non-generic motor position target'

	def on_start_listening(self, *args, **kwargs):
		self.udp_receiver.listen(*args, **kwargs)

	def on_start_speaking(self, *args, **kwargs):
		self.udp_transceiver.speak(*args, **kwargs)

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['button_set', 'button_set'], 
				labels = [['Attach Motor', 'Start Receiver', 
							'Talk to Yourself', 'Talk To The Aether'], 
							['Go Left', 'Go Right', 'Go to Zero']], 
				bindings = [[self.on_attach_motor, 
							self.on_start_listening, 
							[self.on_start_listening, 
							self.on_start_speaking], 
							self.on_start_speaking], 
							[self.on_go_left, self.on_go_right, 
							self.on_go_zero]], 
				bind_events = [['clicked', 'clicked', 
							['clicked', 'clicked'], 
							'clicked'], None]))
		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)

if __name__ == 'libs.dispatcher.libdispatch':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'















