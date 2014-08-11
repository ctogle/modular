#import libs.modular_core.libfundamental as lfu
import modular_core.libfundamental as lfu

import math
import numpy as np
#import cgkit.cgtypes as cgt
import scipy.interpolate as sp
from copy import deepcopy as copy
import types

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

###
#GEOMETRIC UTILITY FUNCTIONS
###
def scalp (vec, scal):
	vec[0] *= scal
	vec[1] *= scal
	vec[2] *= scal

def length(vec):
	return math.sqrt(dot_product(vec, vec))

def dot_product(v1, v2):
	return sum((a*b) for a, b in zip(v1, v2))

def cross_product(x_hat, y_hat):
	return np.cross(x_hat, y_hat)

def angle(v1, v2, unit = None, conv = 1.0):
	#provide a conversion factor, unit, both, or neither
	# use the conv factor
	# determine the conv factor
	# use units instead of conv
	# use 1.0 for conv
	if unit == 'degree': conv = 180.0/np.pi
	elif unit == 'radian': conv = 1.0
	return conv*math.acos(dot_product(v1,v2)/(length(v1)*length(v2)))

def in_bbox(bbox1, bbox2, v_):
	def in_bbox1d(rng, x): return x >= rng[0] and x <= rng[1]
	in_x = in_bbox1d((bbox1[0], bbox2[0]), v_[0])
	in_y = in_bbox1d((bbox1[1], bbox2[1]), v_[1])
	in_z = in_bbox1d((bbox1[2], bbox2[2]), v_[2])
	return in_x and in_y and in_z

def normalize_angle(angle):
	while angle < 0: angle += 360
	while angle > 360: angle -= 360
	return angle

def normalize_vect(vect):
	return np.array([ve/length(vect) for ve in vect])

def clamp(val, min_, max_):
	if val < min_: return min_
	elif val > max_: return max_
	else: return val

def clamp_periodic(val, min_, max_):
	while val < min_: val += (max_ - min_)
	while val > max_: val -= (max_ - min_)
	else: return val

def identity_mat(dim = 4):
	iden = np.zeros((dim, dim), dtype = 'f')
	for d in range(dim): iden[d][d] = 1
	return iden

###
###
###

def mid(arr):
	leng = len(arr)
	if leng % 2: mid = arr[leng/2]
	else: mid = np.mean(arr[leng/2-1:leng/2+1])
	return mid

###
###
###

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
			#values = [float(val) for val in (np.arange(front, 
			#					back + interval, interval))]
			values = [float(val) for val in 
				np.linspace(front, back, interval)]
			res = ', '.join([str(item) for item in values])
			return res

		elif not stg.count('-') > 0 and stg.count(';') > 0:
			print 'mistake?'
			res = ', '.join([str(float(item)) for 
				item in stg[:stg.find(';')].split(',')])
			return res

	ranges = strip_separate(range_, rng_delim)
	ranges = [parse_range(stg) for stg in ranges]
	ranges = ', '.join(ranges)
	return ranges, True

def differences(*args, **kwargs):
	weights = args[0]
	to_fit_to_y = args[1]
	runinterped = args[2]
	bounds = args[3]
	diffs = [abs(to_fit_to_y[k] - runinterped[k])*weight for 
		weight, k in zip(weights, range(bounds[0], bounds[1]))]
	return diffs

def deriv_first_differences(*args, **kwargs):
	dom_weights = args[0]
	to_fit_to_y = args[1]
	runinterped = args[2]
	bounds = args[3]
	to_fit_to_x = args[4]
	runinterped_slope = [(runinterped[k] - runinterped[k - 1])\
				/(to_fit_to_x[k] - to_fit_to_x[k - 1]) 
				for k in range(1, len(to_fit_to_x))]
	to_fit_to_y_slope = [(to_fit_to_y[k] - to_fit_to_y[k - 1])\
						/(to_fit_to_x[k] - to_fit_to_x[k - 1]) 
						for k in range(1, len(to_fit_to_x))]
	return [weight*abs(to_fit_to_y_slope[k] - runinterped_slope[k]) 
								for weight, k in zip(dom_weights, 
								range(bounds[0], bounds[1] -1))]

########################################################################
#	returns a pointwise calculation of a weighted difference in second derivatives between two codomains
#	args : (domain weights, y_data to fit to, the run data post interpolation, domain bounds for the calculation, domain used)
#	intended use is by fitting routines
########################################################################
def deriv_second_differences(*args, **kwargs):
	dom_weights = args[0]
	to_fit_to_y = args[1]
	runinterped = args[2]
	bounds = args[3]
	to_fit_to_x = args[4]
	runinterped_slope = [
		calc_2nd_deriv(to_fit_to_x, runinterped, k) 
			for k in range(1, len(to_fit_to_x) -1)]
	to_fit_to_y_slope = [
		calc_2nd_deriv(to_fit_to_x, to_fit_to_y, k) 
			for k in range(1, len(to_fit_to_x) -1)]
	return [weight*abs(to_fit_to_y_slope[k] - runinterped_slope[k]) 
						for weight, k in zip(dom_weights, range(
								bounds[0] + 1, bounds[1] - 2))]

########################################################################
#	return the second derivative at a point located at x[dex]
#	assumes the index 'dex' will not be too high or low for calculation
########################################################################
def calc_2nd_deriv(x, y, dex):
	del_x_avg = (x[dex + 1] - x[dex - 1])/2.0
	val = (y[dex + 1] - (2*y[dex]) + y[dex - 1])/((del_x_avg)**2)
	return val

def deriv_third_differences(*args, **kwargs):

	def calc_3rd_deriv(x, y, dex):
		top = (y[dex - 2] - (3*y[dex - 1]) +\
					(3*y[dex]) + y[dex + 1])
		del_x_avg = ((x[dex + 1] - x[dex - 2]))/3.0
		return top/((x[dex] - del_x_avg)**3)

	dom_weights = args[0]
	to_fit_to_y = args[1]
	runinterped = args[2]
	bounds = args[3]
	to_fit_to_x = args[4]
	runinterped_slope = [
		calc_3rd_deriv(to_fit_to_x, runinterped, k) 
			for k in range(1, len(to_fit_to_x) -1)]
	to_fit_to_y_slope = [
		calc_3rd_deriv(to_fit_to_x, to_fit_to_y, k) 
			for k in range(1, len(to_fit_to_x) -1)]
	return [weight*abs(to_fit_to_y_slope[k] - runinterped_slope[k]) 
								for weight, k in zip(dom_weights, 
							range(bounds[0] + 2, bounds[1] - 2))]

if __name__ == 'libs.modular_core.libmath':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	#lgm = lfu.gui_pack.lgm
	#lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'



