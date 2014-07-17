import libs.modular_core.libfundamental as lfu
import libs.modular_core.libpostprocess as lpp
import libs.modular_core.libgeometry as lgeo



import pdb

class post_process_plate_reader(lpp.post_process):
	def postproc(self, *args, **kwargs):
		#pool should invariably be a list of 
		#	lists of data objects for each trajectory
		#a method must always be provided by a superclass
		#	a pool and a p_space are optional, default
		#	is to use the ensemble
		self.determine_regime(args[0])
		pool = []
		sources = self.get_source_reference(1, *args, **kwargs)
		from_always = self.parent.parent._children_[0].data
		for inp in self.input_regime:
			inpmobj = lfu.grab_mobj_by_name(inp, from_always)
			lfu.zip_list(pool, [inpmobj.data.data])
		for src in sources: lfu.zip_list(pool, src.data)
		if self.regime == 'all trajectories':
			self.handle_all_trajectories(kwargs['method'], pool)
		elif self.regime == 'manual grouping':
			self.handle_manual_grouping(kwargs['method'], pool)
		elif self.regime == 'per trajectory':
			self.handle_per_trajectory(kwargs['method'], pool)

class post_process_layout_reduction(post_process_plate_reader):
	def __init__(self, *args, **kwargs):
		if not 'base_class' in kwargs.keys():
			kwargs['base_class'] = lfu.interface_template_class(
									object, 'layout reduction')
		if not 'label' in kwargs.keys():
			kwargs['label'] = 'layout reduction'
		if not 'valid_regimes' in kwargs.keys():
			kwargs['valid_regimes'] = ['all trajectories']
		if not 'regime' in kwargs.keys():
			kwargs['regime'] = 'all trajectories'

		#self.impose_default('function_of', None, **kwargs)
		post_process_plate_reader.__init__(self, *args, **kwargs)

	def postproc(self, *args, **kwargs):
		kwargs['method'] = self.reduction
		post_process_plate_reader.postproc(self, *args, **kwargs)

	def reduction(self, *args, **kwargs):
		pdb.set_trace()


		data = lgeo.scalars_from_labels(self.target_list)
		for dex, mean_of in enumerate(self.means_of):
			bin_axes, mean_axes = select_for_binning(
				args[0], self.function_of, mean_of)
			bins, vals = bin_scalars(bin_axes, mean_axes, 
							self.bin_count, self.ordered)
			means = [mean(val) for val in vals]
			data[dex + 1].scalars = means

		data[0].scalars = bins
		return data

	def set_settables(self, *args, **kwargs):
		self.valid_regimes = ['all trajectories']
		self.valid_inputs = self.get_valid_inputs(*args, **kwargs)
		self.handle_widget_inheritance(*args, from_sub = False)
		post_process_plate_reader.set_settables(
					self, *args, from_sub = True)

valid_postproc_base_classes = [
	lfu.interface_template_class(
		post_process_layout_reduction, 
					'layout reduction')]
lpp.valid_postproc_base_classes = valid_postproc_base_classes

if __name__ == 'libs.plate_reader_analyzer.libplatereaderprocesses':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__':
	print 'this is a library!'





