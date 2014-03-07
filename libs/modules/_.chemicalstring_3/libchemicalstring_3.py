#imports
# cython: profile=True
#cimport cython

#from libc.math cimport log as log
#from libc.math cimport sin as sin
#from libc.math cimport cos as cos
from math import log as log
from math import sin as sin
from math import cos as cos

import random
import numpy as np
import re

import pdb


#cdef inline parse(system_string, int dex, string):
def parse(system_string, dex, string):
	#cdef int new_dex
	new_dex = system_string.find(string)
	return system_string[dex:new_dex], new_dex


#turn function strings into compiled lambda functions
def generate_functions(functions, count_targets, counts):

	def convert(substr):
		if substr in count_targets:
			return "".join(["counts[", 
				str(count_targets.index(substr)), "]"])

		else: return substr

	def encode(string):
		return ''.join([convert(substr) for substr in string])

	func_names = [fu[:fu.find('=')] for fu in functions]
	encoded = [fu[fu.find('=') + 1:] for fu in functions]
	encoded = ['lambda counts: ' + encode(re.split('(\W)', string)) 
											for string in encoded]
	funcs = [eval(expr) for expr in encoded]
	return func_names, funcs


#create a function which updates the current functions' values
def generate_update_functions(count_targets, counts, 
							functions, func_names):

	def dummy(): print 'dummy update functions'
	def update_function():
		func_dex = count_targets.index(func_names[0])
		for dex in range(func_dex, len(counts)):
			counts[dex] = functions[dex - func_dex](counts)

	if not func_names: return dummy
	else: return update_function


def generate_reaction(count_targets, counts, functions, func_names, 
				var_vals, variables, rxn_string, rate_call_group):

	#rate was not a float and some stochiometric coefficient > 1; slowest
	def propensity_with_rate_call():
		#cdef double population = 1.0
		population = 1.0
		#cdef double propensity = 1.0
		propensity = 1.0
		#cdef double propensity_minimum = 1e-30
		propensity_minimum = 1e-30
		#cdef int cnt_dex = 1
		cnt_dex = 1
		#cdef int act_dex = 0
		act_dex = 0
		#cdef int cnt
		#cdef int act
		#cdef int k
		for agent in reagents:
			cnt = counts[agent[cnt_dex]]
			act = agent[act_dex]
			for k in range(act): population *= cnt - k
			population /= act

		propensity = population * rate(counts)
		if propensity > propensity_minimum: return propensity
		else: return 0.0

	#rate was not a float and all stochiometric coefficients = 1
	def propensity_simple_with_rate_call():
		#cdef double population = 1.0
		population = 1.0
		#cdef double propensity = 1.0
		propensity = 1.0
		#cdef double propensity_minimum = 1e-30
		propensity_minimum = 1e-30
		#cdef int cnt_dex
		#cdef int cnt
		for cnt_dex in cnt_dexes: population *= counts[cnt_dex]
		propensity = population * rate(counts)
		if propensity > propensity_minimum: return propensity
		else: return 0.0

	#rate was not a float, there is but one stochiometric
	# coefficient and it is equal to 1
	def propensity_very_simple_with_rate_call():
		#cdef double population = 1.0
		population = 1.0
		#cdef double propensity = 1.0
		propensity = 1.0
		#cdef double propensity_minimum = 1e-30
		propensity_minimum = 1e-30
		#cdef double zero = 0.0
		zero = 0.0
		propensity = counts[cnt_dexes[0]] * rate(counts)
		if propensity > propensity_minimum: return propensity
		else: return zero	#is this faster?

	#rate was not a float and there are no reagents
	def propensity_simplest_with_rate_call():
		#cdef double propensity = 1.0
		propensity = 1.0
		#cdef double propensity_minimum = 1e-30
		propensity_minimum = 1e-30
		propensity = rate(counts)
		if propensity > propensity_minimum: return propensity
		else: return 0.0

	#rate was a float and some stochiometric coefficient > 1
	def propensity():
		#cdef double population = 1.0
		population = 1.0
		#cdef double propensity = 1.0
		propensity = 1.0
		#cdef double propensity_minimum = 1e-30
		propensity_minimum = 1e-30
		#cdef int cnt_dex = 1
		cnt_dex = 1
		#cdef int act_dex = 0
		act_dex = 0
		#cdef int cnt
		#cdef int act
		#cdef int k
		for agent in reagents:
			cnt = counts[agent[cnt_dex]]
			act = agent[act_dex]
			for k in range(act): population *= cnt - k
			population /= act

		propensity = population * rate
		if propensity > propensity_minimum: return propensity
		else: return 0.0

	#rate was a float and all stochiometric coefficients = 1
	def propensity_simple():
		#cdef double population = 1.0
		population = 1.0
		#cdef double propensity = 1.0
		propensity = 1.0
		#cdef double propensity_minimum = 1e-30
		propensity_minimum = 1e-30
		#cdef int cnt_dex
		#cdef int cnt
		#list comprehension? probably slower; need to test!
		for cnt_dex in cnt_dexes: population *= counts[cnt_dex]
		propensity = population * rate
		if propensity > propensity_minimum: return propensity
		else: return 0.0

	#rate was a float, there is but one stochiometric
	# coefficient and it is equal to 1
	def propensity_very_simple():
		#cdef double propensity = 1.0
		propensity = 1.0
		#cdef double propensity_minimum = 1e-30
		propensity_minimum = 1e-30
		propensity = counts[cnt_dexes[0]] * rate
		if propensity > propensity_minimum: return propensity
		else: return 0.0

	#rate was a float and there are no reagents
	# this if statement can be preprocessed/configured via lambda function!
	#def propensity_simplest():
	#	cdef double propensity_minimum = 1e-30
	#	cdef double rate
	#	if rate > propensity_minimum: return rate
	#	else: return 0.0

	#if reagents is empty, the reaction is ALWAYS valid
	def validator_constant(): return True

	#if reagents is nonempty, they MUST be checked before reacting
	def validator():
		#cdef int dex
		#cdef int leng = len(cnt_dexes)
		leng = len(cnt_dexes)
		#can this be a list comprehension / does that help?
		for dex in range(leng):
			if counts[cnt_dexes[dex]] < stochios[dex]: return False

		return True

	def reaction():
		for agent in reagents: counts[agent[1]] -= agent[0]
		for agent in products: counts[agent[1]] += agent[0]

	def measure_agent(agent):
		nothings = ['nothing', 'null', '']
		if not agent in nothings:
			one = agent.find('(')
			two = agent.find(')')
			amt = int(agent[one + 1:two])
			spec_dex = count_targets.index(agent[two + 1:])
			return (amt, spec_dex)

		#else: return (0, count_targets.index('null'))
		else: return None

	split = rxn_string.split('->')
	try:
		rate = float(split[1])
		rate_flag = False

	except ValueError:
		try:
			func_dex = func_names.index(split[1])
			rate = functions[func_dex]
			rate_flag = True

		except ValueError:
			var_dex = variables.index(split[1])
			rate = float(var_vals[var_dex])
			rate_flag = False

	#cdef double propensity_minimum = 1e-30
	propensity_minimum = 1e-30
	reagents = [measure_agent(agent) for agent in split[0].split('+')]
	products = [measure_agent(agent) for agent in split[2].split('+')]
	cnt_dexes = [agent[1] for agent in reagents]
	try:
		stochios, cnt_dexes = zip(*[(agent[0], cnt) for agent, cnt 
					in zip(reagents, cnt_dexes) if agent[0] > 0])

	except ValueError: stochios, cnt_dexes = [], []
	if len(cnt_dexes) == 0: has_reagents = False
	elif len(cnt_dexes) == 1 and stochios[0] > 0:
		has_reagents = True; only_one_reagent = True

	else: has_reagents = True; only_one_reagent = False
	if len(stochios) == sum(stochios): single_stochios = True
	rate_call_group.append(rate_flag)
	if not rate_flag:
		if not has_reagents:
			valid = validator_constant
			if rate > propensity_minimum:
				correct_propensity = lambda: rate

			else: correct_propensity = lambda: 0.0

		else:
			valid = validator
			if only_one_reagent and single_stochios:
				correct_propensity = propensity_very_simple

			elif single_stochios: correct_propensity = propensity_simple
			else: correct_propensity = propensity

	else:
		if not has_reagents:
			valid = validator_constant
			correct_propensity = propensity_simplest_with_rate_call

		else:
			valid = validator
			if only_one_reagent and single_stochios:
				correct_propensity = propensity_very_simple_with_rate_call

			elif single_stochios:
				correct_propensity = propensity_simple_with_rate_call

			else: correct_propensity = propensity_with_rate_call

	return correct_propensity, valid, reaction, reagents, products


'''
def generate_reaction(count_targets, counts, functions, func_names, 
				var_vals, variables, rxn_string, rate_call_group):

	#rate was not a float and some stochiometric coefficient > 1; slowest
	def propensity_with_rate_call():
		cdef double population = 1.0
		cdef double propensity = 1.0
		cdef double propensity_minimum = 1e-30
		cdef int cnt_dex = 1
		cdef int act_dex = 0
		cdef int cnt
		cdef int k
		for agent in reagents:
			cnt = counts[agent[cnt_dex]]
			act = agent[act_dex]
			for k in range(act): population *= cnt - k
			population /= act

		propensity = population * rate(counts)
		if propensity > propensity_minimum: return propensity
		else: return 0.0

	#rate was not a float and all stochiometric coefficients = 1
	def propensity_simple_with_rate_call():
		cdef double population = 1.0
		cdef double propensity = 1.0
		cdef double propensity_minimum = 1e-30
		propensity_minimum = 1e-30
		cdef int cnt_dex
		cdef int cnt
		for cnt_dex in cnt_dexes: population *= counts[cnt_dex]
		propensity = population * rate(counts)
		if propensity > propensity_minimum: return propensity
		else: return 0.0

	#rate was not a float, there is but one stochiometric
	# coefficient and it is equal to 1
	def propensity_very_simple_with_rate_call():
		cdef double population = 1.0
		cdef double propensity = 1.0
		cdef double propensity_minimum = 1e-30
		cdef double zero = 0.0
		propensity = counts[cnt_dexes[0]] * rate(counts)
		if propensity > propensity_minimum: return propensity
		else: return zero	#is this faster?

	#rate was not a float and there are no reagents
	def propensity_simplest_with_rate_call():
		cdef double propensity = 1.0
		cdef double propensity_minimum = 1e-30
		propensity_minimum = 1e-30
		propensity = rate(counts)
		if propensity > propensity_minimum: return propensity
		else: return 0.0

	#rate was a float and some stochiometric coefficient > 1
	def propensity():
		cdef double population = 1.0
		cdef double propensity = 1.0
		cdef double propensity_minimum = 1e-30
		cdef int cnt_dex = 1
		cdef int act_dex = 0
		cdef int cnt
		cdef int act
		cdef int k
		for agent in reagents:
			cnt = counts[agent[cnt_dex]]
			act = agent[act_dex]
			for k in range(act): population *= cnt - k
			population /= act

		propensity = population * rate
		if propensity > propensity_minimum: return propensity
		else: return 0.0

	#rate was a float and all stochiometric coefficients = 1
	def propensity_simple():
		cdef double population = 1.0
		cdef double propensity = 1.0
		cdef double propensity_minimum = 1e-30
		cdef int cnt_dex
		cdef int cnt
		#list comprehension? probably slower; need to test!
		for cnt_dex in cnt_dexes: population *= counts[cnt_dex]
		propensity = population * rate
		if propensity > propensity_minimum: return propensity
		else: return 0.0

	#rate was a float, there is but one stochiometric
	# coefficient and it is equal to 1
	def propensity_very_simple():
		cdef double propensity = 1.0
		cdef double propensity_minimum = 1e-30
		propensity = counts[cnt_dexes[0]] * rate
		if propensity > propensity_minimum: return propensity
		else: return 0.0

	def validator_constant(): return True

	#if reagents is nonempty, they MUST be checked before reacting
	def validator():
		cdef int dex
		cdef int leng = len(cnt_dexes)
		#can this be a list comprehension / does that help?
		for dex in range(leng):
			if counts[cnt_dexes[dex]] < stochios[dex]: return False

		return True

	def reaction():
		for agent in reagents: counts[agent[1]] -= agent[0]
		for agent in products: counts[agent[1]] += agent[0]

	def measure_agent(agent):
		nothings = ['nothing', 'null', '']
		if not agent in nothings:
			one = agent.find('(')
			two = agent.find(')')
			amt = int(agent[one + 1:two])
			spec_dex = count_targets.index(agent[two + 1:])
			return (amt, spec_dex)

		else: return (0, count_targets.index('null'))

	split = rxn_string.split('->')
	try:
		rate = float(split[1])
		rate_flag = False

	except ValueError:
		try:
			func_dex = func_names.index(split[1])
			rate = functions[func_dex]
			rate_flag = True

		except ValueError:
			var_dex = variables.index(split[1])
			rate = float(var_vals[var_dex])
			rate_flag = False

	cdef double propensity_minimum = 1e-30
	reagents = [measure_agent(agent) for agent in split[0].split('+')]
	products = [measure_agent(agent) for agent in split[2].split('+')]
	cnt_dexes = [agent[1] for agent in reagents]
	try:
		stochios, cnt_dexes = zip(*[(agent[0], cnt) for agent, cnt 
					in zip(reagents, cnt_dexes) if agent[0] > 0])

	except ValueError: stochios, cnt_dexes = [], []
	if len(cnt_dexes) == 0: has_reagents = False
	elif len(cnt_dexes) == 1 and stochios[0] > 0:
		has_reagents = True; only_one_reagent = True

	else: has_reagents = True; only_one_reagent = False
	if len(stochios) == sum(stochios): single_stochios = True
	rate_call_group.append(rate_flag)
	if not rate_flag:
		if not has_reagents:
			valid = validator_constant
			if rate > propensity_minimum:
				correct_propensity = lambda: rate

			else: correct_propensity = lambda: 0.0

		else:
			valid = validator
			if only_one_reagent and single_stochios:
				correct_propensity = propensity_very_simple

			elif single_stochios: correct_propensity = propensity_simple
			else: correct_propensity = propensity

	else:
		if not has_reagents:
			valid = validator_constant
			correct_propensity = propensity_simplest_with_rate_call

		else:
			valid = validator
			if only_one_reagent and single_stochios:
				correct_propensity = propensity_very_simple_with_rate_call

			elif single_stochios:
				correct_propensity = propensity_simple_with_rate_call

			else: correct_propensity = propensity_with_rate_call

	return correct_propensity, valid, reaction, reagents, products
'''


#cdef uniq(seq):
def uniq(seq):
	seen = {}
	result = []
	for item in seq:
		if item in seen: continue
		seen[item] = 1
		result.append(item)

	return result


def wrap_propensities(propensity_table, propensities, 
				reagents, products, rate_call_group):

	def generate_wrap(lookup):

		def propensity_wrap():
			#cdef int dex
			#cdef int sub_dex
			for dex in range(leng):
				sub_dex = lookup[dex]
				propensity_table[sub_dex] = propensities[sub_dex]()

		#cdef int leng = len(lookup)
		leng = len(lookup)
		return propensity_wrap

	#if any reactions propensity depends on say time, it must be appended
	#	to every lookup
	#		alwayses should consist of the indexes of every propensity 
	#			which requires a rate call
	alwayses = [dex for dex in range(len(rate_call_group)) 
								if rate_call_group[dex]]
	propensity_lookups = [[] for prop in propensities]
	for dex in range(len(reagents)):
		current = set([agent[1] for agent in products[dex]])
		for dex2 in range(len(reagents)):
			temporary = set([agent[1] for agent in reagents[dex2]])
			if temporary & current:
				propensity_lookups[dex].append(dex2)

		propensity_lookups[dex].extend(alwayses)

	propensity_lookups = [uniq(lookup) for lookup in propensity_lookups]
	propensity_lookups.append(range(len(propensity_table)))
	return [generate_wrap(lookup) for lookup in propensity_lookups]


#cdef inline int pick_reaction(double [:] table, double rand, int leng):
def pick_reaction(table, rand, leng):
	#cdef int dex
	for dex in range(leng):
		if rand < table[dex]:
			return dex


def rxn_pass(): pass


def simulate(system_string = '<species>Substrate:10000,Enzyme:5000,ES_Complex:0,Product:0<variables>k:0.5<functions>ratio=Substrate/(Enzyme+k)<reactions>(1)Substrate+(1)Enzyme->1.0->(1)ES_Complex,(1)ES_Complex->0.01->(1)Substrate+(1)Enzyme,(1)ES_Complex->800.0->(1)Enzyme+(1)Product<end>time>=0.00098<capture>increment:time:0.00002<targets>ES_Complex,Product,iteration,time||'):
#def simulate(system_string = '<species>Substrate:10000,Enzyme:5000,ES_Complex:0,Product:0<variables>k:0.5<functions>ratio=Substrate/(Enzyme+k)<reactions>(1)Substrate+(1)Enzyme->1.0->(1)ES_Complex,(1)ES_Complex->0.01->(1)Substrate+(1)Enzyme,(1)ES_Complex->800.0->(1)Enzyme+(1)Product<end>iteration>=10000<capture>increment:time:0.00002<targets>ES_Complex,Product,iteration,time||'):

	capture_dex = 0
	propensity_total_inv = 1.0
	#iteration = 0
	time = 0.0

	species, next_dex = parse(system_string, 0, '<variables>')
	variables, next_dex = parse(system_string, next_dex, '<functions>')
	functions, next_dex = parse(system_string, next_dex, '<reactions>')
	rxns, next_dex = parse(system_string, next_dex, '<end>')
	end, next_dex = parse(system_string, next_dex, '<capture>')
	capture, next_dex = parse(system_string, next_dex, '<targets>')
	targets, next_dex = parse(system_string, next_dex, '||')


	species, counts = zip(*[spec.split(':') for spec in 
			species[species.find('>') + 1:].split(',')])


	sub_var_string = variables[variables.find('>') + 1:].split(',')
	if sub_var_string[0]:
		variables, var_vals = zip(*[vari.split(':') 
					for vari in sub_var_string])
		var_vals = [float(amt) for amt in var_vals]

	else: variables, var_vals = [], []

	count_targets = ['iteration', 'time'] + list(species) + list(variables)
	counts = [0, 0.0] + [int(amt) for amt in counts] + var_vals

	targets = targets[targets.find('>') + 1:].split(',')
	targets = [targ for targ in count_targets if targ in targets]

	functions = functions[functions.find('>') + 1:].split(',')
	if functions[0]:
		func_names, functions = generate_functions(
				functions, count_targets, counts)

	else: func_names, functions = [], []
	update_functions = generate_update_functions(
		count_targets, counts, functions, func_names)
	count_targets.extend(func_names)
	counts.extend([func(counts) for func in functions])

	rxn_split = rxns[rxns.find('>') + 1:].split(',')
	rate_call_group = []
	propensities, validators, reactions, reagents, products =\
			zip(*[generate_reaction(count_targets, counts, functions, 
				func_names, var_vals, variables, rxn_string, 
				rate_call_group) for rxn_string in rxn_split])
	reactions = list(reactions)
	reactions.append(rxn_pass)
	propensity_count = len(rxn_split)
	#cdef double [:] propensity_table
	propensity_table = np.zeros(propensity_count)
	for dex, prop in enumerate(propensities):
		propensity_table[dex] = prop()

	propensities = wrap_propensities(propensity_table, 
		propensities, reagents, products, rate_call_group)

	#cdef double [:] rxn_table
	rxn_table = np.zeros(propensity_count, dtype = np.float)

	#only allow one end criterion, only time limit or iteration limit
	end = end[end.find('>') + 1:]
	if end.startswith('time'):
		end_crit_dex = 1
		end_crit_limit = float(end[end.find('time') + 6:])

	else: print 'end criterion parsing problem'
	#only allow one capture criterion, increment time or increment iteration
	capture = capture[capture.find('>') + 1:].split(':')
	if capture[0].startswith('increment'):
		if capture[1].startswith('time') and end_crit_dex == 1:
			capt_crit_dex = 1
			capt_crit_thresh = float(capture[2])

		else: print 'capture criterion parsing problem'
	else: print 'capture criterion parsing problem'
	total_captures = int(end_crit_limit/capt_crit_thresh)
	print 'tc', total_captures

	data = np.zeros(shape = (len(targets), total_captures), dtype = np.float)
	target_dexes = [count_targets.index(targ) for targ in targets]

	#perform initial state capture -> necessary!
	data[:,capture_dex] = [counts[dex] for dex in target_dexes]
	capture_dex += 1

	while capture_dex < total_captures:
	#while not counts[end_crit_dex] >= end_crit_limit:
		if counts[0] == 10000: print 'time', counts[1]
		#print 'end crit', counts[end_crit_dex], end_crit_limit
		propensity_total = 0.0
		for prop_dex in range(propensity_count):
			if validators[prop_dex]():
				propensity_total += propensity_table[prop_dex]

			rxn_table[prop_dex] = propensity_total

		if propensity_total > 0.0:
			propensity_total_inv = 1.0/propensity_total
			for dex in range(propensity_count):
				rxn_table[dex] = rxn_table[dex] * propensity_total_inv

			#rand_time = rndvar.gen()
			rand_time = random.random()
			time_step = -1.0 * log(rand_time) * propensity_total_inv
			time_step = min([capt_crit_thresh, time_step])
			#rand_rxn = rndvar.gen()
			rand_rxn = random.random()
			rxn_dex = pick_reaction(rxn_table, rand_rxn, propensity_count)

		else:
			print 'all impossible.... continuing...'
			time_step = capt_crit_thresh
			rxn_dex = -1

		counts[0] += 1
		counts[1] += time_step
		if counts[capt_crit_dex] - data[capt_crit_dex][capture_dex] >= capt_crit_thresh:
			time += capt_crit_thresh
			real_time = counts[1]
			counts[1] = time
			update_functions()
			data[:,capture_dex] = [counts[dex] for dex in target_dexes]
			capture_dex += 1
			counts[1] = real_time

		reactions[rxn_dex]()
		propensities[rxn_dex]()

	pdb.set_trace()
	return data, targets




