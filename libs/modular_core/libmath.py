import libs.modular_core.libfundamental as lfu

import math
import numpy as np
import scipy.interpolate as sp
from copy import deepcopy as copy

import pdb

#return index where good values end
def find_infinite_tail(sequence, 
					#ratio_res = 1000.0, 
					ratio_res = 1.0, 
					min_seq_length = 100):

	def max_of_diff_splits(seq):
		middle = len(seq)/2
		split1 = seq[:middle]
		split2 = seq[middle:]
		return split2, split1

	complete_deltas = [sequence[k] - sequence[k - 1] for k in range(len(sequence))][1:]
	if len(complete_deltas) == 0 or len(sequence) < min_seq_length:
		return 0

	deltas = copy(complete_deltas)
	ratio = max(deltas)/min(delt for delt in deltas if delt > 0.0)
	ratio_threshold = ratio/ratio_res		#magnitude of jump, somehow anticpate
	while ratio > ratio_threshold:
		split2, split1 = max_of_diff_splits(deltas)
		try:
			max1 = max(split1)
			max2 = max(split2)

		except ValueError:
			print 'failed to find that tail!'
			return -1

		if max2/max1 > ratio_threshold:
			deltas = split2

		else:
			deltas = split1

		ratio = max(deltas)/min(deltas)
		#print 'ratio | ' + str(ratio)

	last_good_dex = complete_deltas.index(deltas[-1])
	return last_good_dex + 1

def linear_interpolation(list_to_x, list_to_y, to_list_x, kind = 5):
	interpolation = sp.interp1d(list_to_x, list_to_y, 
								bounds_error = False, 
								kind = kind)
								#fill_value = -1.0)	#keyword for interp type exists
	to_list_y = interpolation(to_list_x)
	#pdb.set_trace()
	return to_list_y

def double_numeric_list_density(values, cond = float):
	for k in [2*dex - 1 for dex in range(1, len(values))]:
		try:
			new_val = (cond(values[k + 1]) - cond(values[k]))/2.0
			values.insert(k, cond(values[k - 1]) + new_val)
		except:
			new_val = (cond(values[-1]) - cond(values[-2]))/2.0
			values.insert(k, cond(values[-2]) + new_val)
	return values

def normalize_numeric_list(values):
	return [val/max(values) for val in values]

#THIS FUNCTION IS STILL BROKEN!
def pick_value_from_unsorted_prob_distrib(lookup, sample):
	encode = range(len(lookup))
	sorted_pair = zip(lookup, encode)
	sorted_pair.sort()
	#lookup, encode = zip(*(lookup, encode))
	sorted_dex = [sample < look for look in lookup].index(True)
	dex = encode[sorted_dex]
	pdb.set_trace()
	return dex

def normalize_by_magnitude(values):
	magnitude = math.sqrt(sum([val**2.0 for val in values]))
	return [val/magnitude for val in values]

pwm = []

def pwm_square(*args):
	t = args[0]
	t_w = t % pwm[1]
	if t_w/pwm[1] > pwm[0]: return 0.0
	else:
		#print t, t_w, t_w/pwm[1], pwm[0], t_w/pwm[1] > pwm[0]
		return 1.0

def set_pwm(with_pwm_param, counts, count_targets):
	global pwm
	dex0 = with_pwm_param.find('pwm_square(') + len('pwm_square(')
	dex1 = with_pwm_param[dex0:].find(')') + dex0
	params_str = with_pwm_param[dex0:dex1].split(':')
	params_val = []
	for par in params_str:
		dex = count_targets.index(par)
		params_val.append(counts[dex])

	#params = [counts[dex] for dex in [x for x in range(len(counts)) 
	#								if count_targets[x] in params]]

	pwm.extend(params_val)
	new = with_pwm_param.replace(with_pwm_param[dex0:dex1], 'time')
	return new

def make_range(range_, rng_delim = ':'):

	def strip_separate(stg, delim = ':'):
		return [item.strip() for item in stg.split(delim)]

	def parse_range(stg):
		if stg.strip() == '': return ''
		elif not stg.count('-') > 0 and not stg.count(';') > 0:
			res = ', '.join([str(float(item)) 
				for item in stg.split(',')])
			return res

		elif stg.count('-') > 0 and not stg.count(';') > 0:
			res = ', '.join([str(item) for item in np.arange(
				float(stg[:stg.find('-')]), 
				float(stg[stg.find('-') + 1:]) + 1.0, 1.0)])
			return res

		elif stg.count('-') > 0 and stg.count(';') > 0:
			interval = float(stg[stg.rfind(';') + 1:])
			front = float(stg[:stg.find('-')])
			back = float(stg[stg.find('-') + 1:stg.find(';')])
			values = list(np.arange(front, back, interval))
			if back - values[-1] >= interval:
				values.append(values[-1] + interval)

			res = ', '.join([str(item) for item in values])
			return res

		elif not stg.count('-') > 0 and stg.count(';') > 0:
			res = ', '.join([str(float(item)) for 
				item in stg[:stg.find(';')].split(',')])
			return res

	ranges = strip_separate(range_, rng_delim)
	ranges = [parse_range(stg) for stg in ranges]
	ranges = ', '.join(ranges)
	return ranges, True

if __name__ == 'libs.modular_core.libmath':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'



