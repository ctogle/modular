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


############################################################################
############################################################################

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

############################################################################
############################################################################

####################
### Propensities ###
####################


#############################################################################
# a very long list of propensity classes, depending on the form of reaction #
#############################################################################


# a fast rounding function used by the below classes
cdef inline double zero_if_below_minimum(double value):
	return value if value > 1e-30 else 0.0


# classes for propensities:
# potentially uses / contains:
#		-cnt_dexes: memoryview of reactant count indices
#		-rate: double precision or Rate object
#		-reagents: entries are like (amt, spec_dex)


################
################

# base class for propensities
cdef class PropensityBase:
	cdef int [:] cnt_dexes
	cdef reagents

	# abstract class, cannot calculate propensity
	cpdef double calculate(self):
		raise NotImplementedError

################
################

cdef class Propensity(PropensityBase):
	cdef double rate

	def __init__(self, reagents, rate):
		#print '=== Propensity constructor called ==='
		self.reagents = reagents
		self.rate = rate

	# rate was a float and some stochiometric coefficient > 1
	cpdef double calculate(self):
		global SIM_COUNTS
		
		# index labels for the "agent" tuple
		cdef int cnt_dex, act_dex
		cnt_dex = 1
		act_dex = 0
		
		# working variables
		cdef int [:] agent
		cdef double population, propensity
		population = 1.0		# the mass action term piece of propensity
		propensity = 1.0		# the final total propensity
		
		for agent in self.reagents:
			cnt = SIM_COUNTS[agent[cnt_dex]]
			act = agent[act_dex]

			# for multiple molecules of same species type, compute mass action term
			# e.g. X*(X-1), or just X			
			for k in range(act): population *= cnt - k

			# POTENTIAL ISSUE HERE - needed??
			# divides by the stoichiometric coefficient
			population /= act

		# compute final propensity
		propensity = population * self.rate
		return zero_if_below_minimum(propensity)

################
################


cdef class PropensitySimple(PropensityBase):

	cdef int leng
	cdef double rate

	def __init__(self, cnt_dexes, rate):
		#print '=== PropensitySimple constructor called ==='
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

################
################

cdef class PropensityVerySimple(PropensityBase):

	cdef double rate

	def __init__(self, cnt_dexes, rate):
		#print '=== PropensityVerySimple constructor called ==='
		self.cnt_dexes = cnt_dexes
		self.rate = rate

	#rate was a float, there is but one stochiometric
	# coefficient and it is equal to 1
	cpdef double calculate(self):
		global SIM_COUNTS
		cdef double propensity
		propensity = SIM_COUNTS[self.cnt_dexes[0]] * self.rate
		#print propensity
		return zero_if_below_minimum(propensity)

################
################


cdef class PropensitySimplestWithRateCall(PropensityBase):
	cdef Rate rate

	def __init__(self, rate):
		#print '=== PropensitySimplestWithRateCall constructor called ==='
		self.rate = rate

	#rate was not a float and there are no reagents
	cpdef double calculate(self):
		return zero_if_below_minimum(self.rate.calculate())

################
################

cdef class PropensityVerySimpleWithRateCall(PropensityBase):
	cdef Rate rate

	def __init__(self, cnt_dexes, rate):
		#print '=== PropensityVerySimpleWithRateCall constructor called ==='
		self.cnt_dexes = cnt_dexes
		self.rate = rate

	#rate was not a float, there is but one stochiometric
	# coefficient and it is equal to 1
	cpdef double calculate(self):
		global SIM_COUNTS
		cdef double propensity
		propensity = SIM_COUNTS[self.cnt_dexes[0]] * self.rate.calculate()
		#print propensity
		return zero_if_below_minimum(propensity)

################
################

cdef class PropensitySimpleWithRateCall(PropensityBase):
	cdef Rate rate

	def __init__(self, cnt_dexes, rate):
		#print '=== PropensitySimpleWithRateCall constructor called ==='
		self.cnt_dexes = cnt_dexes
		self.rate = rate

	#rate was not a float and all stochiometric coefficients = 1
	cpdef double calculate(self):
		global SIM_COUNTS
		cdef double population
		cdef double propensity
		cdef int cnt_dex
		
		population = 1.0
		for cnt_dex in self.cnt_dexes:
			population *= SIM_COUNTS[cnt_dex]
		propensity = population * self.rate.calculate()
		return zero_if_below_minimum(propensity)

################
################

# similar to Propensity class, but with recalculation of the rate function
cdef class PropensityWithRateCall(PropensityBase):
	cdef Rate rate

	def __init__(self, cnt_dexes, rate, reagents):
		#print '=== PropensityWithRateCall constructor called ==='
		self.cnt_dexes = cnt_dexes
		self.rate = rate
		self.reagents = reagents

	#rate was not a float and some stochiometric coefficient > 1; slowest
	cpdef double calculate(self):
		global SIM_COUNTS

		# index labels for the "agent" tuple
		cdef int cnt_dex, act_dex
		cnt_dex = 1
		act_dex = 0
		
		# working variables
		cdef int [:] agent
		cdef double population, propensity
		population = 1.0		# the mass action term piece of propensity
		propensity = 1.0		# the final total propensity

		for agent in self.reagents:
			cnt = SIM_COUNTS[agent[cnt_dex]]
			act = agent[act_dex]

			# for multiple molecules of same species type, compute mass action term
			# e.g. X*(X-1), or just X			
			for k in range(act): population *= cnt - k

			# POTENTIAL ISSUE HERE - needed??
			# divides by the stoichiometric coefficient
			population /= act

		# compute final propensity, including recalculation of rate
		propensity = population * self.rate.calculate()
		return zero_if_below_minimum(propensity)


################
################

cdef class PropensityConstant(PropensityBase):

	cdef double val

	def __init__(self, val):
		#print '=== PropensityConstant constructor called ==='
		self.val = val

	cpdef double calculate(self):
		return self.val

########################
### End Propensities ###
########################

############################################################################
############################################################################

#
# propensity updater class
# one updater per reaction
# 
cdef class PropensityUpdater:

	cdef int [:] lookup
	cdef int leng
	cdef double [:] propensity_table
	cdef PropensityBase [:] propensities
	cdef int dex

	# initialize updater to lookup table of reaction propensity updates
	def __init__(self, lookup, propensity_table, propensities):
		#print '=== PropensityUpdater constructor called ===', lookup
		
		self.lookup = lookup
		self.propensity_table = propensity_table
		self.propensities = propensities
		self.leng = len(self.lookup)

	# based on lookup table, update reactions
	cpdef update(self):
		cdef int dex
		for dex in range(self.leng):
			dex = self.lookup[dex]
			self.propensity_table[dex] = \
				(<PropensityBase>self.propensities[dex]).calculate()


############################################################################
############################################################################

##################
### Validators ###
##################

# abstract base class for validator
cdef class Validator:
	cpdef bint validate(self):
		raise NotImplementedError

# TrueValidator: returns valid (True) always
cdef class TrueValidator(Validator):
	#if reagents is empty, the reaction is ALWAYS valid

	cpdef bint validate(self):
		return True

# StochioValidator: returns valid (True) if there is enough reactants to react
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

############################################################################
############################################################################

#################
### Reactions ###
#################

# actually implements a reaction
# seems to work properly
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


# for a "null" reaction (does nothing)
cdef class ReactionPass(Reaction):

	def __init__(self):
		pass

	cpdef react(self):
		pass

#####################
### End Reactions ###
#####################

############################################################################
############################################################################


# a tool to parse system strings at a coarse level
# essentially, chops up the system string based on "<...>" tags
cdef class SystemParser:

	# breaks apart string alternately into tag / property strings
	# returns this as a dictionary
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
		
		# finally, returns a dictionary
		return dict(zip(labels, values))

	# currently used to get species and variable names and counts
	# breaks text into strings separated by ","
	# produces a list of tuples that are name,value
	cpdef parse_name_value_pairs(self, s, operator=None):
		pair_strings = s.split(',')
		
		# if nonempty, process strings to produce name/value pairs (joined in a tuple)
		if pair_strings[0]:
			pairs = [pair_string.split(':') for pair_string in pair_strings]
			names, values = zip(*pairs)
			if operator:
				values = [operator(val) for val in values]
		else:
			names, values = [], []

		return names, values


############################################################################
############################################################################

#################
### Processes ###
#################

# updates function values when called
# stores results in global list SIM_COUNTS
cdef class FunctionUpdater:
	cdef func_names
	cdef functions
	cdef int _ct_leng

	# initialize the functions names and lambda functions
	def __init__(self, func_names, functions):
		self.func_names = func_names
		self.functions = functions

	# call each of the functions, and store the result in SIM_COUNTS
	def update(self):
		global SIM_COUNTS, SIM_COUNTS_LENGTH
		cdef int dex
		for dex in range(SIM_FUNCTION_INDEX, SIM_COUNTS_LENGTH):
			SIM_COUNTS[dex] = self.functions[dex - SIM_FUNCTION_INDEX](SIM_COUNTS)

###################
###################

# when no functions exist???
cdef class FunctionUpdaterDummy(FunctionUpdater):

	def __init__(self):
		pass

	def update(self):
		#print 'dummy update functions'
		pass


###################
###################

# create a FunctionUpdater object which updates the current functions' values
def generate_update_functions(functions, func_names):
	if not func_names:
		return FunctionUpdaterDummy()
	else:
		return FunctionUpdater(func_names, functions)

############################################################################
############################################################################

# input:
#	-agent: string of the form (Number)Species, e.g. (2)X 
#	-count_targets: set of strings to species (... and variables, and functions)
# returns (amt, spec_dex):
#	-amt: the reaction count (e.g. two of X)
#	-spec_dex: index pointing to species in count_targets
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

############################################################################
############################################################################

# returns a validator, which checks if a reaction is allowed to occur
# useful for queueing systems, which do not (necessarily) obey mass action kinetics
def pick_validator(cnt_dexes, stochios):
	#Pick a Validator
	has_reagents = len(cnt_dexes) > 0
	if has_reagents:
		# if reactants exist, always check
		return StochioValidator(stochios, cnt_dexes)
	else:
		# if there are no reactants, the reaction is ALWAYS valid
		return TrueValidator()

############################################################################
############################################################################

# picks and constructs one of the many propensity classes based on criteria
# possible propensity types:
#	-rate_flag False:
#		-no reactants:
#			-PropensityConstant
#		-with reactants:
#			-PropensityVerySimple, for one molecule of one reactant
#			-PropensitySimple, for one molecule of each reactant (?)
#			-Propensity, otherwise
#	-rate_flag True:
#		-no reactants:
#			-PropensitySimplestWithRateCall
#		-with reactants:
#			-PropensityVerySimpleWithRateCall, for one molecule of one reactant
#			-PropensitySimpleWithRateCall, for one molecule of each reactant (?)
#			-PropensityWithRateCall, otherwise
#
# to these propensity classes, potentially pass:
#		-cnt_dexes: reactant indices
#		-rate: double precision or Rate object
#		-reagents: entries are like (amt, spec_dex)
#
cdef PropensityBase pick_propensity_type(int [:] cnt_dexes, rate, rate_flag,
		reagents, stochios):
		
	# if more than one reactant
	has_reagents = len(cnt_dexes) > 0

	# if only one reactant total
	only_one_reagent = len(cnt_dexes) == 1

	# if the number of molecules used equals the number of reactants
	# NOTE: is this true??  What if someone has something like (0)X+(2)Y?  Is this allowed?
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

############################################################################
############################################################################

# reagents: list of the form (amt, species index)
# reagent_cnt_dexes: only species index
# output:
# 	-cnt_dexes: nparray of corresponding indices of reactants
#	-stochios: nparray of amount of reactant used

def get_stochios(reagent_cnt_dexes, reagents):
	try:
		# stochios: list of amount of reactant used
		# cnt_dexes: list of corresponding indices of reactants
		stochios, cnt_dexes = zip(*[(agent[0], cnt) for agent, cnt
			in zip(reagents, reagent_cnt_dexes) if agent[0] > 0])
	except ValueError:
		stochios, cnt_dexes = [], []
	stochios = np.array(stochios, dtype=np.dtype(np.int32))
	cnt_dexes = np.array(cnt_dexes, dtype=np.dtype(np.int32))
	return cnt_dexes, stochios

############################################################################
############################################################################

# get_rate first tries to make the "rate" a float, returns "rate_flag" as false
# get_rate then tries to find "rate" in the defined functions, returns "rate_flag" as true
# get_rate then tries to find "rate" in the defined variables, returns "rate_flag" as false
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

############################################################################
############################################################################

# key method in parsing reaction system string portion
# used to parse a single reaction and add a flag for this reaction to "rate_call_group"
def generate_reaction(count_targets, functions, func_names,
				var_vals, variables, rxn_string, rate_call_group):

	# first split by LHS and RHS of reaction
	# note: propensity tends to be in the middle of two '->' symbols
	rxn_strings = rxn_string.split('->')
	
	# only place "get_rate" is called
	# get_rate first tries to make the "rate" a float, returns "rate_flag" as false
	# get_rate then tries to find "rate" in the defined functions, returns "rate_flag" as true
	# get_rate then tries to find "rate" in the defined variables, returns "rate_flag" as false
	rate, rate_flag = get_rate(func_names, functions, rxn_strings, var_vals, variables)
	
	# adds boolean flag, rate_flag, to the total list of flags, rate_call_group
	# NOTE: this could lead to potential problems with propensity updating
	rate_call_group.append(rate_flag)

	# parse products and reagents
	# only place "measure_agent" is called
	# measure_agent:
	#		-input like (Number)Species, e.g. (2)X
	#		-returns (amt, spec_dex), the reaction count (e.g. two of X) and index of species
	products = [measure_agent(agent, count_targets) for agent in rxn_strings[2].split('+')]
	reagents = [measure_agent(agent, count_targets) for agent in rxn_strings[0].split('+')]
	
	# build a list of products and reagents for the reaction
	# builds a list of tuples
	products = [prod for prod in products if prod]
	reagents = [reag for reag in reagents if reag]
	
	# an array of indices to reagent indices (in string array count_targets)
	# "reagents" entries are like (amt, spec_dex)
	reagent_cnt_dexes = [agent[1] for agent in reagents]
	
	# only place get_stochios is called
	# stochio_dexes: index of reactants
	# stochios: amount of each reactant used
	stochio_dexes, stochios = get_stochios(reagent_cnt_dexes, reagents)

	##########
	##########

	# one of the more complicated calls in this routine
	# finally constructs the reactions and propensities (and validators)
	
	# only place "pick_propensity_type" is called
	# returns a propensity object, which calculates propensities for reactions
	propensity = pick_propensity_type(stochio_dexes, rate, rate_flag, reagents,
		stochios)
	
	# returns validator object, which checks if reaction can occur based on current species counts
	valid = pick_validator(stochio_dexes, stochios)
	
	# make reaction object that actually implements the reaction when called
	reaction = Reaction(reagents, products)
	
	return propensity, valid, reaction, reagents, products

############################################################################
############################################################################

#cdef uniq(seq):
def uniq(seq):
	seen = {}
	result = []
	for item in seq:
		if item in seen: continue
		seen[item] = 1
		result.append(item)

	result.sort()
	#print result
	return result

############################################################################
############################################################################

# simple wrapper method to return a propensity updater object
# more or less just calls the PropensityUpdater constructor
cdef PropensityUpdater wrap_propensity(lookup, propensity_table, propensities):

	# make lookup a numpy array
	lookup = np.array(lookup, dtype=np.dtype(np.int32))

	# return a PropensityUpdater
	return PropensityUpdater(lookup, propensity_table, propensities)

############################################################################
############################################################################

# check if reaction influences its own propensity
# should be true if:
#	at least one reactant does not appear in the products with the same stoichiometry
cdef bint self_affecting(dex, products, reagents):
	prods = [agent[1] for agent in products[dex]]
	# if each reactant does not appear in the products with each stoichiometry,
	#	 rxn is self_affecting
	for agent in reagents[dex]:
		if not agent[1] in prods: return True
		elif not agent[0] == products[prods.index(agent[1])][0]:
			return True
	return False

# error in line: "else: return False"
# cdef bint self_affecting(dex, products, reagents):
# 	prods = [agent[1] for agent in products[dex]]
# 	for agent in reagents[dex]:
# 		if not agent[1] in prods: return True
# 		elif not agent[0] == products[prods.index(agent[1])][0]:
# 			return True
# 		else: return False

############################################################################
############################################################################

# return set of species that are changed in count by a given reaction
def species_changed(dex, products, reagents):
	products_stoic = [agent[0] for agent in products[dex]]
	products = [agent[1] for agent in products[dex]]
	reactants_stoic = [agent[0] for agent in reagents[dex]]
	reactants = [agent[1] for agent in reagents[dex]]
	
	cdef int ii, jj
	changedList = []

	# check that each product is in reactants, and if so, has the same stoichiometry
	# otherwise, add to "changedList"
	for ii in range(len(products)):
		if not products[ii] in reactants:
			changedList.append(products[ii])
		elif len(reactants)>0:
			jj = reactants.index(products[ii])
			if not products_stoic[ii] == reactants_stoic[jj]:
				changedList.append(products[ii])
			
	# check that each reactant is in products, and if so, has the same stoichiometry
	for ii in range(len(reactants)):
		if not reactants[ii] in products:
			changedList.append(reactants[ii])
		elif len(products)>0:
			jj = products.index(reactants[ii])
			if not reactants_stoic[ii] == products_stoic[jj]:
				changedList.append(reactants[ii])

	changedList = set(uniq(changedList))
	#print 'reactants = ', reactants, reactants_stoic
	#print 'products = ', products, products_stoic
	#print 'changed = ', changedList
	
	return changedList


############################################################################
############################################################################


# propensity_table: numpy double array to store current numerical values of propensities
# propensities: propensity objects capable of computing the values of propensities
# reagents, products: 
# rate_call_group: when reactions were parsed, stores whether a reaction should be updated
cdef PropensityUpdater [:] wrap_propensities(propensity_table, propensities,
				reagents, products, rate_call_group):

	# if any reactions propensity depends on say time, it must be appended to every lookup
	#	alwayses should consist of the indexes of every propensity 
	#	which requires a rate call
	alwayses = [dex for dex in range(len(rate_call_group)) 
								if rate_call_group[dex]]
	
	# makes a bunch of empty lists corresponding to each propensity object
	propensity_lookups = [[] for prop in propensities]
	
	# check all reactions for dependences between reactions and propensities
	for dex in range(len(reagents)):

		###
		# currently not used, since the below code tends to overestimate dependencies between reactions
		###
		# check if reaction influences its own propensity
		# only place "self_affecting" is called
		#if self_affecting(dex, products, reagents):
		#	propensity_lookups[dex].append(dex)

		# species changed in count during the reaction		
		changed = species_changed(dex, products, reagents)
		
		# scan over all reactions to compare reactants to changed species
		for dex2 in range(len(reagents)):
			reactants2 = set([agent[1] for agent in reagents[dex2]])
			shared_vals = reactants2 & changed
			if (len(shared_vals)>0):
				propensity_lookups[dex].append(dex2)

		# add this for the "null" reaction that does nothing
		# easy solution for time-dependent propensities
		propensity_lookups[dex].extend(alwayses)

	# get rid of duplicate lookups
	propensity_lookups = [uniq(lookup) for lookup in propensity_lookups]

	# append a range list [0,1,2...] the same length as propensity_table 
	# to be called when the "null" reaction occurs	
	propensity_lookups.append(range(len(propensity_table)))

	# only place "wrap_propensity" is called
	# construct a PropensityUpdater for each reaction 
	return np.array([wrap_propensity(lookup, propensity_table, propensities)
		for lookup in propensity_lookups])

############################################################################
############################################################################

cdef inline int pick_reaction(double [:] table, int leng):
# def pick_reaction(table, leng):
	cdef double rand
	cdef int dex
	
	rand = random.random()
	 
	for dex in range(leng):
		if rand < table[dex]:
			return dex

############################################################################
############################################################################

# returns total propensity for all valid reactions
# also updates the cumulative propensity array, rxn_table
#@cython.boundscheck(False)
#@cython.cdivision(True)
cdef inline double get_propensity(int propensity_count,
		double [:] propensity_table, double [:] rxn_table,
		Validator [:] validators):
	cdef double propensity_total = 0.0
	cdef int dex
	for dex in range(propensity_count):
		
		
		# only add a reaction propensity if the reaction is valid (can occur)
		# reaction is selected later based on "rxn_table" cumulative vector
		if (<Validator> validators[dex]).validate():
			propensity_total += propensity_table[dex]
		
		
		# store the cumulative propensity
		rxn_table[dex] = propensity_total
	return propensity_total

############################################################################
############################################################################

def get_counts():
	global SIM_COUNTS
	return SIM_COUNTS

############################################################################
############################################################################

# count_targets: includes iteration, time, all species, and all variables
# functions_string: list of functions (as a string)
# returns names and compiled lambda functions
def generate_functions(count_targets, functions_string):

	# list of functions as strings
	function_strs = functions_string.split(',')

	##########
	##########

	# only used by the below "encode" function
	# make a string that looks like a python command to the array "counts"
	# but, ONLY if substr matches one of the strings in count_targets
	# CHECK: WHAT IF A SPECIES NAME IS A SUBSTRING OF ANOTHER SPECIES NAME?
	# PRELIMINARY CHECK: THIS IS HANDLED CORRECTLY
	def convert(substr):
		if substr in count_targets:
			return "".join([
				"counts[",
				str(count_targets.index(substr)),
				"]"])
		else:
			return substr
	
	##########
	##########

	# simply calls "convert" on each member, and then joins the results
	# example output: counts[2]*counts[5]+counts[3]*counts[4]
	def encode(string):
		return ''.join([convert(substr) for substr in string])

	##########
	##########

	# simply finds the function names (characters before the "=")
	func_names = [fu[:fu.find('=')] for fu in function_strs]

	# the rest of the string for each function	
	encoded_functions = [fu[fu.find('=') + 1:].replace('&', ',') 
										for fu in function_strs]

	# lambda function with explicit reference to the "count" array, as a string
	# example: ['lambda counts: counts[2]*counts[5]+counts[3]*counts[4]', 'lambda counts: counts[2]-counts[3]']
	#print [re.split('(\W)', string) for string in encoded_functions]
	#print ''.join([encode(re.split('(\W)', string)) for string in encoded_functions])
	encoded_lambdas = ['lambda counts: ' + encode(re.split('(\W)', string))
											for string in encoded_functions]
	
	# test code for future compiled function capability
	#encoded_inline = ['return ' + encode(re.split('(\W)', string)) for string in encoded_functions]
	#print encoded_inline
	
	# WARNING: EVAL CAN BE USED TO RUN ARBITRARY CODE
	# below: brief attempt to sanitize code just before "eval" is called
	encoded_lambdas = [expr.replace('__','') for expr in encoded_lambdas]

	# compiles lambda functions	
	funcs = [eval(expr) for expr in encoded_lambdas]

	# return names and compiled lambda functions
	return func_names, funcs


############################################################################
############################################################################

system_string_samp = '<species>Substrate:10000,Enzyme:5000,ES_Complex:0,Product:0<variables>k:0.5<functions>ratio=Substrate/(Enzyme+k)<reactions>(1)ES_Complex->800.0->(1)Enzyme+(1)Product,(1)Substrate+(1)Enzyme->1.0->(1)ES_Complex,(1)ES_Complex->0.01->(1)Substrate+(1)Enzyme<end>time>=0.00098<capture>increment:time:0.00002<targets>ES_Complex,Product,iteration,time||';

#@cython.boundscheck(False)
#@cython.cdivision(True)
def simulate(system_string = system_string_samp, seed = None):

	# set random number generator seed
	if (not seed == None):
		random.seed(seed)


	#backward compatability
	if system_string[-2:] == '||':
		system_string = system_string[:-2]

	cdef int capture_dex = 0
	#iteration = 0
	cdef double time = 0.0

	##################################
	##################################

	# construct system parsers to break down system string
	cdef SystemParser parser = SystemParser()

	# dictionary of various system property strings
	strs = parser.string_to_dict(system_string)
	
	# assign system property strings to specific variables
	species = strs['species']
	variables = strs['variables']
	functions_string = strs['functions']
	rxns = strs['reactions']
	end = strs['end']
	capture_str = strs['capture']
	targets = strs['targets']

	##################################
	##################################

	# species names and initial counts
	species, species_counts = parser.parse_name_value_pairs(species, float)
	# variable names and initial counts
	variables, var_vals = parser.parse_name_value_pairs(variables, float)

	##################################
	##################################

	# list of strings for the *potential* outputs
	count_targets = ['iteration', 'time'] + list(species) + list(variables)
	# actual counts for the above
	counts = [0, 0.0] + species_counts + var_vals

	##################################
	##################################

	# if the function string is empty, make an empty list of functions
	if functions_string.strip() == '': func_names, functions = [], []
	# otherwise, generate functions using "generate_functions"
	# returns function names and compiled lambda functions that reference the array "counts"
	else: func_names, functions = generate_functions(count_targets, functions_string)

	##################################
	##################################

	# make an object FunctionUpdater using the function "generate_update_functions"
	cdef FunctionUpdater update_functions
	update_functions = generate_update_functions(functions,func_names)
	
	##################################
	##################################

	# index identifying the end of "normal" target indices, and the beginning of function indices
	global SIM_FUNCTION_INDEX
	SIM_FUNCTION_INDEX = len(count_targets)

	# add function names to the count target names
	count_targets.extend(func_names)
	
	# add functions themselves to "counts"
	# probably important that they are called *after* the rest of "counts" has been evaluated
	counts.extend([func(counts) for func in functions])

	##################################
	##################################

	# sample "targets" here: x,y,iteration,time
	targets = targets.split(',')
	# sample "targets" here: ['x', 'y', 'iteration', 'time']
	
	# use a list comprehension to properly order the targets for output
	targets = [targ for targ in count_targets if targ in targets]
	# sample targets here: ['iteration', 'time', 'x', 'y']

	##################################
	##################################

	global SIM_COUNTS, SIM_COUNTS_LIST, SIM_COUNTS_LENGTH

	# numerical array storing a variety of system values, including species, variables, and functions
	SIM_COUNTS = counts
	SIM_COUNTS_LENGTH = len(counts)
	SIM_COUNT_TARGETS = count_targets

	##################################
	##################################

	##################################################
	# one of the most important code calls           #
	# parses reactions and makes appropriate objects #
	##################################################


	# splits string of all reactions, based on comma separation
	rxn_split = rxns.split(',')
	
	# (apparently) a set of flags on whether or not to update propensities
	rate_call_group = []
	
		
	# zip's a list comprehension of generate_reaction calls
	# returns tuples for all: propensities, validators_untyped, reactions, reagents, products
	# generate_reaction:
	#		-only called here
	#		-uses: count_targets, functions, func_names, var_vals, variables, rxn_string, rate_call_group
	#		-returns: propensity, valid, reaction, reagents, products
	propensities, validators_untyped, reactions, reagents, products =\
			zip(*[generate_reaction(count_targets, functions,
				func_names, var_vals, variables, rxn_string,
				rate_call_group) for rxn_string in rxn_split])

	# example types of output:
	# [(<PropensityVerySimple object>,), (<StochioValidator object>,), (<Reaction object>,), \
	#		([(1, 2)],), ([(1, 3)],)]
	
	##################################
	##################################

	# constructs an array of Validator objects, based on the previous command's output
	# simply making an array
	cdef Validator [:] validators = np.array(validators_untyped)

	##################################
	##################################

	# convert tuple of reactions to a list of reactions
	# simply making a list
	reactions = list(reactions)

	# add to reaction list: a reaction that does nothing
	reactions.append(ReactionPass())
	
	##################################
	##################################

	# total number of reactions
	cdef int propensity_count = len(rxn_split)

	# initialize a table of doubles to keep track of propensities
	cdef double [:] propensity_table = np.zeros(propensity_count, dtype=np.float)

	# initialize propensities to their starting values
	cdef int dex
	for dex, prop in enumerate(propensities):
		propensity_table[dex] = prop.calculate()

	# create nparray of propensity objects
	propensities = np.array(propensities)
	
	# make a propensity updater object
	# only place "wrap_propensities" is called
	cdef PropensityUpdater [:] propensity_updaters = wrap_propensities(
		propensity_table, propensities, reagents, products, rate_call_group)

	##################################
	##################################

	# array of propensities (?)
	cdef double [:] rxn_table = np.zeros(propensity_count, dtype = np.float)

	##################################
	##################################

	# only allow one end criterion, only time limit or iteration limit
	if end.startswith('time'):
		end_crit_dex = 1
		end_crit_limit = float(end[end.find('time') + 6:])
	else: print 'end criterion parsing problem'

	##################################
	##################################

	# only allow one capture criterion, increment time or increment iteration
	capture = capture_str.split(':')
	if capture[0].startswith('increment'):
		if capture[1].startswith('time') and end_crit_dex == 1:
			capt_crit_dex = 1
			capt_crit_thresh = float(capture[2])

		else: print 'capture criterion parsing problem'
	else: print 'capture criterion parsing problem'

	# need to add 1 to include last point
	cdef int total_captures = 1+int(end_crit_limit/capt_crit_thresh)

	##################################
	##################################

	data = np.zeros(shape = (len(targets), total_captures), dtype = np.float)
	target_dexes = [count_targets.index(targ) for targ in targets]

	# not needed in current code - always captures the first state
	## perform initial state capture -> necessary!
	#data[:,capture_dex] = [SIM_COUNTS[dex] for dex in target_dexes]
	#capture_dex += 1

	##################################
	##################################

	# main loop of the simulation
	# should be a standard Gillespie simulation
	# basic structure:
	#		-calculate propensities
	#		-determine next reaction time, update tentative simulation time
	#		-potentially:
	#				--capture system output
	#				--determine if time step is too large
	#				--end simulation
	#		-pick a reaction and implement reaction
	#		-loop

	cdef int rxn_dex
	cdef double propensity_total_inv
	cdef double last_time = 0.0
	cdef double real_time = 0.0
	while capture_dex < total_captures:

		# only place "get_propensity" is called
		# returns total propensity for all valid reactions
		# also updates cumulative propensity array, rxn_table
		propensity_total = get_propensity(propensity_count, 
					propensity_table, rxn_table, validators)
		
		# normal Gillespie if the total propensity is greater than 0,
		# otherwise, simply increase the system time by a fixed amount
		if propensity_total > 0.0:

			# normalize the cumulative propensity table, rxn_table
			propensity_total_inv = 1.0/propensity_total
			for dex in range(propensity_count):
				rxn_table[dex] *= propensity_total_inv
	
			# generate next time step
			time_step = -1.0 * log(<double> random.random()) * propensity_total_inv

			# pick next reaction
			# only place "pick_reaction" is called
			rxn_dex = pick_reaction(rxn_table, propensity_count)

		else:
			#print 'all impossible.... continuing...'
			time_step = capt_crit_thresh
			# select the "do nothing" propensity
			rxn_dex = -1

		#SIM_COUNTS[0] += 1
		
		# update (tentatively) the time based on the propensity
		SIM_COUNTS[1] += time_step
		
		# store current simulation time (just after tentative reaction)
		real_time = SIM_COUNTS[1]
		
		
		# output until the next reaction is implemented
		# ERROR in next line - fixed in line after next line
		#while last_time < SIM_COUNTS[1] and capture_dex < total_captures:
		while last_time < real_time and capture_dex < total_captures:

			# temporarily write current output time to the SIM_COUNTS array for output
			SIM_COUNTS[1] = last_time
			
			# increase "last_time" to next output time
			last_time += capt_crit_thresh
			
			# call function updater before output
			update_functions.update()
			
			# write into data output
			data[:,capture_dex] = [SIM_COUNTS[dex] for dex in target_dexes]

			# increment the capture index
			capture_dex += 1


		# restore current simulation time
		SIM_COUNTS[1] = real_time
		SIM_COUNTS[0] += 1
		#SIM_COUNTS[1] += time_step		# error!
		
		# implement the reaction
		(<Reaction> reactions[rxn_dex]).react()

		# update propensity
		(<PropensityBase> propensity_updaters[rxn_dex]).update()
		#update_functions.update()
		#for dex in range(propensity_count):
		#		propensity_table[dex] = propensities[dex].calculate()

	##################################
	##################################

	return data, targets

############################################################################
############################################################################







