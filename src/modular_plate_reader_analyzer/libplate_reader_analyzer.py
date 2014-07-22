import libs.modular_core.libfundamental as lfu
import libs.modular_core.libsettings as lset
import libs.modular_core.liboutput as lo
import libs.modular_core.libgeometry as lgeo
import libs.modular_core.libpostprocess as lpp
#import libs.plate_reader_analyzer.libplatereaderprocesses as lpdap

from collections import OrderedDict
import numpy as np

import os, sys, time, traceback
import pdb



if __name__ == 'libs.plate_reader_analyzer.libplate_reader_analyzer':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'

class data_block(lfu.modular_object_qt):
	swaps = {'\xb0':' Deg '}
	def __init__(self, *args, **kwargs):
		self.raw = args[0]
		lfu.modular_object_qt.__init__(self, *args, **kwargs)
	def display_read(self):
		for key in self.read.keys():
			print '\nkey :', key
			for li in self.read[key]: print '\t' + li
	def _read_(self, *args, **kwargs):
		self.read = args[0]
		#self.display_read()
	def swap_check(self, li):
		swaps = self.swaps
		for sw in swaps.keys(): li = li.replace(sw, swaps[sw])
		return li

class header_block(data_block):
	def __init__(self, *args, **kwargs):
		blks = args[0]
		raw = blks[0].raw + blks[1].raw + blks[2].raw
		data_block.__init__(self, raw, **kwargs)
	def _read_(self):
		read = OrderedDict()
		for li in self.raw:
			ke = li[:li.find(',')].replace(':','')
			read[ke] = [li[li.find(',')+1:]]
		data_block._read_(self, read)

class procedure_block(data_block):
	def __init__(self, *args, **kwargs):
		blks = args[0]
		raw = blks[0].raw + blks[1].raw
		data_block.__init__(self, raw, **kwargs)
	def _read_(self):
		read = OrderedDict()
		relev = self.raw[1:]
		kins = []; kin_on = False
		for li_dex in range(len(relev)):
			li = self.swap_check(relev[li_dex])
			sp = [x.strip() for x in li.split(',')]
			ke = sp[0]
			if ke.startswith('End Kinetic'):
				kin_on = False
			elif kin_on: read[kin_ke].append(li.strip())
			elif li.startswith(','):
				read[read.keys()[-1]].append(li.strip())
			elif ke.startswith('Start Kinetic'):
				kins.append(li_dex); kin_on = True
				kin_ke = 'Kinetic #' + str(len(kins))
				read[kin_ke] = [','.join(sp[1:])]
			else: read[ke] = [','.join(sp[1:])]
		data_block._read_(self, read)

class layout_block(data_block):
	def __init__(self, *args, **kwargs):
		blks = args[0]
		raw = args[0].raw
		data_block.__init__(self, raw, **kwargs)

	def _read_(self):
		sps = [r.split(',') for r in self.raw[2:]]
		rows = len(sps)
		cols = len(sps[1])-1
		reduced = np.ndarray((rows, cols), dtype = object)
		for row in range(rows): reduced[row,:] = sps[row][:-1]
		read = OrderedDict()
		read['rows'] = self.raw[1].split(',')[1:]
		read['cols'] = reduced[:,0]
		read['table'] = reduced[:,1:]
		data_block._read_(self, read)

class obs_data_block(data_block):
	_modu_program_ = 'plate_reader_analyzer'
	def __init__(self, *args, **kwargs):
		self.impose_default('capture_targets',[],**kwargs)
		self.impose_default('replicate_reduced',False,**kwargs)
		blks = args[0]
		raw = blks[0].raw + blks[1].raw
		data_block.__init__(self, *(raw,), **kwargs)
		if not hasattr(self, 'label'): self.label = kwargs['label']
		self.output = lo.output_plan(
			label = self.label + ' Output', parent = self)
		self.output.flat_data = True
		self._children_ = [self.output]
		self.output.output_plt = False
	def _read_(self):
		meas = self.swap_check(self.raw[0])
		self._measurement_ = meas
		layout = self.swap_check(self.raw[1]).split(meas)
		wells = layout[1].replace(',', '',1).split(',')
		well_count = len(wells)
		self._well_key_ = wells
		conds = layout[0].split(',')
		cond_count = len(conds)
		self._cond_key_ = conds
		data_lines = self.raw[2:]
		meas_count = len(data_lines)
		_cond_data_ = np.ndarray((meas_count,cond_count),dtype=object)
		_well_data_ = np.ndarray((meas_count,well_count),dtype=object)
		for re_dex, re in enumerate(data_lines):
			sp = re.split(',')
			_cond_data_[re_dex,:] = sp[:cond_count]
			_well_data_[re_dex,:] = sp[cond_count:]
		self._cond_data_ = _cond_data_
		self._well_data_ = _well_data_
		read = OrderedDict()
		read['measurement'] = [self._measurement_]
		read['condition_key'] = self._cond_key_
		read['condition_data'] = self._cond_data_
		read['wells_key'] = self._well_key_
		read['wells_data'] = self._well_data_
		data_block._read_(self, read)
	def deep_parse(self, *args, **kwargs):
		def empty_check(unic):
			checked = [x for x in unic if not x == '']
			return checked
		def ovrflw_check(unic):
			checked =\
				['1000000.0' if x.count('OVRFLW') else x for x in unic]
			return checked
		def _all_checks_(unic):
			unic = empty_check(unic)
			checked = ovrflw_check(unic)
			return checked
		def hms_to_mins(hms):
			convs = [60.0, 1.0, 1.0/60.0]
			mins = [sum([float(pair[0])*pair[1] for pair 
				in zip(hms[x].split(':'), convs)]) 
				for x in range(len(hms))]
			return mins
		def time_filter(hms):
			hms0 = '0:00:00'
			hms = [min_ for d, min_ in 
				enumerate(hms) if not 
				min_ == hms0 or d == 0]
			mins = hms_to_mins(hms)
			return mins
		known_filters = OrderedDict()
		known_filters['Time'] = time_filter
		known_filters['_all_'] = _all_checks_
		def filter_(key, dat):
			kf = known_filters
			dat = kf['_all_'](dat)
			if key in kf.keys(): dat = kf[key](dat)
			try: return np.array(dat,dtype='f')
			except ValueError: pdb.set_trace()
		measur = self._measurement_
		weldat = self._well_data_
		welkey = self._well_key_
		condat = self._cond_data_
		conkey = self._cond_key_
		con_data = lgeo.scalars_from_labels(conkey)
		for dex, key in enumerate(conkey):
			con_data[dex].scalars = filter_(key, condat[:,dex])
		wel_data = lgeo.scalars_from_labels(welkey)
		for dex, key in enumerate(welkey):
			wel_data[dex].scalars = filter_(key, weldat[:,dex])
		all_data = con_data + wel_data
		self._unreduced_ = lfu.data_container(data = all_data)
		self._reduced_ = self.apply_reduction(self._unreduced_.data)
		self.update_replicate_reduction()
	def apply_reduction(self, unred):
		read = self.parent.parent.read['layout'].read
		flat = lfu.flatten(read['table'])
		well_cnt = len(flat)
		reduced = unred[:len(unred)-well_cnt]	#list of replicate averaged scalers
		con_offset = len(reduced)
		uniq = lfu.uniqfy(flat)
		layout = OrderedDict()
		for dex, key in enumerate(flat):
			if key in layout.keys(): layout[key].append(dex + con_offset)
			else: layout[key] = [dex + con_offset]
		new = lgeo.scalars_from_labels(layout.keys())
		for ndex, key in enumerate(layout.keys()):
			rel_dexes = layout[key]
			rel_dater = [unred[d] for d in rel_dexes]
			zi = zip(*[r.scalars for r in rel_dater])
			new[ndex].scalars = np.array([np.mean(z) for z in zi])
		reduced.extend(new)
		red = lfu.data_container(data = reduced)
		return red
	def _toggle_replication_reduced_(self):
		self.replicate_reduced = not self.replicate_reduced
		self.update_replicate_reduction(self)
	def update_replicate_reduction(self):
		if self.replicate_reduced: self.data = self._reduced_
		else: self.data = self._unreduced_
		self.capture_targets = [x.label for x in self.data.data]
		self.output.rewidget(True)
	def provide_axes_manager_input(self, 
			lp = True, cp = False, bp = False, 
			x_title = 'x-title', y_title = 'y-title', title = 'title'):
		self.use_line_plot = lp
		self.use_color_plot = cp
		self.use_bar_plot = bp
		self.x_title = x_title
		meas = self._measurement_
		self.y_title = meas
		self.title = meas
	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['check_set'], 
				labels = [['Apply Replicate Reduction']], 
				append_instead = [False], 
				instances = [[self]], 
				keys = [['replicate_reduced']], 
				callbacks = [[lgb.create_reset_widgets_wrapper(
					window, self.update_replicate_reduction)]]))
		lfu.modular_object_qt.set_settables(
			self, *args, from_sub = True)

class well_data(object):
	def __init__(self, *args, **kwargs):
		pass
	def doubling(self, lo, hi, vals, t):
		#vals = np.log(dat.scalars)
		#lodelts = [abs(x-lo) for x in dat.scalars]
		#pdb.set_trace()
		lodelts = [abs(x-lo) for x in vals]
		deldex = lodelts.index(min(lodelts))
		t1 = t.scalars[deldex]
		#hidelts = [abs(x-hi) for x in dat.scalars]
		hidelts = [abs(x-hi) for x in vals]
		deldex = hidelts.index(min(hidelts))
		t2 = t.scalars[deldex]
		dbling = t2 - t1
		return dbling
	def growth(self, dbl, dex):
		try: return np.log(2.0)/dbl
		except FloatingPointError: return None
	def get_single_well_data(self):
		# THIS FUNCTION WILL JUST RETURN THE SELECTED WELLS PLOT DATA
		od_dex = self.get_selected_well()
		time_ = self.data.data[0]
		od = self.data.data[od_dex]
		dbl = self._doubling_times_[od_dex]
		gro = self._growth_rates_[od_dex]
		lo, hi = self._thresholds_[od_dex]
		#od.scalars = od.scalars
		y_low = lgeo.scalars('__skip__', [lo]*2, color = 'black')
		#	[self.OD_threshold_low]*2, color = 'black')
		y_high = lgeo.scalars('__skip__', [hi]*2, color = 'black')
		#	[self.OD_threshold_high]*2, color = 'black')
		x_stack = lgeo.scalars('__skip__', 
			[time_.scalars.min(), time_.scalars.max()])
		# CALCULATE THE DOUBLING TIME AND ADD VERTICAL LINES FOR THE POINTS USED
		#  MAKE ALL THESE FLAT LINES DASHED OR SOMETHING
		#pdb.set_trace()
		data = lfu.data_container(
			domains = [time_, x_stack, x_stack], 
			codomains = [od, y_low, y_high], 
			doubling = dbl, growth_rate = gro, 
						thresholds = (lo, hi))
		return data

class optical_density_block(obs_data_block):
	def __init__(self, *args, **kwargs):
		self.impose_default('OD_threshold_low', 0.05)
		self.impose_default('OD_threshold_high', 0.7)
		#lo = 0.05
		#hi = 0.7
		self.impose_default('_well_select_', None)
		obs_data_block.__init__(self, *args, **kwargs)
	def doubling(self, lo, hi, vals, t):
		#vals = np.log(dat.scalars)
		#lodelts = [abs(x-lo) for x in dat.scalars]
		#pdb.set_trace()
		lodelts = [abs(x-lo) for x in vals]
		deldex = lodelts.index(min(lodelts))
		t1 = t.scalars[deldex]
		#hidelts = [abs(x-hi) for x in dat.scalars]
		hidelts = [abs(x-hi) for x in vals]
		deldex = hidelts.index(min(hidelts))
		t2 = t.scalars[deldex]
		dbling = t2 - t1
		return dbling
	def growth(self, dbl, dex):
		try: return np.log(2.0)/dbl
		except FloatingPointError: return None
	def deep_parse(self):
		obs_data_block.deep_parse(self)
		_unred_ = self._unreduced_.data
		ti = _unred_[0]
		low = self.OD_threshold_low
		high = self.OD_threshold_high
		cond_cnt = len(self._cond_key_)
		nones = [None]*cond_cnt
		self._thresholds_ = nones +\
			[(low,high)]*len(_unred_[cond_cnt:])
		self._doubling_times_ = nones +\
			[self.doubling(low,high,np.log(unred.scalars),ti) for 
									unred in _unred_[cond_cnt:]]
		self._growth_rates_ = nones +\
			[self.growth(dbl, dex) for dex, dbl in 
				enumerate(self._doubling_times_[cond_cnt:])]
	def get_selected_well(self):
		try: od_dex = self._well_key_.index(self._well_select_)
		except ValueError:
			od_dex = 0
			self._well_select_ = self._well_key_[od_dex]
		cond_cnt = len(self._cond_key_)
		return od_dex + cond_cnt
	def get_single_well_data(self):
		# THIS FUNCTION WILL JUST RETURN THE SELECTED WELLS PLOT DATA
		od_dex = self.get_selected_well()
		time_ = self.data.data[0]
		od = self.data.data[od_dex]
		dbl = self._doubling_times_[od_dex]
		gro = self._growth_rates_[od_dex]
		lo, hi = self._thresholds_[od_dex]
		#od.scalars = od.scalars
		y_low = lgeo.scalars('__skip__', [lo]*2, color = 'black')
		#	[self.OD_threshold_low]*2, color = 'black')
		y_high = lgeo.scalars('__skip__', [hi]*2, color = 'black')
		#	[self.OD_threshold_high]*2, color = 'black')
		x_stack = lgeo.scalars('__skip__', 
			[time_.scalars.min(), time_.scalars.max()])
		# CALCULATE THE DOUBLING TIME AND ADD VERTICAL LINES FOR THE POINTS USED
		#  MAKE ALL THESE FLAT LINES DASHED OR SOMETHING
		#pdb.set_trace()
		data = lfu.data_container(
			domains = [time_, x_stack, x_stack], 
			codomains = [od, y_low, y_high], 
			doubling = dbl, growth_rate = gro, 
						thresholds = (lo, hi))
		return data
	def recalculate_doubling(self):
		od_dex = self.get_selected_well()
		lo, hi = self._thresholds_[od_dex]
		dat = self.data.data[od_dex]
		t = self.data.data[0]
		self._doubling_times_[od_dex] = self.doubling(lo, hi, dat, t)
		self._growth_rates_[od_dex] =\
			self.growth(self._doubling_times_[od_dex])
		self.rewidget(True)
	def thresh_spin_callback(self, typ):
		def thresh_spin_callback_lo(val, inst, key):
			old = thresh[key][1]
			altered = (val, old)
			return altered
		def thresh_spin_callback_hi(val, inst, key):
			old = thresh[key][0]
			altered = (old, val)
			return altered
		thresh = self._thresholds_
		if typ == 'lo': return thresh_spin_callback_lo
		elif typ == 'hi': return thresh_spin_callback_hi
	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		# WE NEED A PANEL FOR THE SELECTED WELLS DATA - PLOT, THRESHOLD VALUES, CALCULATED DOUBLING TIME
		# RESELECTING THE WELL REFRESHES THE PAGE
		# NEED A BUTTON TO RECALCULATE THAT WELLS DOUBLING TIME USING THAT WELLS THRESHOLDS
		# BUT THE INITIAL DOUBLING TIMES AND THRESHOLDS MUST BE SET AT DEEP_PARSE TIME
		
		data = self.get_single_well_data()
		od_dex = self.get_selected_well()
		lo, hi = self._thresholds_[od_dex]

		od_thresh = lgm.interface_template_gui(
				widgets = ['spin'], 
				layout = 'horizontal', 
				doubles = [[True]], 
				initials = [[lo]], 
				minimum_values = [[0.0]],
				maximum_values = [[10.0]],
				single_steps = [[0.01]], 
				callbacks = [[self.thresh_spin_callback('lo')]], 
				instances = [[self._thresholds_]], 
				keys = [[od_dex]], 
				parents = [[self]], 
				box_labels = ['Low Threshold'])
		od_thresh += lgm.interface_template_gui(
				widgets = ['spin'], 
				doubles = [[True]], 
				initials = [[hi]], 
				minimum_values = [[0.0]],
				maximum_values = [[10.0]],
				single_steps = [[0.01]], 
				callbacks = [[self.thresh_spin_callback('hi')]], 
				instances = [[self._thresholds_]], 
				keys = [[od_dex]], 
				parents = [[self]], 
				box_labels = ['High Threshold'])

		dbl = data.doubling
		gro = data.growth_rate
		dbl_time = lgm.interface_template_gui(
				widgets = ['text', 'text'], 
				layout = 'vertical', 
				read_only = [True, True], 
				initials = [[dbl], [gro]], 
				alignments = [['center'], ['center']], 
				box_labels = ['Doubling Time', 'Growth Rate'])
		dbl_time += lgm.interface_template_gui(
				widgets = ['button_set'], 
				bindings = [[lgb.create_reset_widgets_wrapper(
						window, self.recalculate_doubling)]], 
				labels = [['Recalculate This\nDoubling Time']])

		dbl_meas_template = lgm.interface_template_gui(
				widgets = ['panel'], 
				layout = 'horizontal', 
				templates = [[dbl_time, od_thresh]], 
				box_labels = ['Doubling Time Measurement'])
		dbl_meas_template += lgm.interface_template_gui(
				widgets = ['plot'], 
				datas = [data])
		self.widg_templates.append(dbl_meas_template)

		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['selector'], 
				instances = [[self]],
				keys = [['_well_select_']], 
				initials = [[self._well_select_]], 
				refresh = [[True]], 
				window = [[window]], 
				labels = [self._well_key_], 
				box_labels = ['Relevant Well']))
		obs_data_block.set_settables(self, *args, from_sub = True)

class data_pool(data_block):
	def __init__(self, *args, **kwargs):
		self.data = []
		data_block.__init__(self, [], **kwargs)
	def append(self, value):
		value.parent = self
		self.data.append(value)
		self._children_ = self.data
	def _read_(self):
		for bl in self.data: bl._read_()
	def deep_parse(self):
		for bl in self.data: bl.deep_parse()
	def get_targets(self):
		return [bl.label for bl in self.data]

class plate_reader_analyzer(lfu.modular_object_qt):
	def __init__(self, *args, **kwargs):
		self.impose_default('parsed_data',lfu.data_container(),**kwargs)
		self.impose_default('input_data_file','051214_P2R2.txt',**kwargs)			# TO EXPEDITE TESTING!!
		self.impose_default('input_tmpl_file','061114 template for calc.txt',**kwargs)			# TO EXPEDITE TESTING!!
		#self.impose_default('input_data_file','',**kwargs)
		#self.impose_default('input_tmpl_file','',**kwargs)
		self.settings_manager = lset.settings_manager(parent = self, 
					filename = "plate_reader_analyzer_settings.txt")
		self.settings = self.settings_manager.read_settings()
		self.current_tab_index = 0
		self.current_tab_index_outputs = 0
		self.postprocess_plan = lpp.post_process_plan(
			label = 'Post Process Plan', parent = self)
		self.postprocess_plan._display_for_children_ = True
		lfu.modular_object_qt.__init__(self, *args, **kwargs)
		self._children_ = [self.postprocess_plan]
	def parse_inputs(self):
		self.parse_template()
		self.parse_data()
	def parse_template(self):
		fipath = os.path.join(os.getcwd(), 
			'plate_reader_analyzer', self.input_tmpl_file)
		if not os.path.isfile(fipath):
			print 'cannot find template file:', self.input_tmpl_file
			return
		with open(fipath, 'r') as handle: lines = handle.readlines()
		read = OrderedDict()
		comments = []
		for li in lines:
			l = li.strip()
			if l.startswith('#'): comments.append(l)
			elif not l == '':
				if l.startswith('<') and l.endswith('>'):
					head = l[1:-1].split(',')
					for h in head: read[h] = []
				else:
					body = l.split(',')
					for h, b in zip(read.keys(), body):
						read[h].append(b)
		read['comments'] = comments
		self.template_read = read
	def parse_data(self):
		def to_blocks(lines):
			blocks = []
			for li in lines:
				if li.startswith('\n') or li.startswith('\r'):
					blocks.append([])
				else:
					try: blocks[-1].append(li[:-1])
					except IndexError: blocks.append([])
			bl_objs = []
			[bl_objs.append(data_block(bl)) for bl in blocks if bl]
			return bl_objs
		fipath = os.path.join(os.getcwd(), 
			'plate_reader_analyzer', self.input_data_file)
		if not os.path.isfile(fipath):
			print 'cannot find data file:', self.input_data_file
			return
		with open(fipath, 'r') as handle: lines = handle.readlines()
		blocks = to_blocks(lines)
		header = header_block(blocks[:3])
		procedure = procedure_block(blocks[3:5])
		layout = layout_block(blocks[5])
		obs_blocks = blocks[6:]
		obs_heads = obs_blocks[::2]
		obs_data = obs_blocks[1::2]
		data = data_pool(parent = self)
		self._children_ = [data]
		_OD = 600
		_OD_lam = 600
		_OD_label = str(_OD_lam)+'nm:'+str(_OD)
		for pair in zip(obs_heads, obs_data):
			bl_label = pair[0].raw[0]
			if bl_label == _OD_label:
				data.append(optical_density_block(
						pair, label = bl_label))
			else: data.append(obs_data_block(pair, label = bl_label))
		self.read = {}
		self.read['header'] = header
		self.read['procedure'] = procedure
		self.read['layout'] = layout
		self.read['data'] = data
		for key in self.read.keys(): self.read[key]._read_()
		self.read['data'].deep_parse()
		daters = self.read['data'].get_targets()
		self.postprocess_plan._always_sourceable_ = daters
		self.postprocess_plan.rewidget(True)
		self.rewidget(True)
	def analyze_data(self):
		try:
			print 'performing analysis...'
			check = time.time()
			self.postprocess_plan(self)
			print 'duration of analysis: ', time.time() - check
			return True
		except:
			traceback.print_exc(file=sys.stdout)
			print 'failed to run post processes'
			return False
	def produce_output(self):
		print 'producing output...'
		check_0 = time.time()
		for dex, dat in enumerate(self.read['data'].data):
			if dat.output.must_output():
				dat.provide_axes_manager_input()
				dat.output(dat.data)
			else: print 'skipping output...', dat.output.label
		print 'produced output: ', time.time() - check_0
	def open_file(self):
		print 'open a file'
	def make_tab_book_pages(self, *args, **kwargs):
		window = args[0]
		front_page = lgm.interface_template_gui(
				widgets = ['file_name_box'], 
				layout = 'horizontal', 
				keys = [['input_data_file']], 
				instances = [[self]], 
				initials = [[self.input_data_file, 
					'Possible Inputs (*.txt)']], 
				labels = [['Choose Filename']], 
				box_labels = ['Input Data File'])
		front_page += lgm.interface_template_gui(
				widgets = ['file_name_box'], 
				keys = [['input_data_file']], 
				instances = [[self]], 
				initials = [[self.input_tmpl_file, 
					'Possible Inputs (*.txt)']], 
				labels = [['Choose Filename']], 
				box_labels = ['Input Template File'])
		front_page += lgm.interface_template_gui(
				widgets = ['button_set'], 
				layouts = ['vertical'], 
				bindings = [[lgb.create_reset_widgets_wrapper(
									window, self.parse_inputs), 
					self.analyze_data, self.produce_output]], 
				labels = [['Parse Input Files', 
					'Analyze Parsed Data', 'Produce Output']])
		pages = [('Main', [front_page])]
		output_pages = []
		if hasattr(self, 'read'):
			[output_pages.append((bl.label, 
				bl.output.widg_templates)) 
				for bl in self.read['data'].data]
		for proc in self.postprocess_plan.post_processes:
			try:
				output_pages.append((proc.label, 
					proc.output.widg_templates))
			except AttributeError:
				proc.output.set_settables(*args, **kwargs)
				output_pages.append((proc.label, 
					proc.output.widg_templates))
		output_tabs = lgm.interface_template_gui(
			widgets = ['tab_book'], 
			pages = [output_pages], 
			initials = [[self.current_tab_index_outputs]], 
			instances = [[self]], 
			keys = [['current_tab_index_outputs']])
		pages.append(('Output', [output_tabs]))
		self.postprocess_plan.set_settables(window, self)
		pp_page = lgm.interface_template_gui(
			widgets = ['panel'], 
			templates = [self.postprocess_plan.widg_templates])
		pages.append(('Post Procecssing', [pp_page]))
		if hasattr(self, 'read'):
			[pages.append((bl.label, bl.widg_templates)) 
						for bl in self.read['data'].data]
		return pages
	def rewidget__children_(self, *args, **kwargs):
		kwargs['infos'] = (kwargs['infos'][0], self)
		for child in self._children_:
			if child.rewidget(**kwargs):
				child.set_settables(*kwargs['infos'])
	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		#gear_icon_path = os.path.join(
		#	os.getcwd(), 'resources', 'gear.png')
		wrench_icon_path = os.path.join(
			os.getcwd(), 'resources', 'wrench_icon.png')
		center_icon_path = os.path.join(
			os.getcwd(), 'resources', 'center.png')
		refresh_icon_path = os.path.join(
			os.getcwd(), 'resources', 'refresh.png')
		open_icon_path = os.path.join(
			os.getcwd(), 'resources', 'open.png')
		quit_icon_path = os.path.join(
			os.getcwd(), 'resources', 'quit.png')
		settings_ = lgb.create_action(parent = window, label = 'Settings', 
						bindings = lgb.create_reset_widgets_wrapper(
					window, self.change_settings), icon = wrench_icon_path, 
					shortcut = 'Ctrl+Shift+S', statustip = 'Settings')
		self.refresh_ = lgb.create_reset_widgets_function(window)
		update_gui_ = lgb.create_action(parent = window, 
			label = 'Refresh GUI', icon = refresh_icon_path, 
			shortcut = 'Ctrl+G', bindings = self.refresh_, 
			statustip = 'Refresh the GUI (Ctrl+G)')
		open_file = lgb.create_action(parent = window, label = 'Open', 
						bindings = lgb.create_reset_widgets_wrapper(
						window, self.open_file), icon = open_icon_path, 
					shortcut = 'Ctrl+O', statustip = 'Open Input File')
		quit_ = lgb.create_action(parent = window, label = 'Quit', 
							icon = quit_icon_path, shortcut = 'Ctrl+Q', 
							statustip = 'Quit the Application', 
									bindings = window.on_close)
		center_ = lgb.create_action(parent = window, label = 'Center', 
							icon = center_icon_path, shortcut = 'Ctrl+Shift+C', 
									statustip = 'Center Window', 
									bindings = [window.on_resize, 
												window.on_center])
		self.menu_templates.append(
			lgm.interface_template_gui(
				menu_labels = ['&File', '&File', 
					'&File', '&File', '&File'], 
				menu_actions = [settings_, center_, 
					update_gui_, open_file, quit_]))
		self.tool_templates.append(
			lgm.interface_template_gui(
				tool_labels = ['&Tools', '&Tools', 
					'&Tools', '&Tools', '&Tools'], 
				tool_actions = [settings_, center_, 
					update_gui_, open_file, quit_]))
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




