import modular_core.libfundamental as lfu
import modular_core.libmath as lm
import modular_core.libfiler as lf
import modular_core.libsettings as lset

'''
import libs.modular_core.libfundamental as lfu
import libs.modular_core.libmath as lm
import libs.modular_core.libfiler as lf
import libs.modular_core.libsettings as lset
'''

import itertools as it
import types
import random
import os
import sys
import time
import math
import numpy as np
from copy import deepcopy as copy
from scipy.integrate import simps as integrate

import traceback

import pdb

if __name__ == 'modular_core.libgeometry':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'

class scalars(object):

	def __init__(self, label = 'some scalar', scalars = None, **kwargs):
		self.label = label
		self.tag = 'scalar'
		if not scalars is None:
			if type(scalars) is types.ListType:
				scalars = np.array(scalars)

			self.scalars = scalars

		else: self.scalars = []
		for key in kwargs.keys(): self.__dict__[key] = kwargs[key]

	def as_string_list(self):
		return [str(val) for val in self.scalars]

	def as_string(self):
		return ', '.join([str(val) for val in self.scalars])

class batch_scalars(object):

	def __init__(self, targets, label = 'batch of scalars'):
		self.batch_pool = []
		self.pool_names = targets
		self.override_targets = False
		self.current = 0

	def __iter__(self):
		return [self._get_trajectory_(dex) for 
			dex in range(len(self.batch_pool))].__iter__()

	def __len__(self):
		return len(self.batch_pool)

	def next(self):
		if self.current > self.high:
			raise StopIteration

		else:
			self.current += 1
			return self.current - 1

	def __getitem__(self, key):
		if type(key) is types.IntType:
			try: return self._get_trajectory_(key)
			except IndexError: raise IndexError
		else: raise TypeError

	def get_batch(self):
		return [self._get_trajectory_(dex) for 
			dex in range(len(self.batch_pool))]

	def _get_trajectory_(self, traj_dex):

		def _wrap_(values, dex):
			#if not type(values) is types.ListType:
			if hasattr(values, 'scalars'):
				values = values.scalars
				#pdb.set_trace()

			sca = scalars(label = self.pool_names[dex])
			sca.scalars = values
			return sca

		relevant = self.batch_pool[traj_dex]
		batch = [_wrap_(rele, dex) for dex, rele 
						in enumerate(relevant)]
		return batch

class batch_data_pool(object):
	def __init__(self, *args, **kwargs):
		self.targets = args[0]
		self.trajectory = args[1].trajectory
		self.override_targets = None

		self._id = time.time()
		self.data_pool_ids = ['.'.join(['batch_child', 
			str(self._id), str(dex), 'pkl']) for dex 
					in range(len(self.trajectory))]
		self.data_pools = [None]*len(self.data_pool_ids)

		self.live_pool = None
		self.current = 0

	def get_batch(self):
		pdb.set_trace()

	def _prep_pool_(self, dex):
		self._rid_pool_(self.current)
		self.current = dex
		self.live_pool = []

	def __len__(self):
		return len(self.live_pool)

	def __getitem__(self, key):
		if type(key) is types.IntType:
			try: return self._get_pool_(key)
			except IndexError: raise IndexError
		else: raise TypeError

	def _flatten_(self, pool):
		batch = []
		[batch.extend(self._get_trajectory_(dex)) 
			for dex in range(len(self.live_pool))]
		return batch

	def _get_pool_(self, dex):
		self.current = dex
		try:
			base = lfu.get_data_pool_path()
			sub_pool_id = os.path.join(base, self.data_pool_ids[dex])
			self.live_pool = lf.load_pkl_object(sub_pool_id)

		except IndexError: raise IndexError
		batch = [self._get_trajectory_(dex) for 
			dex in range(len(self.live_pool))]
		return batch

	def _get_trajectory_(self, traj_dex):

		def _wrap_(values, dex):
			sca = scalars(label = self.targets[dex])
			sca.scalars = values
			return sca

		relevant = self.live_pool[traj_dex]
		batch = [_wrap_(rele, dex) for dex, rele 
						in enumerate(relevant)]
		return batch

	def _rid_pool_(self, dex):
		if self.live_pool:
			print 'saving sub pool', dex
			lf.save_pkl_object(self.live_pool, os.path.join(
				lfu.get_data_pool_path(), self.data_pool_ids[dex]))
			print 'saved sub pool', dex
			self.live_pool = []

class bin_vectors(object):
#Note: inheriting from lfu.modular_object here makes things SLOW!

	def __init__(self, label = 'another bin vector'):
		self.counts = [] #updated with a vector 1-1 with self.bins
		self.time = [] #updated once per capture
		self.bins = [] #set once
		self.tag = 'bin_vector'
		self.label = label

class surface_vector(object):

	def __init__(self, data = [], axes = [], surfs = [], 
					label = 'another surface vector'):
		self.tag = 'surface'
		self.label = label
		self.data_scalars = [data for data in data if not data is self]
		self.axis_labels = axes
		self.axis_values = [scalars(label = dat.label, 
			scalars = lfu.uniqfy(dat.scalars)) for dat in 
			self.data_scalars if dat.label in self.axis_labels]
		self.axis_defaults = [da.scalars[0] for da in self.axis_values]
		self.surf_targets = surfs
		self.reduced = None

	def make_surface(self, x_ax = '', y_ax = '', surf_target = ''):

		data = self.data_scalars
		daters = [dater.label for dater in data]
		are_ax = [label in self.axis_labels for label in daters]
		axes = [copy(dater) for dater, is_ax in 
					zip(data, are_ax) if is_ax]
		ax_labs = [ax.label for ax in axes]
		if not (x_ax in ax_labs and y_ax in ax_labs and 
				not x_ax == y_ax and surf_target in self.surf_targets):
			print 'chosen axes do not correspond to surface'
			print 'axes:\n', ax_labs, '\nsurfaces:\n', self.surf_targets
			return False

		surf = lfu.grab_mobj_by_name(surf_target, data)
		x_ax_dex = ax_labs.index(x_ax)
		y_ax_dex = ax_labs.index(y_ax)
		ax_slices = copy(self.axis_defaults)
		ax_slices[x_ax_dex] = None
		ax_slices[y_ax_dex] = None

		reduced = (axes, surf)
		in_slices = []
		for ax_dex, ax in enumerate(axes):
			if ax_slices[ax_dex] is None:
				in_slices.append([True for val in ax.scalars])

			else:
				in_slices.append([(val == ax_slices[ax_dex]) 
									for val in ax.scalars])

		in_every_slice = [(False not in row) for row in zip(*in_slices)]
		sub_surf = scalars_from_labels([surf_target])[0]
		sub_surf.scalars = [sur for sur, in_ in 
			zip(surf.scalars, in_every_slice) if in_]
		sub_axes = scalars_from_labels(self.axis_labels)
		for sub_ax, ax in zip(sub_axes, axes):
			sub_ax.scalars = lfu.uniqfy([val for val, in_ 
				in zip(ax.scalars, in_every_slice) if in_])

		self.reduced = (sub_axes, sub_surf)
		return True

def merge_spaces(subspaces):
	space = parameter_space(subspaces = subspaces)
	return space

def generate_parameter_space_from_run_params(parent, run_params):
	def check_for_nested_contributors(subspaces, par):
		try:
			if type(par) is types.ListType:
				for pa in [para for para in par if 
						isinstance(para, lfu.modular_object_qt)]:
					check_for_nested_contributors(subspaces, par)

			elif type(par) is types.DictionaryType:
				for key in [key for key in par.keys() if 
						isinstance(par[key], lfu.modular_object_qt)]:
					check_for_nested_contributors(subspaces, par[key])

			elif isinstance(par, lfu.modular_object_qt):
				for template in par.parameter_space_templates:
					if template.contribute_to_p_sp:
						subspaces.append(one_dim_space(template))

			#nested = par.__dict__.partition['p_space contributors']
			#for key in nested.keys():
			#	check_for_nested_contributors(subspaces, nested[key])

		except: traceback.print_exc(file=sys.stdout)

	subspaces = []
	for key in run_params.keys():
		param = run_params[key]
		if type(param) is types.ListType:
			for par in [par for par in param if 
					isinstance(par, lfu.modular_object_qt)]:
				check_for_nested_contributors(subspaces, par)

		elif type(param) is types.DictionaryType:
			for subkey in [key for key in param.keys() if 
					isinstance(param[key], lfu.modular_object_qt)]:
				check_for_nested_contributors(subspaces, param[subkey])

		elif not key == '_parent': pdb.set_trace()

	if not subspaces: return None, False
	space = merge_spaces(subspaces)
	space.parent = parent
	return space, True

def generate_coarse_parameter_space_from_fine(fine, 
			magnitudes = False, decimates = False):

	def locate(num, vals):
		delts = [abs(val - num) for val in vals]
		where = delts.index(min(delts))
		found = vals[where]
		return found

	def decimate(fine, orders):

		def create_subrange(dex, num_values):
			lower = relev_mags[dex - 1]
			upper = relev_mags[dex]
			new = np.linspace(lower, upper, num_values)
			return [np.round(val, 20) for val in new]

		left  = locate(fine.bounds[0], orders)
		right = locate(fine.bounds[1], orders)
		if left == right:
			rng = range(2)
			relev_mags = [fine.bounds[0], fine.bounds[1]]

		else:
			rng = range(orders.index(left), orders.index(right) + 1)
			#many_orders = len(rng)
			relev_mags = orders[rng[0]:rng[-1] + 1]

		total_values = 20
		num_values = max([10, int(total_values/len(relev_mags))])
		new_axis = []
		for dex in range(1, len(relev_mags)):
			new_axis.extend([np.round(val, 20) for val in 
					create_subrange(dex, num_values)])

		new_axis = lfu.uniqfy(new_axis)
		#print 'NEW AXIS', new_axis
		if len(new_axis) == 0: pdb.set_trace()
		return new_axis

	def slice_subsp(fine, orders):
		coerced_increment = locate(fine.increment, orders)
		coerced_bounds =\
			[locate(fine.bounds[0], orders), 
			locate(fine.bounds[1], orders)]
		coarse_subsp = one_dim_space(
			interface_template_p_space_axis(
				instance = fine.inst, key = fine.key, 
				p_sp_bounds = coerced_bounds, 
				p_sp_continuous = False, 
				p_sp_perma_bounds = fine.perma_bounds, 
				p_sp_increment = coerced_increment, 
					constraints = fine.constraints))
		coarse_subsp.scalars = orders[
			orders.index(coerced_bounds[0]):
			orders.index(coerced_bounds[1])+1]
		return coarse_subsp

	if decimates:
		for finesp in fine.subspaces:
			finesp.regime = 'decimate'

	elif magnitudes:
		for finesp in fine.subspaces:
			finesp.regime = 'magnitude'

	orders = [10**k for k in [val - 20 for val in range(40)]]
	coarse_subspaces = []
	for finesp in fine.subspaces:
		if finesp.regime == 'decimate':
			temp_orders = decimate(finesp, orders)
			coarse_subspaces.append(slice_subsp(finesp, temp_orders))

		elif finesp.regime == 'magnitude':
			coarse_subspaces.append(slice_subsp(finesp, orders))

		else:
			print 'kept fine space fine'
			print 'PROBABLY NEED TO USE COPY OR SOMETHING'
			coarse_subspaces.append(finesp)

	if not len(coarse_subspaces) == len(fine.subspaces):
		return None, False

	space = merge_spaces(coarse_subspaces)
	space.parent = fine.parent
	return space, True

class one_dim_space(object):

	'''
	one_dim_space objects represent a single axis in a parameter space
	they contain references to alter attributes on mobjects, 
	they contain two sets of bounds, one which is used while
	exploring parameter space, and one which is permenant, and respected
	by the other set
	they can be continuous or discrete
	they can contain constraints which represent some information about
	the value of this axis relative to another axis
	constraints on this axis will change its value to be acceptable
	relative to the values of the axes which this axis is constrained to
	'''
	def __init__(self, template, scalars_ = None):
		self.inst = template.instance
		self.key = template.key
		self.bounds = template.p_sp_bounds
		self.perma_bounds = template.p_sp_perma_bounds
		self.continuous = template.p_sp_continuous
		self.increment = template.p_sp_increment
		self.constraints = template.constraints
		self.label = ' : '.join([template.instance.label, template.key])
		if not self.continuous and not scalars_:
			scalars_ = np.linspace(self.bounds[0], 
				self.bounds[1], self.increment)
			scalars_ = list(scalars_)

		self.scalars = scalars_

	def initialize(self, *args, **kwargs):
		for con in self.constraints: con.initialize(*args, **kwargs)

	def honor_constraints(self):
		for con in self.constraints: con.abide()

	def move_to(self, value):
		#if not self.continuous: pdb.set_trace()
		self.inst.__dict__[self.key] = value

	def current_location(self):
		return float(self.inst.__dict__[self.key])

	def validate_step_continuous(self, step):
		old_value = self.current_location()
		if old_value + step < self.bounds[0]:
			over_the_line = abs(step) - abs(old_value - self.bounds[0])
			step = over_the_line - old_value

		elif old_value + step > self.bounds[1]:
			over_the_line = abs(step) - abs(self.bounds[1] - old_value)
			step = self.bounds[1] - over_the_line - old_value

		return step

	def validate_step_discrete(self, step):
		old_value = self.current_location()
		space_leng = len(self.scalars)
		val_dex_rng = range(space_leng)
		try: val_dex = self.scalars.index(old_value)
		except ValueError:
			delts = [abs(val - old_value) for val in self.scalars]
			closest = delts.index(min(delts))
			val_dex = closest

		if val_dex + step > (len(val_dex_rng) - 1):
			over = val_dex + step - (len(val_dex_rng) - 1)
			step = (len(val_dex_rng) - 1) - val_dex - over

		if val_dex + step < 0:
			over = abs(val_dex + step)
			step = over - val_dex

		return self.scalars[val_dex + step] - old_value

	def validate_step(self, step):
		if self.continuous:
			return np.round(self.validate_step_continuous(step), 20)

		else: return np.round(self.validate_step_discrete(step), 20)

	def step_sample(self, norm = 3, fact = 1):
		if self.continuous: leng = self.bounds[1] - self.bounds[0]
		else: leng = len(self.scalars)
		sig = leng/norm
		self.direct = random.choice([-1.0, 1.0])
		raw_step = random.gauss(sig, sig)
		if self.continuous: step = abs(raw_step)*fact*self.direct
		else: step = int(max([1, abs(raw_step*fact)])*self.direct)
		step = self.validate_step(step)
		return step

class axis_constraint(lfu.modular_object_qt):

	def __init__(self, *args, **kwargs):
		self.impose_default('inst', None, **kwargs)
		self.impose_default('key', None, **kwargs)
		self.impose_default('inst_ruler', None, **kwargs)
		self.impose_default('key_ruler', None, **kwargs)
		self.impose_default('op', None, **kwargs)
		lfu.modular_object_qt.__init__(self, *args, **kwargs)

	def get_values(self):
		this_ax_val = self.inst.__dict__[self.key]
		the_ax_val = self.inst_ruler.__dict__[self.key_ruler]
		return this_ax_val, the_ax_val

	def less(self):
		this_ax_val, the_ax_val = self.get_values()
		return this_ax_val < the_ax_val

	def more(self):
		this_ax_val, the_ax_val = self.get_values()
		return this_ax_val > the_ax_val

	def abide(self, *args, **kwargs):
		if self.op in ['<', '<=']: rule = self.less
		elif self.op in ['>', '>=']: rule = self.more
		if not rule():
			self.inst.__dict__[self.key] =\
				self.inst_ruler.__dict__[self.key_ruler]

class parameter_space_location(lfu.modular_object_qt):

	#def __init__(self, label = 'p-space position', 
	def __init__(self, 
			location = [], trajectory_count = 1):
		self.location = location
		self.trajectory_count = trajectory_count
		#lfu.modular_object_qt.__init__(self, label = label)
		lfu.modular_object_qt.__init__(self)

	def __setitem__(self, key, value):
		self.location[key] = value

	def __getitem__(self, key):
		return self.location[key]

	def __len__(self):
		return len(self.location)

class parameter_space_step(lfu.modular_object_qt):

	def __init__(self, location = [], 
						initial = [], 
						final = [], 
						delta_quality = []):
		lfu.modular_object_qt.__init__(self)
		self.location = location
		self.initial = initial
		self.final = final
		self.delta_quality = delta_quality

	def step_forward(self):
		for k in range(len(self.location)):
			#print 'actually set value to: ' + str(self.final[k])
			self.location[k][0].__dict__[
				self.location[k][1]] = float(self.final[k])

	def step_backward(self):
		for k in range(len(self.location)):
			#print 'actually reset value to: ' + str(self.final[k])
			self.location[k][0].__dict__[
				self.location[k][1]] = float(self.initial[k])

def parse_p_space(p_sub, ensem):

	def validate(rng):
		valid = []
		for val in rng.split(','):
			try: valid.append(float(val))
			except: pass

		return valid

	def turn_on_mobjs_first_p_space_axis(mobj):
		dex = axes.index(mobj.label)
		mobj_attr = variants[dex]
		mobj.set_settables(0, ensem)
		for p_temp in mobj.parameter_space_templates:
			if mobj_attr == p_temp.key:
				p_temp.contribute_to_p_sp = True
				p_temp.p_sp_bounds = rng_bounds[dex]
				p_temp.p_sp_perma_bounds = rng_bounds[dex]
				p_temp.p_sp_increment = increments[dex]

	def read_increment(rng):
		if rng.count(';') > 0: read = float(rng[rng.rfind(';')+1:])
		else: read = 10
		return read

	if p_sub[0][0].count('<product_space>'):
		comp_meth = 'Product Space'

	elif p_sub[0][0].count('<zip_space>'): comp_meth = '1 - 1 Zip'
	elif p_sub[0][0].count('<fitting_space>'): comp_meth = 'Fitting'

	if comp_meth == 'Product Space' or comp_meth == '1 - 1 Zip':
		ax_lines = p_sub[1:]

	elif comp_meth == 'Fitting':
		ax_lines = []
		con_lines = []
		for li in p_sub[1:]:
			if li[0].startswith('#'): continue
			elif li[0].count('<axes>'): sub_parser = 'axes'
			elif li[0].count('<constraints>'): sub_parser = 'constraints'
			else:
				if sub_parser == 'axes': ax_lines.append(li)
				elif sub_parser == 'constraints': con_lines.append(li)

	def parse_axes(lines):
		axes = [ax[0] for ax in lines]
		variants = [ax[1] for ax in lines]
		ax_rngs = [ax[2] for ax in lines]
		return axes, variants, ax_rngs

	def parse_constraint(li, subspaces):
		ops = ['<', '>', '<=', '>=']
		op_in = [li.count(op) for op in ops]
		try:
			op = ops[op_in.index(True)]
			spl = li.split(op)
			which = subspaces[int(spl[0])]
			target = subspaces[int(spl[-1])]
			con = axis_constraint(
				op = op, inst = which.inst, key = which.key, 
				inst_ruler = target.inst, key_ruler = target.key)
			which.constraints.append(con)

		except:
			traceback.print_exc(file=sys.stdout)
			print 'unable to parse constraint', li

	axes, variants, ax_rngs = parse_axes(ax_lines)
	increments = [read_increment(rng) for rng in ax_rngs]
	ranges = [lm.make_range(rng)[0] for rng in ax_rngs]
	rng_bounds = [[validate(rng)[0], validate(rng)[-1]] 
									for rng in ranges]
	poss_contribs = ['species', 'variables', 'reactions']
	p_mobjs = ensem.cartographer_plan.parameter_space_mobjs
	for key in p_mobjs.keys():
		if key in poss_contribs:
			if type(p_mobjs[key]) is types.DictionaryType:
				for sub_key in p_mobjs[key].keys():
					mobj = p_mobjs[key][sub_key]
					if mobj.label in axes:
						turn_on_mobjs_first_p_space_axis(mobj)

			if type(p_mobjs[key]) is types.ListType:
				for mobj in p_mobjs[key]:
					if mobj.label in axes:
						turn_on_mobjs_first_p_space_axis(mobj)

	ensem.cartographer_plan.generate_parameter_space()
	selected = [ensem.cartographer_plan.\
		parameter_space.get_start_position()]

	if comp_meth == 'Product Space' or comp_meth == '1 - 1 Zip':
		traj_dlg = lgd.trajectory_dialog(parent = None, 
			base_object = selected, composition_method = comp_meth, 
			p_space = ensem.cartographer_plan.parameter_space)

		for ax, vari, rng in zip(axes, variants, ranges):
			trj_dlg_dex = traj_dlg.axis_labels.index(
							' : '.join([ax, vari]))
			traj_dlg.variations[trj_dlg_dex] = validate(rng)

		traj_dlg.on_make()
		if traj_dlg.made:
			ensem.cartographer_plan.trajectory_string =\
								traj_dlg.result_string
			ensem.cartographer_plan.on_delete_selected_pts(
										preselected = None)
			ensem.cartographer_plan.on_reset_trajectory_parameterization()
			ensem.cartographer_plan.on_append_trajectory(traj_dlg.result)

		ensem.cartographer_plan.traj_count = p_sub[0][1]
		ensem.cartographer_plan.on_assert_trajectory_count(all_ = True)

	elif comp_meth == 'Fitting':
		subspaces = ensem.cartographer_plan.parameter_space.subspaces
		for li in lfu.flatten(con_lines):
			parse_constraint(li, subspaces)

class parameter_space(lfu.modular_object_qt):

	'''
	initialize with template to make a space
		templates are interface_template_p_space_axis objects
	or initialize with subsps to make a space
		subsps are one_dim_space objects
	the first overrides the second
	'''
	def __init__(self, *args, **kwargs):
		if 'base_obj' in kwargs.keys():
		#if not base_obj is None:
			self.subspaces = []
			for template in base_obj.parameter_space_templates:
				if template.contribute_to_p_sp:
					self.subspaces.append(one_dim_space(template)) 

		else:
			try: self.subspaces = kwargs['subspaces']
			except KeyError:
				traceback.print_exc(file=sys.stdout)
				msg = '''\
					parameter space __init__ requires either subspaces\
					or a base_obj to make subspaces from\
					'''
				lfu.debug_filter(msg, verbosity = 0)
				self.subspaces = []

			self.set_simple_space_lookup()

		self.impose_default('steps', [], **kwargs)
		self.impose_default('step_normalization', 4.0, **kwargs)
		self.dimensions = len(self.subspaces)
		lfu.modular_object_qt.__init__(self, *args, **kwargs)

	def set_start_position(self):
		self.undo_level = 0
		for subsp in self.subspaces:
			subsp.initialize()
			rele_val = subsp.current_location()
			print 'starting position of', subsp.label, ':', rele_val, ':', subsp.bounds

	def get_start_position(self):
		location = [sp.inst.__dict__[sp.key] 
					for sp in self.subspaces]
		return parameter_space_location(location = location)

	def get_current_position(self):
		return [(axis.inst.label, axis.key, 
			str(axis.current_location())) 
			for axis in self.subspaces]

	def set_current_position(self, position):
		for pos, axis in zip(position, self.subspaces):
			axis.move_to(pos[-1])

		self.validate_position()

	def validate_position(self):
		for axis in self.subspaces:
			if axis.constraints:
				axis.honor_constraints()

	#bias_axis is the index of the subspace in subspaces
	#bias is the number of times more likely that axis is than the rest
	def set_simple_space_lookup(self, bias_axis = None, bias = 1.0):
		self.param_lookup = [float(sp_dex + 1) for sp_dex in 
								range(len(self.subspaces))]
		if bias_axis != None:
			if type(bias_axis) is types.ListType:
				for ax_dex in bias_axis:
					if ax_dex == 0:
						bump = self.param_lookup[ax_dex]*bias -\
								self.param_lookup[ax_dex]

					else:
						bump = (self.param_lookup[ax_dex] -\
								self.param_lookup[ax_dex - 1])*bias -\
									(self.param_lookup[ax_dex] -\
									self.param_lookup[ax_dex - 1])

					self.param_lookup = self.param_lookup[:ax_dex] +\
						[self.param_lookup[k] + bump for k in range(
							ax_dex, len(self.param_lookup))]

			else:
				if bias_axis == 0:
					bump = self.param_lookup[bias_axis]*bias -\
							self.param_lookup[bias_axis]

				else:
					bump = (self.param_lookup[bias_axis] -\
							self.param_lookup[bias_axis - 1])*bias -\
								(self.param_lookup[bias_axis] -\
								self.param_lookup[bias_axis - 1])

				self.param_lookup = self.param_lookup[:bias_axis] +\
					[self.param_lookup[k] + bump for k in range(
							bias_axis, len(self.param_lookup))]

		#print 'subsp prob: ' + str(self.param_lookup)
		self.param_lookup = lm.normalize_numeric_list(self.param_lookup)

	def undo_step(self):
		try:
			#print 'undoing a step!'
			self.undo_level += 1
			self.steps.append(parameter_space_step(
				location = self.steps[-1].location, 
				initial = self.steps[-1].final, 
				final = self.steps[-1].initial))
			self.steps[-1].step_forward()

		except IndexError: print 'no steps to undo!'

	def step_up_discrete(self, step, dex, rng):
		if dex + step not in rng:
			over = dex + step - rng[-1]
			dex = rng[-1] - over

		else: dex += step
		return dex

	def step_down_discrete(self, step, dex, rng):
		if dex - step not in rng:
			dex = step - dex

		else: dex -= step
		return dex

	def set_up_discrete_step(self, param_dex, factor, direc):
		subsp = self.subspaces[param_dex]
		old_value = subsp.current_location()
		step = subsp.step_sample(self.step_normalization, 
							factor/self.initial_factor)
		self.steps[-1].location.append((subsp.inst, subsp.key))
		self.steps[-1].initial.append(old_value)
		self.steps[-1].final.append(step + old_value)
		return step, old_value

	def set_up_continuous_step(self, param_dex, factor, direc):
		subsp = self.subspaces[param_dex]
		old_value = subsp.current_location()
		step = subsp.step_sample(
			self.step_normalization, 
			factor/self.initial_factor)
		self.steps[-1].location.append((
			self.subspaces[param_dex].inst, 
			self.subspaces[param_dex].key))
		self.steps[-1].initial.append(old_value)
		self.steps[-1].final.append(step + old_value)
		return step, old_value

	def take_biased_step_along_axis(self, factor = 1.0, bias = 1000.0):

		def get_direction(dex):
			delta = self.steps[-1].final[dex] -\
				float(self.steps[-1].initial[dex])
			if delta: return delta/abs(delta)
			return None

		if not self.steps: self.take_proportional_step(factor)
		objs = [sp.inst for sp in self.subspaces]
		step_objs = [local[0] for local in self.steps[-1].location]
		last_ax_dexes = [objs.index(obj) for obj in step_objs]
		last_ax_direcs = [get_direction(k) for k in 
				range(len(self.steps[-1].initial))]
		self.set_simple_space_lookup(last_ax_dexes, bias)
		self.take_proportional_step(factor, 
			even_odds = False, many_steps = len(last_ax_dexes), 
			last_ax_pairs = zip(last_ax_dexes, last_ax_direcs))

	def take_proportional_step(self, factor = 1.0, even_odds = True, 
								many_steps = 3, last_ax_pairs = None):
		if even_odds: self.set_simple_space_lookup()
		param_dexes = self.lookup_distinct_axes(many_steps)
		if last_ax_pairs: last_axes, last_direcs = zip(*last_ax_pairs)
		else:
			last_axes = []
			last_direcs = []

		self.steps.append(parameter_space_step(
			location = [], initial = [], final = []))
		for param_dex in param_dexes:
			if param_dex in last_axes:
				direc = last_direcs[last_axes.index(param_dex)]
				if direc is None: direc = random.choice([-1.0, 1.0])

			else: direc = random.choice([-1.0, 1.0])
			if self.subspaces[param_dex].continuous:
				step, param = self.set_up_continuous_step(
								param_dex, factor, direc)

			else:
				step, param = self.set_up_discrete_step(
								param_dex, factor, direc)

		self.steps[-1].step_forward()

	def lookup_distinct_axes(self, many_steps):
		dexes = []
		while len(dexes) < min([len(self.subspaces), many_steps]):
			rand = random.random()
			new_dex = [rand < lup for lup in 
				self.param_lookup].index(True)
			if not new_dex in dexes: dexes.append(new_dex)

		return dexes

class interface_template_p_space_axis(lfu.interface_template_new_style):

	rewidget_ = True

	def __init__(self, instance = None, key = None, parent = None, 
			visible_attributes = ['reference', 'linkages'], 
			contribute_to_p_sp = False, gui_give_p_sp_control = True, 
			p_sp_continuous = True, p_sp_bounds = [1, 10], 
			p_sp_perma_bounds = [0, 100], p_sp_increment = 1.0, 
			gui_give_p_sp_cont_disc_control = False, constraints = None):
		self.instance = instance
		self.key = key
		if constraints: self.constraints = constraints
		else: self.constraints = []
		self.contribute_to_p_sp = contribute_to_p_sp
		self.gui_give_p_sp_control = gui_give_p_sp_control
		self.p_sp_continuous = p_sp_continuous
		self.p_sp_bounds = p_sp_bounds
		self.p_sp_perma_bounds = p_sp_perma_bounds
		self.p_sp_increment = p_sp_increment
		self.gui_give_p_sp_cont_disc_control =\
				gui_give_p_sp_cont_disc_control
		if lgm: self.mason = lgm.standard_mason(parent = self)
		lfu.interface_template_new_style.__init__(self, 
			parent = parent, visible_attributes = visible_attributes)

	def rewidget(self, *args, **kwargs):
		try:
			if type(args[0]) is types.BooleanType:
				self.rewidget_ = args[0]
				if hasattr(self, 'parent') and self.rewidget_:
					if self.parent is not None:
						self.parent.rewidget(self.rewidget_)

			else: print 'unrecognized argument for rewidget; ignoring'

		except IndexError:
			#self.rewidget__children_(**kwargs)
			return self.rewidget_

	def _show_dialog_widgets_(self, *args, **kwargs):
		self.dialog_panel = lgb.create_scroll_area(lgb.create_panel(
							self.widg_dialog_templates, self.mason))
		gear_icon = os.path.join(os.getcwd(), 'resources', 'gear.png')
		self.dialog_panel.setWindowIcon(lgb.create_icon(gear_icon))
		for temp in self.widg_dialog_templates:
			if hasattr(temp, 'panel_label'):
				self.dialog_panel.setWindowTitle(temp.panel_label)

		panel_x = self.dialog_panel.sizeHint().width()*1.5
		panel_y = self.dialog_panel.sizeHint().height()*1.25
		panel_x, panel_y = min([panel_x, 1600]), min([panel_y, 900])
		self.dialog_panel.setGeometry(150, 120, panel_x, panel_y)
		self.dialog_panel.show()

	def set_settables(self, *args, **kwargs):
		#self.handle_widget_inheritance(*args, **kwargs)
		self.widg_templates = []
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['check_set', 'button_set'], 
				instances = [[self], None], 
				keys = [['contribute_to_p_sp'], None], 
				labels = [['Contribute to Parameter Space'], 
						['More Settings']], 
				append_instead = [False, None], 
				bindings = [None, [self._show_dialog_widgets_]], 
				box_labels = ['Parameter Space']))
		self.widg_dialog_templates = []
		self.widg_dialog_templates.append(
			lgm.interface_template_gui(
				widgets = ['spin', 'spin'], 
				doubles = [[True], [True]], 
				initials = [[self.p_sp_bounds[0]], 
							[self.p_sp_bounds[1]]], 
				minimum_values = [[-sys.float_info.max], 
								[-sys.float_info.max]], 
				maximum_values = [[sys.float_info.max], 
								[sys.float_info.max]], 
				instances = [[self.p_sp_bounds], 
							[self.p_sp_bounds]], 
				keys = [[0], [1]], 
				box_labels = ['Subspace Minimum', 
							'Subspace Maximum'], 
				panel_label = 'Parameter Space'))

		#lfu.modular_object_qt.set_settables(
		#		self, *args, from_sub = True)
		self.rewidget(False)

class cartographer_plan(lfu.plan):

	def __init__(self, label = 'mapping plan', parent = None, 
			parameter_space_mobjs = {}, traj_count = 1, key_path = ''):
		self.parameter_space = None
		self.parameter_space_mobjs = parameter_space_mobjs
		self.trajectory = []
		self.iteration = 0
		self.controller_ref = None
		self.traj_count = traj_count
		self.key_path = key_path
		self.trajectory_string = ''
		use = lset.get_setting('mapparameterspace')
		lfu.plan.__init__(self, label = label, 
			parent = parent, use_plan = use)

	def to_string(self):
		if self.trajectory:
			#cnt = self.trajectory[0][1].trajectory_count
			cnt = str(self.traj_count)

		else: cnt = '1'
		lines = [self.trajectory_string.replace('#', cnt)]
		return lines

	def generate_parameter_space(self):
		self.parameter_space, valid =\
			generate_parameter_space_from_run_params(
					self, self.parameter_space_mobjs)
		if valid:
			self.trajectory = [[0] +\
				[self.parameter_space.get_start_position()]]
			self.rewidget(True)

		else:
			lgd.message_dialog(None, 
				'No parameter space axes specified!', 'Problem')

	def selected_locations_lookup(self):
		try:
			ref_children = self.controller_ref[0].children()
			list_widg_dex = [issubclass(widg.__class__, 
							lgb.QtGui.QItemSelectionModel) 
						for widg in ref_children].index(True)
			list_widg = ref_children[list_widg_dex]
			row_widg_dex = [issubclass(widg.__class__, 
							lgb.QtCore.QAbstractItemModel) 
						for widg in ref_children].index(True)
			row_count = ref_children[row_widg_dex].rowCount()

		except:
			self.rewidget(True)
			print 'update_widgets!'
			return []

		sel_rows = list_widg.selectedRows()
		sel_dexes = [item.row() for item in sel_rows]
		return [dex in sel_dexes for dex in range(row_count)]

	def positions_from_lookup(self, selected):
		return [locale for locale, select in 
			zip(self.trajectory, selected) if select]

	def on_reset_trajectory_parameterization(self):
		for dex in range(len(self.trajectory)):
			self.trajectory[dex][0] = dex

	def on_append_trajectory(self, new_trajectory):
		traj_leng = len(self.trajectory)
		self.trajectory.extend([[dex, locale] for dex, locale in 
								zip(range(traj_leng, traj_leng +\
							len(new_trajectory)), new_trajectory)])

	def on_delete_selected_pts(self, preselected = None):
		if preselected is None:
			selected = [not value for value in 
				self.selected_locations_lookup()]

		else:
			selected = [not value for value in preselected]

		self.trajectory = self.positions_from_lookup(selected)
		self.on_reset_trajectory_parameterization()
		self.rewidget(True)

	def on_output_trajectory_key(self):

		def pretty_line(locale, lengs):
			li = [str(loc).rjust(lengs[dex] + 5) for loc, dex 
				in zip(locale[1].location, range(len(lengs)))]
			line = '\t'.join([' Index: ' + str(locale[0]).ljust(4)+str(
				locale[1].trajectory_count).rjust(22), '\t'.join(li)])
			return line

		if not self.parameter_space is None:
			axis_labels = [subsp.label for subsp in 
					self.parameter_space.subspaces]

		else:
			lgd.message_dialog(None, 'Can\'t output key without' +\
								' a parameter space!', 'Problem')
			return

		label_lengs = [len(label) for label in axis_labels]
		lines = ['\t||\tTrajectory Key\t||\t\n']
		lines.append('Trajectory number'.ljust(25) +\
					'Trajectory Count'.ljust(25) +\
					'\t '.join([label.ljust(leng + 5) for 
					label, leng in zip(axis_labels, label_lengs)]))
		lines.append('-'*120)
		label_lengs.insert(0, 20)
		lines.extend([pretty_line(locale, label_lengs) 
						for locale in self.trajectory])
		if self.key_path is None or self.key_path == '':
			self.key_path = os.path.join(os.getcwd(), 
						'p_space_trajectory_key.txt')
			self.rewidget(True)

		lf.output_lines(lines, self.key_path)

	def on_assert_trajectory_count(self, all_ = False):
		if all_:
			relevant_locations =\
				self.positions_from_lookup([True]*len(self.trajectory))

		else:
			relevant_locations = self.positions_from_lookup(
							self.selected_locations_lookup())

		for locale in relevant_locations:
			locale[1].trajectory_count = self.traj_count

		self.rewidget(True)

	def generate_traj_diag_function(self, window, method = 'blank'):

		def on_create_trajectory():

			if method == 'blank':
				try: selected = [self.parameter_space.get_start_position()]
				except AttributeError:
					lgd.message_dialog(None, ' '.join(['Can\'t', 
						'create', 'trajectory', 'without', 'a', 
							'parameter', 'space!']), 'Problem')
					return

			else:
				selected = [item[1] for item in 
					self.positions_from_lookup(
					self.selected_locations_lookup())]
				to_replace = self.selected_locations_lookup()

			#traj_dlg = create_trajectory_dialog(
			#	parent = window, base_object = selected, 
			#			p_space = self.parameter_space)
			traj_dlg = lgd.trajectory_dialog(
				parent = window, base_object = selected, 
						p_space = self.parameter_space)
			made = traj_dlg()
			if made:
				if method == 'modify':
					self.on_delete_selected_pts(preselected = to_replace)
					self.on_reset_trajectory_parameterization()

				self.on_append_trajectory(traj_dlg.result)
				self.trajectory_string = traj_dlg.result_string

		return lgb.create_reset_widgets_wrapper(
					window, on_create_trajectory)

	def move_to(self, t):
		move_to = self.trajectory[t][1]
		for loc, subsp in zip(move_to, self.parameter_space.subspaces):
			subsp.move_to(loc)

	#def sanitize(self, *args, **kwargs):
	#	self.create_traj_templates = []
	#	lfu.plan.sanitize(self)

	def set_settables(self, *args, **kwargs):
		window = args[0]
		self.handle_widget_inheritance(*args, **kwargs)
		#self.widg_templates.append(
		right_side = [lgm.interface_template_gui(
				layout = 'grid', 
				panel_position = (0, 2), 
				widg_positions = [(0, 0), (1, 0), (2, 0)], 
				layouts = ['vertical', 'vertical', 'vertical'], 
				widgets = ['button_set', 'spin', 'full_path_box'], 
				initials = [None, [self.traj_count], 
					[self.key_path, 'Possible Outputs (*.txt)']], 
				minimum_values = [None, [1], None], 
				maximum_values = [None, [100000], None], 
				instances = [None, [self], [self]], 
				keys = [None, ['traj_count'], ['key_path']], 
				bindings = [[lgb.create_reset_widgets_wrapper(
						window, self.generate_parameter_space), 
					self.generate_traj_diag_function(window, 'blank'), 
					self.generate_traj_diag_function(window, 'modify'), 
					lgb.create_reset_widgets_wrapper(window, 
							self.on_delete_selected_pts), 
					self.on_output_trajectory_key, 
					lgb.create_reset_widgets_wrapper(window, 
						self.on_assert_trajectory_count)], None, None], 
				labels = [['Generate Parameter Space', 
					'Create Trajectory', 'Replace Selected Points', 
					'Delete Selected Points', 'Output Trajectory Key', 
					'Assert Trajectory Count\n to Selected'], None, 
											['Choose File Path']], 
				box_labels = [None, 'Trajectory Count', 
						'Trajectory Key File Path'])]
		split_widg_templates = [
			lgm.interface_template_gui(
				widgets = ['splitter'], 
				orientations = [['horizontal']], 
				templates = [right_side])]
		if not self.parameter_space is None:
			#a point consists of a list of 2 components
			#	the first is the index of the location
			#	the second is the values in 1-1 with 
			#	p-space subspaces
			headers = [subsp.label for subsp in 
				self.parameter_space.subspaces] + ['']
			#self.widg_templates.append(
			left_side = [lgm.interface_template_gui(
					widgets = ['list_controller'], 
					panel_position = (0, 0), 
					panel_span = (3, 2), 
					handles = [(self, 'controller_ref')], 
					labels = [['Index'.ljust(16), 
						'Trajectory Count'] + headers], 
					minimum_sizes = [[(500, 300)]], 
					entries = [self.trajectory], 
					box_labels = ['Trajectory In Parameter Space'])]
			split_widg_templates[-1].templates =\
						[left_side + right_side]

		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['panel'], 
				templates = [split_widg_templates], 
				scrollable = [True], 
				box_labels = ['Parameter Space']))
		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)

def scalars_from_labels(targeted):
	return [scalars(label = target) for target in targeted]

def bin_vectors_from_labels(targeted):
	return [bin_vectors(label = target) for target in targeted]

def sort_data_by_type(data, specifics = []):
	if not specifics: specifics = [dater.label for dater in data]
	sorted_data = {'scalars': {}, 'coords': {}}
	for dater in [dater for dater in data if dater.label in specifics]:
		if dater.tag == 'scalar':
			sorted_data['scalars'][dater.label] = dater.scalars

		elif dater.tag == 'coordinates':
			sorted_data['coords']['_'.join(dater.coords.keys())] = dater.coords

	return sorted_data

class metric(lfu.modular_object_qt):

	#ABSTRACT
	'''
	a metric takes two sets of data and runs some method which
	returns one scalar representing some sort of distance
	'''
	def __init__(self, *args, **kwargs):
		if not 'valid_base_classes' in kwargs.keys():
			global valid_metric_base_classes
			kwargs['valid_base_classes'] = valid_metric_base_classes

		if not 'base_class' in kwargs.keys():
			kwargs['base_class'] = lfu.interface_template_class(
									object, 'abstract metric')

		self.impose_default('best_measure', 0, **kwargs)
		self.impose_default('display_threshold', 0, **kwargs)
		self.impose_default('display_time', 1.0, **kwargs)
		self.impose_default('acceptance_weight', 1.0, **kwargs)
		self.impose_default('best_advantage', 2.0, **kwargs)
		self.impose_default('best_flag', False, **kwargs)
		self.impose_default('is_heaviest', False, **kwargs)
		lfu.modular_object_qt.__init__(self, *args, **kwargs)
		self._children_ = []

	def check_best(self, display = False):
		if self.best_flag:
			if not self.is_heaviest:
				self.acceptance_weight /= self.best_advantage

		self.best_flag = False
		if self.data[0].scalars[-1] == min(self.data[0].scalars):
			self.best_measure = len(self.data[0].scalars) - 1
			self.best_flag = True
			if not self.is_heaviest:
				self.acceptance_weight *= self.best_advantage

		if (self.best_flag or display) and self.is_heaviest:
			meas = self.data[0].scalars[-1]
			print ' '.join(['\nmetric', self.label, 'measured best', 
					str(meas), str(len(self.data[0].scalars) - 1)])
			for pos in self.parent.parameter_space.get_current_position():
				print pos
			#lgd.quick_plot_display(to_fit_to[0], 
			#	to_fit_to[1:] + run_data_interped, 
			#			delay = self.display_time)
			print '\n'

	def measure(self, *args, **kwargs):
		to_fit_to = args[0]
		run_data = args[1]
		dom_weight_max = 5.0
		domain_weights = np.exp(np.linspace(dom_weight_max, 
							0, len(to_fit_to[0].scalars)))
		#domain_weights = [1 for val in 
		#	np.linspace(0, 1, len(to_fit_to[0].scalars))]
		#domain_weights = np.linspace(dom_weight_max, 
		#				1, len(to_fit_to[0].scalars))
		if self.best_flag:
			self.best_flag = False
			self.acceptance_weight /= 2.0

		try: report_only = kwargs['report_only']
		except KeyError: report_only = False

		labels = [[do.label for do in de] for de in args]
		run_data_domain = run_data[labels[1].index(labels[0][0])]
		try:
			run_data_codomains = [run_data[labels[1].index(
					labels[0][lab_dex+1])] for lab_dex 
						in range(len(labels[0][1:]))]
		except ValueError: pdb.set_trace()
		run_data_interped = [scalars(
			label = 'interpolated result - ' + codomain.label, 
			scalars = lm.linear_interpolation(run_data_domain.scalars, 
					codomain.scalars, to_fit_to[0].scalars, 'linear')) 
								for codomain in run_data_codomains]
		x_meas_bnds = (0, len(to_fit_to[0].scalars))
		meas = [[diff for diff in kwargs['measurement'](
			fit_to.scalars, interped.scalars, x_meas_bnds, 
			to_fit_to[0].scalars, domain_weights) if not 
				math.isnan(diff)] for fit_to, interped in 
					zip(to_fit_to[1:], run_data_interped)]
		meas = np.mean([np.mean(mea) for mea in meas])
		if not report_only:
			self.data[0].scalars.append(meas)
			if meas == min(self.data[0].scalars) and\
					meas < self.data[0].scalars[self.best_measure]:
				self.best_measure = len(self.data[0].scalars) - 1
				#self.best_flag = self.best_measure > self.display_threshold
				self.best_flag = True

			if self.best_flag:
				if 'weight' in kwargs.keys():
					self.acceptance_weight = kwargs['weight']

				else: self.acceptance_weight *= 2.0
			if (self.best_flag or kwargs['display']) and self.is_heaviest:
				print ' '.join(['metric', self.label, 'measured', 
					str(meas), str(len(self.data[0].scalars))])
				print self.parent.parameter_space.get_current_position()
				lgd.quick_plot_display(to_fit_to[0], 
					to_fit_to[1:] + run_data_interped, 
							delay = self.display_time)

		else: return meas

class metric_avg_ptwise_diff_on_domain(metric):

	def __init__(self, *args, **kwargs):
		if not 'label' in kwargs.keys():
			kwargs['label'] = 'pointwise difference metric'

		metric.__init__(self, *args, **kwargs)

	def initialize(self, *args, **kwargs):
		self.data = scalars_from_labels(['mean difference'])
		metric.initialize(self, *args, **kwargs)

	def measure(self, *args, **kwargs):
		#if not 'report_only' in kwargs.keys():
		#	kwargs['report_only'] = False
		kwargs['measurement'] = self.differences
		return metric.measure(self, *args, **kwargs)

	def differences(self, *args, **kwargs):
		to_fit_to_y = args[0]
		runinterped = args[1]
		bounds = args[2]
		dom_weights = args[4]
		return [weight*abs(to_fit_to_y[k] - runinterped[k]) 
						for weight, k in zip(dom_weights, 
							range(bounds[0], bounds[1]))]

class metric_slope_1st_derivative(metric):

	def __init__(self, *args, **kwargs):
		if not 'label' in kwargs.keys():
			kwargs['label'] = 'slope metric'

		metric.__init__(self, *args, **kwargs)

	def initialize(self, *args, **kwargs):
		self.data = scalars_from_labels(['mean slope difference'])
		metric.initialize(self, *args, **kwargs)

	def measure(self, *args, **kwargs):
		kwargs['measurement'] = self.slope_differences
		return metric.measure(self, *args, **kwargs)

	def slope_differences(self, *args, **kwargs):
		to_fit_to_y = args[0]
		runinterped = args[1]
		bounds = args[2]
		to_fit_to_x = args[3]
		dom_weights = args[4]
		runinterped_slope = [(runinterped[k] - runinterped[k - 1])\
					/(to_fit_to_x[k] - to_fit_to_x[k - 1]) 
					for k in range(1, len(to_fit_to_x))]
		to_fit_to_y_slope = [(to_fit_to_y[k] - to_fit_to_y[k - 1])\
							/(to_fit_to_x[k] - to_fit_to_x[k - 1]) 
							for k in range(1, len(to_fit_to_x))]
		return [weight*abs(to_fit_to_y_slope[k] - runinterped_slope[k]) 
				for weight, k in zip(dom_weights, 
				range(bounds[0], bounds[1] -1))]

class metric_slope_2nd_derivative(metric):

	def __init__(self, *args, **kwargs):
		if not 'label' in kwargs.keys():
			kwargs['label'] = '2nd derivative metric'

		metric.__init__(self, *args, **kwargs)

	def initialize(self, *args, **kwargs):
		self.data = scalars_from_labels(['mean 2nd derivative'])
		metric.initialize(self, *args, **kwargs)

	def measure(self, *args, **kwargs):
		kwargs['measurement'] = self.second_derivative_differences
		return metric.measure(self, *args, **kwargs)

	def second_derivative_differences(self, *args, **kwargs):

		def calc_2nd_deriv(x, y, dex):
			del_x_avg = (x[dex + 1] - x[dex - 1])/2.0
			return (y[dex + 1] - (2*y[dex]) + y[dex - 1])\
								/((x[dex] - del_x_avg)**2)

		to_fit_to_y = args[0]
		runinterped = args[1]
		bounds = args[2]
		to_fit_to_x = args[3]
		dom_weights = args[4]
		runinterped_slope = [
			calc_2nd_deriv(to_fit_to_x, runinterped, k) 
				for k in range(1, len(to_fit_to_x) -1)]
		to_fit_to_y_slope = [
			calc_2nd_deriv(to_fit_to_x, to_fit_to_y, k) 
				for k in range(1, len(to_fit_to_x) -1)]
		return [weight*abs(to_fit_to_y_slope[k] - runinterped_slope[k]) 
							for weight, k in zip(dom_weights, range(
									bounds[0] + 1, bounds[1] - 2))]

class metric_slope_3rd_derivative(metric):

	def __init__(self, *args, **kwargs):
		if not 'label' in kwargs.keys():
			kwargs['label'] = '3rd derivative metric'

		metric.__init__(self, *args, **kwargs)

	def initialize(self, *args, **kwargs):
		self.data = scalars_from_labels(['mean 3rd derivative'])
		metric.initialize(self, *args, **kwargs)

	def measure(self, *args, **kwargs):
		kwargs['measurement'] = self.third_derivative_differences
		return metric.measure(self, *args, **kwargs)

	def third_derivative_differences(self, *args, **kwargs):

		def calc_3rd_deriv(x, y, dex):
			top = (y[dex - 2] - (3*y[dex - 1]) +\
						(3*y[dex]) + y[dex + 1])
			del_x_avg = ((x[dex + 1] - x[dex - 2]))/3.0
			return top/((x[dex] - del_x_avg)**3)

		to_fit_to_y = args[0]
		runinterped = args[1]
		bounds = args[2]
		to_fit_to_x = args[3]
		dom_weights = args[4]
		runinterped_slope = [
			calc_3rd_deriv(to_fit_to_x, runinterped, k) 
				for k in range(1, len(to_fit_to_x) -1)]
		to_fit_to_y_slope = [
			calc_3rd_deriv(to_fit_to_x, to_fit_to_y, k) 
				for k in range(1, len(to_fit_to_x) -1)]
		return [weight*abs(to_fit_to_y_slope[k] - runinterped_slope[k]) 
				for weight, k in zip(dom_weights, 
				range(bounds[0] + 2, bounds[1] - 2))]

class metric_slope_4th_derivative(metric):

	def __init__(self, *args, **kwargs):
		if not 'label' in kwargs.keys():
			kwargs['label'] = '4th derivative metric'

		metric.__init__(self, *args, **kwargs)

	def initialize(self, *args, **kwargs):
		self.data = scalars_from_labels(['mean 4th derivative'])
		metric.initialize(self, *args, **kwargs)

	def measure(self, *args, **kwargs):
		kwargs['measurement'] = self.fourth_derivative_differences
		return metric.measure(self, *args, **kwargs)

	def fourth_derivative_differences(self, *args, **kwargs):

		def calc_4th_deriv(x, y, dex):
			left = (y[dex - 2] - (2*y[dex - 1]) + y[dex])
			right = (y[dex] - (2*y[dex + 1]) + y[dex + 2])
			#top = (y[dex - 2] - (3*y[dex - 1]) +\
			#			(3*y[dex]) + y[dex + 1])
			del_x_avg = ((x[dex + 2] - x[dex - 2]))/4.0
			print 'DONT USE THIS YET!'; return None
			return top/((x[dex] - del_x_avg)**4)

		to_fit_to_y = args[0]
		runinterped = args[1]
		bounds = args[2]
		to_fit_to_x = args[3]
		runinterped_slope = [
			calc_4th_deriv(to_fit_to_x, runinterped, k) 
				for k in range(1, len(to_fit_to_x) -1)]
		to_fit_to_y_slope = [
			calc_4th_deriv(to_fit_to_x, to_fit_to_y, k) 
				for k in range(1, len(to_fit_to_x) -1)]
		return [abs(to_fit_to_y_slope[k] - runinterped_slope[k]) 
				for k in range(bounds[0] + 2, bounds[1] - 3)]

def array_to_string(arr):
	string = ' '
	string = string.join([str(value) for value in arr])
	string += ' '
	return string

def coords_to_string(x, y, z):
	#concat = x + y + z
	concat = np.concatenate((x, y, z))
	array = [[concat[k], concat[k + len(x)], concat[k + 2*len(x)]] \
										for k in range(len(x))]
	array = [item for sublist in array for item in sublist]
	return array_to_string(array)

def quality_coords_to_string(x, y, z, Q, dims):
	string = str()
	xdim = int(dims[0]) + 1
	ydim = int(dims[1]) + 1
	zdim = int(dims[2]) + 1
	npts = xdim*ydim*zdim
	flat = ['0']*npts
	for j in range(len(Q)):
		try:
			flat[int(z[j])*xdim*ydim + int(y[j])*xdim + int(x[j])]=str(Q[j])

		except IndexError:
			print 'Youve got an indexing problem'
			pdb.set_trace()

	string = array_to_string(flat)
	return string

valid_metric_base_classes = [
	lfu.interface_template_class(
		metric_slope_1st_derivative, 
			'slope-1 comparison metric'), 
	lfu.interface_template_class(
		metric_slope_2nd_derivative, 
			'slope-2 comparison metric'), 
	lfu.interface_template_class(
		metric_slope_3rd_derivative, 
			'slope-3 comparison metric'), 
	lfu.interface_template_class(
		metric_avg_ptwise_diff_on_domain, 
			'pointwise difference metric')]





