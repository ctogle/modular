import libs.modular_core.libfundamental as lfu
import libs.modular_core.libsettings as lset

import pdb

if __name__ == 'libs.gui_template_sandbox.libgui_template_sandbox':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'

class gui_template_sandbox(lfu.modular_object_qt):

	def __init__(self, *args, **kwargs):

		self.slide_value = 0
		self.domain_units = 'minutes'
		self.range_scheme = 'normalized'

		self.settings_manager = lset.settings_manager(parent = self, 
					filename = 'gui_template_sandbox_settings.txt')
		self.settings = self.settings_manager.read_settings()
		lfu.modular_object_qt.__init__(self, *args, **kwargs)

	def _get_slider_template_(self, *args, **kwargs):
		return lgm.interface_template_gui(
			layout = 'horizontal', 
			widgets = ['slider'], 
			initials = [[self.slide_value]], 
			orientations = [['horizontal']], 
			minimum_values = [[-10]], 
			maximum_values = [[10]], 
			positions = [['above']], 
			intervals = [[5]], 
			instances = [[self]], 
			keys = [['slide_value']], 
			box_labels = ['Slider Example'])

	def _get_radio_template_(self, *args, **kwargs):
		return lgm.interface_template_gui(
			layout = 'vertical', 
			widgets = ['radio', 'radio'], 
			labels = [['seconds', 'minutes', 'hours', 'milliseconds'], 
					['absolute', 'normalized', 'differential']], 
			initials = [[self.domain_units], [self.range_scheme]], 
			instances = [[self], [self]], 
			keys = [['domain_units'], ['range_scheme']], 
			box_labels = ['Delay Units', 'Position Units'])

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)

		template1 = self._get_slider_template_()
		template2 = self._get_radio_template_()
		self.widg_templates.append(template1 + template2 + template1)
		self.widg_templates.append(template2 + template1 + template2)

		lfu.modular_object_qt.set_settables(
			self, *args, from_sub = True)









