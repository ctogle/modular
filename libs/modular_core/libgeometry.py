import libs.modular_core.libfundamental as lfu
import libs.modular_core.libmath as lm
import libs.modular_core.libfiler as lf
import libs.modular_core.libsettings as lset

import itertools as it
import types
import random
import os
import time
import math
import numpy as np
from copy import deepcopy as copy
from scipy.integrate import simps as integrate

#import matplotlib.pyplot as plt
#plt.ion()
#plt.show()

import pdb

if __name__ == 'libs.modular_core.libgeometry':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'

'''
class scalers(object):
#Note: inheriting from lfu.modular_object here makes things SLOW!

	def __init__(self, label = 'another scaler'):
		self.scalers = []
		self.tag = 'scaler'
		self.label = label
'''

class scalers(object):

	def __init__(self, label = 'some scaler', scalers = []):
		self.label = label
		self.scalers = scalers
		self.tag = 'scaler'

class batch_scalers(object):

	def __init__(self, targets, label = 'batch of scalers'):
		self.batch_pool = []
		self.pool_names = targets
		self.current = 0

	#def append(self, value):
		#values are in order corresponding to targets
		#store them corresponding to self.pool_names
		#targets should always contain the same items as targets
		#reorder = []
		#for name in self.pool_names:
		#	dex = targets.index(name)
		#	reorder.append(value[dex])

		#self.batch_pool.append(reorder)
	#	self.batch_pool.append(value)
	#	self.high = len(self.batch_pool)

	#def extend(self, values):
	#	self.batch_pool.extend(values)
	#	self.high = len(self.batch_pool)

	def __iter__(self):
		print '__iter__ of batch scalers'
		#batch = [self._get_trajectory_(dex) for dex in range(len(self))]
		#return batch.__iter__()
		return [self._get_trajectory_(dex) for 
			dex in range(len(self.batch_pool))].__iter__()

	def next(self):
		if self.current > self.high:
			raise StopIteration

		else:
			pdb.set_trace()
			self.current += 1
			return self.current - 1

	#def __getitem__(self, key):
	#	print key, self
	#	return self.batch_pool.__getitem__(key)

	def get_batch(self):
		print 'get_batch', len(self.batch_pool)
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

class bin_vectors(object):
#Note: inheriting from lfu.modular_object here makes things SLOW!

	def __init__(self, label = 'another bin vector'):
		self.counts = [] #updated with a vector 1-1 with self.bins
		self.time = [] #updated once per capture
		self.bins = [] #set once
		self.tag = 'bin_vector'
		self.label = label

class surface_vector(object):

	def __init__(self, data = [], axes = [], 
			label = 'another surface vector'):
		self.tag = 'surface'
		self.label = label

		self.data_scalers = data
		self.axis_labels = axes
		self.reduced = None

	def make_surface(self, axis_defaults = [3.0, 3.0, 9.0], 
			x_ax = 'formation of x1 (rate is lambda1) : rate', 
			y_ax = 'formation of x2 (rate is lambda2) : rate', 
					surf_target = 'correlation coefficients'):

		data = self.data_scalers
		daters = [dater.label for dater in data]
		are_ax = [label in self.axis_labels for label in daters]
		axes = [copy(dater) for dater, is_ax in 
					zip(data, are_ax) if is_ax]
		ax_labs = [ax.label for ax in axes]
		surf = lfu.grab_mobj_by_name(surf_target, data)
		x_ax_dex = ax_labs.index(x_ax)
		y_ax_dex = ax_labs.index(y_ax)
		ax_slices = copy(axis_defaults)
		ax_slices[x_ax_dex] = None
		ax_slices[y_ax_dex] = None

		def make_reduction(ax_slices, reduct_dex, last_reduction):
			in_slice = [val == ax_slices[reduct_dex] for val in 
						last_reduction[0][reduct_dex].scalers]
			reduction = [[val for val, in_ in zip(ax.scalers, in_slice) 
								if in_] for ax in last_reduction[0]]
			subsp_axes = [lfu.uniqfy(red) for red in reduction]
			for axi, sub_axi in zip(last_reduction[0], subsp_axes):
				axi.scalers = sub_axi

			surf = scalers_from_labels([surf_target])[0]
			surf.scalers = [sur for sur, in_ in 
				zip(last_reduction[1].scalers, in_slice) if in_]
			return (last_reduction[0], surf)

		reduced = (axes, surf)
		for ax_dex in range(len(axes)):
			if not ax_dex in [x_ax_dex, y_ax_dex]:
				reduced = make_reduction(ax_slices, ax_dex, reduced)

		self.reduced = reduced

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

			nested = par.__dict__.partition['p_space contributors']
			for key in nested.keys():
				check_for_nested_contributors(subspaces, nested[key])

		except: pass

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

class one_dim_space(scalers):

	def __init__(self, template):
		self.inst = template.instance
		self.key = template.key
		self.bounds = template.p_sp_bounds
		label = ' : '.join([template.instance.label, template.key])
		scalers.__init__(self, label = label)

	def move_to(self, value):
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

class parameter_space(lfu.modular_object_qt):

	'''
	initialize with template to make a space
		templates are interface_template_p_space_axis objects
	or initialize with subsps to make a space
		subsps are one_dim_space objects
	the first overrides the second
	'''
	#def __init__(self, label = 'another parameter space', 
	def __init__(self, 
			base_obj = None, subspaces = [], 
			parent = None, steps = []): 

		#initial_factor = 1.0, steps = []):
		#self.rand_1 = random.random()
		#self.initial_factor = initial_factor

		if not base_obj is None:
			self.subspaces = []
			for template in base_obj.parameter_space_templates:
				if template.contribute_to_p_sp:
					self.subspaces.append(one_dim_space(template)) 

		else:
			self.subspaces = subspaces
			self.set_simple_space_lookup()

		self.steps = steps
		self.dimensions = len(self.subspaces)
		lfu.modular_object_qt.__init__(self, 
			#label = label, parent = parent)
			parent = parent)

	def to_string(self):
		lines = []
		#ENCODE SOMETHING LIKE THE FOLLOWING
		#	workers : 8
		pdb.set_trace()
		return lines

	def get_start_position(self):
		location = [sp.inst.__dict__[sp.key] 
					for sp in self.subspaces]
		return parameter_space_location(location = location)

	def get_current_position(self):
		vector = [(axis.name, 
				str(axis.base_obj.__dict__[axis.base_template.name])) 
										for axis in self.subspaces]
		return vector

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

	def undo_step(self):
		try:
			print 'undoing a step!'
			self.undo_level += 1
			self.steps.append(
					parameter_space_step(location = self.steps[-1].location, 
											initial = self.steps[-1].final, 
											final = self.steps[-1].initial))
			self.steps[-1].step_forward()

		except IndexError:
			print 'no steps to undo!'

	def step_up_discrete(self, step, dex, rng):
		if dex + step not in rng:
			print 'i cant step up anymore!'
			dex = rng[-1]
			#dex = self.step_down(step, dex, rng)

		else:
			dex += step

		return dex

	def step_down_discrete(self, step, dex, rng):
		if dex - step not in rng:
			print 'i cant step down anymore!'
			dex = rng[0]
			#dex = self.step_up(step, dex, rng)

		else:
			dex -= step

		return dex

	def set_up_discrete_step(self, param_dex, factor):
		param = self.subspaces[param_dex].base_obj.__dict__[
				self.subspaces[param_dex].base_template.name]
		val_dex_rng = range(len(self.subspaces[param_dex].scalers))
		try:
			val_dex = self.subspaces[param_dex].scalers.index(param)

		except ValueError:
			print 'step was out of bounds - adjust?'
			pdb.set_trace()
			val_dex = int(len(val_dex_rng)/2)

		step = 1 + int(factor)
		print 'stepped: ' + str(step)
		self.steps.append(
				parameter_space_step(
					location = (self.subspaces[param_dex].base_obj, 
								self.subspaces[param_dex].base_template.name), 
								initial = param))
		self.parent.last_subsp_bias =\
			self.subspaces[param_dex].base_template.subsp_tag
		return val_dex, val_dex_rng, step, param

	def take_discrete_step(self, par_dex, val_dex):
		param =	self.subspaces[par_dex].scalers[val_dex]
		self.steps[-1].final = param
		self.steps[-1].step_forward()
		print 'now its this: ' + str(param)

	def set_up_continuous_step(self, param_dex, factor, direc):
		old_value = self.subspaces[param_dex].base_obj.__dict__[
					self.subspaces[param_dex].base_template.name]
		#space_leng = len(self.subspaces[param_dex].scalers)
		space_leng = self.subspaces[param_dex].base_template.p_sp_bounds[1] -\
						self.subspaces[param_dex].base_template.p_sp_bounds[0]
		space_leng *= self.subspaces[param_dex].base_template.p_sp_step_order
		print 'parameter: ' + str(self.subspaces[param_dex].name) + ' with space leng: ' + str(space_leng)
		step = random.gauss(0, space_leng/5.0)*\
					(factor/self.initial_factor)
		#if direc != None:
		#	step = abs(step)*direc

		self.steps[-1].location.append((self.subspaces[param_dex].base_obj, 
						self.subspaces[param_dex].base_template.name))
		self.steps[-1].initial.append(old_value)
		#self.steps.append(
		#		parameter_space_step(
		#			location = (self.subspaces[param_dex].base_obj, 
		#				self.subspaces[param_dex].base_template.name), 
		#				initial = old_value))
		#self.parent.last_subsp_bias =\
		#	self.subspaces[param_dex].base_template.subsp_tag
		
		print 'stepped: ' + str(step) + ' | ' + str(factor/self.initial_factor)
		return step, old_value

	#def take_continuous_step(self, par_dex, param, step):
	def take_continuous_step(self, par_dexes, params):
		#self.steps[-1].final = param + step
		self.steps[-1].final = []
		for k in range(len(params)):
			self.steps[-1].final.append(params[k][0] + params[k][1])
			rules = self.subspaces[par_dexes[k]].\
					base_template.p_sp_continuous_rules
			fixes = self.subspaces[par_dexes[k]].\
					base_template.p_sp_continuous_fixes
			for j in range(len(rules)):
				if not rules[j](self.steps[-1].final[-1]):
					self.steps[-1].final[-1] = fixes[j](self.steps[-1].final[-1])

		self.steps[-1].step_forward()
		#print 'now its continuously this: ' + str(self.steps[-1].final)

	def take_biased_step_along_axis(self, factor = 1.0, 
					bias = 10.0, pref_subsp_tag = None, flip_dirs = False):
		if pref_subsp_tag != None:
			pref_ax_dexes = [dex for dex in range(len(self.subspaces)) 
						if self.subspaces[dex].base_template.subsp_tag 
													== pref_subsp_tag]
			print 'the preferred axes! ' + str(pref_ax_dexes)
			self.set_simple_space_lookup(pref_ax_dexes, bias)
			self.take_proportional_step(factor, even_odds = False)

		else:
			try:
				#last_ax_dex = [sp.base_obj for sp in 
				#				self.subspaces].index(
				#				self.steps[-1].location[0])
				objs = [sp.base_obj for sp in self.subspaces]
				step_objs = [local[0] for local in self.steps[-1].location]
				last_ax_dexes = [objs.index(obj) for obj in step_objs]
				last_ax_direcs = [(self.steps[-1].final[k] - self.steps[-1].initial[k])\
									/abs(self.steps[-1].final[k] - self.steps[-1].initial[k]) 
									for k in range(len(self.steps[-1].initial))]
				if flip_dirs:
					last_ax_direcs = [val*-1.0 for val in last_ax_dexes]

				print 'lasting leng: ' + str(last_ax_dexes)

			except ZeroDivisionError:
				print 'its probably time to call it quits....'
				print 'failed to continue old step!'
				self.take_proportional_step(factor)
				return

			except:
				print 'failed to continue old step!'
				pdb.set_trace()
				self.take_proportional_step(factor)
				return

			self.set_simple_space_lookup(last_ax_dexes, bias)
			self.take_proportional_step(factor, even_odds = False, many_steps = len(last_ax_dexes), last_ax_pairs = zip(last_ax_dexes, last_ax_direcs))
			print 'biasing step old fashioned way!'

	#BROKEN FUNCTION!!
	def continue_along_axis(self, factor = 1.0):
		try:
			param_dex = [sp.base_obj for sp in 
							self.subspaces].index(
							self.steps[-1].location[0])

		except IndexError:
			print 'failed to continue old step!'
			pdb.set_trace()
			self.take_proportional_step(factor)
			return

		if self.subspaces[param_dex].base_template.p_sp_continuous:
			step, param = self.set_up_continuous_step(
									param_dex, factor)
			self.take_continuous_step(param_dex, param, step)

		else:
			val_dex, val_dex_rng, step, param = self.set_up_discrete_step(
														param_dex, factor)
			print 'continuing old step from: ' + str(param)
			#self.steps.append(
			#		parameter_space_step(
			#				location = self.steps[-1].location, 
			#				initial = self.steps[-1].final))
			if self.rand_1 < 0.5:
				val_dex = self.step_down(step, val_dex, val_dex_rng)

			elif self.rand_1 > 0.5:
				val_dex = self.step_up(step, val_dex, val_dex_rng)

			self.take_discrete_step(param_dex, val_dex)

	def take_proportional_step(self, factor = 1.0, 
			even_odds = True, many_steps = 1, last_ax_pairs = None):
		if even_odds:
			self.set_simple_space_lookup()

		#self.rand_1 = random.random()
		self.rands = [random.random() for k in range(many_steps)]
		self.rand_lookup = random.random()
		#param_dex = LM.pick_value_from_unsorted_prob_distrib(
		#					self.param_lookup, self.rand_lookup)
		#param_dex = [self.rand_lookup < lookup 
		#			for lookup in self.param_lookup].index(True)


		param_dexes = self.lookup_distinct_axes(many_steps)

		#param_dexes = [[rand < lookup 
		#				for lookup in self.param_lookup].index(True) for rand in self.rands]
		try:
			last_axes, last_direcs = zip(*last_ax_pairs)

		except:
			last_axes = []
			last_direcs = []

		step_param_collection = []
		self.steps.append(
				parameter_space_step(
					location = [], 
					initial = []))
		for param_dex in param_dexes:
			if self.subspaces[param_dex].base_template.p_sp_continuous:
				if param_dex in last_axes:
					direc = last_direcs[last_axes.index(param_dex)]

				else:
					direc = None

				step, param = self.set_up_continuous_step(
									param_dex, factor, direc)
				#self.take_continuous_step(param_dex, param, step)
				step_param_collection.append((step, param))

			else:
				val_dex, val_dex_rng, step, param = \
					self.set_up_discrete_step(param_dex, factor)

				print 'taking new step from: ' + str(param)
				#self.steps.append(
				#		parameter_space_step(
				#			location = (self.subspaces[param_dex].base_obj, 
				#						self.subspaces[param_dex].base_template.name), 
				#						initial = param))
				if val_dex is val_dex_rng[-1] or self.rand_1 < 0.5:
					val_dex = self.step_down(step, val_dex, val_dex_rng)

				elif val_dex is val_dex_rng[0] or self.rand_1 > 0.5:
					val_dex = self.step_up(step, val_dex, val_dex_rng)

				self.take_discrete_step(param_dex, val_dex)

		self.take_continuous_step(param_dexes, step_param_collection)

	def lookup_distinct_axes(self, many_steps):
		dexes = []
		#lookup = copy(self.param_lookup)
		while len(dexes) < many_steps:
			rand = random.random()
			new_dex = [rand < lup for lup in self.param_lookup].index(True)
			if not new_dex in dexes:
				dexes.append(new_dex)
			#[val - lookup[dexes[-1]] for val in lookup[dexes[-1] + 1:]]
			#del lookup[dexes[-1]]

		print 'dexes: ' + str(dexes)
		#pdb.set_trace()
		return dexes

class interface_template_p_space_axis(lfu.interface_template_new_style):

	def __init__(self, instance = None, key = None, parent = None, 
			visible_attributes = ['reference', 'linkages'], 
			contribute_to_p_sp = False, gui_give_p_sp_control = True, 
			p_sp_continuous = True, p_sp_bounds = [1, 10], 
			gui_give_p_sp_cont_disc_control = False):
		self.instance = instance
		self.key = key
		self.contribute_to_p_sp = contribute_to_p_sp
		self.gui_give_p_sp_control = gui_give_p_sp_control
		self.p_sp_continuous = p_sp_continuous
		self.p_sp_bounds = p_sp_bounds
		self.gui_give_p_sp_cont_disc_control =\
				gui_give_p_sp_cont_disc_control
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

	def set_settables(self, *args, **kwargs):
		#self.handle_widget_inheritance(*args, **kwargs)
		self.widg_templates = []
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['check_set'], 
				instances = [[self]], 
				keys = [['contribute_to_p_sp']], 
				labels = [['Contribute to Parameter Space']], 
				append_instead = [False], 
				box_labels = ['Parameter Space']))
		self.rewidget(False)
		#lfu.modular_object_qt.set_settables(
		#		self, *args, from_sub = True)

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
		use = lset.get_setting('mapparameterspace')
		lfu.plan.__init__(self, label = label, 
			parent = parent, use_plan = use)

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
	def __init__(self, label = 'another metric', bRelevant = True, 
		parent = None, data = [], source_1 = None, source_2 = None, 
		domain_dater_id_1 = None, domain_dater_id_2 = None, 
		codomain_dater_ids_1 = [], codomain_dater_id_1 = None, 
		codomain_dater_ids_2 = [], codomain_dater_id_2 = None, 
		valid_base_classes = None, base_class = None):
		if valid_base_classes is None:
			global valid_criterion_base_classes
			valid_base_classes = valid_criterion_base_classes

		if base_class is None:
			base_class = lfu.interface_template_class(
							object, 'abstract metric')

		self.bRelevant = bRelevant
		self.source_1 = source_1
		self.source_2 = source_2
		self.domain_dater_id_1 = domain_dater_id_1
		self.domain_dater_id_2 = domain_dater_id_2
		self.codomain_dater_ids_1 = codomain_dater_ids_1
		self.codomain_dater_ids_2 = codomain_dater_ids_2
		self.codomain_dater_id_1 = codomain_dater_id_1
		self.codomain_dater_id_2 = codomain_dater_id_2
		lfu.modular_object_qt.__init__(self, label = label, data = data, 
							parent = parent, base_class = base_class, 
							valid_base_classes = valid_base_classes)

	def initialize(self):
		pass
		#self.data = lgeo.scalers_from_labels(self.codomain_dater_ids)

	def grab_data_attribute(self, data_obj, id_y):
		
		dex_x = [dater.name for dater in data_obj.data].index(
										self.compare_to_id_x)
		dex_y = [dater.name for dater in data_obj.data].index(id_y)
		dater_x = data_obj.data[dex_x]
		dater_y = data_obj.data[dex_y]
		return dater_x, dater_y

	'''
	def display_trajectory(self, x_axis, y_values_1, y_values_2):
		plt.plot(x_axis, y_values_1)
		plt.plot(x_axis, y_values_2)
		plt.draw()
		time.sleep(2)
		plt.close()
	'''

	def find_bounds(x_axis_1, x_axis_2):
		bounds = (	max(x_axis_1[0], x_axis_2[0]), 
					min(x_axis_1[-1], x_axis_2[-1])	)
		print 'valid bounds: ' + str(bounds)
		return bounds

	def measure(self):
		if not self.source_1 is None and not self.source_2 is None:
			pdb.set_trace()
		'''
		if self.compare_to is not None:
			to_compare_x, to_compare_y_list = self.to_compare
			for k in range(len(self.compare_to_id_y_list)):
				to_compare_y = to_compare_y_list[[dater.name 
					for dater in to_compare_y_list].index(
									self.compare_to_id_y[k])]
				compare_to_x, compare_to_y = self.grab_data_attribute(
							self.compare_to, self.compare_to_id_y[k])
				#self.compare_to_x, _y should be data from pkl or whatever
				compare_to_y = LM.linear_interpolation(
										self.compare_to_x.scalers, 
										self.compare_to_y.scalers, 
										to_compare_x.scalers, 'linear')
				#does linear interpolation allow for bounds?
				try:
					bad_dex = [math.isnan(val) for val 
								in compare_to_y].index(True)
					compare_to_y = compare_to_y[:bad_dex]
					to_compare_x.scalers = to_compare_x.scalers[:bad_dex]
					to_compare_y.scalers = to_compare_y.scalers[:bad_dex]

				except ValueError:
					pass

				bounds = self.find_bounds(self.compare_to_x.scalers, 
												to_compare_x.scalers)
				measurement = self.make_measurement(
								to_compare_x.scalers, 
								to_compare_y.scalers, 
								compare_to_y, bounds)
				self.data[k].scalers.append(measurement)
				if self.show_trajectory:
					self.display_trajectory(to_compare_x.scalers, 
								compare_to_y, to_compare_y.scalers)
		'''

	#to_compare_y is a list of recent resultant y_values
	#compare_to_y is an interpolated list of y_values 
	#	from data object belonging to the metric
	#returns a tuple of measurements indicating quality of fit

	#def make_measurement(self, to_compare_x, 
	#		to_compare_y, compare_to_y, bounds = None):
	#	return None
		
	def set_settables(self, *args, **kwargs):
		ensem = args[0]
		frame = args[1]
		recaster = lgm.recasting_mason(frame)
		self.handle_widget_inheritance(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widget_layout = 'vert', 
				key = ['label'], 
				instance = [self], 
				widget = ['text'],
				box_label = 'Metric Name', 
				initial = [self.label], 
				sizer_position = (0, 0)))
		classes = [template._class for template 
					in self.valid_base_classes]
		tags = [template._tag for template 
				in self.valid_base_classes]
		self.widg_templates.append(
			lgm.interface_template_gui(
				widget_mason = recaster, 
				widget_layout = 'vert', 
				key = ['_class'], 
				instance = [[self.base_class, self]], 
				widget = ['rad'], 
				hide_none = [True], 
				box_label = 'Metric Type', 
				initial = [self.base_class._tag], 
				possibles = [tags], 
				possible_objs = [classes], 
				sizer_position = (1, 0)))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widget_layout = 'vert', 
				instance = [	[self]	], 
				key = [	['bRelevant']	], 
				gui_labels = [	['use this metric']	], 
				initial = [	[self.bRelevant]	], 
				append_instead = [False], 
				widget = ['check_set'],
				box_label = 'Relevance', 
				sizer_position = (2, 0)))
		'''
		self.templates.append(
			lfu.interface_template(
					name = 'compare_to', 
					instance = self, 
					gui_widg = 'fetch_obj', 
					gui_label = 'Grab Some Data', 
					sizer_position = (0, 0), 
					initial_valuable = self.compare_to, 
					diag_class = LGDIG.load_pkl_dialog))
		if self.compare_to is not None:
			compare_to_dater_names = [dater.name for dater 
									in self.compare_to.data]

		else:
			compare_to_dater_names = []

		self.templates.append(
			lfu.interface_template(
					name = 'compare_to_id_x', 
					instance = self, 
					gui_widg = 'rad', 
					gui_label = 'Data To Compare To (x-axis)', 
					sizer_position = (0, 1), 
					values = compare_to_dater_names,
					valuables = compare_to_dater_names, 
					initial_value = self.compare_to_id_x))
		self.templates.append(
			lfu.interface_template(
					name = 'compare_to_id_y_list', 
					instance = self, 
					gui_widg = 'check_list', 
					gui_label = 'Data To Compare To (y-axis)', 
					sizer_position = (0, 2), 
					values = compare_to_dater_names,
					valuables = compare_to_dater_names, 
					initial_value = self.compare_to_id_y_list))
		print '\n'
		print self.compare_to_id_y_list
		print compare_to_dater_names
		print '\n'
		'''

class metric_slope_fit_quality(metric):

	def __init__(self, label = 'another slope metric', 
			parent = None, data = [], source_1 = None, source_2 = None, 
			domain_dater_id_1 = None, domain_dater_id_2 = None, 
			codomain_dater_ids_1 = [], codomain_dater_id_1 = None, 
			codomain_dater_ids_2 = [], codomain_dater_id_2 = None, 
			slope_bias_factor = 10000.0):
		self.slope_bias_factor = slope_bias_factor
		metric.__init__(self, label = label, parent = parent, 
			data = data, source_1 = source_1, source_2 = source_2, 
			domain_dater_id_1 = domain_dater_id_1, 
			domain_dater_id_2 = domain_dater_id_2, 
			codomain_dater_ids_1 = codomain_dater_ids_1, 
			codomain_dater_id_1 = codomain_dater_id_1, 
			codomain_dater_ids_2 = codomain_dater_ids_2, 
			codomain_dater_id_2 = codomain_dater_id_2)

	def make_measurement(self, compare_x, 
			to_compare_y, compare_to_y, bounds = None):
		to_slope = [(to_compare_y[k] - to_compare_y[k - 1])\
					/(compare_x[k] - compare_x[k - 1]) 
						for k in range(1, len(compare_x))]
		slope_to = [(compare_to_y[k] - compare_to_y[k - 1])\
					/(compare_x[k] - compare_x[k - 1]) 
						for k in range(1, len(compare_x))]
		sign_bias = [1.0]*len(to_slope)
		slope_sign_agreement = [not abs(sum([to_s])) < max([s_to]) 
						for to_s in to_slope for s_to in slope_to]
		for agreement, bias in slope_sign_agreement, sign_bias:
			if not agreement:
				bias *= self.slope_bias_factor

		slope_differences = [abs(to_slope[k] - slope_to[k])*sign_bias[k] 
										for k in range(len(to_slope))]
		return slope_differences

	def set_settables(self, *args, **kwargs):
		ensem = args[0]
		frame = args[1]
		self.handle_widget_inheritance(*args, from_sub = False)
		'''
		self.widg_templates.append(
			lgm.interface_template_gui(
						widget_layout = 'vert', 
						key = [	'max_time'	], 
						instance = [self], 
						widget = ['text'],
						box_label = 'Max Simulation Time', 
						initial = [self.max_time], 
						sizer_position = (0, 2)))
		'''
		super(metric_slope_fit_quality, self).set_settables(
									*args, from_sub = True)

class metric_integral_fit_quality(metric):

	def __init__(self, *args, **kwargs):
		if not 'label' in kwargs.keys():
			kwargs['label'] = 'another integral metric'

		metric.__init__(self, *args, **kwargs)

	def make_measurement(self, to_compare_y, 
				compare_to_y, bounds = None):
		integral_diffs = abs(integrate(to_compare_y) - \
								integrate(compare_to_y))
		return integral_diffs

class metric_avg_ptwise_diff_on_domain(metric):

	def __init__(self, *args, **kwargs):
		if not 'label' in kwargs.keys():
			kwargs['label'] = 'pointwise difference metric', 

		metric.__init__(self, *args, **kwargs)

	'''
	def measure(self):
		if self.fit_to is not None:
			to_fit_x, to_fit_y_list = self.to_fit
			#total_measure = 0.0
			measures = []
			for fit_to_id_y in self.fit_to_id_y_list:
				to_fit_y = to_fit_y_list[[dater.name 
						for dater in to_fit_y_list].index(fit_to_id_y)]
				self.fit_to_id_y = fit_to_id_y
				self.fit_to_x, self.fit_to_y = self.grab_data_attribute(
															self.fit_to)
				#self.fit_to_x, _y should be data from pkl or whatever
				fit_to_y = LM.linear_interpolation(
										self.fit_to_x.scalers, 
										self.fit_to_y.scalers, 
										to_fit_x.scalers, 'linear')
				x_meas_bnds = (0, len(to_fit_x.scalers))
				x_meas_differences =\
					[abs(to_fit_y.scalers[k] - fit_to_y[k]) 
						for k in range(x_meas_bnds[0], x_meas_bnds[1])]
					#[math.sqrt((to_fit_y.scalers[k] - fit_to_y[k])**2) 
					#	for k in range(x_meas_bnds[0], x_meas_bnds[1])]
				x_meas_init = np.mean(x_meas_differences[0:10])
				try:
					x_meas_integral_difference =\
						abs(integrate(to_fit_y.scalers) - \
							integrate([val for val in fit_to_y 
										if math.isnan(val) == False]))

				except IndexError:
					x_meas_integral_difference = 1e12

				x_meas_differences = [diff for diff in x_meas_differences 
											if math.isnan(diff) == False]
				#print 'meas leng: ' + str(len(x_meas_differences))
				if len(x_meas_differences) <= 100:
					#pdb.set_trace()
					measures.append((1e12, fit_to_id_y, 0.0))
					continue
				#total_measure += np.mean(x_meas_differences)
				measures.append((np.mean(x_meas_differences), 
						#fit_to_id_y, len(x_meas_differences)))
						fit_to_id_y, len(x_meas_differences), 
						x_meas_integral_difference, x_meas_init))

				plt.plot(to_fit_x.scalers, fit_to_y)
				plt.plot(to_fit_x.scalers, to_fit_y.scalers)

				#x_measurement corresponds to interpolation along x-axes
				#	so differences is in terms of y values
			#return total_measure
			try:
				measures.append((10000.0*abs(to_fit_x.scalers[-1] -\
									self.fit_to_x.scalers[-1]), 
										'time-span comparison', 
										len(to_fit_x.scalers), 0.0, 1e10))
			except:
				measures.append((100000000, fit_to_id_y, 0, 0.0, 1e10))

			plt.draw()
			time.sleep(2)
			plt.close()
			return measures

		else:
			print 'metric is missing its fit_to data!'
			return None
	'''

	def make_measurement(self, *args, **kwargs):
		pdb.set_trace()

class scalers_exponential_curve(lfu.modular_object_qt):

	def __init__(self, parent = None, 
			label = 'another exponential curve', domain = range(100), 
						exp_fact = 1, y_offset = 0, x_offset = 0):
		self.domain = domain
		self.exp_fact = exp_fact
		self.y_offset = y_offset
		self.x_offset = x_offset
		self.parent = parent
		self.set_curve()
		lfu.modular_object_qt.__init__(self, 
			label = label, parent = parent)

	def fix_lists(self):

		def fix_to_list(valued):
			if type(valued) != types.ListType:
				valued = [float(valued) for x in self.domain]

			elif len(valued) >= len(self.domain):
				valued = [float(valued[k]) for k 
					in range(len(self.domain))]

			else:
				valued.extend([float(valued)[-1]]*\
					(len(self.domain) - len(valued)))

			return valued

		self.exp_fact = fix_to_list(self.exp_fact)
		self.x_offset = fix_to_list(self.x_offset)
		self.y_offset = fix_to_list(self.y_offset)

	def set_curve(self):
		self.fix_lists()
		self.scalers = [math.exp(exp * (x - x_0)) + y_0 for 
						exp, x, x_0, y_0 in zip(self.exp_fact, 
					self.domain, self.x_offset, self.y_offset)]
		#self.scalers = [math.exp(self.exp_fact[k]*\
		#					self.domain[k] - self.x_offset[k]) +\
		#						self.y_offset[k] 
		#						for k in range(len(self.domain))]

	def set_settables(self, *args, **kwargs):
		ensem = args[0]
		frame = args[1]
		self.set_curve()
		self.handle_widget_inheritance(*args, from_sub = False)
		self.widg_templates.append(
			lgm.interface_template_gui(
					widget_layout = 'vert', 
					key = ['exp_fact'], 
					instance = [self], 
					widget = ['text'], 
					box_label = 'Exponent Coefficient', 
					initial = [self.exp_fact], 
					value = [[True, False]], 
					sizer_position = (0, 0), 
					minimum_size = (128, 24)))
		self.widg_templates.append(
			lgm.interface_template_gui(
					widget_layout = 'vert', 
					key = ['x_offset'], 
					instance = [self], 
					widget = ['text'], 
					box_label = 'Horizontal Offset', 
					initial = [self.x_offset], 
					value = [[True, False]], 
					sizer_position = (0, 1), 
					minimum_size = (128, 24)))
		self.widg_templates.append(
			lgm.interface_template_gui(
					widget_layout = 'vert', 
					key = ['y_offset'], 
					instance = [self], 
					widget = ['text'], 
					box_label = 'Vertical Offset', 
					initial = [self.y_offset], 
					value = [[True, False]], 
					sizer_position = (1, 1), 
					minimum_size = (128, 24)))
		self.widg_templates.append(
			lgm.interface_template_gui(
					widget_layout = 'vert', 
					key = ['domain'], 
					instance = [self], 
					widget = ['text'], 
					box_label = 'Domain', 
					initial = [self.domain], 
					value = [[True, False]], 
					sizer_position = (1, 0), 
					minimum_size = (128, 24)))
		self.widg_templates.append(
			lgm.interface_template_gui(
					widget_layout = 'vert', 
					key = ['exp_fact'], 
					instance = [self], 
					widget = ['text'], 
					box_label = 'Exponent Coefficient', 
					initial = [self.exp_fact], 
					value = [[True, True]], 
					sizer_position = (2, 0), 
					minimum_size = (400, 36)))
		self.widg_templates.append(
			lgm.interface_template_gui(
					widget_layout = 'vert', 
					key = ['x_offset'], 
					instance = [self], 
					widget = ['text'], 
					box_label = 'Horizontal Offset', 
					initial = [self.x_offset], 
					value = [[True, True]], 
					sizer_position = (2, 1), 
					minimum_size = (400, 36)))
		self.widg_templates.append(
			lgm.interface_template_gui(
					widget_layout = 'vert', 
					key = ['y_offset'], 
					instance = [self], 
					widget = ['text'], 
					box_label = 'Vertical Offset', 
					initial = [self.y_offset], 
					value = [[True, True]], 
					sizer_position = (3, 1), 
					minimum_size = (400, 36)))
		self.widg_templates.append(
			lgm.interface_template_gui(
					widget_layout = 'vert', 
					key = ['domain'], 
					instance = [self], 
					widget = ['text'], 
					box_label = 'Domain', 
					initial = [self.domain], 
					value = [[True, True]], 
					sizer_position = (3, 0), 
					minimum_size = (400, 36)))



#THESE ARE IN THE WRONG PLACE
def array_to_string(arr):
	'''
	file_str = StringIO()
	[file_str.write(`value`) for value in arr]
	return file_str.getvalue()
	'''
	#this should use cstrings....
	try:
		string = ' '
		string = string.join([str(value) for value in arr])
		string += ' '

	except:
		pdb.set_trace()

	return string

def coords_to_string(x, y, z):
	concat = x + y + z
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





#THESE HAVEN'T BEEN UPDATED/DEBUGGED
class coordinates(lfu.modular_object_qt):

	#*args should be a list of scalers
	def __init__(self, dims = int(3), args = []):
		self.coords = {}
		for k in range(min(len(args), dims)):
			self.coords[args[k].name] = args[k].scalers
		
		self.name = '_'.join(self.coords.keys())
		self.tag = 'coordinates'

class piecewise_curve(scalers):

	def __init__(self, parent = None, 
					name = 'another piecewise curve', 
					values = range(100)):
		scalers.__init__(self, name)
		self.parent = parent
		values = [0] + [0.5]*100 + [1]*50 + [2]*40 + [3]*30 + [4]*20 + [5]*10 +\
				range(5, 150) +\
				range(150, 400, 2) +\
				range(400, 600, 4) +\
				range(600, 800, 6) + range(800, 1000, 7)
		print 'lenght of cooling curve: ' + str(len(values))
		values.reverse()
		#values = [int(val/4) for val in values]
		#values = [25.0, 24.0, 23.0, 22.0, 21.0, 20.0, 19.0, 18.0, 17.0, 16.0, 15.0, 14.0, 14.0, 13.0, 13.0, 12.0, 12.0, 11.0, 11.0, 10.0, 10.0, 9.0, 9.0, 9.0, 8.0, 8.0, 8.0, 7.0, 7.0, 7.0, 6.0, 6.0, 6.0, 5.0, 5.0, 5.0, 4.0, 4.0, 4.0, 4.0, 3.0, 3.0, 3.0, 3.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0]
		self.scalers = values
		self.set_settables()

	def set_settables(self):
		self.templates = []
		self.templates.append(
			lfu.interface_template(
					name = 'scalers', 
					instance = self, 
					gui_widg = 'text_list', 
					gui_label = 'Values', 
					sizer_position = (0, 0), 
					initial_value = self.scalers, 
					conditioning = LG.vals_str_to_arr, 
					spare_conditioning = float))




#THIS SHOULD BE BROKEN MEOW
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
			self.location[k][0].__dict__[self.location[k][1]] = self.final[k]
			print 'actually set value to: ' + str(self.final[k])

	def step_backward(self):
		for k in range(len(self.location)):
			self.location[k][0].__dict__[self.location[k][1]] = self.initial[k]
			print 'actually reset value to: ' + str(self.final[k])




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





