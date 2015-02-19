import modular_core.libfundamental as lfu
import modular_core.libsettings as lset
import modular_core.libmath as lm

import modular_core.io.libfiler as lf
import modular_core.data.libdatacontrol as ldc

import pdb,sys,os,traceback,time,math,itertools,types,random
import numpy as np
from scipy.integrate import simps as integrate

if __name__ == 'modular_core.libgeometry':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'libgeometry of modular_core'

###############################################################################
###############################################################################














###############################################################################
###############################################################################

def generate_coarse_parameter_space_from_fine(fine, 
            magnitudes = False, decimates = False):

    def locate(num, vals):
        delts = [abs(val - num) for val in vals]
        where = delts.index(min(delts))
        found = vals[where]
        return found

    def decimate(fine, orders):

        def create_subrange(dex, num_values):
            lower = relev_mags[dex - 1]
            upper = relev_mags[dex]
            new = np.linspace(lower, upper, num_values)
            return [np.round(val, 20) for val in new]

        left  = locate(fine.bounds[0], orders)
        right = locate(fine.bounds[1], orders)
        if left == right:
            rng = range(2)
            relev_mags = [fine.bounds[0], fine.bounds[1]]

        else:
            rng = range(orders.index(left), orders.index(right) + 1)
            #many_orders = len(rng)
            relev_mags = orders[rng[0]:rng[-1] + 1]

        total_values = 20
        num_values = max([10, int(total_values/len(relev_mags))])
        new_axis = []
        for dex in range(1, len(relev_mags)):
            new_axis.extend([np.round(val, 20) for val in 
                    create_subrange(dex, num_values)])

        new_axis = lfu.uniqfy(new_axis)
        #print 'NEW AXIS', new_axis
        if len(new_axis) == 0: pdb.set_trace()
        return new_axis

    def slice_subsp(fine, orders):
        coerced_increment = locate(fine.increment, orders)
        coerced_bounds =\
            [locate(fine.bounds[0], orders), 
            locate(fine.bounds[1], orders)]
        coarse_subsp = one_dim_space(
            interface_template_p_space_axis(
                instance = fine.inst, key = fine.key, 
                p_sp_bounds = coerced_bounds, 
                p_sp_continuous = False, 
                p_sp_perma_bounds = fine.perma_bounds, 
                p_sp_increment = coerced_increment, 
                    constraints = fine.constraints))
        coarse_subsp.scalars = orders[
            orders.index(coerced_bounds[0]):
            orders.index(coerced_bounds[1])+1]
        return coarse_subsp

    if decimates:
        for finesp in fine.subspaces:
            finesp.regime = 'decimate'

    elif magnitudes:
        for finesp in fine.subspaces:
            finesp.regime = 'magnitude'

    orders = [10**k for k in [val - 20 for val in range(40)]]
    coarse_subspaces = []
    for finesp in fine.subspaces:
        if finesp.regime == 'decimate':
            temp_orders = decimate(finesp, orders)
            coarse_subspaces.append(slice_subsp(finesp, temp_orders))

        elif finesp.regime == 'magnitude':
            coarse_subspaces.append(slice_subsp(finesp, orders))

        else:
            print 'kept fine space fine'
            print 'PROBABLY NEED TO USE COPY OR SOMETHING'
            coarse_subspaces.append(finesp)

    if not len(coarse_subspaces) == len(fine.subspaces):
        return None, False

    space = merge_spaces(coarse_subspaces)
    space.parent = fine.parent
    return space, True

class one_dim_space(object):

    '''
    one_dim_space objects represent a single axis in a parameter space
    they contain references to alter attributes on mobjects, 
    they contain two sets of bounds, one which is used while
    exploring parameter space, and one which is permenant, and respected
    by the other set
    they can be continuous or discrete
    they can contain constraints which represent some information about
    the value of this axis relative to another axis
    constraints on this axis will change its value to be acceptable
    relative to the values of the axes which this axis is constrained to
    '''
    def __init__(self, template, scalars_ = None):
        self.inst = template.instance
        self.key = template.key
        self.bounds = template.p_sp_bounds
        self.perma_bounds = template.p_sp_perma_bounds
        self.continuous = template.p_sp_continuous
        self.increment = template.p_sp_increment
        self.constraints = template.constraints
        self.name = ' : '.join([template.instance.name,template.key])
        if not self.continuous and not scalars_:
            scalars_ = np.linspace(self.bounds[0], 
                self.bounds[1], self.increment)
            scalars_ = list(scalars_)

        self.scalars = scalars_

    def initialize(self, *args, **kwargs):
        for con in self.constraints: con.initialize(*args, **kwargs)

    def honor_constraints(self):
        for con in self.constraints: con.abide()

    def move_to(self, value):
        #if not self.continuous: pdb.set_trace()
        self.inst.__dict__[self.key] = value

    def current_location(self):
        return float(self.inst.__dict__[self.key])

    def validate_step_continuous(self, step):
        old_value = self.current_location()
        if old_value + step < self.bounds[0]:
            over_the_line = abs(step) - abs(old_value - self.bounds[0])
            step = over_the_line - old_value

        elif old_value + step > self.bounds[1]:
            over_the_line = abs(step) - abs(self.bounds[1] - old_value)
            step = self.bounds[1] - over_the_line - old_value

        return step

    def validate_step_discrete(self, step):
        old_value = self.current_location()
        space_leng = len(self.scalars)
        val_dex_rng = range(space_leng)
        try: val_dex = self.scalars.index(old_value)
        except ValueError:
            delts = [abs(val - old_value) for val in self.scalars]
            closest = delts.index(min(delts))
            val_dex = closest

        if val_dex + step > (len(val_dex_rng) - 1):
            over = val_dex + step - (len(val_dex_rng) - 1)
            step = (len(val_dex_rng) - 1) - val_dex - over

        if val_dex + step < 0:
            over = abs(val_dex + step)
            step = over - val_dex

        return self.scalars[val_dex + step] - old_value

    def validate_step(self, step):
        if self.continuous:
            return np.round(self.validate_step_continuous(step), 20)

        else: return np.round(self.validate_step_discrete(step), 20)

    def step_sample(self, norm = 3, fact = 1):
        if self.continuous: leng = self.bounds[1] - self.bounds[0]
        else: leng = len(self.scalars)
        sig = leng/norm
        self.direct = random.choice([-1.0, 1.0])
        raw_step = random.gauss(sig, sig)
        if self.continuous: step = abs(raw_step)*fact*self.direct
        else: step = int(max([1, abs(raw_step*fact)])*self.direct)
        step = self.validate_step(step)
        return step

class parameter_space_step(lfu.mobject):

    def __init__(self, location = [], 
                        initial = [], 
                        final = [], 
                        delta_quality = []):
        lfu.mobject.__init__(self)
        self.location = location
        self.initial = initial
        self.final = final
        self.delta_quality = delta_quality

    def step_forward(self):
        for k in range(len(self.location)):
            #print 'actually set value to: ' + str(self.final[k])
            self.location[k][0].__dict__[
                self.location[k][1]] = float(self.final[k])

    def step_backward(self):
        for k in range(len(self.location)):
            #print 'actually reset value to: ' + str(self.final[k])
            self.location[k][0].__dict__[
                self.location[k][1]] = float(self.initial[k])



class parameter_space(lfu.mobject):

    def set_start_position(self):
        self.undo_level = 0
        for subsp in self.subspaces:
            subsp.initialize()
            rele_val = subsp.current_location()
            print 'starting position of', subsp.name, ':', rele_val, ':', subsp.bounds

    #bias_axis is the index of the subspace in subspaces
    #bias is the number of times more likely that axis is than the rest
    def set_simple_space_lookup(self, bias_axis = None, bias = 1.0):
        self.param_lookup = [float(sp_dex + 1) for sp_dex in 
                                range(len(self.subspaces))]
        if bias_axis != None:
            if type(bias_axis) is types.ListType:
                for ax_dex in bias_axis:
                    if ax_dex == 0:
                        bump = self.param_lookup[ax_dex]*bias -\
                                self.param_lookup[ax_dex]

                    else:
                        bump = (self.param_lookup[ax_dex] -\
                                self.param_lookup[ax_dex - 1])*bias -\
                                    (self.param_lookup[ax_dex] -\
                                    self.param_lookup[ax_dex - 1])

                    self.param_lookup = self.param_lookup[:ax_dex] +\
                        [self.param_lookup[k] + bump for k in range(
                            ax_dex, len(self.param_lookup))]

            else:
                if bias_axis == 0:
                    bump = self.param_lookup[bias_axis]*bias -\
                            self.param_lookup[bias_axis]

                else:
                    bump = (self.param_lookup[bias_axis] -\
                            self.param_lookup[bias_axis - 1])*bias -\
                                (self.param_lookup[bias_axis] -\
                                self.param_lookup[bias_axis - 1])

                self.param_lookup = self.param_lookup[:bias_axis] +\
                    [self.param_lookup[k] + bump for k in range(
                            bias_axis, len(self.param_lookup))]

        #print 'subsp prob: ' + str(self.param_lookup)
        self.param_lookup = lm.normalize_numeric_list(self.param_lookup)

    def undo_step(self):
        try:
            #print 'undoing a step!'
            self.undo_level += 1
            self.steps.append(parameter_space_step(
                location = self.steps[-1].location, 
                initial = self.steps[-1].final, 
                final = self.steps[-1].initial))
            self.steps[-1].step_forward()

        except IndexError: print 'no steps to undo!'

    def step_up_discrete(self, step, dex, rng):
        if dex + step not in rng:
            over = dex + step - rng[-1]
            dex = rng[-1] - over

        else: dex += step
        return dex

    def step_down_discrete(self, step, dex, rng):
        if dex - step not in rng:
            dex = step - dex

        else: dex -= step
        return dex

    def set_up_discrete_step(self, param_dex, factor, direc):
        subsp = self.subspaces[param_dex]
        old_value = subsp.current_location()
        step = subsp.step_sample(self.step_normalization, 
                            factor/self.initial_factor)
        self.steps[-1].location.append((subsp.inst, subsp.key))
        self.steps[-1].initial.append(old_value)
        self.steps[-1].final.append(step + old_value)
        return step, old_value

    def set_up_continuous_step(self, param_dex, factor, direc):
        subsp = self.subspaces[param_dex]
        old_value = subsp.current_location()
        step = subsp.step_sample(
            self.step_normalization, 
            factor/self.initial_factor)
        self.steps[-1].location.append((
            self.subspaces[param_dex].inst, 
            self.subspaces[param_dex].key))
        self.steps[-1].initial.append(old_value)
        self.steps[-1].final.append(step + old_value)
        return step, old_value

    def take_biased_step_along_axis(self, factor = 1.0, bias = 1000.0):

        def get_direction(dex):
            delta = self.steps[-1].final[dex] -\
                float(self.steps[-1].initial[dex])
            if delta: return delta/abs(delta)
            return None

        if not self.steps: self.take_proportional_step(factor)
        objs = [sp.inst for sp in self.subspaces]
        step_objs = [local[0] for local in self.steps[-1].location]
        last_ax_dexes = [objs.index(obj) for obj in step_objs]
        last_ax_direcs = [get_direction(k) for k in 
                range(len(self.steps[-1].initial))]
        self.set_simple_space_lookup(last_ax_dexes, bias)
        self.take_proportional_step(factor, 
            even_odds = False, many_steps = len(last_ax_dexes), 
            last_ax_pairs = zip(last_ax_dexes, last_ax_direcs))

    def take_proportional_step(self, factor = 1.0, even_odds = True, 
                                many_steps = 3, last_ax_pairs = None):
        if even_odds: self.set_simple_space_lookup()
        param_dexes = self.lookup_distinct_axes(many_steps)
        if last_ax_pairs: last_axes, last_direcs = zip(*last_ax_pairs)
        else:
            last_axes = []
            last_direcs = []

        self.steps.append(parameter_space_step(
            location = [], initial = [], final = []))
        for param_dex in param_dexes:
            if param_dex in last_axes:
                direc = last_direcs[last_axes.index(param_dex)]
                if direc is None: direc = random.choice([-1.0, 1.0])

            else: direc = random.choice([-1.0, 1.0])
            if self.subspaces[param_dex].continuous:
                step, param = self.set_up_continuous_step(
                                param_dex, factor, direc)

            else:
                step, param = self.set_up_discrete_step(
                                param_dex, factor, direc)

        self.steps[-1].step_forward()

    def lookup_distinct_axes(self, many_steps):
        dexes = []
        while len(dexes) < min([len(self.subspaces), many_steps]):
            rand = random.random()
            new_dex = [rand < lup for lup in 
                self.param_lookup].index(True)
            if not new_dex in dexes: dexes.append(new_dex)

        return dexes

class cartographer_plan(lfu.plan):

    def selected_locations_lookup(self):
        try:
            ref_children = self.controller_ref[0].children()
            list_widg_dex = [issubclass(widg.__class__, 
                            lgb.QtGui.QItemSelectionModel) 
                        for widg in ref_children].index(True)
            list_widg = ref_children[list_widg_dex]
            row_widg_dex = [issubclass(widg.__class__, 
                            lgb.QtCore.QAbstractItemModel) 
                        for widg in ref_children].index(True)
            row_count = ref_children[row_widg_dex].rowCount()

        except:
            self.rewidget(True)
            print 'update_widgets!'
            return []

        sel_rows = list_widg.selectedRows()
        sel_dexes = [item.row() for item in sel_rows]
        return [dex in sel_dexes for dex in range(row_count)]

    def positions_from_lookup(self, selected):
        return [locale for locale, select in 
            zip(self.trajectory, selected) if select]

    def on_reset_trajectory_parameterization(self):
        for dex in range(len(self.trajectory)):
            self.trajectory[dex][0] = dex

    def on_append_trajectory(self, new_trajectory):
        traj_leng = len(self.trajectory)
        self.trajectory.extend([[dex, locale] for dex, locale in 
                                zip(range(traj_leng, traj_leng +\
                            len(new_trajectory)), new_trajectory)])

    def on_delete_selected_pts(self, preselected = None):
        if preselected is None:
            selected = [not value for value in 
                self.selected_locations_lookup()]

        else:
            selected = [not value for value in preselected]

        self.trajectory = self.positions_from_lookup(selected)
        self.on_reset_trajectory_parameterization()
        self.rewidget(True)

    def on_output_trajectory_key(self):

        def pretty_line(locale, lengs):
            li = [str(loc).rjust(lengs[dex] + 5) for loc, dex 
                in zip(locale[1].location, range(len(lengs)))]
            line = '\t'.join([' Index: ' + str(locale[0]).ljust(4)+str(
                locale[1].trajectory_count).rjust(22), '\t'.join(li)])
            return line

        if not self.parameter_space is None:
            axis_labels = [subsp.name for subsp in 
                    self.parameter_space.subspaces]

        else:
            lgd.message_dialog(None, 'Can\'t output key without' +\
                                ' a parameter space!', 'Problem')
            return

        label_lengs = [len(label) for label in axis_labels]
        lines = ['\t||\tTrajectory Key\t||\t\n']
        lines.append('Trajectory number'.ljust(25) +\
                    'Trajectory Count'.ljust(25) +\
                    '\t '.join([label.ljust(leng + 5) for 
                    label, leng in zip(axis_labels, label_lengs)]))
        lines.append('-'*120)
        label_lengs.insert(0, 20)
        lines.extend([pretty_line(locale, label_lengs) 
                        for locale in self.trajectory])
        if self.key_path is None or self.key_path == '':
            self.key_path = os.path.join(os.getcwd(), 
                        'p_space_trajectory_key.txt')
            self.rewidget(True)

        lf.output_lines(lines, self.key_path)

    def on_assert_trajectory_count(self, all_ = False):
        if all_:
            relevant_locations =\
                self.positions_from_lookup([True]*len(self.trajectory))

        else:
            relevant_locations = self.positions_from_lookup(
                            self.selected_locations_lookup())

        for locale in relevant_locations:
            locale[1].trajectory_count = self.traj_count

        self.rewidget(True)

    def generate_traj_diag_function(self, window, method = 'blank'):

        def on_create_trajectory():

            if method == 'blank':
                try: selected = [self.parameter_space.get_start_position()]
                except AttributeError:
                    lgd.message_dialog(None, ' '.join(['Can\'t', 
                        'create', 'trajectory', 'without', 'a', 
                            'parameter', 'space!']), 'Problem')
                    return

            else:
                selected = [item[1] for item in 
                    self.positions_from_lookup(
                    self.selected_locations_lookup())]
                to_replace = self.selected_locations_lookup()

            #traj_dlg = create_trajectory_dialog(
            #   parent = window, base_object = selected, 
            #           p_space = self.parameter_space)
            traj_dlg = lgd.trajectory_dialog(
                parent = window, base_object = selected, 
                        p_space = self.parameter_space)
            made = traj_dlg()
            if made:
                if method == 'modify':
                    self.on_delete_selected_pts(preselected = to_replace)
                    self.on_reset_trajectory_parameterization()

                self.on_append_trajectory(traj_dlg.result)
                self.trajectory_string = traj_dlg.result_string

        return lgb.create_reset_widgets_wrapper(
                    window, on_create_trajectory)








