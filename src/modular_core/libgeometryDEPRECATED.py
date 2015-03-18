
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



class cartographer_plan(lfu.plan):


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








