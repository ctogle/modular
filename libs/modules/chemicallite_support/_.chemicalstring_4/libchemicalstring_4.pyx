#imports
# cython: profile=False
#cimport cython

from libc.math cimport log
#from libc.math cimport sin as sin
#from libc.math cimport cos as cos
from math import sin as sin
from math import cos as cos
# from libc.math cimport fmax
# from math import log

import random
import numpy as np
import re

from numpy import pi

#System State Variables
cdef SIM_COUNTS
cdef int SIM_COUNTS_LENGTH
cdef int SIM_FUNCTION_INDEX
cdef SIM_COUNT_TARGETS

#############
### Rates ###
#############

cpdef double heaviside(double value):
	return 1.0 if value > 0.0 else 0.0

cpdef double gauss_noise(double value, double SNR):
	noise = random.gauss(0.0, 1.0)
	return value + value*noise/SNR

#TODO consider using __call__ instead of calculate
cdef class Rate:
	"""
	Rate that represents a lambda function
	"""
	cdef lam

	def __init__(self, lam):
		self.lam = lam

	cpdef double calculate(self):
		global SIM_COUNTS
		return self.lam(SIM_COUNTS)

#################
### End Rates ###
#################

####################
### Propensities ###
####################

cdef inline double zero_if_below_minimum(double value):
	return value if value > 1e-30 else 0.0


cdef class PropensityBase:
	cdef int [:] cnt_dexes
	cdef reagents
	cdef double propensity_minimum

	cpdef double calculate(self):
		raise NotImplementedError

cdef class Propensity(PropensityBase):
	cdef double rate

	def __init__(self, reagents, rate):
		self.reagents = reagents
		self.rate = rate

	#rate was a float and some stochiometric coefficient > 1
	cpdef double calculate(self):
		global SIM_COUNTS
		cdef int cnt_dex
		cdef int [:] agent
		population = 1.0
		propensity = 1.0
		propensity_minimum = 1e-30
		cnt_dex = 1
		act_dex = 0
		for agent in self.reagents:
			cnt = SIM_COUNTS[agent[cnt_dex]]
			act = agent[act_dex]
			for k in range(act): population *= cnt - k
			population /= act

		propensity = population * self.rate
		return zero_if_below_minimum(propensity)

cdef class PropensitySimple(PropensityBase):

	cdef int leng
	cdef double rate

	def __init__(self, cnt_dexes, rate):
		self.cnt_dexes = cnt_dexes
		self.leng = len(cnt_dexes)
		self.rate = rate

	#rate was a float and all stochiometric coefficients = 1
	cpdef double calculate(self):
		global SIM_COUNTS
		cdef double population = 1.0
		cdef int cnt_dex
		for cnt_dex in range(self.leng):
			population = population * SIM_COUNTS[self.cnt_dexes[cnt_dex]]
		cdef double propensity = population * self.rate
		return zero_if_below_minimum(propensity)

cdef class PropensityVerySimple(PropensityBase):

	cdef double rate

	def __init__(self, cnt_dexes, rate):
		self.cnt_dexes = cnt_dexes
		self.rate = rate

	#rate was a float, there is but one stochiometric
	# coefficient and it is equal to 1
	cpdef double calculate(self):
		return zero_if_below_minimum(SIM_COUNTS[self.cnt_dexes[0]] * self.rate)

cdef class PropensitySimplestWithRateCall(PropensityBase):
	cdef Rate rate

	def __init__(self, rate):
		self.rate = rate

	#rate was not a float and there are no reagents
	cpdef double calculate(self):
		return zero_if_below_minimum(self.rate.calculate())

cdef class PropensityVerySimpleWithRateCall(PropensityBase):
	cdef Rate rate

	def __init__(self, cnt_dexes, rate):
		self.cnt_dexes = cnt_dexes
		self.rate = rate

	#rate was not a float, there is but one stochiometric
	# coefficient and it is equal to 1
	cpdef double calculate(self):
		global SIM_COUNTS
		propensity = SIM_COUNTS[self.cnt_dexes[0]] * self.rate.calculate()
		return zero_if_below_minimum(propensity)

cdef class PropensitySimpleWithRateCall(PropensityBase):
	cdef Rate rate

	def __init__(self, cnt_dexes, rate):
		self.cnt_dexes = cnt_dexes
		self.rate = rate

	#rate was not a float and all stochiometric coefficients = 1
	cpdef double calculate(self):
		global SIM_COUNTS
		cdef double population = 1.0
		cdef double propensity
		cdef int cnt_dex
		for cnt_dex in self.cnt_dexes:
			population *= SIM_COUNTS[cnt_dex]
		propensity = population * self.rate.calculate()
		return zero_if_below_minimum(propensity)

cdef class PropensityWithRateCall(PropensityBase):
	cdef Rate rate

	def __init__(self, cnt_dexes, rate, reagents):
		self.cnt_dexes = cnt_dexes
		self.rate = rate
		self.reagents = reagents

	#rate was not a float and some stochiometric coefficient > 1; slowest
	cpdef double calculate(self):
		global SIM_COUNTS
		population = 1.0
		cnt_dex = 1
		act_dex = 0
		for agent in self.reagents:
			cnt = SIM_COUNTS[agent[cnt_dex]]
			act = agent[act_dex]
			for k in range(act): population *= cnt - k
			population /= act

		propensity = population * self.rate.calculate()
		return zero_if_below_minimum(propensity)

cdef class PropensityConstant(PropensityBase):

	cdef double val

	def __init__(self, val):
		self.val = val

	cpdef double calculate(self):
		return self.val

########################
### End Propensities ###
########################


cdef class PropensityUpdater:

	cdef int [:] lookup
	cdef int leng
	cdef double [:] propensity_table
	cdef PropensityBase [:] propensities
	cdef int dex

	def __init__(self, lookup, propensity_table, propensities):
		self.lookup = lookup
		self.propensity_table = propensity_table
		self.propensities = propensities
		self.leng = len(self.lookup)

	cpdef update(self):
		cdef int dex
		for dex in range(self.leng):
			dex = self.lookup[dex]
			self.propensity_table[dex] = \
				(<PropensityBase>self.propensities[dex]).calculate()


##################
### Validators ###
##################

cdef class Validator:
	cpdef bint validate(self):
		raise NotImplementedError

cdef class TrueValidator(Validator):
	#if reagents is empty, the reaction is ALWAYS valid

	cpdef bint validate(self):
		return True

cdef class StochioValidator(Validator):

	cdef int [:] stochios
	cdef int [:] stochio_dexes
	cdef int stochio_len

	def __init__(self, stochios, stochio_dexes):
		self.stochios = stochios
		self.stochio_dexes = stochio_dexes
		self.stochio_len = len(self.stochio_dexes)


	#if reagents is nonempty, they MUST be checked before reacting
	cpdef bint validate(self):
		global SIM_COUNTS
		cdef int dex
		for dex in range(self.stochio_len):
			#make sure there is enough of a reagent to react
			if SIM_COUNTS[self.stochio_dexes[dex]] < self.stochios[dex]:
				return False
		return True


######################
### End Validators ###
######################

#################
### Reactions ###
#################


cdef class Reaction:
	cpdef reagents
	cpdef products

	def __init__(self, reagents, products):
		self.reagents = reagents
		self.products = products

	cpdef react(self):
		global SIM_COUNTS
		for agent in self.reagents: SIM_COUNTS[agent[1]] -= agent[0]
		for agent in self.products: SIM_COUNTS[agent[1]] += agent[0]

cdef class ReactionPass(Reaction):

	def __init__(self):
		pass

	cpdef react(self):
		pass


#####################
### End Reactions ###
#####################

cdef class SystemParser:

	cpdef string_to_dict(self, system_string):
		"""
		Take a system string and convert it to a dict of label, string pairs

		:param system_string: a string that represents system state
		:rtype : dict
		"""
		ptx = re.compile('<(.*?)>')
		parts = ptx.split(system_string)[1:]
		labels = parts[::2]
		values = parts[1::2]
		return dict(zip(labels, values))

	cpdef parse_name_value_pairs(self, s, operator=None):
		pair_strings = s.split(',')
		if pair_strings[0]:
			pairs = [pair_string.split(':') for pair_string in pair_strings]
			names, values = zip(*pairs)
			if operator:
				values = [operator(val) for val in values]
		else:
			names, values = [], []

		return names, values





#################
### Processes ###
#################

cdef class FunctionUpdater:
	cdef func_names
	cdef functions
	cdef int _ct_leng

	def __init__(self, func_names, functions):
		self.func_names = func_names
		self.functions = functions

	def update(self):
		global SIM_COUNTS, SIM_COUNTS_LENGTH
		cdef int dex
		for dex in range(SIM_FUNCTION_INDEX, SIM_COUNTS_LENGTH):
			SIM_COUNTS[dex] = self.functions[dex - SIM_FUNCTION_INDEX](SIM_COUNTS)

cdef class FunctionUpdaterDummy(FunctionUpdater):

	def __init__(self):
		pass

	def update(self):
		#print 'dummy update functions'
		pass


#create a function which updates the current functions' values
def generate_update_functions(functions, func_names):
	if not func_names:
		return FunctionUpdaterDummy()
	else:
		return FunctionUpdater(func_names, functions)

def measure_agent(agent, count_targets):
	nothings = ['nothing', 'null', '']
	if not agent in nothings:
		one = agent.find('(')
		two = agent.find(')')
		amt = int(agent[one + 1:two])
		spec_dex = count_targets.index(agent[two + 1:])
		return (amt, spec_dex)

	#else: return (0, count_targets.index('null'))
	else: return None


def pick_validator(cnt_dexes, stochios):
	#Pick a Validator
	has_reagents = len(cnt_dexes) > 0
	if has_reagents:
		return StochioValidator(stochios, cnt_dexes)
	else:
		return TrueValidator()

cdef PropensityBase pick_propensity_type(int [:] cnt_dexes, rate, rate_flag,
		reagents, stochios):

	has_reagents = len(cnt_dexes) > 0
	only_one_reagent = len(cnt_dexes) == 1
	single_stochios = len(stochios) == sum(stochios)

	#Pick a Propensity Type
	if not rate_flag:
		if not has_reagents:
			return PropensityConstant(zero_if_below_minimum(rate))
		else:
			if only_one_reagent and single_stochios:
				return PropensityVerySimple(cnt_dexes, rate)
			elif single_stochios:
				return PropensitySimple(cnt_dexes, rate)
			else:
				return Propensity(reagents, rate)
	else:
		if not has_reagents:
			return PropensitySimplestWithRateCall(rate)
		else:
			if only_one_reagent and single_stochios:
				return PropensityVerySimpleWithRateCall(cnt_dexes, rate)
			elif single_stochios:
				return PropensitySimpleWithRateCall(cnt_dexes, rate)
			else:
				return PropensityWithRateCall(cnt_dexes, rate, reagents)

def get_stochios(reagent_cnt_dexes, reagents):
	try:
		stochios, cnt_dexes = zip(*[(agent[0], cnt) for agent, cnt
			in zip(reagents, reagent_cnt_dexes) if agent[0] > 0])
	except ValueError:
		stochios, cnt_dexes = [], []
	stochios = np.array(stochios, dtype=np.dtype(np.int32))
	cnt_dexes = np.array(cnt_dexes, dtype=np.dtype(np.int32))
	return cnt_dexes, stochios

def get_rate(func_names, functions, rxn_strings, var_vals, variables):
	try:
		rate = float(rxn_strings[1])
		rate_flag = False

	except ValueError:
		try:
			func_dex = func_names.index(rxn_strings[1])
			rate = Rate(functions[func_dex])
			rate_flag = True

		except ValueError:
			var_dex = variables.index(rxn_strings[1])
			rate = float(var_vals[var_dex])
			rate_flag = False
	return rate, rate_flag

def generate_reaction(count_targets, functions, func_names,
				var_vals, variables, rxn_string, rate_call_group):

	rxn_strings = rxn_string.split('->')
	rate, rate_flag = get_rate(func_names, functions, rxn_strings, var_vals, variables)
	rate_call_group.append(rate_flag)

	products = [measure_agent(agent, count_targets) for agent in rxn_strings[2].split('+')]
	reagents = [measure_agent(agent, count_targets) for agent in rxn_strings[0].split('+')]
	products = [prod for prod in products if prod]
	reagents = [reag for reag in reagents if reag]
	reagent_cnt_dexes = [agent[1] for agent in reagents]

	stochio_dexes, stochios = get_stochios(reagent_cnt_dexes, reagents)

	propensity = pick_propensity_type(stochio_dexes, rate, rate_flag, reagents,
		stochios)
	valid = pick_validator(stochio_dexes, stochios)
	reaction = Reaction(reagents, products)
	return propensity, valid, reaction, reagents, products

#cdef uniq(seq):
def uniq(seq):
	seen = {}
	result = []
	for item in seq:
		if item in seen: continue
		seen[item] = 1
		result.append(item)

	return result


cdef PropensityUpdater wrap_propensity(lookup, propensity_table, propensities):
	lookup = np.array(lookup, dtype=np.dtype(np.int32))
	return PropensityUpdater(lookup, propensity_table, propensities)

cdef PropensityUpdater [:] wrap_propensities(propensity_table, propensities,
				reagents, products, rate_call_group):

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
	return np.array([wrap_propensity(lookup, propensity_table, propensities)
		for lookup in propensity_lookups])


cdef inline int pick_reaction(double [:] table, int leng):
# def pick_reaction(table, leng):
	cdef double rand = random.random()
	cdef int dex
	for dex in range(leng):
		if rand < table[dex]:
			return dex


cdef inline double get_propensity(int propensity_count,
		double [:] propensity_table, double [:] rxn_table,
		Validator [:] validators):
# def get_propensity(propensity_count, propensity_table, rxn_table, validators):
	cdef double propensity_total = 0.0
	cdef int dex
	for dex in range(propensity_count):
		if (<Validator> validators[dex]).validate():
			propensity_total += propensity_table[dex]
		rxn_table[dex] = propensity_total
	return propensity_total

def get_counts():
	global SIM_COUNTS
	return SIM_COUNTS

#turn function strings into compiled lambda functions
def generate_functions(count_targets, functions_string):
	function_strs = functions_string.split(',')

	def convert(substr):
		if substr in count_targets:
			return "".join([
				"counts[",
				str(count_targets.index(substr)),
				"]"])
		else:
			return substr

	def encode(string):
		return ''.join([convert(substr) for substr in string])

	func_names = [fu[:fu.find('=')] for fu in function_strs]
	encoded_functions = [fu[fu.find('=') + 1:].replace('&', ',') 
										for fu in function_strs]
	encoded_lambdas = ['lambda counts: ' + encode(re.split('(\W)', string))
											for string in encoded_functions]
	funcs = [eval(expr) for expr in encoded_lambdas]
	return func_names, funcs


#def simulate(system_string = '<species>Substrate:10000,Enzyme:5000,ES_Complex:0,Product:0<variables>k:0.5<functions>ratio=gauss_noise(heaviside(sin(time*62800.0))&10.0)<reactions>(1)Substrate+(1)Enzyme->1.0->(1)ES_Complex,(1)ES_Complex->0.01->(1)Substrate+(1)Enzyme,(1)ES_Complex->ratio->(1)Enzyme+(1)Product<end>time>=0.00098<capture>increment:time:0.00002<targets>ES_Complex,Product,iteration,time,ratio||'):
def simulate(system_string = '<species>Substrate:10000,Enzyme:5000,ES_Complex:0,Product:0<variables>k:0.5<functions>ratio=Substrate/(Enzyme+k)<reactions>(1)ES_Complex->800.0->(1)Enzyme+(1)Product,(1)Substrate+(1)Enzyme->1.0->(1)ES_Complex,(1)ES_Complex->0.01->(1)Substrate+(1)Enzyme<end>time>=0.00098<capture>increment:time:0.00002<targets>ES_Complex,Product,iteration,time||'):
#def simulate(system_string = '<species>Substrate:10000,Enzyme:5000,ES_Complex:0,Product:0<variables>k:0.5<functions>ratio=Substrate/(Enzyme+k)<reactions>(1)Substrate+(1)Enzyme->1.0->(1)ES_Complex,(1)ES_Complex->0.01->(1)Substrate+(1)Enzyme,(1)ES_Complex->800.0->(1)Enzyme+(1)Product<end>iteration>=10000<capture>increment:time:0.00002<targets>ES_Complex,Product,iteration,time||'):

	#backward compatability
	if system_string[-2:] == '||':
		system_string = system_string[:-2]

	capture_dex = 0
	#iteration = 0
	time = 0.0

	cdef SystemParser parser = SystemParser()
	strs = parser.string_to_dict(system_string)
	species = strs['species']
	variables = strs['variables']
	functions_string = strs['functions']
	rxns = strs['reactions']
	end = strs['end']
	capture_str = strs['capture']
	targets = strs['targets']


	species, species_counts = parser.parse_name_value_pairs(species, float)
	variables, var_vals = parser.parse_name_value_pairs(variables, float)

	count_targets = ['iteration', 'time'] + list(species) + list(variables)
	counts = [0, 0.0] + species_counts + var_vals
	if functions_string.strip() == '': func_names, functions = [], []
	else: func_names, functions = generate_functions(count_targets, functions_string)

	cdef FunctionUpdater update_functions
	update_functions = generate_update_functions(functions,func_names)

	global SIM_FUNCTION_INDEX
	SIM_FUNCTION_INDEX = len(count_targets)

	count_targets.extend(func_names)
	counts.extend([func(counts) for func in functions])

	targets = targets.split(',')
	targets = [targ for targ in count_targets if targ in targets]

	global SIM_COUNTS, SIM_COUNTS_LIST, SIM_COUNTS_LENGTH
	SIM_COUNTS = counts
	SIM_COUNTS_LENGTH = len(counts)
	SIM_COUNT_TARGETS = count_targets


	rxn_split = rxns.split(',')
	rate_call_group = []
	propensities, validators_untyped, reactions, reagents, products =\
			zip(*[generate_reaction(count_targets, functions,
				func_names, var_vals, variables, rxn_string,
				rate_call_group) for rxn_string in rxn_split])
	cdef Validator [:] validators = np.array(validators_untyped)
	reactions = list(reactions)
	reactions.append(ReactionPass())
	cdef int propensity_count = len(rxn_split)
	cdef double [:] propensity_table = np.zeros(propensity_count, dtype=np.float)
	cdef int dex
	for dex, prop in enumerate(propensities):
		propensity_table[dex] = prop.calculate()

	propensities = np.array(propensities)
	cdef PropensityUpdater [:] propensity_updaters = wrap_propensities(
		propensity_table, propensities, reagents, products, rate_call_group)

	cdef double [:] rxn_table = np.zeros(propensity_count, dtype = np.float)

	#only allow one end criterion, only time limit or iteration limit
	if end.startswith('time'):
		end_crit_dex = 1
		end_crit_limit = float(end[end.find('time') + 6:])
	else: print 'end criterion parsing problem'
	#only allow one capture criterion, increment time or increment iteration
	capture = capture_str.split(':')
	if capture[0].startswith('increment'):
		if capture[1].startswith('time') and end_crit_dex == 1:
			capt_crit_dex = 1
			capt_crit_thresh = float(capture[2])

		else: print 'capture criterion parsing problem'
	else: print 'capture criterion parsing problem'
	total_captures = int(end_crit_limit/capt_crit_thresh)

	data = np.zeros(shape = (len(targets), total_captures), dtype = np.float)
	target_dexes = [count_targets.index(targ) for targ in targets]

	#perform initial state capture -> necessary!
	#data[:,capture_dex] = [SIM_COUNTS[dex] for dex in target_dexes]
	#capture_dex += 1

	cdef int rxn_dex
	cdef double propensity_total_inv
	cdef double last_time = 0.0
	while capture_dex < total_captures:
		propensity_total = get_propensity(propensity_count, 
					propensity_table, rxn_table, validators)
		if propensity_total > 0.0:
			propensity_total_inv = 1.0/propensity_total
			for dex in range(propensity_count):
				rxn_table[dex] *= propensity_total_inv

			time_step = -1.0 * log(<double> random.random()) * propensity_total_inv
			rxn_dex = pick_reaction(rxn_table, propensity_count)

		else:
			#print 'all impossible.... continuing...'
			time_step = capt_crit_thresh
			rxn_dex = -1

		#SIM_COUNTS[0] += 1
		#SIM_COUNTS[1] += time_step
		while last_time < SIM_COUNTS[1] and capture_dex < total_captures:
			real_time = SIM_COUNTS[1]
			last_time += capt_crit_thresh
			SIM_COUNTS[1] = last_time
			update_functions.update()
			data[:,capture_dex] = [SIM_COUNTS[dex] for dex in target_dexes]
			capture_dex += 1
			SIM_COUNTS[1] = real_time

		SIM_COUNTS[0] += 1
		SIM_COUNTS[1] += time_step
		(<Reaction> reactions[rxn_dex]).react()
		(<PropensityBase> propensity_updaters[rxn_dex]).update()

	return data, targets

