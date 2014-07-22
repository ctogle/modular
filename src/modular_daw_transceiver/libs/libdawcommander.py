import libs.modular_core.libfundamental as lfu
import libs.modular_core.libudp as ludp
import libs.daw_transceiver.libs.libsorter as lso
import libs.daw_transceiver.libs.libsignaler as lsg
import libs.modular_core.libsettings as lset

import os, time

import pdb

class daw_commander(lfu.modular_object_qt):
	label = 'daw commander'
	script_sorter = lso.sorter_script()
	daw_signaler = lsg.signaler()

	current_tab_index = 0

	def __init__(self, *args, **kwargs):
		self.settings_manager = lset.settings_manager(
			parent = self, filename = 'daw_trans_settings.txt')
		self.settings = self.settings_manager.read_settings()
		def_ip = lset.get_setting('default_IP')
		self.udp_receiver = ludp.receiver(
			parent = self, default_IP = def_ip)
		self.udp_transceiver = ludp.transceiver(
			parent = self, default_IP = def_ip)
		self.script_sorter.parent = self
		self.daw_signaler.parent = self
		lfu.modular_object_qt.__init__(self, *args, **kwargs)
		self._children_ = [self.script_sorter, 
			self.daw_signaler, self.udp_transceiver, self.udp_receiver]

	def on_test_udp_receiver_transceiver(self, *args, **kwargs):
		self.udp_receiver.listen(*args, **kwargs)
		self.udp_transceiver.speak(*args, **kwargs)

	def interpret_udp(self, *args, **kwargs):
		msgs = ['UDP Test Passed...', 
			'dawcommander doesn\'t interpret udp messages:'+args[0]]
		if args[0].startswith('hello world!'): print msgs[0]
		else: print msgs[1] 

	def on_speak_go_left(self):
		self.udp_transceiver.speak(message = 'left')

	def on_speak_go_right(self):
		self.udp_transceiver.speak(message = 'right')

	def on_speak_go_zero(self):
		self.udp_transceiver.speak(message = 'zero')

	def on_speak_message(self, message):
		self.udp_transceiver.speak(message = message)

	def make_tab_book_pages(self, *args, **kwargs):
		window = args[0]
		udp_temps = []
		script_temps = []
		signal_temps = []
		udp_temps.append(
			lgm.interface_template_gui(
				widgets = ['button_set'], 
				labels = [['Test UDP System']], 
				bindings = [[self.on_test_udp_receiver_transceiver]]))
		udp_temps.append(
			lgm.interface_template_gui(
				widgets = ['panel'], 
				templates = [self.udp_receiver.widg_templates]))
		udp_temps.append(
			lgm.interface_template_gui(
				widgets = ['panel'], 
				templates = [self.udp_transceiver.widg_templates]))
		script_temps.append(
			lgm.interface_template_gui(
				widgets = ['panel'], 
				templates = [self.script_sorter.widg_templates]))
		signal_temps.append(
			lgm.interface_template_gui(
				widgets = ['button_set'], 
				layouts = ['horizontal'], 
				layout = 'vertical', 
				labels = [['Say Left', 'Say Right', 'Say Zero']], 
				bindings = [[self.on_speak_go_left, 
					self.on_speak_go_right, self.on_speak_go_zero]]))
		signal_temps[-1] +=\
			lgm.interface_template_gui(
				widgets = ['panel'], 
				templates = [self.daw_signaler.widg_templates])
		pages = [('Signaling', signal_temps), 
				('Script Sorting', script_temps), 
				('UDP', udp_temps)]
		return pages

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		wrench_icon_path = os.path.join(
			os.getcwd(), 'resources', 'wrench_icon.png')
		refresh_icon_path = os.path.join(
			os.getcwd(), 'resources', 'refresh.png')
		center_icon_path = os.path.join(
			os.getcwd(), 'resources', 'center.png')
		wrench_icon = lgb.create_icon(wrench_icon_path)
		refresh_icon = lgb.create_icon(refresh_icon_path)
		center_icon = lgb.create_icon(center_icon_path)
		settings_ = lgb.create_action(parent = window, label = 'Settings', 
					bindings = lgb.create_reset_widgets_wrapper(
					window, self.change_settings), icon = wrench_icon, 
					shortcut = 'Ctrl+Shift+S', statustip = 'Settings')
		self.refresh_ = lgb.create_reset_widgets_function(window)
		update_gui_ = lgb.create_action(parent = window, 
			label = 'Refresh GUI', icon = refresh_icon, 
			shortcut = 'Ctrl+G', bindings = self.refresh_, 
			statustip = 'Refresh the GUI (Ctrl+G)')
		center_ = lgb.create_action(parent = window, label = 'Center', 
					bindings = [window.on_resize, window.on_center], 
							icon = center_icon, shortcut = 'Ctrl+C', 
										statustip = 'Center Window')
		self.menu_templates.append(
			lgm.interface_template_gui(
				menu_labels = ['&File', '&File', '&File'], 
				menu_actions = [settings_, center_, update_gui_]))
		self.tool_templates.append(
			lgm.interface_template_gui(
				tool_labels = ['&Tools', '&Tools', '&Tools'], 
				tool_actions = [settings_, center_, update_gui_]))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['tab_book'], 
				verbosities = [0], 
				pages = [self.make_tab_book_pages(*args, **kwargs)], 
				initials = [[self.current_tab_index]], 
				handles = [(self, 'tab_ref')], 
				instances = [[self]], 
				keys = [['current_tab_index']]))
		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)

if __name__ == 'libs.daw_transceiver.libs.libdawcommander':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'




