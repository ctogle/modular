import libs.modular_core.libfundamental as lfu
import libs.modular_core.libmath as lm
import libs.modular_core.libfiler as lf
import libs.modular_core.libsettings as lset

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

if __name__ == 'libs.modular_core.libgeometry':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'

class scalers(object):

	def __init__(self, label = 'some scaler', scalers = None):
		self.label = label
		if not scalers is None: self.scalers = scalers
		else: self.scalers = []
		self.tag = 'scaler'

	def as_string_list(self):
		return [str(val) for val in self.scalers]

	def as_string(self):
		return ', '.join([str(val) for val in self.scalers])

class batch_scalers(object):

	def __init__(self, targets, label = 'batch of scalers'):
		self.batch_pool = []
		self.pool_names = targets
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
			sca = scalers(label = self.pool_names[dex])
			sca.scalers = values
			return sca

		relevant = self.batch_pool[traj_dex]
		batch = [_wrap_(rele, dex) for dex, rele 
						in enumerate(relevant)]
		return batch

class batch_data_pool(object):
	def __init__(self, *args, **kwargs):
		self.targets = args[0]
		self.trajectory = args[1].trajectory

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
			self.live_pool = lf.load_pkl_object(os.path.join(
								os.getcwd(), 'data_pools', 
								self.data_pool_ids[dex]))

		except: raise IndexError
		batch = [self._get_trajectory_(dex) for 
			dex in range(len(self.live_pool))]
		return batch

	def _get_trajectory_(self, traj_dex):

		def _wrap_(values, dex):
			sca = scalers(label = self.targets[dex])
			sca.scalers = values
			return sca

		relevant = self.live_pool[traj_dex]
		batch = [_wrap_(rele, dex) for dex, rele 
						in enumerate(relevant)]
		return batch

	def _rid_pool_(self, dex):
		if self.live_pool:
			print 'saving sub pool', dex
			lf.save_pkl_object(self.live_pool, 
				os.path.join(os.getcwd(), 'data_pools', 
							self.data_pool_ids[dex]))
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
		self.data_scalers = [data for data in data if not data is self]
		self.axis_labels = axes
		self.axis_values = [scalers(label = dat.label, 
			scalers = lfu.uniqfy(dat.scalers)) for dat in 
			self.data_scalers if dat.label in self.axis_labels]
		self.axis_defaults = [da.scalers[0] for da in self.axis_values]
		self.surf_targets = surfs
		self.reduced = None

	def make_surface(self, x_ax = '', y_ax = '', surf_target = ''):

		data = self.data_scalers
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
				in_slices.append([True for val in ax.scalers])

			else:
				in_slices.append([(val == ax_slices[ax_dex]) 
									for val in ax.scalers])

		in_every_slice = [(False not in row) for row in zip(*in_slices)]
		sub_surf = scalers_from_labels([surf_target])[0]
		sub_surf.scalers = [sur for sur, in_ in 
			zip(surf.scalers, in_every_slice) if in_]
		sub_axes = scalers_from_labels(self.axis_labels)
		for sub_ax, ax in zip(sub_axes, axes):
			sub_ax.scalers = lfu.uniqfy([val for val, in_ 
				in zip(ax.scalers, in_every_slice) if in_])

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

		if type(param) is types.DictionaryType:
			for subkey in [key for key in param.keys() if 
					isinstance(param[key], lfu.modular_object_qt)]:
				check_for_nested_contributors(subspaces, param[subkey])

	if not subspaces: return None, False
	space = merge_spaces(subspaces)
	space.parent = parent
	return space, True

def generate_coarse_parameter_space_from_fine(fine):

	def coerce_bounds(inbounds, orders):
		outbounds = [coerce_to_magnitude_order(bnd, dir_, orders) 
				for bnd, dir_ in zip(inbounds, ['down', 'up'])]
		return outbounds

	def coerce_to_magnitude_order(val, bounds, orders):

		def resolve_bounded(orders, val, bnds):
			bottom = orders.index(bnds[0])
			top = orders.index(bnds[1])
			#middle = int((bottom + top)/2.0)
			#return orders[middle]
			return orders[top - 1]

		def resolve_no_bounds(orders, val, dir_):
			if dir_ == 'up': bump = 1
			else: bump = -1
			try: resolved = 10.0**int(math.log10(val) + bump)
			except ValueError:
				if val == 0.0:
					if dir_ == 'up': resolved = 1.0
					else: resolved = 0.1

			return resolved

		fl = float(val)
		if bounds in ['down', 'up']:
			return resolve_no_bounds(orders, fl, bounds)
		else: return resolve_bounded(orders, fl, bounds)

	orders = [0.000000001, 0.00000001, 0.0000001, 0.000001, 
			0.00001, 0.0001, 0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 
					1000.0, 10000.0, 100000, 1000000, 10000000]
	coarse_subspaces = []
	for fine_subsp in fine.subspaces:
		coerced_bounds = coerce_bounds(fine_subsp.bounds, orders)
		coarse_subsp = one_dim_space(interface_template_p_space_axis(
			instance = fine_subsp.inst, key = fine_subsp.key, 
			p_sp_continuous = False, p_sp_bounds = coerced_bounds, 
			p_sp_increment = coerce_to_magnitude_order(
				fine_subsp.increment, coerced_bounds, orders)))
		coarse_subsp.inst.__dict__[coarse_subsp.key] =\
			coerce_to_magnitude_order(
				fine.subspaces[0].inst.__dict__[
				fine.subspaces[0].key], 'up', orders)
		coarse_subsp.scalers = orders[
				orders.index(coerced_bounds[0]):
				orders.index(coerced_bounds[1])+1]
		coarse_subspaces.append(coarse_subsp)

	if not coarse_subspaces: return None, False
	space = merge_spaces(coarse_subspaces)
	space.parent = fine.parent
	return space, True

class one_dim_space(object):

	def __init__(self, template, scalers_ = None):
		self.inst = template.instance
		self.key = template.key
		self.bounds = template.p_sp_bounds
		self.continuous = template.p_sp_continuous
		self.increment = template.p_sp_increment
		label = ' : '.join([template.instance.label, template.key])
		self.label = label
		if not self.continuous and not scalers_:
			scalers_ = np.arange(self.bounds[0], 
					self.bounds[1], self.increment)
			scalers_ = list(scalers_)
			if self.bounds[1] - scalers_[-1] >= self.increment:
				scalers_.append(scalers_[-1] + self.increment)

		self.scalers = scalers_

	def move_to(self, value):
		if not self.continous: pdb.set_trace()
		self.inst.__dict__[self.key] = value

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

class parameter_space(lfu.modular_object_qt):

	'''
	initialize with template to make a space
		templates are interface_template_p_space_axis objects
	or initialize with subsps to make a space
		subsps are one_dim_space objects
	the first overrides the second
	'''
	def __init__(self, base_obj = None, subspaces = [], 
							parent = None, steps = []): 

		if not base_obj is None:
			self.subspaces = []
			for template in base_obj.parameter_space_templates:
				if template.contribute_to_p_sp:
					self.subspaces.append(one_dim_space(template)) 

		else:
			self.subspaces = subspaces
			self.set_simple_space_lookup()

		self.steps = steps
		self.step_normalization = 10.0
		self.dimensions = len(self.subspaces)
		lfu.modular_object_qt.__init__(self, 
			#label = label, parent = parent)
			parent = parent)

	def get_start_position(self):
		location = [sp.inst.__dict__[sp.key] 
					for sp in self.subspaces]
		return parameter_space_location(location = location)

	def get_current_position(self):
		return [(axis.inst.label, axis.key, 
			str(axis.inst.__dict__[axis.key])) 
					for axis in self.subspaces]

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

	def set_start_pt(self):
		self.undo_level = 0
		for subsp in self.subspaces:
			rele_val = subsp.inst.__dict__[subsp.key]
			
			'''
			for subsubsp in subsp.subspaces:
				rele_val = subsubsp.base_obj.__dict__[
							subsubsp.base_template.name]
				if subsubsp.base_template.p_sp_continuous:
					check_rele_val = [rule(rele_val) for rule in 
						subsubsp.base_template.p_sp_continuous_rules]
					if False in check_rele_val:
						print 'initial value "' + str(rele_val) +\
							'" not found in continuous parameter' +\
								' space - adjusting to 0'
						subsubsp.base_obj.__dict__[
							subsubsp.base_template.name] = 0.0

					else:
						if subsubsp.base_template.conditioning(rele_val)\
												not in subsubsp.scalers:
							new_dex = int(len(subsubsp.scalers)/2)
							subsubsp.base_obj.__dict__[
								subsubsp.base_template.name] =\
											subsubsp.scalers[new_dex]
							print 'initial value "' + str(rele_val) +\
								'" not found in specified parameter' +\
									' space - adjusting to ' +\
										str(subsubsp.scalers[new_dex])
			'''

	def undo_step(self):
		try:
			#print 'undoing a step!'
			self.undo_level += 1
			self.steps.append(parameter_space_step(
				location = self.steps[-1].location, 
				initial = self.steps[-1].final, 
				final = self.steps[-1].initial))
			self.steps[-1].step_forward()

		except IndexError:
			print 'no steps to undo!'

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
		#type_ = type(self.subspaces[param_dex].inst.__dict__[
		#					self.subspaces[param_dex].key])
		old_value = self.subspaces[param_dex].inst.__dict__[
							self.subspaces[param_dex].key]
		space_leng = len(self.subspaces[param_dex].scalers)
		val_dex_rng = range(space_leng)
		try:val_dex = self.subspaces[param_dex].scalers.index(old_value)
		except ValueError:
			print 'discrete parameter was off of lattice'
			val_dex = int(space_leng/2)

		space_leng = len(self.subspaces[param_dex].scalers)
		step = abs(int(random.gauss(0, 
		#step = 1 + abs(int(random.gauss(0, 
			space_leng/self.step_normalization)*\
					(factor/self.initial_factor)))
		self.steps[-1].location.append((
			self.subspaces[param_dex].inst, 
			self.subspaces[param_dex].key))
		self.steps[-1].initial.append(old_value)
		if not direc: rand = random.random()
		else: rand = direc
		if rand < 0.5:
			val_dex = self.step_down_discrete(
					step, val_dex, val_dex_rng)

		else:
			val_dex = self.step_up_discrete(
				step, val_dex, val_dex_rng)

		param = self.subspaces[param_dex].scalers[val_dex]
		return param - old_value, old_value

	def set_up_continuous_step(self, param_dex, factor, direc):
		old_value = float(self.subspaces[param_dex].inst.__dict__[
									self.subspaces[param_dex].key])
		space_leng =\
			self.subspaces[param_dex].bounds[1] -\
			self.subspaces[param_dex].bounds[0]
		step = random.gauss(0, 
			space_leng/self.step_normalization)*\
					(factor/self.initial_factor)
		if direc:
			if not step/abs(step) == direc: step = -1.0 * step

		if old_value + step < self.subspaces[param_dex].bounds[0]:
			over_the_line = abs(step) -\
				abs(old_value - self.subspaces[param_dex].bounds[0])
			step = over_the_line - old_value

		if old_value + step > self.subspaces[param_dex].bounds[1]:
			over_the_line = abs(step) -\
				abs(self.subspaces[param_dex].bounds[1] - old_value)
			step = self.subspaces[param_dex].bounds[1] -\
								over_the_line - old_value

		self.steps[-1].location.append((
			self.subspaces[param_dex].inst, 
			self.subspaces[param_dex].key))
		self.steps[-1].initial.append(old_value)
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
			#even_odds = False, many_steps = len(last_ax_dexes)/4, 
			even_odds = False, many_steps = int(len(last_ax_dexes)), 
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

			else: direc = None
			if self.subspaces[param_dex].continuous:

				step, param = self.set_up_continuous_step(
								param_dex, factor, direc)
				self.steps[-1].final.append(step + float(param))

			else:
				step, param = self.set_up_discrete_step(
								param_dex, factor, direc)
				self.steps[-1].final.append(step + float(param))

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
			gui_give_p_sp_cont_disc_control = False, 
			p_sp_increment = 1.0):
		self.instance = instance
		self.key = key
		self.contribute_to_p_sp = contribute_to_p_sp
		self.gui_give_p_sp_control = gui_give_p_sp_control
		self.p_sp_continuous = p_sp_continuous
		self.p_sp_bounds = p_sp_bounds
		self.p_sp_increment = p_sp_increment
		self.gui_give_p_sp_cont_disc_control =\
				gui_give_p_sp_cont_disc_control
		self.mason = lgm.standard_mason(parent = self)
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

def scalers_from_labels(targeted):
	return [scalers(label = target) for target in targeted]

def bin_vectors_from_labels(targeted):
	return [bin_vectors(label = target) for target in targeted]

def sort_data_by_type(data, specifics = []):
	if not specifics: specifics = [dater.label for dater in data]
	sorted_data = {'scalers': {}, 'coords': {}}
	for dater in [dater for dater in data if dater.label in specifics]:
		if dater.tag == 'scaler':
			sorted_data['scalers'][dater.label] = dater.scalers

		elif dater.tag == 'coordinates':
			sorted_data['coords']['_'.join(dater.coords.keys())] = dater.coords

	return sorted_data

class metric(lfu.modular_object_qt):

	#ABSTRACT
	'''
	a metric takes two sets of data and runs some method which
	returns one scaler representing some sort of distance
	'''
	def __init__(self, *args, **kwargs):
		if not 'valid_base_classes' in kwargs.keys():
			global valid_metric_base_classes
			kwargs['valid_base_classes'] = valid_metric_base_classes

		if not 'base_class' in kwargs.keys():
			kwargs['base_class'] = lfu.interface_template_class(
									object, 'abstract metric')

		self.impose_default('best_measure', None, **kwargs)
		self.impose_default('display_threshold', 500, **kwargs)
		lfu.modular_object_qt.__init__(self, *args, **kwargs)
		self._children_ = []

	def finalize(self, *args, **kwargs):
		dat = self.data[0].scalers
		norm = max(dat)
		self.data[0].scalers = [val/norm for val in dat]

	def measure(self, *args, **kwargs):
		to_fit_to = args[0]
		run_data = args[1]
		best_flag = False
		labels = [[do.label for do in de] for de in args]
		run_data_domain = run_data[labels[1].index(labels[0][0])]
		run_data_codomain = run_data[labels[1].index(labels[0][1])]
		run_data_interped = scalers(label = 'interpolated result', 
			scalers = lm.linear_interpolation(run_data_domain.scalers, 
			run_data_codomain.scalers, to_fit_to[0].scalers, 'linear'))
		x_meas_bnds = (0, len(to_fit_to[0].scalers))
		meas = np.mean([diff for diff in 
			kwargs['measurement'](to_fit_to[1].scalers, 
				run_data_interped.scalers, x_meas_bnds, 
				to_fit_to[0].scalers) if not math.isnan(diff)])
		self.data[0].scalers.append(meas)
		if meas == min(self.data[0].scalers):
			self.best_measure = len(self.data[0].scalers) - 1
			best_flag = self.best_measure > self.display_threshold

		if best_flag:
		#if best_flag or kwargs['display']:
			print 'metric', self.label, 'measured', meas
			lgd.quick_plot_display(to_fit_to[0], 
				[to_fit_to[1], run_data_interped])

		return meas

class metric_slope_fit_quality(metric):

	def __init__(self, *args, **kwargs):
		if not 'label' in kwargs.keys():
			kwargs['label'] = 'slope metric'

		metric.__init__(self, *args, **kwargs)

	def initialize(self, *args, **kwargs):
		self.data = scalers_from_labels(['mean slope difference'])
		metric.initialize(self, *args, **kwargs)

	def measure(self, *args, **kwargs):
		kwargs['measurement'] = self.slope_differences
		metric.measure(self, *args, **kwargs)

	def slope_differences(self, *args, **kwargs):
		to_fit_to_y = args[0]
		runinterped = args[1]
		bounds = args[2]
		to_fit_to_x = args[3]
		runinterped_slope = [(runinterped[k] - runinterped[k - 1])\
					/(to_fit_to_x[k] - to_fit_to_x[k - 1]) 
					for k in range(1, len(to_fit_to_x))]
		to_fit_to_y_slope = [(to_fit_to_y[k] - to_fit_to_y[k - 1])\
							/(to_fit_to_x[k] - to_fit_to_x[k - 1]) 
							for k in range(1, len(to_fit_to_x))]
		return [abs(to_fit_to_y_slope[k] - runinterped_slope[k]) 
						for k in range(bounds[0], bounds[1] -1)]

class metric_integral_fit_quality(metric):

	def __init__(self, *args, **kwargs):
		if not 'label' in kwargs.keys():
			kwargs['label'] = 'integral metric'

		metric.__init__(self, *args, **kwargs)

	def initialize(self, *args, **kwargs):
		self.data = scalers_from_labels(['mean integral difference'])
		metric.initialize(self, *args, **kwargs)

	def measure(self, *args, **kwargs):
		kwargs['measurement'] = self.integral_differences
		metric.measure(self, *args, **kwargs)

	def integral_differences(self, *args, **kwargs):
		to_fit_to_y = args[0]
		runinterped = args[1]
		integral_diffs = abs(integrate(runinterped) - \
								integrate(to_fit_to_y))
		return [integral_diffs]

class metric_avg_ptwise_diff_on_domain(metric):

	def __init__(self, *args, **kwargs):
		if not 'label' in kwargs.keys():
			kwargs['label'] = 'pointwise difference metric'

		metric.__init__(self, *args, **kwargs)

	def initialize(self, *args, **kwargs):
		self.data = scalers_from_labels(['mean difference'])
		metric.initialize(self, *args, **kwargs)

	def measure(self, *args, **kwargs):
		kwargs['measurement'] = self.differences
		metric.measure(self, *args, **kwargs)

	def differences(self, *args, **kwargs):
		to_fit_to_y = args[0]
		runinterped = args[1]
		bounds = args[2]
		return [abs(to_fit_to_y[k] - runinterped[k]) 
				for k in range(bounds[0], bounds[1])]

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
		metric_slope_fit_quality, 
			'slope comparison metric'), 
	lfu.interface_template_class(
		metric_slope_fit_quality, 
			'integral comparison metric'), 
	lfu.interface_template_class(
		metric_slope_fit_quality, 
			'pointwise difference metric')]





