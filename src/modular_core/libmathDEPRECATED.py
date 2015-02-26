import modular_core.libfundamental as lfu

import pdb,types,math
import numpy as np
import scipy.interpolate as sp

if __name__ == 'libs.modular_core.libmath':
    lfu.check_gui_pack()
    #lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'libmath of modular_core'

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

    deltas = complete_deltas[:]
    ratio = max(deltas)/min(delt for delt in deltas if delt > 0.0)
    ratio_threshold = ratio/ratio_res       #magnitude of jump, somehow anticpate
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

def minmax(vals):
    check = [v for v in vals if not v is None]
    if not check: raise ValueError
    else:
        mi = check[0]
        ma = check[0]
        for v in check:
            #if v is None: pass
            if v < mi: mi = v
            elif v > ma: ma = v
        return mi,ma

def linear_interpolation(list_to_x,list_to_y,to_list_x,kind = 5):
    interpolation = sp.interp1d(list_to_x,list_to_y,
                  bounds_error = False,kind = kind)
    to_list_y = interpolation(to_list_x)
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

def mid(arr):
    leng = len(arr)
    if leng % 2: mid = arr[leng/2]
    else: mid = np.mean(arr[leng/2-1:leng/2+1])
    return mid






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
#   returns a pointwise calculation of a weighted difference in second derivatives between two codomains
#   args : (domain weights, y_data to fit to, the run data post interpolation, domain bounds for the calculation, domain used)
#   intended use is by fitting routines
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
#   return the second derivative at a point located at x[dex]
#   assumes the index 'dex' will not be too high or low for calculation
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



