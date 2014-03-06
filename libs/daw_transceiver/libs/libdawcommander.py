import libs.modular_core.libfundamental as lfu
import libs.modular_core.libudp as ludp
import libs.daw_transceiver.libs.libsorter as lso
import libs.daw_transceiver.libs.libsignaler as lsg
import libs.modular_core.libsettings as lset

import pdb

class daw_commander(lfu.modular_object_qt):
	label = 'daw commander'
	udp_receiver = ludp.receiver()
	udp_transceiver = ludp.transceiver()
	script_sorter = lso.sorter_script()
	daw_signaler = lsg.signaler()
	_children_ = [script_sorter, daw_signaler, udp_transceiver]
	#_children_ = [script_sorter, udp_receiver, udp_transceiver]

	def __init__(self, *args, **kwargs):
		self.settings_manager = lset.settings_manager(
			parent = self, filename = 'daw_trans_settings.txt')
		self.settings = self.settings_manager.read_settings()
		self.udp_receiver.parent = self
		self.udp_transceiver.parent = self
		self.script_sorter.parent = self
		self.daw_signaler.parent = self
		lfu.modular_object_qt.__init__(self, *args, **kwargs)

	def on_test_udp_receiver_transceiver(self, *args, **kwargs):
		self.udp_receiver.listen(*args, **kwargs)
		self.udp_transceiver.speak(*args, **kwargs)

	def on_speak_go_left(self):
		self.udp_transceiver.speak(message = 'left')

	def on_speak_go_right(self):
		self.udp_transceiver.speak(message = 'right')

	def on_speak_go_zero(self):
		self.udp_transceiver.speak(message = 'zero')

	def on_speak_message(self, message):
		self.udp_transceiver.speak(message = message)

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['button_set'], 
				labels = [['Test UDP System']], 
				bindings = [[self.on_test_udp_receiver_transceiver]]))
		#self.widg_templates.append(
		#	lgm.interface_template_gui(
		#		widgets = ['panel'], 
		#		templates = [self.udp_receiver.widg_templates]))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['panel'], 
				templates = [self.udp_transceiver.widg_templates]))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['panel'], 
				templates = [self.script_sorter.widg_templates]))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['panel'], 
				templates = [self.daw_signaler.widg_templates]))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['button_set'], 
				labels = [['Say Left', 'Say Right', 'Say Zero']], 
				bindings = [[self.on_speak_go_left, 
					self.on_speak_go_right, self.on_speak_go_zero]]))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['button_set'], 
				labels = [['Update GUI']], 
				bindings = [[lgb.create_reset_widgets_function(window)]]))
		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)

if __name__ == 'libs.daw_transceiver.libs.libdawcommander':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'




