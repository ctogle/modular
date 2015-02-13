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



def merge_spaces(subspaces):
    space = parameter_space(subspaces = subspaces)
    return space

def generate_parameter_space_from_run_params(parent, run_params):
    def check_for_nested_contributors(subspaces, par):
        try:
            if type(par) is types.ListType:
                for pa in [para for para in par if 
                        isinstance(para, lfu.mobject)]:
                    check_for_nested_contributors(subspaces, par)

            elif type(par) is types.DictionaryType:
                for key in [key for key in par.keys() if 
                        isinstance(par[key], lfu.mobject)]:
                    check_for_nested_contributors(subspaces, par[key])

            elif isinstance(par, lfu.mobject):
                for template in par.parameter_space_templates:
                    if template.contribute_to_p_sp:
                        subspaces.append(one_dim_space(template))

            #nested = par.__dict__.partition['p_space contributors']
            #for key in nested.keys():
            #   check_for_nested_contributors(subspaces, nested[key])

        except: traceback.print_exc(file=sys.stdout)

    subspaces = []
    for key in run_params.keys():
        param = run_params[key]
        if type(param) is types.ListType:
            for par in [par for par in param if 
                    isinstance(par, lfu.mobject)]:
                check_for_nested_contributors(subspaces, par)

        elif type(param) is types.DictionaryType:
            for subkey in [key for key in param.keys() if 
                    isinstance(param[key], lfu.mobject)]:
                check_for_nested_contributors(subspaces, param[subkey])

        elif not key == '_parent': pdb.set_trace()

    if not subspaces: return None, False
    space = merge_spaces(subspaces)
    space.parent = parent
    return space, True

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

class axis_constraint(lfu.mobject):

    def __init__(self, *args, **kwargs):
        self.impose_default('inst', None, **kwargs)
        self.impose_default('key', None, **kwargs)
        self.impose_default('inst_ruler', None, **kwargs)
        self.impose_default('key_ruler', None, **kwargs)
        self.impose_default('op', None, **kwargs)
        lfu.mobject.__init__(self, *args, **kwargs)

    def get_values(self):
        this_ax_val = self.inst.__dict__[self.key]
        the_ax_val = self.inst_ruler.__dict__[self.key_ruler]
        return this_ax_val, the_ax_val

    def less(self):
        this_ax_val, the_ax_val = self.get_values()
        return this_ax_val < the_ax_val

    def more(self):
        this_ax_val, the_ax_val = self.get_values()
        return this_ax_val > the_ax_val

    def abide(self, *args, **kwargs):
        if self.op in ['<', '<=']: rule = self.less
        elif self.op in ['>', '>=']: rule = self.more
        if not rule():
            self.inst.__dict__[self.key] =\
                self.inst_ruler.__dict__[self.key_ruler]

class parameter_space_location(lfu.mobject):

    def __init__(self,location = [],trajectory_count = 1):
        self.location = location
        self.trajectory_count = trajectory_count
        lfu.mobject.__init__(self)

    def __setitem__(self, key, value):
        self.location[key] = value

    def __getitem__(self, key):
        return self.location[key]

    def __len__(self):
        return len(self.location)

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

def parse_p_space(p_sub, ensem):
    
    print 'parsepspace',p_sub
    pdb.set_trace()
  
    def validate(rng):
        valid = []
        for val in rng.split(','):
            try: valid.append(float(val))
            except: pass

        return valid

    def turn_on_mobjs_first_p_space_axis(mobj):
        dex = axes.index(mobj.name)
        mobj_attr = variants[dex]
        #mobj.set_settables(0, ensem)
        mobj.set_pspace_settables(0, ensem)
        for p_temp in mobj.parameter_space_templates:
            if mobj_attr == p_temp.key:
                p_temp.contribute_to_p_sp = True
                p_temp.p_sp_bounds = rng_bounds[dex]
                p_temp.p_sp_perma_bounds = rng_bounds[dex]
                p_temp.p_sp_increment = increments[dex]

    def read_increment(rng):
        if rng.count(';') > 0: read = float(rng[rng.rfind(';')+1:])
        else: read = 10
        return read

    if p_sub[0][0].count('<product_space>'):
        comp_meth = 'Product Space'

    elif p_sub[0][0].count('<zip_space>'): comp_meth = '1 - 1 Zip'
    elif p_sub[0][0].count('<fitting_space>'): comp_meth = 'Fitting'

    if comp_meth == 'Product Space' or comp_meth == '1 - 1 Zip':
        ax_lines = p_sub[1:]

    elif comp_meth == 'Fitting':
        ax_lines = []
        con_lines = []
        for li in p_sub[1:]:
            if li[0].startswith('#'): continue
            elif li[0].count('<axes>'): sub_parser = 'axes'
            elif li[0].count('<constraints>'): sub_parser = 'constraints'
            else:
                if sub_parser == 'axes': ax_lines.append(li)
                elif sub_parser == 'constraints': con_lines.append(li)

    def parse_axes(lines):
        axes = [ax[0] for ax in lines]
        variants = [ax[1] for ax in lines]
        ax_rngs = [ax[2] for ax in lines]
        return axes, variants, ax_rngs

    def parse_constraint(li, subspaces):
        ops = ['<', '>', '<=', '>=']
        op_in = [li.count(op) for op in ops]
        try:
            op = ops[op_in.index(True)]
            spl = li.split(op)
            which = subspaces[int(spl[0])]
            target = subspaces[int(spl[-1])]
            con = axis_constraint(
                op = op, inst = which.inst, key = which.key, 
                inst_ruler = target.inst, key_ruler = target.key)
            which.constraints.append(con)

        except:
            traceback.print_exc(file=sys.stdout)
            print 'unable to parse constraint', li

    axes, variants, ax_rngs = parse_axes(ax_lines)
    increments = [read_increment(rng) for rng in ax_rngs]
    ranges = [lm.make_range(rng)[0] for rng in ax_rngs]
    rng_bounds = [[validate(rng)[0], validate(rng)[-1]] 
                                    for rng in ranges]
    poss_contribs = ['species', 'variables', 'reactions']
    p_mobjs = ensem.cartographer_plan.parameter_space_mobjs
    for key in p_mobjs.keys():
        if key in poss_contribs:
            if type(p_mobjs[key]) is types.DictionaryType:
                for sub_key in p_mobjs[key].keys():
                    mobj = p_mobjs[key][sub_key]
                    if mobj.name in axes:
                        turn_on_mobjs_first_p_space_axis(mobj)

            if type(p_mobjs[key]) is types.ListType:
                for mobj in p_mobjs[key]:
                    if mobj.name in axes:
                        turn_on_mobjs_first_p_space_axis(mobj)

    ensem.cartographer_plan.generate_parameter_space()
    selected = [ensem.cartographer_plan.\
        parameter_space.get_start_position()]

    if comp_meth == 'Product Space' or comp_meth == '1 - 1 Zip':
        traj_dlg = p_space_proxy(parent = None, 
            base_object = selected, composition_method = comp_meth, 
            p_space = ensem.cartographer_plan.parameter_space)

        for ax, vari, rng in zip(axes, variants, ranges):
            trj_dlg_dex = traj_dlg.axis_labels.index(
                            ' : '.join([ax, vari]))
            traj_dlg.variations[trj_dlg_dex] = validate(rng)

        traj_dlg.on_make()
        ensem.cartographer_plan.trajectory_string =\
                            traj_dlg.result_string
        ensem.cartographer_plan.on_delete_selected_pts(
                                    preselected = None)
        ensem.cartographer_plan.on_reset_trajectory_parameterization()
        ensem.cartographer_plan.on_append_trajectory(traj_dlg.result)
        ensem.cartographer_plan.traj_count = p_sub[0][1]
        ensem.cartographer_plan.on_assert_trajectory_count(all_ = True)

    elif comp_meth == 'Fitting':
        subspaces = ensem.cartographer_plan.parameter_space.subspaces
        for li in lfu.flatten(con_lines):
            parse_constraint(li, subspaces)

class p_space_proxy(object):
    def __init__(self, *args, **kwargs):
        self.base_object = kwargs['base_object']
        self.p_space = kwargs['p_space']
        self.parent = kwargs['parent']

        self.result_string = None
        self.result = None
        self.constructed = []
        self.max_locations = 10000
        #variations is a list (in 1-1 with subspaces)
        #   of lists of values
        self.variations = [None]*len(self.p_space.subspaces)
        if not self.variations: self.NO_AXES_FLAG = True
        else: self.NO_AXES_FLAG = False
        self.comp_methods = ['Product Space', '1 - 1 Zip']
        self.axis_labels = [subsp.name for subsp in 
                            self.p_space.subspaces]
        if 'composition_method' in kwargs.keys():
            self.composition_method = kwargs['composition_method']
        else: self.composition_method = 'Product Space'

    def wrap_nones(self):
        for dex in range(len(self.variations)):
            if not self.variations[dex]:
                self.variations[dex] = [None]

    def create_product_space_locations(self):
        self.wrap_nones()
        tuple_table = itertools.product(*self.variations)
        for tup in tuple_table:
            fixed_tup = []
            for elem, dex in zip(tup, range(len(tup))):
                if elem is None:
                    fixed_tup.append(self.base_object[0][dex])

                else: fixed_tup.append(tup[dex])

            if len(self.constructed) > self.max_locations:
                print ''.join(['WILL NOT MAKE', str(len(
                    self.constructed)-1), '+LOCATIONS!'])
                break

            self.constructed.append(parameter_space_location(
                                location = list(fixed_tup)))

        vari_string = '\n\t\t'.join([' : '.join([ax, ', '.join(
                [str(var) for var in vari])]) for ax, vari in 
            zip(self.axis_labels, self.variations) if vari])
        self.result_string = '\t<product_space> #\n\t\t' + vari_string

    def create_one_to_one_locations(self):
        self.wrap_nones()
        max_leng = max([len(variant) for variant in self.variations])
        if max_leng > self.max_locations:
            print ''.join(['WILL NOT MAKE', str(len(
                    self.constructed)-1), '+LOCATIONS!'])
            return

        for dex in range(len(self.variations)):
            if self.variations[dex][0] is None:
                self.variations[dex] =\
                    [self.base_object[0][dex]]*max_leng

            elif len(self.variations[dex]) < max_leng:
                leng_diff = max_leng - len(self.variations[dex])
                last_value = self.variations[dex][-1]
                [self.variations[dex].append(last_value) for k in
                                                range(leng_diff)]

        for dex in range(max_leng):
            locale = [var[dex] for var in self.variations] 
            self.constructed.append(parameter_space_location(
                                        location = locale))

        self.result_string = '<zip>\n\t'
        pdb.set_trace()

    def on_make(self):
        if self.composition_method == 'Product Space':
            self.create_product_space_locations()
        elif self.composition_method == '1 - 1 Zip':
            self.create_one_to_one_locations()
        self.result = self.constructed

class parameter_space(lfu.mobject):

    '''
    initialize with template to make a space
        templates are interface_template_p_space_axis objects
    or initialize with subsps to make a space
        subsps are one_dim_space objects
    the first overrides the second
    '''
    def __init__(self, *args, **kwargs):
        if 'base_obj' in kwargs.keys():
        #if not base_obj is None:
            self.subspaces = []
            for template in base_obj.parameter_space_templates:
                if template.contribute_to_p_sp:
                    self.subspaces.append(one_dim_space(template)) 

        else:
            try: self.subspaces = kwargs['subspaces']
            except KeyError:
                traceback.print_exc(file=sys.stdout)
                msg = '''\
                    parameter space __init__ requires either subspaces\
                    or a base_obj to make subspaces from\
                    '''
                lfu.debug_filter(msg, verbosity = 0)
                self.subspaces = []

            self.set_simple_space_lookup()

        self.impose_default('steps', [], **kwargs)
        self.impose_default('step_normalization', 5.0, **kwargs)
        self.dimensions = len(self.subspaces)
        lfu.mobject.__init__(self, *args, **kwargs)

    def set_start_position(self):
        self.undo_level = 0
        for subsp in self.subspaces:
            subsp.initialize()
            rele_val = subsp.current_location()
            print 'starting position of', subsp.name, ':', rele_val, ':', subsp.bounds

    def get_start_position(self):
        location = [sp.inst.__dict__[sp.key] 
                    for sp in self.subspaces]
        return parameter_space_location(location = location)

    def get_current_position(self):
        return [(axis.inst.name, axis.key, 
            str(axis.current_location())) 
            for axis in self.subspaces]

    def set_current_position(self, position):
        for pos, axis in zip(position, self.subspaces):
            axis.move_to(pos[-1])

        self.validate_position()

    def validate_position(self):
        for axis in self.subspaces:
            if axis.constraints:
                axis.honor_constraints()

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

#class interface_template_p_space_axis(lfu.data_container):
class pspace_axis(lfu.mobject):

    def __init__(self,*args,**kwargs):
        self._default('instance',None,**kwargs)
        self._default('key',None,**kwargs)
        self._default('continuous',True,**kwargs)
        self._default('bounds',[0,1],**kwargs)
        self._default('permanent_bounds',[0,1],**kwargs)
        self._default('increment',0.1,**kwargs)
        self._default('contribute',False,**kwargs)
        if lgm: self.mason = lgm.standard_mason(parent = self)
        lfu.mobject.__init__(self,*args,**kwargs)

    def _display(self):
        #panel_x = self.panel.sizeHint().width()*1.5
        #panel_y = self.panel.sizeHint().height()*1.25
        #panel_x,panel_y = min([panel_x,1600]),min([panel_y,900])
        panel_x,panel_y = 256,256
        lfu.mobject._display(self,self.mason,(150,120,panel_x,panel_y))

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['check_set','button_set'], 
                instances = [[self],None], 
                keys = [['contribute'],None], 
                labels = [['Contribute to Parameter Space'],['More Settings']],
                append_instead = [False,None], 
                bindings = [None,[self._display]], 
                box_labels = ['Parameter Space']))
        self.widg_dialog_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin','spin'], 
                doubles = [[True],[True]], 
                initials = [[self.bounds[0]],[self.bounds[1]]], 
                minimum_values = [[-sys.float_info.max],[-sys.float_info.max]],
                maximum_values = [[sys.float_info.max],[sys.float_info.max]], 
                instances = [[self.bounds],[self.bounds]], 
                keys = [[0],[1]], 
                box_labels = ['Subspace Minimum','Subspace Maximum'], 
                panel_label = 'Parameter Space'))
        lfu.mobject._widget(self,*args,from_sub = True)

class cartographer_plan(lfu.plan):

    def __init__(self,parent = None,name = 'mapping plan',
            parameter_space_mobjs = {},traj_count = 1,key_path = ''):
        self.parameter_space = None
        self.parameter_space_mobjs = parameter_space_mobjs
        self.trajectory = []
        self.iteration = 0
        self.controller_ref = None
        self.traj_count = traj_count
        self.key_path = key_path
        self.trajectory_string = ''
        use = lset.get_setting('mapparameterspace')
        lfu.plan.__init__(self,name = name,parent = parent,use_plan = use)

    def to_string(self):
        if self.trajectory:
            #cnt = self.trajectory[0][1].trajectory_count
            cnt = str(self.traj_count)

        else: cnt = '1'
        lines = [self.trajectory_string.replace('#', cnt)]
        return lines

    def generate_parameter_space(self):
        self.parameter_space, valid =\
            generate_parameter_space_from_run_params(
                    self, self.parameter_space_mobjs)
        if valid:
            self.trajectory = [[0] +\
                [self.parameter_space.get_start_position()]]
            self.rewidget(True)

        else:
            lgd.message_dialog(None, 
                'No parameter space axes specified!', 'Problem')

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

    def move_to(self, t):
        move_to = self.trajectory[t][1]
        for loc, subsp in zip(move_to, self.parameter_space.subspaces):
            subsp.move_to(loc)

    #def sanitize(self, *args, **kwargs):
    #   self.create_traj_templates = []
    #   lfu.plan.sanitize(self)

    def set_settables(self, *args, **kwargs):
        window = args[0]
        self.handle_widget_inheritance(*args, **kwargs)
        #self.widg_templates.append(
        right_side = [lgm.interface_template_gui(
                layout = 'grid', 
                panel_position = (0, 2), 
                widg_positions = [(0, 0), (1, 0), (2, 0)], 
                layouts = ['vertical', 'vertical', 'vertical'], 
                widgets = ['button_set', 'spin', 'full_path_box'], 
                initials = [None, [self.traj_count], 
                    [self.key_path, 'Possible Outputs (*.txt)']], 
                minimum_values = [None, [1], None], 
                maximum_values = [None, [100000], None], 
                instances = [None, [self], [self]], 
                keys = [None, ['traj_count'], ['key_path']], 
                bindings = [[lgb.create_reset_widgets_wrapper(
                        window, self.generate_parameter_space), 
                    self.generate_traj_diag_function(window, 'blank'), 
                    self.generate_traj_diag_function(window, 'modify'), 
                    lgb.create_reset_widgets_wrapper(window, 
                            self.on_delete_selected_pts), 
                    self.on_output_trajectory_key, 
                    lgb.create_reset_widgets_wrapper(window, 
                        self.on_assert_trajectory_count)], None, None], 
                labels = [['Generate Parameter Space', 
                    'Create Trajectory', 'Replace Selected Points', 
                    'Delete Selected Points', 'Output Trajectory Key', 
                    'Assert Trajectory Count\n to Selected'], None, 
                                            ['Choose File Path']], 
                box_labels = [None, 'Trajectory Count', 
                        'Trajectory Key File Path'])]
        split_widg_templates = [
            lgm.interface_template_gui(
                widgets = ['splitter'], 
                orientations = [['horizontal']], 
                templates = [right_side])]
        if not self.parameter_space is None:
            #a point consists of a list of 2 components
            #   the first is the index of the location
            #   the second is the values in 1-1 with 
            #   p-space subspaces
            headers = [subsp.name for subsp in 
                self.parameter_space.subspaces] + ['']
            #self.widg_templates.append(
            left_side = [lgm.interface_template_gui(
                    widgets = ['list_controller'], 
                    panel_position = (0, 0), 
                    panel_span = (3, 2), 
                    handles = [(self, 'controller_ref')], 
                    labels = [['Index'.ljust(16), 
                        'Trajectory Count'] + headers], 
                    minimum_sizes = [[(500, 300)]], 
                    entries = [self.trajectory], 
                    box_labels = ['Trajectory In Parameter Space'])]
            split_widg_templates[-1].templates =\
                        [left_side + right_side]

        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['panel'], 
                templates = [split_widg_templates], 
                scrollable = [True], 
                box_labels = ['Parameter Space']))
        lfu.mobject.set_settables(
                self, *args, from_sub = True)

class metric(lfu.mobject):

    #ABSTRACT
    '''
    a metric takes two sets of data and runs some method which
    returns one scalar representing some sort of distance
    '''
    def __init__(self, *args, **kwargs):
        if not 'valid_base_classes' in kwargs.keys():
            global valid_metric_base_classes
            kwargs['valid_base_classes'] = valid_metric_base_classes

        if not 'base_class' in kwargs.keys():
            kwargs['base_class'] = lfu.interface_template_class(
                                    object, 'abstract metric')

        self.impose_default('best_measure', 0, **kwargs)
        self.impose_default('display_threshold', 0, **kwargs)
        self.impose_default('display_time', 1.0, **kwargs)
        self.impose_default('prints_for_best', False, **kwargs)
        self.impose_default('acceptance_weight', 1.0, **kwargs)
        self.impose_default('best_advantage', 2.0, **kwargs)
        self.impose_default('best_flag', False, **kwargs)
        self.impose_default('is_heaviest', False, **kwargs)
        lfu.mobject.__init__(self, *args, **kwargs)
        self._children_ = []

    def check_best(self, display = False):
        if self.best_flag:
            if not self.is_heaviest:
                self.acceptance_weight /= self.best_advantage

        self.best_flag = False
        if self.data[0].scalars[-1] == min(self.data[0].scalars):
            self.best_measure = len(self.data[0].scalars) - 1
            self.best_flag = True
            #self.best_flag = True and self.prints_for_best
            if not self.is_heaviest:
                self.acceptance_weight *= self.best_advantage

        if (self.best_flag or display) and self.is_heaviest:
            meas = self.data[0].scalars[-1]
            print ' '.join(['\nmetric', self.name, 'measured best', 
                    str(meas), str(len(self.data[0].scalars) - 1)])
            for pos in self.parent.parameter_space.get_current_position():
                print pos
            #lgd.quick_plot_display(to_fit_to[0], 
            #   to_fit_to[1:] + run_data_interped, 
            #           delay = self.display_time)
            print '\n'

    def measure(self, *args, **kwargs):
        to_fit_to = args[0]
        run_data = args[1]
        dom_weight_max = 5.0
        domain_weights = np.exp(np.linspace(dom_weight_max, 
                            0, len(to_fit_to[0].scalars)))
        #domain_weights = [1 for val in 
        #   np.linspace(0, 1, len(to_fit_to[0].scalars))]
        #domain_weights = np.linspace(dom_weight_max, 
        #               1, len(to_fit_to[0].scalars))
        if self.best_flag:
            self.best_flag = False
            self.acceptance_weight /= 2.0

        try: report_only = kwargs['report_only']
        except KeyError: report_only = False

        labels = [[do.name for do in de] for de in args]
        run_data_domain = run_data[labels[1].index(labels[0][0])]
        try:
            run_data_codomains = [run_data[labels[1].index(
                    labels[0][lab_dex+1])] for lab_dex 
                        in range(len(labels[0][1:]))]
        except ValueError: pdb.set_trace()
        run_data_interped = [scalars(
            label = 'interpolated result - ' + codomain.name, 
            scalars = lm.linear_interpolation(run_data_domain.scalars, 
                    codomain.scalars, to_fit_to[0].scalars, 'linear')) 
                                for codomain in run_data_codomains]
        x_meas_bnds = (0, len(to_fit_to[0].scalars))
        meas = [[diff for diff in kwargs['measurement'](
            fit_to.scalars, interped.scalars, x_meas_bnds, 
            to_fit_to[0].scalars, domain_weights) if not 
                math.isnan(diff)] for fit_to, interped in 
                    zip(to_fit_to[1:], run_data_interped)]
        meas = np.mean([np.mean(mea) for mea in meas])
        if not report_only:
            self.data[0].scalars.append(meas)
            if meas == min(self.data[0].scalars) and\
                    meas < self.data[0].scalars[self.best_measure]:
                self.best_measure = len(self.data[0].scalars) - 1
                #self.best_flag = self.best_measure > self.display_threshold
                #self.best_flag = True and self.prints_for_best
                self.best_flag = True

            if self.best_flag:
                if 'weight' in kwargs.keys():
                    self.acceptance_weight = kwargs['weight']

                else: self.acceptance_weight *= 2.0
            if (self.best_flag or kwargs['display']) and self.is_heaviest:
                print ' '.join(['metric', self.name, 'measured', 
                    str(meas), str(len(self.data[0].scalars))])
                print self.parent.parameter_space.get_current_position()
                lgd.quick_plot_display(to_fit_to[0], 
                    to_fit_to[1:] + run_data_interped, 
                            delay = self.display_time)

        else: return meas

class metric_avg_ptwise_diff_on_domain(metric):

    def __init__(self, *args, **kwargs):
        if not 'name' in kwargs.keys():
            kwargs['name'] = 'pointwise difference metric'
        metric.__init__(self, *args, **kwargs)

    def initialize(self, *args, **kwargs):
        #self.data = scalars_from_labels(['mean difference'])
        self.data = ldc.scalars_from_labels(['mean difference'])
        metric.initialize(self, *args, **kwargs)

    def measure(self, *args, **kwargs):
        #if not 'report_only' in kwargs.keys():
        #   kwargs['report_only'] = False
        kwargs['measurement'] = self.differences
        return metric.measure(self, *args, **kwargs)

    def differences(self, *args, **kwargs):
        to_fit_to_y = args[0]
        runinterped = args[1]
        bounds = args[2]
        dom_weights = args[4]
        return [weight*abs(to_fit_to_y[k] - runinterped[k]) 
                        for weight, k in zip(dom_weights, 
                            range(bounds[0], bounds[1]))]

class metric_slope_1st_derivative(metric):

    def __init__(self, *args, **kwargs):
        if not 'name' in kwargs.keys():
            kwargs['name'] = 'slope metric'
        metric.__init__(self, *args, **kwargs)

    def initialize(self, *args, **kwargs):
        #self.data = scalars_from_labels(['mean slope difference'])
        self.data = ldc.scalars_from_labels(['mean slope difference'])
        metric.initialize(self, *args, **kwargs)

    def measure(self, *args, **kwargs):
        kwargs['measurement'] = self.slope_differences
        return metric.measure(self, *args, **kwargs)

    def slope_differences(self, *args, **kwargs):
        to_fit_to_y = args[0]
        runinterped = args[1]
        bounds = args[2]
        to_fit_to_x = args[3]
        dom_weights = args[4]
        runinterped_slope = [(runinterped[k] - runinterped[k - 1])\
                    /(to_fit_to_x[k] - to_fit_to_x[k - 1]) 
                    for k in range(1, len(to_fit_to_x))]
        to_fit_to_y_slope = [(to_fit_to_y[k] - to_fit_to_y[k - 1])\
                            /(to_fit_to_x[k] - to_fit_to_x[k - 1]) 
                            for k in range(1, len(to_fit_to_x))]
        return [weight*abs(to_fit_to_y_slope[k] - runinterped_slope[k]) 
                for weight, k in zip(dom_weights, 
                range(bounds[0], bounds[1] -1))]

class metric_slope_2nd_derivative(metric):

    def __init__(self, *args, **kwargs):
        if not 'name' in kwargs.keys():
            kwargs['name'] = '2nd derivative metric'
        metric.__init__(self, *args, **kwargs)

    def initialize(self, *args, **kwargs):
        #self.data = scalars_from_labels(['mean 2nd derivative'])
        self.data = ldc.scalars_from_labels(['mean 2nd derivative'])
        metric.initialize(self, *args, **kwargs)

    def measure(self, *args, **kwargs):
        kwargs['measurement'] = self.second_derivative_differences
        return metric.measure(self, *args, **kwargs)

    def second_derivative_differences(self, *args, **kwargs):

        def calc_2nd_deriv(x, y, dex):
            del_x_avg = (x[dex + 1] - x[dex - 1])/2.0
            return (y[dex + 1] - (2*y[dex]) + y[dex - 1])\
                                /((x[dex] - del_x_avg)**2)

        to_fit_to_y = args[0]
        runinterped = args[1]
        bounds = args[2]
        to_fit_to_x = args[3]
        dom_weights = args[4]
        runinterped_slope = [
            calc_2nd_deriv(to_fit_to_x, runinterped, k) 
                for k in range(1, len(to_fit_to_x) -1)]
        to_fit_to_y_slope = [
            calc_2nd_deriv(to_fit_to_x, to_fit_to_y, k) 
                for k in range(1, len(to_fit_to_x) -1)]
        return [weight*abs(to_fit_to_y_slope[k] - runinterped_slope[k]) 
                            for weight, k in zip(dom_weights, range(
                                    bounds[0] + 1, bounds[1] - 2))]

class metric_slope_3rd_derivative(metric):

    def __init__(self, *args, **kwargs):
        if not 'name' in kwargs.keys():
            kwargs['name'] = '3rd derivative metric'
        metric.__init__(self, *args, **kwargs)

    def initialize(self, *args, **kwargs):
        #self.data = scalars_from_labels(['mean 3rd derivative'])
        self.data = ldc.scalars_from_labels(['mean 3rd derivative'])
        metric.initialize(self, *args, **kwargs)

    def measure(self, *args, **kwargs):
        kwargs['measurement'] = self.third_derivative_differences
        return metric.measure(self, *args, **kwargs)

    def third_derivative_differences(self, *args, **kwargs):

        def calc_3rd_deriv(x, y, dex):
            top = (y[dex - 2] - (3*y[dex - 1]) +\
                        (3*y[dex]) + y[dex + 1])
            del_x_avg = ((x[dex + 1] - x[dex - 2]))/3.0
            return top/((x[dex] - del_x_avg)**3)

        to_fit_to_y = args[0]
        runinterped = args[1]
        bounds = args[2]
        to_fit_to_x = args[3]
        dom_weights = args[4]
        runinterped_slope = [
            calc_3rd_deriv(to_fit_to_x, runinterped, k) 
                for k in range(1, len(to_fit_to_x) -1)]
        to_fit_to_y_slope = [
            calc_3rd_deriv(to_fit_to_x, to_fit_to_y, k) 
                for k in range(1, len(to_fit_to_x) -1)]
        return [weight*abs(to_fit_to_y_slope[k] - runinterped_slope[k]) 
                for weight, k in zip(dom_weights, 
                range(bounds[0] + 2, bounds[1] - 2))]

class metric_slope_4th_derivative(metric):

    def __init__(self, *args, **kwargs):
        if not 'name' in kwargs.keys():
            kwargs['name'] = '4th derivative metric'
        metric.__init__(self, *args, **kwargs)

    def initialize(self, *args, **kwargs):
        #self.data = scalars_from_labels(['mean 4th derivative'])
        self.data = ldc.scalars_from_labels(['mean 4th derivative'])
        metric.initialize(self, *args, **kwargs)

    def measure(self, *args, **kwargs):
        kwargs['measurement'] = self.fourth_derivative_differences
        return metric.measure(self, *args, **kwargs)

    def fourth_derivative_differences(self, *args, **kwargs):

        def calc_4th_deriv(x, y, dex):
            left = (y[dex - 2] - (2*y[dex - 1]) + y[dex])
            right = (y[dex] - (2*y[dex + 1]) + y[dex + 2])
            #top = (y[dex - 2] - (3*y[dex - 1]) +\
            #           (3*y[dex]) + y[dex + 1])
            del_x_avg = ((x[dex + 2] - x[dex - 2]))/4.0
            print 'DONT USE THIS YET!'; return None
            return top/((x[dex] - del_x_avg)**4)

        to_fit_to_y = args[0]
        runinterped = args[1]
        bounds = args[2]
        to_fit_to_x = args[3]
        runinterped_slope = [
            calc_4th_deriv(to_fit_to_x, runinterped, k) 
                for k in range(1, len(to_fit_to_x) -1)]
        to_fit_to_y_slope = [
            calc_4th_deriv(to_fit_to_x, to_fit_to_y, k) 
                for k in range(1, len(to_fit_to_x) -1)]
        return [abs(to_fit_to_y_slope[k] - runinterped_slope[k]) 
                for k in range(bounds[0] + 2, bounds[1] - 3)]






