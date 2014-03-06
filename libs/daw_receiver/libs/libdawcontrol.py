import libs.modular_core.libfundamental as lfu
import libs.modular_core.libudp as ludp
import libs.daw_receiver.libs.libphidgmotor as lpm
import libs.modular_core.libsettings as lset

import types
import time
import os

import pdb

class motor_manager(lfu.modular_object_qt):
	label = 'motor manager'
	motors = []
	allow_manual = True
	range_scheme = 'normalized'
	slider_resolution = 5000
	max_offset = lpm.max_offset

	log_path = os.path.join(os.getcwd(), 'libs', 
		'daw_receiver', 'libs', 'receiver.log')

	udp_receiver = ludp.receiver()
	udp_transceiver = ludp.transceiver()
	_children_ = [udp_receiver, udp_transceiver]

	def __init__(self, *args, **kwargs):
		self.settings_manager = lset.settings_manager(
			parent = self, filename = 'daw_rec_settings.txt')
		self.settings = self.settings_manager.read_settings()

		self.udp_receiver.parent = self
		self.udp_transceiver.parent = self

		self.jog_distance = '0.1'
		self.jog_units	  = 'normalized'

		self.max_position = self.max_offset
		self.min_position = -self.max_offset

		self.left_state = lpm.motor_state_left(parent = self)
		self.right_state = lpm.motor_state_right(parent = self)
		self.zero_state = lpm.motor_state_zero(parent = self)
		self.follow_state = lpm.motor_state_follow(parent = self)
		self.on_attach_motor()
		self.log_event(' : '.join(['receiver initiated', 
							str(time.ctime()), '\n\n']))
		self.current_position = self.motors[-1].get_position()
		lfu.modular_object_qt.__init__(self, *args, **kwargs)

	def follow_slider(self):
		if self.allow_manual:
			print 'slider will follow!', self.current_position
			self.log_event(' '.join(['slider will follow:', 
								str(self.current_position)]))
			self.follow_state.set_in_state(self.current_position)

	def update_current_position_slider(self):
		self.current_position = self.motors[-1].get_position()
		self.current_position_slider[0].children()[1].setValue(
										self.current_position)

	def log_event(self, event_string):
		with open(self.log_path, 'a') as log:
			final = ' : '.join([event_string, 
					str(time.ctime()), '\n'])
			log.write(final)

	def on_go_left(self):
		if self.allow_manual:
			print 'manually told to go left!'
			self.log_event('manually told to go left!')
			self.left_state.set_in_state()
			self.update_current_position_slider()

	def on_go_right(self):
		if self.allow_manual:
			print 'manually told to go right!'
			self.log_event('manually told to go right!')
			self.right_state.set_in_state()
			self.update_current_position_slider()

	def on_go_zero(self):
		if self.allow_manual:
			print 'manually told to go to zero!'
			self.log_event('manually told to go to zero!')
			self.zero_state.set_in_state()
			self.update_current_position_slider()

	def jog_plus(self):
		if self.allow_manual:
			print 'manually told to go jog right!'
			self.log_event('manually told to go jog right!')
			self.follow_state.set_in_state(
				self.follow_state.motor.get_position() +\
				self.convert_jog_distance(self.jog_distance))
			self.update_current_position_slider()

	def jog_minus(self):
		if self.allow_manual:
			print 'manually told to go jog left!'
			self.log_event('manually told to go jog left!')
			self.follow_state.set_in_state(
				self.follow_state.motor.get_position() -\
				self.convert_jog_distance(self.jog_distance))
			self.update_current_position_slider()

	def convert_jog_distance(self, distance):
		if self.jog_units == 'normalized':
			conv_factor = int(abs(int(self.max_position) -\
							int(self.min_position)) / 2.0)

		elif self.jog_units == 'differential':
			conv_factor = (55000.0 / 31.5)

		elif self.jog_units == 'absolute': conv_factor = 1.0
		return int(conv_factor * float(distance))

	def interpret_udp(self, data):
		print 'udp instructed to ', data
		self.log_event(''.join(['udp instructed to ', data]))
		if data == 'left': self.on_go_left()
		elif data == 'right': self.on_go_right()
		elif data == 'zero': self.on_go_zero()
		else:
			try:
				data = int(data)
				self.follow_state.set_in_state(data)

			except:
				print 'received a non-generic motor position target'
				self.log_event(
					'received a non-generic motor position target')

	#def on_start_listening(self, *args, **kwargs):
	#	self.udp_receiver.listen(*args, **kwargs)

	#def on_start_speaking(self, *args, **kwargs):
	#	self.udp_transceiver.speak(*args, **kwargs)

	def on_attach_motor(self):
		self.motors.append(lpm.motor(dex = len(self.motors)))
		self.left_state.motor = self.motors[-1]
		self.right_state.motor = self.motors[-1]
		self.zero_state.motor = self.motors[-1]
		self.follow_state.motor = self.motors[-1]

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		jog_widg_template = lgm.interface_template_gui(
				layout = 'grid', 
				widg_positions = [(0, 0), (1, 0), (0, 1), (2, 0)], 
				widg_spans = [(1, 1), (1, 1), (3, 3), (1, 1)], 
				grid_spacing = 10, 
				widgets = ['button_set', 'radio', 'text'], 
				minimum_sizes = [None, [(125, 125)], None], 
				maximum_sizes = [None, None, [(100, 75)]], 
				alignments = [None, None, ['center']], 
				initials = [[None], [self.jog_units], 
							[self.jog_distance]], 
				instances = [None, [self], [self]], 
				keys = [None, ['jog_units'], ['jog_distance']], 
				labels = [['Jog +', 'Jog -'], 
					['absolute', 'normalized', 'differential'], None], 
				bindings = [[self.jog_plus, 
					self.jog_minus], None, None], 
				box_labels = [None, 'Jog Units', 'Jog Distance'])
		extremum_control_widg_template = lgm.interface_template_gui(
				widgets = ['slider_advanced', 
					'slider_advanced', 'slider_advanced'], 
				layout = 'horizontal', 
				initials = [[self.max_position], 
					[self.min_position], [self.current_position]], 
				orientations = [['vertical'], 
					['vertical'], ['vertical']], 
				minimum_values = [[-self.max_offset], 
					[-self.max_offset], [-self.max_offset]], 
				maximum_values = [[self.max_offset], 
					[self.max_offset], [self.max_offset]], 
				positions = [['left'], ['right'], ['both']], 
				intervals = [[self.slider_resolution], 
							[self.slider_resolution], 
							[self.slider_resolution]], 
				instances = [[self], [self], [self]], 
				keys = [['max_position'], 
					['min_position'], ['current_position']], 
				handles = [None, None, (self, 
					'current_position_slider')], 
				bind_events = [[None, None], [None, None], 
					[['released', 'changed'], ['enter']]], 
				bindings = [[None, None], [None, None], 
					[[self.follow_slider], [self.follow_slider]]], 
				box_labels = ['Max Position (+1.0)', 
					'Min Position (-1.0)', 'Current Position'])
		split_widg_template_left = lgm.interface_template_gui(
				widgets = ['splitter'], 
				orientations = [['vertical']], 
				templates = [[jog_widg_template, 
					extremum_control_widg_template]])
		split_widg_template_right_top = lgm.interface_template_gui(
				widgets = ['button_set'], 
				labels = [['Attach Motor']], 
					#'Start Receiver', 
					#'Talk to Yourself', 'Talk To The Aether']], 
				bindings = [[self.on_attach_motor]])#, 
							#self.on_start_listening, 
							#[self.on_start_listening, 
							#self.on_start_speaking], 
							#self.on_start_speaking]], 
				#bind_events = [['clicked']], 'clicked', ['clicked', 
				#							'clicked'], 'clicked']])
		split_widg_template_right_mid = self.udp_receiver.widg_templates
		split_widg_template_right_bottom = lgm.interface_template_gui(
				widgets = ['button_set'], 
				labels = [['Go Left', 'Go Right', 'Go to Zero']], 
				bindings = [[self.on_go_left, self.on_go_right, 
							self.on_go_zero]])
		split_widg_template_right = lgm.interface_template_gui(
				widgets = ['splitter'], 
				orientations = [['vertical']], 
				templates = [[split_widg_template_right_top, 
						split_widg_template_right_bottom] +\
							split_widg_template_right_mid])
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['splitter'], 
				orientations = [['horizontal']], 
				templates = [[split_widg_template_left, 
						split_widg_template_right]]))
		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)

if __name__ == 'libs.daw_receiver.libs.libdawcontrol':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'












