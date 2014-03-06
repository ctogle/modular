import libs.modular_core.libfundamental as lfu
from libs.modular_core.libfundamental import modular_object_qt as modular_object
import libs.modular_core.libsimcomponents as lsc
import libs.modular_core.libmath as lm
import libs.modular_core.libgeometry as lgeo
import libs.modular_core.libfitroutine as lfr
import libs.modular_core.libpostprocess as lpp
import libs.modular_core.libcriterion as lc

import types
import random
from math import log as log

import pdb

if __name__ == 'libs.modules.libchemical':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is the chemical module library!'

#UNCOMMENT TO ADD THIS MODULE BACK INTO MODULAR!
#module_name = 'chemical'
run_param_keys = [	'End Criteria', 
					'Capture Criteria', 
					'Plot Targets', 
					'Fit Routines', 
					'Post Processes', 
					'Parameter Space Map', 
					'Multiprocessing', 
					'Output Plans'	] +\
				[	'Reactions', 'Species', 'Injections'	]

def generate_gui_templates(frame, ensemble):
	select_labels = [None]*11
	for k in range(len(select_labels)):
		if frame.selected_objs[k] is not None:
			select_labels[k] = frame.selected_objs[k].label

	panel_template_lookup = []
	plot_target_labels = ['iteration', 'time'] +\
			ensemble.run_params['species'].keys()
	ensemble.simulation_plan.set_settables(*frame.settables_infos, 
							end_crit_dex = 0, capt_crit_dex = 1, 
							target_labels = plot_target_labels)
	panel_template_lookup.append(('end_criteria', 
		lgm.interface_template_gui(
			frame = frame, 
			widget_mason = frame.mason, 
			key = 'end_criteria', 
			widget_templates =\
				ensemble.simulation_plan.widg_templates_end_criteria)))
	panel_template_lookup.append(('capture_criteria', 
		lgm.interface_template_gui(
			frame = frame, 
			widget_mason = frame.mason, 
			key = 'capture_criteria', 
			widget_templates =\
				ensemble.simulation_plan.widg_templates_capture_criteria)))
	panel_template_lookup.append(('plot_targets', 
		lgm.interface_template_gui(
			frame = frame, 
			widget_mason = frame.mason, 
			key = 'plot_targets', 
			widget_templates =\
				ensemble.simulation_plan.widg_templates_plot_targets)))
	ensemble.fitting_plan.set_settables(
		*frame.settables_infos, fit_rout_dex = 4)
	panel_template_lookup.append(('fit_routines', 
		lgm.interface_template_gui(
			frame = frame, 
			widget_mason = frame.mason, 
			key = 'fit_routines', 
			widget_templates =\
				ensemble.fitting_plan.widg_templates)))
	ensemble.postprocess_plan.set_settables(
		*frame.settables_infos, postproc_dex = 5)
	panel_template_lookup.append(('post_processes', 
		lgm.interface_template_gui(
			frame = frame, 
			widget_mason = frame.mason, 
			key = 'post_processes', 
			widget_templates =\
				ensemble.postprocess_plan.widg_templates)))
	ensemble.cartographer_plan.set_settables(*frame.settables_infos)
	panel_template_lookup.append(('p_space_map', 
		lgm.interface_template_gui(
			frame = frame, 
			widget_mason = frame.mason, 
			key = 'p_space_map', 
			widget_templates =\
				ensemble.cartographer_plan.widg_templates)))
	ensemble.multiprocess_plan.set_settables(*frame.settables_infos)
	panel_template_lookup.append(('multiprocessing', 
		lgm.interface_template_gui(
			frame = frame, 
			widget_mason = frame.mason, 
			key = 'multiprocessing', 
			widget_templates =\
				ensemble.multiprocess_plan.widg_templates)))
	output_plan_dex = 4		
	panel_template_lookup.append(('output_plans', 
		lgm.interface_template_gui(
			frame = frame, 
			widget_mason = frame.mason, 
			key = 'output_plans', 
			widget_templates = [			
				lgm.interface_template_gui(
						widget_layout = 'grid', 
						layout_rows = 3, 
						layout_columns = 3, 
						widget = [	'mobj_inspector', 
									'selector'	], 
						functions = [	[None], [None]	], 
						instance = [	[frame.selected_objs[
											output_plan_dex]], 
										frame.selected_objs[
											output_plan_dex]], 
						gui_labels = [	[None], 
										lfu.grab_mobj_names(
											ensemble.run_params[
												'output_plans'])], 
						where_store = [	[None], 
										ensemble.run_params	], 
						initial = [	[None], select_labels[
										output_plan_dex]], 
						dex = [	[None], output_plan_dex	], 
						key = [	[None], 
								'output_plans'	], 
						box_label = '', 
						box_positions = [(1, 0), (0, 0)], 
						sizer_position = (0, 0))])))
	reaction_dex = 8
	panel_template_lookup.append(('reactions', 
		lgm.interface_template_gui(
			frame = frame, 
			widget_mason = frame.mason, 
			key = 'reactions', 
			widget_templates = [
				lgm.interface_template_gui(
						widget_layout = 'grid', 
						layout_rows = 3, 
						layout_columns = 3, 
						widget = [	'mobj_inspector', 
									'add_rem_drop_list'	], 
						instance = [	[frame.selected_objs[
												reaction_dex]], 
										frame.selected_objs[
											reaction_dex]], 
						gui_labels = [	[None], 
										['Add Reaction', 
										'Remove Reaction', 
										select_labels[reaction_dex]]], 
						where_store = [	[None], 
										[ensemble.run_params, None]	], 
						value = [	[None], 
									lfu.grab_mobj_names(
										ensemble.run_params[
											'reactions'])	], 
						key = [[None], 'reactions'], 
						dex = [[None], reaction_dex], 
						base_class = [[None], [reaction]], 
						box_label = '', 
						box_positions = [	(0, 0), (0, 2), 
											(1, 2), (1, 0)	], 
						sizer_position = (0, 0))])))
	species_dex = 9
	panel_template_lookup.append(('species', 
		lgm.interface_template_gui(
			frame = frame, 
			widget_mason = frame.mason, 
			key = 'species', 
			widget_templates = [
				lgm.interface_template_gui(
						widget_layout = 'grid', 
						layout_rows = 3, 
						layout_columns = 3, 
						widget = [	'mobj_inspector', 
									'add_rem_drop_list'	], 
						instance = [[frame.selected_objs[species_dex]], 
									frame.selected_objs[species_dex]], 
						gui_labels = [	[None], 
										['Add Species', 
										'Remove Species', 
										select_labels[species_dex]]	], 
						where_store = [	[None], 
										[ensemble.run_params, None]	], 
						value = [	[None], 
									lfu.grab_mobj_names(
										ensemble.run_params[
											'species'])	], 
						key = [[None], 'species'], 
						dex = [[None], species_dex], 
						base_class = [[None], [species]], 
						box_label = '', 
						box_positions = [	(0, 0), (0, 2), 
											(1, 2), (1, 0)	], 
						sizer_position = (0, 0))])))
	injection_dex = 10
	panel_template_lookup.append(('injections', 
		lgm.interface_template_gui(
			frame = frame, 
			widget_mason = frame.mason, 
			key = 'injections', 
			widget_templates = [
				lgm.interface_template_gui(
						widget_layout = 'grid', 
						layout_rows = 3, 
						layout_columns = 3, 
						widget = [	'mobj_inspector', 
									'add_rem_drop_list'	], 
						instance = [[frame.selected_objs[injection_dex]], 
									frame.selected_objs[injection_dex]], 
						gui_labels = [	[None], 
										['Add Injections', 
										'Remove Injections', 
										select_labels[injection_dex]]], 
						where_store = [	[None], 
										[ensemble.run_params, None]	], 
						value = [	[None], 
									lfu.grab_mobj_names(
										ensemble.run_params[
											'injections'])	], 
						key = [[None], 'injections'], 
						dex = [[None], injection_dex], 
						base_class = [[None], [injection]], 
						box_label = '', 
						box_positions = [	(0, 0), (0, 2), 
											(1, 2), (1, 0)	], 
						sizer_position = (0, 0))])))

	return lgb.tree_book_panels_from_lookup(
		panel_template_lookup, frame, ensemble)

def set_parameters(ensem):
	ensem.run_params['species'] = {}
	ensem.run_params['reactions'] = []
	ensem.run_params['injections'] = []
	ensem.run_params['plot_targets'] = ['iteration', 'time']
	output_plan = ensem.run_params['output_plans']['Simulation']
	output_plan.targeted = ['iteration', 'time']
	for dex in range(len(output_plan.outputs)):
		output_plan.outputs[dex] = ['iteration', 'time']

	ensem.run_params['bool_expressions'] = lfu.dictionary()
	ensem.run_params['bool_expressions']['end'] = ''
	ensem.run_params['bool_expressions']['capt'] = ''
	ensem.run_params['end_criteria'] = [lc.criterion_iteration()]
	ensem.run_params.create_partition('system', 
		[	'species', 'reactions', 'injections', 'end_criteria', 
			'capture_criteria', 'plot_targets', 'bool_expressions'	])
	#ensem.cartographer_plan.parameter_space_mobjs =\
	#			ensem.run_params.partition['system']
	ensem.run_params.create_partition('template owners', 
								['reactions', 'species'])

#this should be capable of handling
# everything in run_param_keys
#FIX THIS
def parse_mcfg(lines, *args):
	params = args[0]

	def parse_reaction_line(data):

		def left_right_process(left, right):
			left = [(left[k + 1], int(left[k])) for k in 
					[num*2 for num in range(len(left)/2)]]
			right = [(right[k + 1], int(right[k])) for k in 
					[num*2 for num in range(len(right)/2)]]
			return left, right

		data = data.split(' ')
		try:
			label = ' '.join(data[data.index(':') + 1:])

		except ValueError:
			label = 'a reaction'

		try:
			divider = [item.find('-') for item in data].index(0)
				
		except:
			try:
				divider = [item.find('-') for item in data].index(1)

			except:
				print 'cant interpret divider in reaction'
				return []

		if data[divider] == '<->':
			rates = [float(data[divider - 1]), float(data[divider + 1])]
			left = [item for item in data[:divider - 1] if item != '+']
			try:
				right = [item for item in data[divider + 2:data.index(':')] if item != '+']

			except ValueError:
				right = [item for item in data[divider + 2:] if item != '+']

			left, right = left_right_process(left, right)
			return [reaction(label, rates[0],  
					propensity_scheme = 'classic', 
						used=left, produced=right),
					reaction(label, rates[1], 
					propensity_scheme = 'classic', 
						used=right, produced=left)]

		elif data[divider] == '->':
			rates = [float(data[divider - 1])]
			left = [item for item in data[:divider - 1] if item != '+']
			try:
				right = [item for item in 
						data[divider + 1:data.index(':')] 
										if item != '+']

			except ValueError:
				right = [item for item in data[divider + 1:] if item != '+']

			left, right = left_right_process(left, right)
			return [reaction(label, rates[0], 
						propensity_scheme = 'classic', 
							used=left, produced=right)]

		elif data[divider] == '<-':
			rates = [float(data[divider + 1])]
			left = [item for item in data[:divider] if item != '+']
			try:
				right = [item for item in data[divider + 2:data.index(':')] if item != '+']

			except ValueError:
				right = [item for item in data[divider + 2:] if item != '+']

			left, right = left_right_process(left, right)
			return [reaction(label, rates[0], 
					propensity_scheme = 'classic', 
						used=right, produced=left)]

		#except:
		if data != ['']:
			print 'unable to parse reaction: ' + str(data)
			pdb.set_trace()

		return []

	def parse_species_line(data):
		try:
			data = [dat.strip() for dat in data.split(':')]
			return data[0], int(data[1])

		except:
			print 'unable to parse species: ' + str(data)

	def fix_species_list(rxns, specs):
		agents = {}
		for rxn in rxns:
			for agent in rxn.used + rxn.produced:
				agents[agent[0]] = species(
									label = agent[0], 
									initial_count = 0, 
									current_count = 0)

		for key in specs.keys():
			try:
				agents.keys().index(key)
				agents[key] = specs[key]

			except ValueError:
				print 'agent: ' + key + ' does not react - neglecting'

		specs = agents
		return rxns, specs

	parser = ''
	for line in lines:
		if line.startswith('#') == True or line.strip() == '':
			continue

		elif line.startswith('<reactions>'):
			parser = 'reaction'
			continue

		elif line.startswith('<species>'):
			parser = 'species'
			continue

		elif line.startswith('<end criteria>'):
			parser = 'end_criteria'
			continue

		else:
			if parser == 'reaction':
				params['reactions'].extend(
					parse_reaction_line(line[:-1]))

			elif parser == 'species':
				spec, value = parse_species_line(line[:-1])
				params['species'][spec] = species(
											spec, 
											initial_count = value, 
											current_count = value)

			elif parser == 'end_criteria':
				pass

	params['reactions'], params['species'] = \
		fix_species_list(params['reactions'], params['species'])

#an instance of this object represents an indepedant simulation system
class sim_system(lsc.sim_system):

	def __init__(self, ensem = None, 
			label = 'another chemical system', params = {}):
		lsc.sim_system.__init__(self, ensem = ensem, 
					label = label, params = params)

	def handle_mobj_initializations(self):
		#these initializations should appear in the classes
		for rxn in self.reactions:
			rxn.system = self
			rxn.rate = float(rxn.rate)
			rxn.propensity_function_maker.initialize(self)
			for amount in [tup[1] for tup in rxn.used]:
				amount = int(amount)

			for amount in [tup[1] for tup in rxn.produced]:
				amount = int(amount)		

		for speckey in self.species.keys():
			self.species[speckey].system = self
			self.species[speckey].current_count =\
				int(self.species[speckey].initial_count)

		for inject in self.injections:
			inject.initialize(self)

		super(sim_system, self).handle_mobj_initializations()

	def initialize(self):
		self.reactions = self.parameters['reactions']
		self.species = self.parameters['species']
		self.injections = self.parameters['injections']
		self.probability = []
		self.handle_mobj_initializations()
		self.determine_reaction()

	def iterate(self):
		try:
			self.affect_injections()
			reaction_index = self.determine_reaction()
			self.reactions[reaction_index].react(self)

		except TypeError:
			if reaction_index == '':
				#print 'all reactions impossible'
				injection_stats = [inj.supply > 0 and 
								inj.verify_criteria_list(
								inj.active_criteria, (self)) 
								for inj in self.injections]

				if injection_stats.count(True) == 0:
					#print 'all injections irrelevant'
					#print 'simulation ending'
					self.bAbort = True

			else:
				print 'sim_system.iterate() failed!'
				self.bAbort = True

	def decommission(self):
		print 'chemical system decommissioned'

	def affect_injections(self):
		for injection in self.injections:
			injection.iterate()

	def determine_reaction(self):
		reaction_random_0_to_1 = random.random()
		temporal_random_0_to_1 = random.random()
		reaction_table = []
		reaction_propensity_norm = 0.0
		for rxn in self.reactions:
			reaction_propensity_norm += rxn.determine_propensity(self)
			reaction_table.append(reaction_propensity_norm)

		try:
			del_t = log(temporal_random_0_to_1) / reaction_propensity_norm
			self.time.append(self.time[-1] - 1 * del_t)

		except IndexError:
			self.time.append(0.0)

		except ZeroDivisionError:
			def validate_time(dex):
				validex = lm.find_infinite_tail(self.data[dex].scalers)
				if validex < 100:
					return len(self.data[dex].scalers) - 10

				else:
					return validex

			timedex = [dater.label for dater in self.data].index('time')
			self.determine_end_valid_data = (validate_time, (timedex))
			#print 'ending simulation: time step has gone to infinity'
			return ''

		try:
			reaction_table = [pr/reaction_propensity_norm 
								for pr in reaction_table]

		except ZeroDivisionError:
			print 'you probably chose a very stupid initial condition...'
			#just assert even probability - STUPID solution
			reaction_table = [(k + 1)/len(reaction_table) 
							for k in range(len(reaction_table))]

		self.probability.append(reaction_table)
		for idx in range(len(reaction_table)):
			if reaction_random_0_to_1 <= reaction_table[idx]:
				return idx

	def capture_plot_data(self):
		for k in range(len(self.parameters['plot_targets'])):
			if self.data[k].tag == 'scaler':
				try:
					self.data[k].scalers.append(self.species[self.data[k].label].current_count)

				except KeyError:
					try:
						self.data[k].scalers.append(self.__dict__[self.data[k].label][-1])

					except:
						self.data[k].scalers.append(self.__dict__[self.data[k].label])

			elif self.data[k].tag == 'coordinates':
				#these might get handled by pointers because pointers pwn
				pass

#class reaction(lfu.modular_object):
class reaction(modular_object):

	def __init__(self, label = 'another reaction', 
			rate = float(10.0), propensity_scheme = 'classic', 
			propensity_function_maker = None, 
			occurrences = [], used = None, produced = None, 
			visible_attributes = ['label', 'propensity_scheme', 
								'rate', 'used', 'produced', 
								'propensity_function_maker']):
		self.__dict__ = lfu.dictionary()
		self.system = None
		self.rate = rate
		if occurrences is None:
			self.occurrences = []

		else:
			self.occurrences = occurrences

		#instances of these are somehow coupled unless a 
		#	used and produced list is passed to init, 
		#	EVEN an empty list will do (used = [] does not!)
		if used is None:
			self.used = []

		else:
			self.used = used

		if produced is None:
			self.produced = []

		else:
			self.produced = produced

		self.propensity = 1.0
		self.propensity_minimum = 1e-30
		self.propensity_scheme = propensity_scheme
		if propensity_function_maker is None:
			self.propensity_function_maker =\
				function_maker_eval_statement_chemical_system()

		parameter_space_templates =\
			[lgeo.interface_template_p_space_axis(
				p_sp_bounds = [0.0000001, 1000.0], 
					instance = self, key = 'rate')]
		lfu.modular_object.__init__(self, label = label, 
				visible_attributes = visible_attributes, 
				parameter_space_templates = parameter_space_templates)
		self.__dict__.create_partition('template owners', 
							['propensity_function_maker'])
		self.__dict__.create_partition('p_space contributors', 
							['propensity_function_maker'])

	def react(self, system):
		enough_agent = [system.species[agent[0]].current_count >=\
								agent[1] for agent in self.used]
		try:
			enough_agent.index(False)
			return False

		#THIS SHOULD NOT BE HANDLED THIS WAY; EXCEPT SHOULD BE RARE!!
		except ValueError:
			for agent in self.used:
				system.species[agent[0]].current_count -= int(agent[1])

			for agent in self.produced:
				system.species[agent[0]].current_count += int(agent[1])

			try:
				self.occurrences.append((system.iteration, system.time[-1]))

			except IndexError:
				self.occurrences.append((0, 0))

			return True

		return False

	def determine_propensity(self, system):
		try:
			return self.propensity_scheme(system)

		except TypeError:
			if self.propensity_scheme == 'classic':
				self.propensity_scheme =\
					self.classic_propensity
				return self.determine_propensity(system)

			elif self.propensity_scheme == 'function':
				try:
					self.propensity_function_maker.make_function()
					self.propensity_scheme =\
						self.propensity_function_maker

				except TypeError:
					self.revert_to_classic_propensity()

				return self.determine_propensity(system)

			elif self.propensity_scheme == '':
				self.revert_to_classic_propensity()

	def revert_to_classic_propensity(self):
		print '\nreaction propensity function failed'
		print 'reverting to classic propensity scheme for:'
		print '\t', self.label, '\n'
		self.propensity_scheme = self.classic_propensity

	def classic_propensity(self, system):
		population = 1.0
		for agent in self.used:
			for k in range(int(agent[1])):
				population *= float(system.species[
									agent[0]].current_count - k)

		self.propensity = population * self.rate
		if self.propensity > self.propensity_minimum:
			return self.propensity

		else:
			return 0.0

	def set_settables(self, *args, **kwargs):
		ensem = args[0]
		spec_list = ensem.run_params['species'].keys()
		frame = args[1]
		cartographer_support = lgm.cartographer_mason(frame)
		#self.widg_templates = []
		self.handle_widget_inheritance(*args, **kwargs)
		if not self.parameter_space_templates:
			self.parameter_space_templates =\
				[lgeo.interface_template_p_space_axis(
					p_sp_bounds = [0.0000001, 1000.0], 
						instance = self, key = 'rate')]
		self.parameter_space_templates[0].set_settables(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widget_layout = 'vert', 
				widget_mason = cartographer_support, 
				key = ['label', 'rate', 'propensity_scheme'], 
				instance = [self, self, self], 
				widget = ['text', 'text', 'rad'], 
				sub_box_labels = [	'Reaction Name',
									'Reaction Rate', 
									'Propensity Scheme'	], 
				initial = [	self.label, self.rate, 
							self.propensity_scheme	], 
				force_widget_reset = [False, False, True], 
				hide_none = [None, None, True], 
				possibles = [	None, None, 
								[	'classic', 
									'function'	]	], 
				possible_objs = [	None, None, 
									[	'classic', 
										'function'	]	], 
				sizer_position = (0, 3), 
				sizer_proportions = [1, 2, 2], 
				box_label = '', 
				parameter_space_templates = [None, 
					self.parameter_space_templates[0], None]))
		self.widg_templates.append(
			lgm.interface_template_gui(
						widget_layout = 'vert', 
						widget = ['check_spin_list'], 
						key = ['used'], 
						instance = [self], 
						append_instead = [True], 
						gui_labels = [spec_list],
						box_label = 'Reagents', 
						sizer_position = (0, 0), 
						sizer_span = (1, 1)))
		self.widg_templates.append(
			lgm.interface_template_gui(
						widget_layout = 'vert', 
						widget = ['check_spin_list'], 
						key = ['produced'], 
						instance = [self], 
						append_instead = [True], 
						gui_labels = [spec_list], 
						box_label = 'Products', 
						sizer_position = (0, 1), 
						sizer_span = (1, 1)))
		
		if self.propensity_scheme == 'function':
			self.propensity_function_maker.set_settables(*args, **kwargs)
			self.widg_templates.append(
				lgm.interface_template_gui(
					widget_layout = 'vert', 
					box_label = 'Propensity Function', 
					widget = ['panel'], 
					sizer_position = (0, 2), 
					sizer_span = (1, 1), 
					instance = self.propensity_function_maker, 
					frame = frame, 
					widget_mason = frame.mason, 
					widget_templates =\
						self.propensity_function_maker.widg_templates))

#class species(lfu.modular_object):
class species(modular_object):

	def __init__(self, label = 'another species', 
			initial_count = 10000, current_count = None, 
			visible_attributes = ['label', 'initial_count']):
		self.system = None
		self.initial_count = initial_count
		if current_count == None:
			self.current_count = initial_count

		else:
			self.current_count = current_count

		self.brand_new = True
		parameter_space_templates =\
			[lgeo.interface_template_p_space_axis(
				instance = self, key = 'initial_count', 
							p_sp_bounds = [0, 1000000])]
		lfu.modular_object.__init__(self, label = label, 
				visible_attributes = visible_attributes, 
				parameter_space_templates = parameter_space_templates)

	def set_settables(self, *args, **kwargs):
		ensem = args[0]
		where_reference = ensem.run_params['species']
		if self.brand_new:
			ensem.run_params['plot_targets'].append(self.label)
			plan = ensem.run_params['output_plans']['Simulation']
			plan.targeted.append(self.label)
			for subtargeted in plan.outputs:
				subtargeted.append(self.label)

			self.brand_new = not self.brand_new

		label_data_links = [lfu.interface_template_dependance(
								(self, 'label', self.label), 
								linkages = [(ensem.run_params, 
										'plot_targets', True, 
											'append_list')])]
		#this will cause a bug if a propensity_function_maker class
		# with a .key attribute which should not be linked to the
		# species name exists - so do not use one with this module
		#on the other hand, a subclass which uses .key exploits this
		#	this bug can be fixed with name mangling on the base class!!
		for rxn in ensem.run_params['reactions']:
			if hasattr(rxn.propensity_function_maker, 'references'):
				label_data_links.append(
					lfu.interface_template_dependance(
						(self, 'label', self.label), linkages =\
						[(rxn.propensity_function_maker.references[ref_key], 
							'key', True, 'direct') for ref_key in 
							rxn.propensity_function_maker.references.keys()]))

		label_data_links.extend([lfu.interface_template_dependance(
			(self, 'label', self.label), linkages =\
				[(ensem.run_params['output_plans']['Simulation'], 
							'targeted', True, 'append_list')])])
		[label_data_links.extend([lfu.interface_template_dependance(
			(self, 'label', self.label), linkages =\
				[(ensem.run_params['output_plans']['Simulation'], 
					'outputs', True, 'append_list_nested', dex)])]) 
											for dex in range(4)]
		label_data_links.extend(
			[lfu.interface_template_dependance(
				(self, 'label', self.label), 
				linkages = [(rxn, 'used', True, 
					'append_tuples_list', 0, 0)]) 
					for rxn in ensem.run_params['reactions']])
		label_data_links.extend(
			[lfu.interface_template_dependance(
				(self, 'label', self.label), 
				linkages = [(rxn, 'produced', True, 
					'append_tuples_list', 0, 0)]) 
					for rxn in ensem.run_params['reactions']])
		frame = args[1]
		dictionary_support = lgm.dictionary_support_mason(frame)
		cartographer_support = lgm.cartographer_mason(frame)
		self.handle_widget_inheritance(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
						widget_layout = 'vert', 
						widget_mason = dictionary_support, 
						data_links = [label_data_links], 
						key = ['label'], 
						instance = [self], 
						where_store = where_reference, 
						widget = ['text'],
						box_label = 'Species Name', 
						initial = [self.label], 
						sizer_position = (0, 0)))
		if not self.parameter_space_templates:
			self.parameter_space_templates =\
				[lgeo.interface_template_p_space_axis(
					instance = self, key = 'initial_count', 
								p_sp_bounds = [0, 1000000])]

		self.parameter_space_templates[0].set_settables(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widget_layout = 'vert', 
				widget_mason = cartographer_support, 
				widget = ['spin'], 
				instance = [	[	self	]	], 
				key = [	[	'initial_count'	]	], 
				initial = [	[self.initial_count]	], 
				value = [	(0, 1000000)	], 
				box_label = 'Initial Count', 
				sizer_position = (0, 1), 
				parameter_space_templates =\
					[self.parameter_space_templates[0]]))

#class injection(lfu.modular_object):
class injection(modular_object):

	def __init__(self, label = 'another injection', 
			amount = 1000, inject_type = 'species', 
			inject_types = ['species', 'reaction'], 
			finite_supply = True, supply = 10000, freq = 1.0, 
			base_species = None, base_reaction = None, 
			active_criteria = None, active = True,	
			bool_expression = None, increments = []):
		self.__dict__ = lfu.dictionary()
		self.system = None
		if not active_criteria is None:
			self.active_criteria = active_criteria

		else:
			self.active_criteria = []

		self.selected_criterion = None
		self.default_crit = lc.criterion
		self.bool_expression = bool_expression
		self.inject_type = inject_type
		self.inject_types = inject_types

		self.base_reaction = base_reaction
		self.active = active

		self.base_species = base_species
		self.freq = freq
		self.amount = amount
		self.finite = finite_supply
		self.supply = supply
		self.increments = increments
		self.parameter_space_templates =\
			[lgeo.interface_template_p_space_axis(
				p_sp_bounds = [0.0, 1000000000.0], 
				instance = self, key = 'amount'), 
			lgeo.interface_template_p_space_axis(
				p_sp_bounds = [0.0, 1000000000.0], 
				instance = self, key = 'freq'), 				
			lgeo.interface_template_p_space_axis(
				p_sp_bounds = [0.0, 1000000000.0], 
				instance = self, key = 'supply')]
		lfu.modular_object.__init__(self, label = label)
		self.__dict__.create_partition(
			'template owners', ['active_criteria'])

	def initialize(self, system):
		self.system = system
		self.freq = float(self.freq)
		if self.active_criteria:
			[crit.initialize(system) for crit in self.active_criteria]
		
		if not self.base_species is None:
			self.base_species = lfu.grab_mobj_by_name(
				self.base_species, system.species)

		if not self.base_reaction is None:
			self.base_reaction = lfu.grab_mobj_by_name(
				self.base_reaction, system.reactions)

	def iterate(self):
		try:
			return self.inject_type(self.system)

		except TypeError:
			if self.inject_type == 'species':
				self.inject_type =\
					self.iterate_species_type
				return self.inject_type(self.system)

			elif self.inject_type == 'reaction':
				self.inject_type =\
					self.iterate_reactions_type
				return self.inject_type(self.system)

	def iterate_reactions_type(self, system):
		if self.active_criteria and self.verify_criteria_list_boolean(
									self.active_criteria, (self.system), 
								bool_expression = self.bool_expression):
			if not self.active:
				self.active = True
				print 'num rxns', str(len(self.system.reactions))
				self.system.reactions.append(self.base_reaction)
				print 'num rxns', str(len(self.system.reactions))

		else:
			if self.active:
				self.active = False
				#dex = self.system.reactions.index(self.base_reaction)
				print 'num rxns', str(len(self.system.reactions))
				self.system.reactions.remove(self.base_reaction)
				print 'num rxns', str(len(self.system.reactions))

	def iterate_species_type(self, system):
		if not self.active_criteria or self.verify_criteria_list_boolean(
									self.active_criteria, (self.system), 
								bool_expression = self.bool_expression):
			amount = self.measure()
			if amount > 0:
				self.inject(amount)

	def measure(self):

		def get_last_inject_time():
			try:
				last_time_inject = self.increments[-1][1]

			except IndexError:
				last_time_inject = 0.0

			return last_time_inject
			
		def get_measured(last_time):
			try:
				passed_time = self.system.time[-1] - last_time
				measured_amount = int(round(self.amount*(
								self.freq*passed_time)))
				return measured_amount		

			except IndexError:
				return 0

		last_time_inject = get_last_inject_time()
		measured_amount = get_measured(last_time_inject)
		if self.finite:
			if self.supply >= 0:
				if max(0, self.supply - measured_amount) == 0:
					measured_amount = self.supply

				return measured_amount

			else:
				print 'injection is empty!'
				return 0

		else:
			return measured_amount

	def inject(self, amount):
		self.base_species.current_count += amount
		self.supply -= amount
		self.increments.append((amount, self.system.time[-1]))

	def generate_add_crit_func(self, frame):

		def on_add_crit(event):
			self.active_criteria.append(lc.criterion_iteration())
			self.active_criteria[-1].set_settables(
							*frame.settables_infos)

		return on_add_crit

	def generate_remove_crit_func(self, frame):

		def on_remove_crit(event):
			try:
				label = self.selected_criterion.label
				dex = lfu.grab_mobj_dex_by_name(
					label, self.active_criteria)
				self.active_criteria.remove(self.selected_criterion)
				self.selected_criterion = self.active_criteria[-1]

			except AttributeError:
				pass

			except IndexError:
				self.selected_criterion = None

		return on_remove_crit

	def generate_select_crit_func(self, frame):

		def on_select_crit(event):
			label = event.GetEventObject().GetLabel()
			dex = lfu.grab_mobj_dex_by_name(
				label, self.active_criteria)
			self.selected_criterion = self.active_criteria[dex]

		return on_select_crit

	def set_settables(self, *args, **kwargs):
		frame = args[1]
		cartographer_support = lgm.cartographer_mason(frame)
		ensem = args[0]
		if not self.parameter_space_templates:
			self.parameter_space_templates =\
				[lgeo.interface_template_p_space_axis(
					p_sp_bounds = [0.0, 1000000000.0], 
					instance = self, key = 'amount'), 
				lgeo.interface_template_p_space_axis(
					p_sp_bounds = [0.0, 1000000000.0], 
					instance = self, key = 'freq'), 				
				lgeo.interface_template_p_space_axis(
					p_sp_bounds = [0.0, 1000000000.0], 
					instance = self, key = 'supply')]

		#self.widg_templates = []
		self.handle_widget_inheritance(*args, from_sub = True)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widget_layout = 'vert', 
				key = ['label', 'inject_type'], 
				instance = [self, self], 
				widget = ['text', 'rad'],
				box_label = '', 
				hide_none = [None, True], 
				initial = [self.label, self.inject_type], 
				possibles = [None, self.inject_types], 
				possible_objs = [None, self.inject_types], 
				sub_box_labels = ['Injection Name', 
								'Type of Injection'], 
				sizer_position = (0, 0)))
		self.parameter_space_templates[0].set_settables(*args, **kwargs)
		self.parameter_space_templates[1].set_settables(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widget_layout = 'vert', 
				widget_mason = cartographer_support, 
				widget = ['spin', 'text'], 
				instance = [	[self], self	], 
				key = [	['amount'], 'freq'	], 
				initial = [	[self.amount], self.freq	], 
				value = [	(0, 1000000), None	], 
				box_label = 'Dosage', 
				sub_box_labels = ['Amount', 'Frequency of Dose'], 
				sizer_position = (0, 3), 
				sizer_span = (3, 1), 
				parameter_space_templates =\
					[self.parameter_space_templates[0], 
					self.parameter_space_templates[1]]))
		self.parameter_space_templates[2].set_settables(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widget_layout = 'vert', 
				widget_mason = cartographer_support, 
				widget = ['check_set', 'spin'], 
				instance = [[self], [self]], 
				key = [	['finite'], ['supply']	], 
				initial = [	None, [self.supply]	], 
				value = [	None, (0, 1000000)], 
				append_instead = [False, None], 
				box_label = 'Total Supply', 
				dex = [None, None], 
				gui_labels = [['Has Finite Supply'], None], 
				sub_box_labels = [None, None], 
				sizer_position = (0, 4), 
				sizer_span = (3, 1), 
				sizer_proportions = [1, 2], 
				parameter_space_templates =\
					[None, self.parameter_space_templates[2]]))
		spec_list = lfu.grab_mobj_names(ensem.run_params['species'])
		if spec_list:
			self.widg_templates.append(
				lgm.interface_template_gui(
					widget_layout = 'vert', 
					key = ['base_species'], 
					instance = [self], 
					widget = ['rad'], 
					box_label = 'Species to Inject', 
					hide_none = [True], 
					initial = [self.base_species], 
					possibles = [spec_list], 
					possible_objs = [spec_list], 
					sizer_position = (0, 2)))

		else:
			self.widg_templates.append(
				lgm.interface_template_gui(
					widget_layout = 'vert', 
					key = ['base_species'], 
					instance = [self], 
					widget = ['rad'], 
					box_label = 'Species to Inject', 
					hide_none = [True], 
					initial = ['No Species Present!'], 
					possibles = [['No Species Present!']], 
					possible_objs = [['No Species Present!']], 
					sizer_position = (0, 2)))

		rxn_list = lfu.grab_mobj_names(ensem.run_params['reactions'])
		if rxn_list:
			self.widg_templates.append(
				lgm.interface_template_gui(
					widget_layout = 'vert', 
					key = ['base_reaction'], 
					instance = [self], 
					widget = ['rad'], 
					box_label = 'Reaction to Engage', 
					hide_none = [True], 
					initial = [self.base_reaction], 
					possibles = [rxn_list], 
					possible_objs = [rxn_list], 
					sizer_position = (0, 1)))

		else:
			self.widg_templates.append(
				lgm.interface_template_gui(
					widget_layout = 'vert', 
					key = ['base_reaction'], 
					instance = [self], 
					widget = ['rad'], 
					box_label = 'Reaction to Engage', 
					hide_none = [True], 
					initial = ['No Reactions Present!'], 
					possibles = [['No Reactions Present!']], 
					possible_objs = [['No Reactions Present!']], 
					sizer_position = (0, 1)))

		if not self.selected_criterion is None:
			selected_crit_label = self.selected_criterion.label
			self.selected_criterion.set_settables(*args, **kwargs)
			self.widg_templates.append(
				lgm.interface_template_gui(
					widget_layout = 'vert', 
					box_label = 'Be Active Criterion', 
					widget = ['panel'], 
					sizer_position = (1, 1), 
					sizer_span = (2, 2), 
					instance = self.selected_criterion, 
					frame = frame, 
					widget_mason = frame.mason, 
					widget_templates =\
						self.selected_criterion.widg_templates))

		else:
			selected_crit_label = None

		if self.bool_expression is None:
			self.bool_expression = ''

		self.widg_templates.append(
			lgm.interface_template_gui(
				widget = ['button_set', 'selector', 'text'], 
				widget_layout = 'vert', 
				key = [None, None, 'bool_expression'], 
				instance = [None, None, self], 
				functions = [[self.generate_add_crit_func(frame), 
							self.generate_remove_crit_func(frame)], 
							[self.generate_select_crit_func(frame)], 
															None], 
				gui_labels = [	[	'Add Criterion', 
									'Remove Criterion'	], 
								[	crit.label for crit 
									in self.active_criteria	], None	], 
				initial = [None, selected_crit_label, 
								self.bool_expression], 
				sub_box_labels = [	'', '', 
									'Boolean Expression of Criteria'], 
				sizer_proportions = [1, 1, 1, 2], 
				box_label = 'Be Active Criteria', 
				sizer_position = (1, 0)))

class criterion_spec_included_scaler_increment(
				lc.criterion_scaler_increment):

	def __init__(self, increment = 10.0, key = 'iteration', 
			base_class = lfu.interface_template_class(
					object, 'species scaler increment'), 
			label = 'scaler increment criterion', visible_attributes =\
			['label', 'base_class', 'bRelevant', 'key', 'increment']):
		lc.criterion_scaler_increment.__init__(self, label = label, 
			base_class = base_class, increment = increment, key = key)

	def find_last_value(self, system):
		try:
			last_value = system.species[self.key].current_count

		except:
			try:
				#this works for lists
				last_value = system.__dict__[self.key][-1]

			except TypeError:
				#if its just a value instead of a list
				last_value = system.__dict__[self.key]

		return last_value

	def set_settables(self, *args, **kwargs):
		ensem = args[0]
		self.keys = ['iteration', 'time'] +\
					ensem.run_params['species'].keys()
		self.handle_widget_inheritance(*args, from_sub = False)
		super(criterion_spec_included_scaler_increment, 
				self).set_settables(*args, from_sub = True)

class criterion_species_count(lc.criterion):

	def __init__(self, *args, **kwargs):
		if not 'base_class' in kwargs.keys():
			kwargs['base_class'] = lfu.interface_template_class(
										object, 'species count')

		if not 'label' in kwargs.keys():
			kwargs['label'] = 'species count criterion'

		if not 'visible_attributes' in kwargs.keys():
			kwargs['visible_attributes'] = ['label', 'base_class', 
								'bRelevant', 'spec_count_target']

		self.impose_default('key', None, **kwargs)
		self.impose_default('keys', [], **kwargs)
		self.impose_default('spec_count_target', 100, **kwargs)
		lc.criterion.__init__(self, *args, **kwargs)

	'''	
	def __init__(self, spec_count_target = 100.0, base_class =\
		lfu.interface_template_class(object, 'species count'), 
			label = 'species count criterion', visible_attributes =\
			['label', 'base_class', 'bRelevant', 'spec_count_target'], 
											key = None, keys = []):
		lc.criterion.__init__(self, label = label, 
						base_class = base_class)
		self.key = key
		self.keys = keys
		self.spec_count_target = spec_count_target
	'''

	def initialize(self, *args, **kwargs):
		self.spec_count_target = float(self.spec_count_target)

	def verify_pass(self, system):
		for spec in system.species.keys():
			if self.key == spec:
				if sorted([	self.spec_count_target, 
							system.species[spec].current_count, 
							system.species[spec].initial_count	])[1]\
											== self.spec_count_target:
					#print 'criterion: reached target species count'
					return True

		return False

	def set_uninheritable_settables(self, *args, **kwargs):
		self.visible_attributes = ['label', 'base_class', 
			'bRelevant', 'spec_count_target', 'key', 'keys']
		#this has to be overridden even if this class lacks
		# its own uninheritable settables
		pass

	def set_settables(self, *args, **kwargs):
		ensem = args[0]
		self.keys = ensem.run_params['species'].keys()
		if not self.keys:
			self.keys = ['no available species!']
			self.key = 'no available species!'

		self.handle_widget_inheritance(*args, from_sub = False)
		self.widg_templates.append(
			lgm.interface_template_gui(
						widget_layout = 'vert', 
						key = [	'spec_count_target'	], 
						instance = [self], 
						widget = ['text'],
						box_label = 'Target Species Count', 
						initial = [self.spec_count_target], 
						sizer_position = (0, 2)))
		self.widg_templates.append(
			lgm.interface_template_gui(
						widget_layout = 'vert', 
						key = ['key'], 
						instance = [self], 
						widget = ['rad'], 
						box_label = 'Species', 
						hide_none = [True], 
						initial = [self.key], 
						possibles = [self.keys], 
						possible_objs = [self.keys], 
						sizer_position = (1, 2)))
		super(criterion_species_count, self).set_settables(
									*args, from_sub = True)

lc.valid_criterion_base_classes = [
	lfu.interface_template_class(
		lc.criterion_sim_time, 'time limit'), 
	lfu.interface_template_class(
		lc.criterion_iteration, 'iteration limit'), 
	lfu.interface_template_class(
		lc.criterion_capture_count, 'capture limit'), 
	lfu.interface_template_class(
		criterion_spec_included_scaler_increment, 
					'species scaler increment'), 
	lfu.interface_template_class(
		criterion_species_count, 'species count')]

class interface_template_reference_chemical_system(
				lsc.interface_template_reference):

	def __init__(self, label = 'x', one_of_a_kind = True,  
			instance = None, key = None, keys = [], value = 10):
		self.__dict__ = lfu.dictionary()
		lsc.interface_template_reference.__init__(self, 
			label = label, one_of_a_kind = one_of_a_kind, 
						instance = instance, key = key, 
							keys = keys, value = value)

	def refer(self):
		if self.key == 'time':
			try:
				return self.instance.__dict__[self.key][-1]

			except IndexError:
				return 0.0

		else:
			return lsc.interface_template_reference.refer(self)

	def set_settables(self, *args, **kwargs):
		self.keys = ['none', 'time', 'iteration'] +\
					args[0].run_params['species'].keys()
		self.handle_widget_inheritance(*args, from_sub = False)
		super(interface_template_reference_chemical_system, 
				self).set_settables(*args, from_sub = True)

class function_maker_eval_statement_chemical_system(
					lm.function_maker_eval_statement):

	def __init__(self, eval_statement = '', valid_base_classes = None, 
			references = None, reference_template_class =\
			interface_template_reference_chemical_system, 
			base_class = lfu.interface_template_class(object, 
									'chemical system eval'), 
					label = 'eval statement function maker'):
		if valid_base_classes is None:
			self.valid_base_classes =\
				lm.valid_function_maker_base_classes

		self.__dict__ = lfu.dictionary()
		lm.function_maker_eval_statement.__init__(self, label = label, 
			base_class = base_class, eval_statement = eval_statement, 
				reference_template_class = reference_template_class, 
											references = references)
		self.__dict__.create_partition(
			'template owners', ['references'])
		self.__dict__.create_partition(
			'p_space contributors', ['references'])

	def initialize(self, *args, **kwargs):
		system = args[0]
		#the reference templates in self.references must 
		#  be set properly here, depend on the string 
		#  chosen to correspond to their .key attributes
		for ref_key in self.references.keys():
			ref = self.references[ref_key]
			if ref.key is None:
				pass

			elif ref.key == 'time' or ref.key == 'iteration':
				ref.instance = system

			else:
				ref.instance = system.species[ref.key]
				ref.key = 'current_count'

		lm.function_maker_eval_statement.initialize(
							self, *args, **kwargs)

lm.valid_function_maker_base_classes = [
	lfu.interface_template_class(
		function_maker_eval_statement_chemical_system, 
							'chemical system eval')]






