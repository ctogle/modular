import sys

import pdb

#handles one run of a simulation including output
def run_system(*args, **kwargs):
	ensemble = args[0]
	libmodule = sys.modules['libs.modules.lib' + ensemble.module]
	system = libmodule.sim_system(ensemble, params =\
			ensemble.run_params.partition['system'])
	system.initialize(); system.capture_plot_data()
	while not system.verify_end_criteria() and not system.bAbort:
		system.iterate(); system.iteration += 1
		if system.verify_capture_criteria(): system.capture_plot_data()

	system.decommission()
	if system.bAbort: system.toss_bad_daters()
	return system.data

if __name__ == '__main__': print 'this is a library!'




