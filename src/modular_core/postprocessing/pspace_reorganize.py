

class post_process_reorganize_data(post_process):

    #the purpose of this process is to reorganize data
    #so that measurements are taken as a function of p-space index
    #within the p-space trajectory, to be resolved into color plots
    #representing 2-d subspaces of the p-space
    #thus any process which can use p-space, can be reorganized
    #if not using p-space, data won't be in the proper structure - 
    # this process then cannot be used and must be ignored
    def __init__(self, *args, **kwargs):
    #def __init__(self, label = 'reorganize data', 
    #       capture_targets = [], input_regime = ['simulation'], 
    #       valid_inputs = ['simulation'], dater_ids = None, 
    #       slice_dex = 0, regime = 'all trajectories', 
    #       base_class = None, valid_regimes = ['all trajectories']):
    #   if base_class is None:
    #       base_class = lfu.interface_template_class(
    #                       object, 'reorganize data')
        if not 'base_class' in kwargs.keys():
            kwargs['base_class'] = lfu.interface_template_class(
                                    object, 'reorganize data')

        if not 'label' in kwargs.keys():
            kwargs['label'] = 'reorganize'

        if not 'valid_regimes' in kwargs.keys():
            kwargs['valid_regimes'] = ['all trajectories', 
                                'by parameter space']

        if not 'regime' in kwargs.keys():
            kwargs['regime'] = 'all trajectories'

        self._default('dater_ids', None, **kwargs)
        #post_process.__init__(self, label = label, regime = regime, 
        #   base_class = base_class, valid_regimes = valid_regimes, 
        #   input_regime = input_regime, valid_inputs = valid_inputs, 
        #   capture_targets = capture_targets)
        post_process.__init__(self, *args, **kwargs)

    def to_string(self):
        #reorg : reorganize data : 2 : all
        inps = self._string_inputs()
        phrase = 'all'
        return '\t' + ' : '.join([self.label, 
            'reorganize data', inps, phrase])

    def provide_axes_manager_input(self):
        self.use_line_plot = True
        #self.use_line_plot = False
        self.use_color_plot = True
        self.use_voxel_plot = False
        self.use_bar_plot = False

    def postproc(self, *args, **kwargs):
        if not args[0].cartographer_plan.use_plan and\
                    not args[0].fitting_plan.use_plan:
            print 'ensemble is not mapping p-space' +\
                        '\n\treorganize will be ignored'
            return

        kwargs['method'] = self.data_by_trajectory
        #this is a hack to fix an undiagnosed bug
        self.valid_regimes = ['all trajectories']
        post_process.postproc(self, *args, **kwargs)

    def handle_all_trajectories(self, method, pool, p_space):
        self.data = [method(pool, p_space)]
        self.output.flat_data = False

    #take a collection of trajectories in 1 - 1 with p_space trajectory
    #create a dater of indices for that trajectory
    #create new daters in 1 - 1 with that dater, 
    #one for each dater in each trajectory of the original collection, 
    #which aggregates the original collection of trajectories
    def data_by_trajectory(self, *args, **kwargs):
        trajectory = args[0]
        p_space_map = args[1]
        #data = lgeo.scalars_from_labels(
        data = ldc.scalars_from_labels(
                ['parameter space location index'] +\
                self.axis_labels + [label for label in self.dater_ids])
        for dex, locale in enumerate(trajectory):
            data[0].scalars.append(dex)
            p_space_locale_values =\
                p_space_map.trajectory[dex][1].location
            [dater.scalars.append(float(loc)) for loc, dater in 
                                    zip(p_space_locale_values, 
                        data[1:len(self.axis_labels) + 1])]
            for dater in data[len(self.axis_labels) + 1:]:
                try:
                    value = lfu.grab_mobj_by_name(
                        dater.label, locale).scalars[-1]
                except: pdb.set_trace()
                dater.scalars.append(value)

        surf_targets =\
            ['parameter space location index'] + self.dater_ids
        #data.append(lgeo.surface_vector_reducing(data, 
        data.append(ldc.surface_vector_reducing(data, 
            self.axis_labels, surf_targets, 'reorg surface vector'))
        return data

    def _target_settables(self, *args, **kwargs):
        self.valid_inputs = self._valid_inputs(*args, **kwargs)
        capture_targetable = self._targetables(*args, **kwargs)
        if self.dater_ids is None: self.dater_ids = []
        try:
            self.axis_labels = [subsp.label for subsp in 
                args[1].cartographer_plan.parameter_space.subspaces]

        except AttributeError: self.axis_labels = []
        self.capture_targets = ['parameter space location index'] +\
            self.axis_labels + [label for label in self.dater_ids] +\
            ['reorg surface vector']
        self.output.targeted = [targ for targ in self.output.targeted 
                                    if targ in self.capture_targets]
        post_process._target_settables(self, *args, **kwargs)

    def set_settables(self, *args, **kwargs):
        self.handle_widget_inheritance(*args, from_sub = False)
        capture_targetable = self._targetables(*args, **kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                keys = [['dater_ids']], 
                instances = [[self]], 
                widgets = ['check_set'], 
                box_labels = ['Relevant Data'], 
                append_instead = [True], 
                provide_master = [True], 
                labels = [capture_targetable]))
        super(post_process_reorganize_data, 
            self).set_settables(*args, from_sub = True)
