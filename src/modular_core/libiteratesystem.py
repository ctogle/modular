#import libs.modular_core.libmath as lm
import modular_core.modules
import modular_core.libmath as lm

import sys, traceback
import random
import math
import numpy as np
import heapq

import pdb

#handles one run of a simulation; returns data
def run_system(*args, **kwargs):
    ensemble = args[0]
    try:libmodule = __import__(ensemble.module)
    except:traceback.print_exc(file=sys.stdout)
    system = libmodule.main.sim_system(ensemble, params =\
            ensemble.run_params.partition['system'])

    if 'timeout' in kwargs.keys(): system.timeout = kwargs['timeout']
    if 'identifier' in kwargs.keys():
        system.identifier = kwargs['identifier']

    system.initialize(); system.capture_plot_data()
    while not system.verify_end_criteria() and not system.bAbort:
        system.iterate(); system.iteration += 1
        if system.verify_capture_criteria(): system.capture_plot_data()

    system.decommission()
    if system.bAbort: system.toss_bad_daters()
    return system.data

#run a system and use its data to perform a measurement
# measurement is on raw data not wrapped in objects
def run_system_measurement(*args, **kwargs):
    args = args[0]
    kwargs = args[1]
    args = args[0]
    ensemble = args[0]
    to_fit_to = [args[1][k].scalars for k in range(len(args[1]))]
    target_key = args[2]
    weights = args[3]
    p_space = args[4]
    deviation = args[5]
    rulers = args[6]
    for deviant, subsp in zip(deviation, p_space.subspaces):
        subsp.move_to(deviant[-1])

    p_space.validate_position()
    run = run_system(ensemble, **kwargs)
    if run is False: return False
    return raw_measure(to_fit_to, run, target_key, weights, rulers)

def raw_measure(*args):
    to_fit_to = args[0]
    run_data = args[1]
    labels = args[2]
    domain_weights = args[3]
    methods = args[4]

    run_data_domain = run_data[labels[1].index(labels[0][0])]
    run_data_codomains = [run_data[labels[1].index(
                labels[0][lab_dex+1])] for lab_dex 
                    in range(len(labels[0][1:]))]
    run_data_interped = [lm.linear_interpolation(
        run_data_domain, codomain, to_fit_to[0], 'linear') 
                    for codomain in run_data_codomains]
    x_meas_bnds = (0, len(to_fit_to[0]))

    meas = [[[diff for diff in method(domain_weights, 
            fit_to, interped, x_meas_bnds, to_fit_to[0]) 
            if not math.isnan(diff)] for fit_to, interped 
                in zip(to_fit_to[1:], run_data_interped)] 
                                    for method in methods]
    measurement = [np.mean([np.mean(mea) for mea in measur]) 
                    for measur, method in zip(meas, methods)]
    return measurement

if __name__ == '__main__': print 'this is a library!'




