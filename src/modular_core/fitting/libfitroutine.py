import modular_core.libfundamental as lfu
import modular_core.libgeometry as lgeo
import modular_core.libiteratesystem as lis
import modular_core.libsettings as lset
import modular_core.libmath as lm
import modular_core.libmultiprocess as lmp

import modular_core.io.libvtkoutput as lvtk
import modular_core.io.libfiler as lf
import modular_core.io.liboutput as lo
import modular_core.data.libdatacontrol as ldc
import modular_core.criteria.libcriterion as lc

from copy import deepcopy as copy
import multiprocessing as mp
import traceback
import numpy as np
import time
import heapq
import math
import types
import os
import random
import sys

import pdb

if __name__ == 'modular_core.fitting.libfitroutine':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__': print 'this is a library!'

class fit_routine_plan(lfu.plan):

    def __init__(self, *args, **kwargs):
        self._default('label', 'fit routine plan', **kwargs)
        self._default('routines', [], **kwargs)
        self._default('selected_routine', None, **kwargs)
        self._default('selected_routine_label', None, **kwargs)
        self._default('show_progress_plots', True, **kwargs)
        kwargs['use_plan'] = lset.get_setting('fitting')
        lfu.plan.__init__(self, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        #data_pool = self.parent.set_data_scheme()
        data_pool = args[1]
        if self.show_progress_plots:
            if self.parent.multithread_gui:
                try: app = lgb.QtGui.QApplication(sys.argv)
                except RuntimeError: pass#  this should not be so silent!
            else: self.show_progress_plots = False
        return self.enact_plan(*args, dpool = data_pool, **kwargs)

    def enact_plan(self, *args, **kwargs):
        for routine in self.routines:
            check1 = time.time()
            routine(*args, **kwargs)
            print ' '.join(['completed fit routine:', routine.label, 
                        'in:', str(time.time() - check1), 'seconds'])
        return kwargs['dpool']

    def add_routine(self, new = None):
        if not new: new = fit_routine_simulated_annealing(parent = self)
        self.routines.append(new)
        self._children_.append(new)
        self.rewidget(True)

    def remove_routine(self, selected = None):
        if selected: select = selected
        else: select = self.get_selected()
        if select:
            self.routines.remove(select)
            self._children_.remove(select)
            del self.parent.run_params['output_plans'][
                            select.label + ' output']
            select._destroy_()
        self.rewidget(True)

    def remove_routine(self):
        select = self.get_selected()
        if select:
            self.routines.remove(select)
            self._children_.remove(select)
        self.rewidget(True)

    def move_routine_up(self, *args, **kwargs):
        select = self.get_selected()
        if select:
            select_dex = lfu.grab_mobj_dex_by_name(
                        select.label, self.routines)
            self.routines.pop(select_dex)
            self.routines.insert(select_dex - 1, select)
            #self._widget(select_dex - 1)
            self.rewidget_routines()

    def move_routine_down(self, *args, **kwargs):
        select = self.get_selected()
        if select:
            select_dex = lfu.grab_mobj_dex_by_name(
                        select.label, self.routines)
            self.routines.pop(select_dex)
            self.routines.insert(select_dex + 1, select)
            #self._widget(select_dex + 1)
            self.rewidget_routines()

    def rewidget_routines(self, rewidg = True):
        [rout.rewidget(rewidg) for rout in self.routines]

    def get_selected(self):
        key = 'routine_selector'
        if not hasattr(self, key):
            print 'no selector'; return

        try:
            select = self.__dict__[key][
                self.__dict__[key][0].currentIndex()]
            return select

        except IndexError:
            print 'no routine selected'; return

    def _widget(self,*args,**kwargs):
        window = args[0]
        self._sanitize(*args,**kwargs)

        try: select_label = self.selected_routine.label
        except AttributeError: select_label = None
        self.widg_templates.append(
            lgm.interface_template_gui(
                layout = 'grid', 
                widg_positions = [(0, 0), (0, 2), (1, 2), 
                                (2, 2), (3, 2), (4, 2)], 
                widg_spans = [(3, 2), None, None, None, None, None], 
                grid_spacing = 10, 
                widgets = ['mobj_catalog', 'button_set'], 
                verbosities = [1,1], 
                instances = [[self.routines, self], None], 
                keys = [[None, 'selected_routine_label'], None], 
                handles = [(self, 'routine_selector'), None], 
                labels = [None, ['Add Fit Routine', 
                                'Remove Fit Routine', 
                                'Move Up In Hierarchy', 
                                'Move Down In Hierarchy']], 
                initials = [[select_label], None], 
                bindings = [None, [lgb.create_reset_widgets_wrapper(
                                        window, self.add_routine), 
                        lgb.create_reset_widgets_wrapper(window, 
                                self.remove_routine), 
                        lgb.create_reset_widgets_wrapper(window, 
                                self.move_routine_up), 
                        lgb.create_reset_widgets_wrapper(window, 
                                self.move_routine_down)]]))
        lfu.plan._widget(self, *args, from_sub = True)

def parse_fitting_line(*args):
    data = args[0]
    ensem = args[1]
    parser = args[2]
    procs = args[3]
    routs = args[4]
    split = [item.strip() for item in data.split(' : ')]
    for fit_type in valid_fit_routine_base_classes:
        if split: name = split[0]
        if len(split) > 1:
            if split[1].strip() == fit_type._tag:
                rout = fit_type._class(label = name, 
                    parent = ensem.fitting_plan)
                routs.append(rout)
            if len(split) > 2: rout.regime = split[2].strip()
            if len(split) > 3:
                input_data_path = split[3].strip()
                rout.input_data_file = input_data_path
                try: rout.get_input_data()
                except: traceback.print_exc(file=sys.stdout)
            if len(split) > 4:
                alias = split[4]
                l = alias.find('{') + 1
                r = alias.rfind('}')
                sub_alias = alias[l:r].split(',')
                aliases = {}
                for alias in sub_alias:
                    spl = alias.split(':')
                    al, ias = spl[0], spl[1]
                    aliases[al] = ias
                rout.input_data_aliases = aliases

    ensem.fitting_plan.add_routine(new = rout)
    if lfu.using_gui(): rout._widget(0, ensem)

class fit_routine(lfu.mobject):

    #ABSTRACT
    #base class should not assume scalars are the data object
    '''
    fit_routine subclasses should have several regimes
    fine: runs the routine on the parameter space as specified
    coarse-magnitude: coerce the parameter space into a discrete 
        parameter space; impose new bounds on the old 
        parameter space (which is not in general discrete) based
        on the best fit
    coarse-decimate: coerce the parameter space into a discrete 
        space with bounds and increments such that each space has
        some number of values; impose results as coarse-magnitude does
    these secondary regimes can run in either of the above two regimes:
        on_simulation: run a simulation; use its output as input 
            any relevant metrics
        on_process: a series of post processes can be run
            on the output of a simulation at a location
                processes can be run in the 'per trajectory' or
                    'all trajectories' regimes
            must specify how many trajectories are run per
                location and then fed into the post process chain
            input data must be based on final post process output goal
            measurement and acceptance/rejection is exactly the same
            can't use raw_measure pipeline... -> slow

    fitting routines can be used in series, which is particularly 
        useful when each provides information for the next
        this is the express purpose of the coarse regime
        but the fine regime should also allow this option
            the option will be on available on both

    fitting routines should be able to run on each other - 
        use a fitting routine to hone another fitting routine

        this could allow a single recursing routine which 
        runs the coarse regime several times and then the fine
        regime or whatever is desired

    fitting routines can have many metrics and many criteria for
        both accepting a parameter space step and for the end of 
        the fitting routine which are for now assumed to be 
        implicitly joined by AND statements

    fitting routines can accept any number of lines as input 
        for metric minimization (the assumed criterion for fitterness
        for now)

    input data should be identical to the output of modular via
        pkl format - scalars objects wrapped in a data_container
    '''
    def __init__(self, *args, **kwargs):
        self.impose_default('parameter_space', None, **kwargs)
        self.impose_default('many_steps', 1, **kwargs)
        self.impose_default('p_sp_trajectory', [], **kwargs)
        self.impose_default('p_sp_step_factor', 1.0, **kwargs)
        self.impose_default('capture_targets', [], **kwargs)
        self.impose_default('bAbort', False, **kwargs)
        self.impose_default('brand_new', True, **kwargs)
        self.impose_default('iteration', 0, **kwargs)
        self.impose_default('auto_overwrite_key', True, **kwargs)
        self.impose_default('initial_creep_factor', 20, **kwargs)
        self.impose_default('display_frequency', 500, **kwargs)
        self.impose_default('max_sim_wait_time', 1.0, **kwargs)
        self.impose_default('last_best', 0, **kwargs)
        self.impose_default('timeouts', 0, **kwargs)
        self.impose_default('use_time_out', True, **kwargs)
        self.impose_default('use_genetics', False, **kwargs)
        self.impose_default('use_mean_fitting', False, **kwargs)
        self.impose_default('regime', 'fine', **kwargs)
        self.impose_default('valid_regimes', 
            ['fine', 'coarse-magnitude', 'coarse-decimate'], **kwargs)

        self.impose_default('metrics', [], **kwargs)
        self.metrics.append(
            lgeo.metric_avg_ptwise_diff_on_domain(
                parent = self, acceptance_weight = 1.0))
        self.metrics.append(
            lgeo.metric_slope_1st_derivative(
                parent = self, acceptance_weight = 0.85))
        self.metrics.append(
            lgeo.metric_slope_2nd_derivative(
                parent = self, acceptance_weight = 0.75))
        self.metrics.append(
            lgeo.metric_slope_3rd_derivative(
                parent = self, acceptance_weight = 0.5))
        self.impose_default('metric_weights', 
                [met.acceptance_weight for met 
                    in self.metrics], **kwargs)
        self.metric_rulers = [lm.differences, 
                lm.deriv_first_differences, 
                lm.deriv_second_differences, 
                lm.deriv_third_differences]
        self.impose_default('prime_metric', 0, **kwargs)
        self.prime_metric =\
            self.metric_weights.index(max(self.metric_weights))
        self.metrics[self.prime_metric].is_heaviest = True

        self.impose_default('fitted_criteria', [], **kwargs)
        self.fitted_criteria.append(lc.criterion_iteration(
                    parent = self, max_iterations = 2500))
        self.fitted_criteria.append(criterion_impatient(
                    parent = self, max_timeouts = 50, 
                            max_last_best = 1000))

        self.impose_default('fitter_criteria', [], **kwargs)
        self.fitter_criteria.append(
            criterion_minimize_measures(parent = self))

        self.impose_default('data_to_fit_to', None, **kwargs)
        self.impose_default('input_data_file', '', **kwargs)
        self.impose_default('input_data_domain', '', **kwargs)
        self.impose_default('input_data_codomains', [], **kwargs)
        self.impose_default('input_data_targets', [], **kwargs)
        self.impose_default('input_data_aliases', {}, **kwargs)
        self.input_data_file = ''
        if not 'visible_attributes' in kwargs.keys():
            kwargs['visible_attributes'] = None

        if not 'valid_base_classes' in kwargs.keys():
            kwargs['valid_base_classes'] =\
                valid_fit_routine_base_classes

        if not 'base_class' in kwargs.keys():
            kwargs['base_class'] = lfu.interface_template_class(
                                object, 'fit routine abstract')

        lfu.mobject.__init__(self, *args, **kwargs)
        self.output = lo.output_plan(label = ' '.join(
                [self.label, 'output']), parent = self)
        #self.output.flat_data = False
        #self._children_ = [self.output] + self.metrics +\
        #   self.fitted_criteria + self.fitter_criteria
        self._children_ = [self.output]

    def __call__(self, *args, **kwargs):
        self.initialize(*args, **kwargs)
        run_func = lis.run_system_measurement
        #data_pool = self.ensemble.data_pool.batch_pool
        #data_pool = self.ensemble.set_data_scheme().batch_pool#data_pool.batch_pool
        data_pool = kwargs['dpool'].batch_pool
        worker_pool = None
        if self.use_mean_fitting or self.use_genetics:
            ensem_to_loc = self.ensemble.set_run_params_to_location
            worker_pool = mp.Pool(processes = self.worker_count, 
                initializer = ensem_to_loc)

        if self.use_genetics:
            iterate = self.iterate_genetic
            self.iterate(run_func, data_pool, worker_pool)

        else:
            iterate = self.iterate

        while not self.bAbort and not self.verify_criteria_list(
                                    self.fitted_criteria, self):
            iterate(run_func, data_pool, worker_pool)

        if self.use_genetics:
            worker_pool.close()
            worker_pool.join()

        self.finalize(*args, **kwargs)

    def get_input_data(self, read = True):
        if not os.path.exists(self.input_data_file):
            dat_file = self.input_data_file.split(os.path.sep)[-1]
            #self.input_data_file = lfu.resolve_filepath(dat_file)
            def_input_dir = lset.get_setting(
                'default_fitting_input_path')
            self.input_data_file = os.path.join(def_input_dir, dat_file)
        if not os.path.exists(self.input_data_file):
            print 'input data file not found!'
            if lfu.using_gui():
                fidlg = lgd.create_dialog('Choose Input File', 
                    'File?', 'file', 'pkl files (*.pkl)', os.getcwd())
                file_ = fidlg()
            else:
                file_ = raw_input('enter full path to a new default input directory')
                pdb.set_trace()
            self.input_data_file = file_
        data = lf.load_pkl_object(self.input_data_file)
        self.input_data_targets = [dater.label for dater in data.data]
        self.rewidget(True)
        if read:
            self.input_data_domain = self.input_data_targets[0]
            self.input_data_codomains = self.input_data_targets[1:]
            self.input_data_aliases = {}
            for targ, codom in zip(self.input_data_targets, 
                                [self.input_data_domain] +\
                                self.input_data_codomains):
                self.input_data_aliases[targ] = codom

        else:
            for dater in data.data:
                dater.label = self.input_data_aliases[dater.label]

            relevant = self.input_data_aliases.values()
            data = [dater for dater in data.data 
                    if dater.label in relevant]
            for dater in data:
                if type(dater.scalars) is types.ListType:
                    dater.scalars = np.array(dater.scalars)

            return data

    def initialize(self, *args, **kwargs):
        self.output.flat_data = True
        self.ensemble = self.parent.parent
        self.worker_count =\
            self.parent.parent.multiprocess_plan.worker_count
        self.proginy_count = 100
        if False and self.ensemble.multiprocess_plan.use_plan and\
                not self.regime.endswith('magnitude'):
            self.use_genetics = True
            self.proginy_count = 100

        else: self.use_genetics = False
        #self.ensemble.data_pool = self.ensemble.set_data_scheme()
        self.run_targets = self.ensemble.run_params['plot_targets']
        self.data_to_fit_to = self.get_input_data(read = False)
        self.target_key = [[dat.label for dat in 
            self.data_to_fit_to], self.run_targets]

        def expo_weights(leng):
            dom_weight_max = 5.0
            dom_weight_x = np.linspace(dom_weight_max, 0, leng)
            return np.exp(dom_weight_x)

        def para_weights(leng):
            dom_weight_max = 9.0
            x = np.linspace(0, leng, leng)
            y = x*(x - x[-1])
            y_0 = min(y)
            y = y - y_0
            y = dom_weight_max*y/max(y) + 1
            #for k in range(0, 2) + range(-3, -1): y[k] = 0.0
            return y

        def affi_weights(leng):
            x = np.linspace(0, leng, leng)
            b = 5.0
            m = -4.0/x[-1]
            y = m*x + b
            return y

        def flat_weights(leng):
            y = [1.0 for val in range(leng)]
            return y

        fit_x_leng = len(self.data_to_fit_to[0].scalars)
        #self.domain_weights = expo_weights(fit_x_leng)
        self.domain_weights = para_weights(fit_x_leng)
        #self.domain_weights = affi_weights(fit_x_leng)
        #self.domain_weights = flat_weights(fit_x_leng)
        self.iteration = 0
        self.timeouts = 0
        self.parameter_space =\
            self.parent.parent.cartographer_plan.parameter_space
        if self.regime == 'coarse-magnitude':
            self.use_mean_fitting = False
            self.parameter_space, valid =\
                lgeo.generate_coarse_parameter_space_from_fine(
                        self.parameter_space, magnitudes = True)
            if not valid:
                traceback.print_exc(file=sys.stdout)
                lgd.message_dialog(None, 
                    'P-Spaced couldnt be coarsened!', 'Problem')

        elif self.regime == 'coarse-decimate':
            self.use_mean_fitting = False
            self.parameter_space, valid =\
                lgeo.generate_coarse_parameter_space_from_fine(
                        self.parameter_space, decimates = True)
            if not valid:
                traceback.print_exc(file=sys.stdout)
                lgd.message_dialog(None, 
                    'P-Spaced couldnt be coarsened!', 'Problem')

        elif self.regime == 'fine': pass
        print '\tstarted fit routine', self.label, 'regime', self.regime
        self.parameter_space.set_start_position()
        for metric in self.metrics:
            metric.initialize(self, *args, **kwargs)
        self.data = ldc.scalars_from_labels(['fitting iteration'] +\
                [met.label + ' measurement' for met in self.metrics])

    def kill_proginy(self, *args):
        measurements = args[0]
        survivor_weights = []
        group_data = zip(*measurements)
        group_means = [np.mean(measure) for measure in group_data]
        group_mins = [min(measure) for measure in group_data]
        met_weights = self.metric_weights
        for surv_dex, proginy in enumerate(measurements):
            improves = []
            for meas_dex, measure in enumerate(proginy):
                min_ = group_mins[meas_dex]
                improves.append(
                    group_data[meas_dex][surv_dex] - min_ <=\
                            (group_means[meas_dex] - min_))

            weights = [we/sum(met_weights) for we, imp in 
                        zip(met_weights, improves) if imp]
            weight = sum(weights)
            survivor_weights.append(weight)

        survivors = heapq.nlargest(1, survivor_weights)
        return [survivor_weights.index(surv) for surv in survivors]

    #proginy are acceptable arguments for run_system_measurement
    def create_proginy(self, dex, start, fact):
        deviation = [[item for item in tup] for tup in start]
        subs = self.parameter_space.subspaces
        norm = self.parameter_space.step_normalization
        initial_factor = self.parameter_space.initial_factor
        dims = self.parameter_space.dimensions
        many_steps = int(min([dims, 
            max([1, abs(random.gauss(dims, dims))*\
            (self.p_sp_step_factor/initial_factor)])]))
        dirs_ = random.sample(range(dims), many_steps)
        #for dir_ in dirs_:
        #   ax, subsp = deviation[dir_], subs[dir_]
        for sp_dex in range(len(deviation)):
            if sp_dex in dirs_:
                ax = deviation[sp_dex]
                subsp = subs[sp_dex]
                new_location =\
                    subsp.step_sample(norm, fact) +\
                            subsp.current_location()
                ax[-1] = new_location

        child = (self.ensemble, self.data_to_fit_to, 
                self.target_key, self.domain_weights, 
                    self.parameter_space, deviation, 
                            self.metric_rulers, dex)
        return child

    #def iterate_genetic(self, run_func, data_pool, worker_pool):
    def iterate_genetic(self, *args, **kwargs):
        run_func = args[0]
        data_pool = args[1]
        worker_pool = args[2]
        dims = self.parameter_space.dimensions
        st_loc = self.parameter_space.get_current_position()
        fact = self.p_sp_step_factor/self.parameter_space.initial_factor
        print 'making', self.proginy_count, 'children'
        children = [self.create_proginy(dex, st_loc, fact) 
                    for dex in range(self.proginy_count)]
        processor_count = self.worker_count
        measurements = []
        dex0 = 0
        while dex0 < self.proginy_count:
            check_time = time.time()
            runs_left = self.proginy_count - dex0
            if runs_left >= processor_count: 
                runs_this_round = processor_count

            else: runs_this_round = runs_left % processor_count
            dex0 += runs_this_round
            result = worker_pool.map_async(run_func, 
                children[dex0:dex0+runs_this_round], 
                    callback = measurements.extend)
            result.wait()
            print 'multicore reported...', ' location: ', dex0

        survivors = self.kill_proginy(measurements)
        axial_motions = [[] for d in range(dims)]
        for winner in survivors:
            survivor_deviation = children[winner][5]
            [axial_motions[sub_dex].append(float(
                survivor_deviation[sub_dex][-1])) 
                    for sub_dex in range(dims)]

        axial_motions = [np.mean(ax) for ax in axial_motions]
        print 'axial motions', axial_motions, 'at', self.iteration
        self.parameter_space.steps.append(
                lgeo.parameter_space_step(
            location = [], initial = [], final = []))
        for dex, subsp in enumerate(self.parameter_space.subspaces):
            curr = subsp.current_location()
            new = axial_motions[dex]
            self.parameter_space.steps[-1].location.append(
                                    (subsp.inst, subsp.key))
            self.parameter_space.steps[-1].initial.append(curr)
            self.parameter_space.steps[-1].final.append(new)

        self.parameter_space.steps[-1].step_forward()
        self.parameter_space.validate_position()
        iterat = self.iterate(run_func, data_pool, worker_pool)

    def iterate(self, *args, **kwargs):
        self.iteration += 1
        run_func = args[0]
        worker_pool = args[2]
        display = self.iteration % self.display_frequency == 0
        if display:
            print ' '.join(['\niteration:', str(self.iteration), 
                        'temperature:', str(self.temperature)])

        current_position = self.parameter_space.get_current_position()
        argu = (self.ensemble, self.data_to_fit_to, 
            self.target_key, self.domain_weights, 
            self.parameter_space, current_position, 
                            self.metric_rulers, 0)
        kwds = {'timeout': self.max_sim_wait_time}
        if self.use_mean_fitting:
            processor_count = self.worker_count
            measurements = []
            dex0 = 0
            while dex0 < self.proginy_count:
                check_time = time.time()
                runs_left = self.proginy_count - dex0
                if runs_left >= processor_count: 
                    runs_this_round = processor_count

                else: runs_this_round = runs_left % processor_count
                dex0 += runs_this_round

                worker_pool._initializer()

                result = worker_pool.map_async(run_func, 
                        [(argu, kwds)]*runs_this_round, 
                        callback = measurements.extend)
                result.wait()
                print 'multicore reported...', ' location: ', dex0

            measurements = [meas for meas in measurements 
                                    if not meas is False]
            if not measurements: measurements = False
            else:
                measurements = [np.mean(measure) for 
                    measure in zip(*measurements)]

        else:
            self.ensemble.set_run_params_to_location()
            measurements = run_func((argu, kwds))
        if measurements is False:
            print 'no valid measurements...undoing...'
            self.timeouts += 1
            self.move_in_parameter_space(bypass = True)
            return False

        for dex, met in enumerate(self.metrics):
            met.data[0].scalars.append(measurements[dex])
            met.check_best(display)

        if self.metrics[self.prime_metric].best_flag:
            self.last_best = 0

        else: self.last_best += 1
        self.capture_plot_data()
        self.p_sp_trajectory.append(current_position)
        self.move_in_parameter_space()
        return True

    def move_in_parameter_space_genetic(self, bypass = False):
        if bypass or not self.verify_criteria_list(
                self.fitter_criteria, self.metrics):
            self.parameter_space.undo_step()
            print 'undoing...'
        else: print 'keeping...'
        self.parameter_space.validate_position()

    def move_in_parameter_space(self, bypass = False, insist = False):
        initial_factor = self.parameter_space.initial_factor
        dims = self.parameter_space.dimensions
        self.many_steps = int(max([1, abs(random.gauss(dims, dims))]))
        #self.many_steps = int(max([1, abs(random.gauss(dims, 
        #   dims))*(self.p_sp_step_factor/initial_factor)]))
        if (not bypass and self.verify_criteria_list(
                self.fitter_criteria, self.metrics)) or insist:
            #power = 1.0/(self.parameter_space.step_normalization*2)
            #creep_factor = self.initial_creep_factor*\
            #   (self.parameter_space.initial_factor/\
            #           self.p_sp_step_factor)**(power)
            creep_factor = self.initial_creep_factor
            self.parameter_space.take_biased_step_along_axis(
                factor = self.p_sp_step_factor/creep_factor)
                        #   factor = self.p_sp_step_factor)

        else:
            self.parameter_space.undo_step()
            self.parameter_space.take_proportional_step(
                        factor = self.p_sp_step_factor, 
                        many_steps = self.many_steps)

        self.parameter_space.validate_position()

    def capture_plot_data(self, *args, **kwargs):
        self.data[0].scalars.append(self.iteration)
        bump = 1#number of daters preceding metric daters
        for dex, met in enumerate(self.metrics):
            try:
                self.data[dex + bump].scalars.append(
                        met.data[0].scalars[-1])
            except IndexError: pdb.set_trace()

    def finalize(self, *args, **kwargs):

        def get_interped_y(label, data, x, x_to):
            run_y = lfu.grab_mobj_by_name(label, data)
            run_interped = ldc.scalars(
                label = 'interpolated best result - ' + label, 
                scalars = lm.linear_interpolation(
                    x.scalars, run_y.scalars, 
                    x_to.scalars, 'linear'))
            return run_interped

        self.best_fits = [(met.best_measure, 
            met.data[0].scalars[met.best_measure]) 
            for met in self.metrics]
        self.handle_fitting_key()
        self.parameter_space.set_current_position(
            self.p_sp_trajectory[self.best_fits[
                        self.prime_metric][0]])
        best_run_data = lis.run_system(self.ensemble)
        best_run_data = [ldc.scalars(label = lab, scalars = dat) 
            for lab, dat in zip(self.run_targets, best_run_data)]
        best_run_data_x = lfu.grab_mobj_by_name(
            self.data_to_fit_to[0].label, best_run_data)
        best_run_data_ys = [get_interped_y(
            lab, best_run_data, best_run_data_x, self.data_to_fit_to[0]) 
                for lab in lfu.grab_mobj_names(self.data_to_fit_to[1:])]

        print 'fit routine:', self.label, 'best fit:', self.best_fits
        print '\tran using regime:', self.regime
        best_data = self.data_to_fit_to + best_run_data_ys
        #lgd.quick_plot_display(best_data[0], best_data[1:], delay = 5)
        #self.data.extend(best_data)
        #self.capture_targets = [d.label for d in self.data]
        #self.output.targeted = self.capture_targets[:]
        #self.output.set_target_settables()
        #pdb.set_trace()
        kwargs['dpool'].pool_names =\
            [dat.label for dat in best_data]
        kwargs['dpool'].batch_pool.append(best_data)
        kwargs['dpool'].override_targets = True
        #self.ensemble.data_pool.pool_names =\
        #   [dat.label for dat in best_data]
        #self.ensemble.data_pool.batch_pool.append(best_data)
        #self.ensemble.data_pool.override_targets = True
        if self.regime.startswith('coarse'):
            self.impose_coarse_result_to_p_space()
            self.ensemble.cartographer_plan.parameter_space.\
                set_current_position(self.p_sp_trajectory[
                    self.best_fits[self.prime_metric][0]])

    def impose_coarse_result_to_p_space(self):

        def locate(num, vals):
            delts = [abs(val - num) for val in vals]
            where = delts.index(min(delts))
            found = vals[where]
            return found

        fine_space = self.ensemble.cartographer_plan.parameter_space
        print 'fine p-space modified by coarse p-space'
        print '\tbefore'
        for sub in fine_space.subspaces:
            print sub.label
            print sub.inst.__dict__[sub.key], sub.increment, sub.bounds

        orders = [10**k for k in [val - 20 for val in range(40)]]
        for spdex, finesp, subsp in zip(range(len(fine_space.subspaces)), 
                fine_space.subspaces, self.parameter_space.subspaces):
            wheres = range(len(subsp.scalars))
            best_val = float(self.p_sp_trajectory[
                self.best_fits[self.prime_metric][0]][spdex][-1])
            delts = [abs(val - best_val) for val in subsp.scalars]
            where = delts.index(min(delts))
            finesp.move_to(best_val)
            cut = int(len(wheres) / 6)
            print 'THE CUT', cut

            #if len(wheres) >= 4:
            if cut > 0:
                if where in wheres[2*cut:-2*cut]:
                    keep = subsp.scalars[cut:-cut]

                elif where in wheres[:-2*cut]:
                    keep = subsp.scalars[:-cut]

                elif where in wheres[2*cut:]:
                    keep = subsp.scalars[cut:]

                else: keep = subsp.scalars[:]

            else:
                print 'CUT IS ZERO', cut
                if self.regime.endswith('decimate'):
                    pdb.set_trace()

                elif self.regime.endswith('magnitude'):
                    current = subsp.scalars[where]
                    if current in orders[:2]:
                        left = orders[0]
                        right = orders[4]
                        print 'PINNED', left, right

                    elif current in orders[-2:]:
                        left = orders[-5]
                        right = orders[-1]
                        print 'PINNED', left, right

                    else:
                        left = locate(current/100.0, orders)
                        right = locate(current*100.0, orders)

                    if left < finesp.perma_bounds[0]:
                        left = locate(finesp.perma_bounds[0], orders)
                        right = orders[orders.index(left) + 5]
                        print 'out of bounds left', left, right

                    if right > finesp.perma_bounds[1]:
                        right = locate(finesp.perma_bounds[1], orders)
                        left = orders[orders.index(right) - 5]
                        print 'out of bounds right', left, right

                    keep = [left, right]
                    print 'slid from', subsp.scalars[wheres[0]:wheres[-1]+1], 'to', keep

                else:
                    print 'WHAT SHOULD HAPPEN HERE??'
                    pdb.set_trace()

            finesp.bounds = [keep[0], keep[-1]]

        print '\tafter'
        for sub in fine_space.subspaces:
            print sub.label
            print sub.inst.__dict__[sub.key], sub.increment, sub.bounds

    def handle_fitting_key(self):

        def location_to_lines(k, met_dex):
            loc_measure = self.metrics[met_dex].data[0].scalars[k]
            lines.append(' : '.join(['Best fit from metric', 
                self.metrics[met_dex].label, str(loc_measure)]))
            lines.append('\tTrajectory : ' + str(k + 1))
            for ax in self.p_sp_trajectory[k]:
                lines.append('\t\t' + ' : '.join(ax))

        lines = ['Fit Routine Fitting Key: ']
        for dex, met_best in enumerate(self.best_fits):
            k = met_best[0]
            lines.append('\n')
            location_to_lines(k, dex)
            lines.append('\n')
            location_to_lines(0, dex)

        if not os.path.exists(self.output.save_directory):
            self.output.save_directory = os.getcwd()
        lf.output_lines(lines, self.output.save_directory, 
            'fitting_key.txt', dont_ask = self.auto_overwrite_key)

    def _widget(self, *args, **kwargs):
        window = args[0]
        ensem = args[1]
        if self.brand_new:
            self.brand_new = not self.brand_new
            self.mp_plan_ref = ensem.multiprocess_plan
            ensem.run_params['output_plans'][
                self.label + ' output'] = self.output

        self.output.label = self.label + ' output'
        self.handle_widget_inheritance(*args, **kwargs)
        domain_alias_templates = []
        codomains_alias_templates = []
        if self.input_data_targets:
            domain_alias_templates.append(
                lgm.interface_template_gui(
                    widgets = ['text'], 
                    instances = [[self.input_data_aliases]], 
                    keys = [[self.input_data_domain]], 
                    initials = [[self.input_data_aliases[
                                self.input_data_domain]]], 
                    inst_is_dict = [(True, self)]))
            [codomains_alias_templates.append(
                lgm.interface_template_gui(
                    widgets = ['text'], 
                    instances = [[self.input_data_aliases]], 
                    #keys = [[self.input_data_codomains[k]]], 
                    keys = [[self.input_data_targets[k]]], 
                    initials = [[self.input_data_aliases[
                            #self.input_data_codomains[k]]]], 
                            self.input_data_targets[k]]]], 
                    inst_is_dict = [(True, self)])) for k in 
                        #range(len(self.input_data_codomains))]
                        range(len(self.input_data_targets))]

        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['radio', 'check_set', 'panel', 'panel'], 
                layout = 'grid', 
                layouts = ['vertical', 'vertical', 
                        'vertical', 'vertical'], 
                widg_positions = [(0, 0), (1, 0), (0, 1), (1, 1)], 
                #widg_spans = [None, None, (2, 1)], 
                labels = [self.input_data_targets, 
                    self.input_data_targets, None, None], 
                append_instead = [None, True, None, None], 
                provide_master = [None, True, None, None], 
                initials = [[self.input_data_domain], 
                    self.input_data_codomains, None, None], 
                instances = [[self], [self], None, None], 
                keys = [['input_data_domain'], 
                    ['input_data_codomains'], None, None], 
                templates = [None, None, 
                    domain_alias_templates, 
                    codomains_alias_templates], 
                box_labels = [None, None, 
                    'Domain Alias', 'Codomain Aliases'], 
                panel_label = 'Input Data Domain/Codomains'))
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['button_set', 'full_path_box'], 
                initials = [None, [self.input_data_file, 
                                'Pickled Data (*.pkl)']], 
                instances = [None, [self]], 
                keys = [None, ['input_data_file']], 
                labels = [['Read Data'], ['Choose Input File']], 
                bindings = [[lgb.create_reset_widgets_wrapper(
                        window, self.get_input_data)], None], 
                panel_label = 'Input Data'))
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['radio'], 
                labels = [self.valid_regimes], 
                initials = [[self.regime]], 
                instances = [[self]], 
                keys = [['regime']], 
                box_labels = ['P-Space Walk Regime']))
        recaster = lgm.recasting_mason()
        classes = [template._class for template 
                    in self.valid_base_classes]
        tags = [template._tag for template 
                in self.valid_base_classes]
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['radio'], 
                mason = recaster, 
                keys = [['_class']], 
                instances = [[(self.base_class, self)]], 
                box_labels = ['Routine Method'], 
                labels = [tags], 
                initials = [[self.base_class._tag]]))
        self.widg_templates.append(
            lgm.interface_template_gui(
                keys = [['label']], 
                minimum_sizes = [[(150, 50)]], 
                instances = [[self]], 
                widgets = ['text'], 
                box_labels = ['Fit Routine Name']))
        lfu.mobject._widget(
                self, *args, from_sub = True)

class fit_routine_simulated_annealing(fit_routine):

    def __init__(self, *args, **kwargs):
        if not 'label' in kwargs.keys():
            kwargs['label'] = 'simulated annealing routine'

        if not 'base_class' in kwargs.keys():
            kwargs['base_class'] = lfu.interface_template_class(
                                object, 'simulated annealing')

        self.impose_default('cooling_curve', None, **kwargs)
        self.impose_default('max_temperature', 1000, **kwargs)
        self.impose_default('temperature', None, **kwargs)
        fit_routine.__init__(self, *args, **kwargs)

    def initialize(self, *args, **kwargs):
        if not self.cooling_curve:
            self.final_iteration =\
                self.fitted_criteria[0].max_iterations
            lam = -1.0 * np.log(self.max_temperature)/\
                                self.final_iteration
            cooling_domain = np.array(range(self.final_iteration))
            cooling_codomain = self.max_temperature*np.exp(
                                        lam*cooling_domain)
            self.cooling_curve = ldc.scalars(
                label = 'cooling curve', scalars = cooling_codomain)

        fit_routine.initialize(self, *args, **kwargs)
        self.data.extend(ldc.scalars_from_labels(
                        ['annealing temperature']))
        self.temperature = self.cooling_curve.scalars[self.iteration]
        self.parameter_space.initial_factor = self.temperature

    def iterate_genetic(self, *args, **kwargs):
        self.temperature = self.cooling_curve.scalars[self.iteration]
        rev_iter =\
            len(self.cooling_curve.scalars) - 1  - self.iteration
        self.proginy_count =\
            int(self.cooling_curve.scalars[rev_iter]) +\
                                        self.worker_count
        self.p_sp_step_factor = self.temperature
        fit_routine.iterate_genetic(self, *args, **kwargs)

    def iterate(self, *args, **kwargs):
        self.temperature = self.cooling_curve.scalars[self.iteration]
        rev_iter =\
            len(self.cooling_curve.scalars) - 1  - self.iteration
        self.proginy_count =\
            int(self.cooling_curve.scalars[rev_iter]) +\
                                        self.worker_count
        self.p_sp_step_factor = self.temperature
        fit_routine.iterate(self, *args, **kwargs)

    '''#
    def move_in_parameter_space(self, *args, **kwargs):
        self.temperature = self.cooling_curve.scalars[self.iteration]
        self.p_sp_step_factor = self.temperature
        initial_factor = self.parameter_space.initial_factor
        dims = self.parameter_space.dimensions
        self.many_steps = int(max([1, abs(random.gauss(1, 
            dims))*(self.p_sp_step_factor/initial_factor)]))
        fit_routine.move_in_parameter_space(self, *args, **kwargs)
    '''#

    def capture_plot_data(self, *args, **kwargs):
        fit_routine.capture_plot_data(self, *args, **kwargs)
        self.data[-1].scalars.append(self.temperature)

    def _widget(self, *args, **kwargs):
        self.capture_targets =\
                ['fitting iteration'] +\
                [met.label + ' measurement' 
                    for met in self.metrics] +\
                    ['annealing temperature']
        self.handle_widget_inheritance(*args, from_sub = False)
        fit_routine._widget(self, *args, from_sub = True)

class criterion_impatient(lc.criterion_abstract):

    def __init__(self, *args, **kwargs):
        if not 'label' in kwargs.keys():
            kwargs['label'] = 'timeout criterion'

        if not 'base_class' in kwargs.keys():
            kwargs['base_class'] = lfu.interface_template_class(
                            criterion_impatient, 'timeout limit')

        self.impose_default('max_timeouts', 100, **kwargs)
        self.impose_default('max_last_best', 100, **kwargs)
        lc.criterion_abstract.__init__(self, *args, **kwargs)

    def to_string(self):
        return '\ttimeout limit : ' + str(self.max_timeouts)

    def initialize(self, *args, **kwargs):
        self.max_timeouts = float(self.max_timeouts)

    def verify_pass(self, *args):
        obj = args[0]
        try:
            #print 'TIMEOUTS', obj.timeouts, self.max_timeouts
            too_many_timeouts = obj.timeouts >= self.max_timeouts
            no_longer_better = obj.last_best >= self.max_last_best
            if too_many_timeouts or no_longer_better: return True

        except AttributeError:
            print   'timeout criterion applied \
                    \n to object without .timeouts'
            return True

        return False

    def set_uninheritable_settables(self, *args, **kwargs):
        self.visible_attributes = ['label', 'base_class', 
                            'bRelevant', 'max_timeouts']

    def _widget(self, *args, **kwargs):
        self.handle_widget_inheritance(*args, from_sub = False)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin'], 
                doubles = [[False]], 
                initials = [[int(self.max_timeouts)]], 
                minimum_values = [[0]], 
                maximum_values = [[sys.maxint]], 
                instances = [[self]], 
                keys = [['max_timeouts']], 
                box_labels = ['Timeout Limit']))
        criterion._widget(self, *args, from_sub = True)

class criterion_minimize_measures(lc.criterion_abstract):

    def __init__(self, *args, **kwargs):
        lc.criterion_abstract.__init__(self, *args, **kwargs)
        self.rejects = 1
        self.accepts = 1
        self.reject_probability = 0.5
        self.use_window = False

    def verify_pass(self, *args):
        metrics = args[0]
        #ratio = float(self.accepts)/\
        #   (float(self.accepts) + float(self.rejects))
        #print 'crit accept ratio: ', ratio
        improves = []
        for met in metrics:
            sca = met.data[0].scalars
            if len(sca) <= 100 or not self.use_window:
                improves.append(sca[-1] - min(sca) <=\
                        #   (np.mean(sca) - min(sca)))
                        (np.mean(sca) - min(sca))/25.0)

            else:
                improves.append(sca[-1] - min(sca) <=\
                    (np.mean(sca[-100:]) - min(sca))/20.0)

        weights = [met.acceptance_weight for met in metrics]
        weights = [we/sum(weights) for we, imp in 
                    zip(weights, improves) if imp]
        weight = sum(weights)
        if weight >= self.reject_probability:
        #if improves.count(True) > int(len(improves)/2):
        #if improves.count(True) == len(improves):
            self.accepts += 1
            return True

        self.rejects += 1
        return False










