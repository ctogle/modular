
class post_process_standard_statistics(post_process):

    def __init__(self, *args, **kwargs):
        if not 'base_class' in kwargs.keys():
            kwargs['base_class'] = lfu.interface_template_class(
                                object, 'standard statistics')

        if not 'label' in kwargs.keys():
            kwargs['label'] = 'standard statistics'

        if not 'valid_regimes' in kwargs.keys():
            kwargs['valid_regimes'] = ['all trajectories', 
                                'by parameter space']

        if not 'regime' in kwargs.keys():
            kwargs['regime'] = 'all trajectories'

        self._default('function_of', None, **kwargs)
        self._default('mean_of', None, **kwargs)
        self._default('bin_count', 100, **kwargs)
        self._default('ordered', True, **kwargs)
        post_process.__init__(self, *args, **kwargs)

    def to_string(self):
        #x stats : standard statistics : 0 : x of time : 10 : ordered
        inps = self._string_inputs()
        phrase = ' of '.join([self.mean_of, self.function_of])
        bins = str(self.bin_count)
        if self.ordered: ordered = 'ordered'
        else: ordered = 'unordered'
        return '\t' + ' : '.join([self.label, 'standard statistics', 
                                inps, phrase, bins, ordered])

    def postproc(self, *args, **kwargs):
        kwargs['method'] = self.meanfield
        post_process.postproc(self, *args, **kwargs)

    def meanfield(self, *args, **kwargs):
        bin_axes, mean_axes = select_for_binning(
            args[0], self.function_of, self.mean_of)
        bins, vals = bin_scalars(bin_axes, mean_axes, 
                        self.bin_count, self.ordered)
        means = [np.mean(val) for val in vals]
        medians = [np.median(val) for val in vals]
        stddevs = [np.stddev(val) for val in vals]
        if 0.0 in means or 0.0 in stddevs: coeff_var_dont_flag = True
        else: coeff_var_dont_flag = False
        if coeff_var_dont_flag:
            print 'COEFFICIENT OF VARIATIONS WAS SET TO ZERO TO SAVE THE DATA'
            coeff_variations = [0.0 for stddev_, mean_ 
                                in zip(stddevs, means)]

        else:
            coeff_variations = [stddev_ / mean_ for 
                stddev_, mean_ in zip(stddevs, means)]

        #variances = [mean(val) for val in vals]
        variances = [variance(val) for val in vals]
        #data = lgeo.scalars_from_labels(self.target_list)
        data = ldc.scalars_from_labels(self.target_list)
        data[0].scalars = bins
        data[1].scalars = means
        data[2].scalars = medians
        data[3].scalars = variances
        data[4].scalars = stddevs
        data[5].scalars = [means[k] + stddevs[k] 
                    for k in range(len(means))]
        data[6].scalars = [means[k] - stddevs[k] 
                    for k in range(len(means))]
        data[7].scalars = coeff_variations
        return data

    #this is a stupid hack!
    def provide_axes_manager_input(self):
        self.use_line_plot = True
        self.use_color_plot = False
        self.use_bar_plot = False
        self.use_voxel_plot = False
        self.x_title = self.function_of

    def _target_settables(self, *args, **kwargs):
        self.valid_regimes = ['all trajectories','by parameter space']
        self.valid_inputs = self._valid_inputs(*args, **kwargs)
        capture_targetable = self._targetables(*args, **kwargs)
        if self.mean_of is None and capture_targetable:
            self.mean_of = capture_targetable[0]

        if self.function_of is None and capture_targetable:
            self.function_of = capture_targetable[0]

        self.target_list = [self.function_of, 
            self.mean_of + ' mean', self.mean_of + ' median', 
            self.mean_of + ' variance', '1 stddev of ' + self.mean_of, 
            self.mean_of + ' +1 stddev', self.mean_of + ' -1 stddev', 
            self.mean_of + ' coefficient of variation']
        self.capture_targets = self.target_list
        post_process._target_settables(self, *args, **kwargs)

    def set_settables(self, *args, **kwargs):
        self.handle_widget_inheritance(*args, from_sub = False)
        capture_targetable = self._targetables(*args, **kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                panel_position = (1, 3), 
                widgets = ['check_set'], 
                append_instead = [False], 
                instances = [[self]], 
                #rewidget = [[True]], 
                keys = [['ordered']], 
                labels = [['Domain is Ordered']], 
                box_labels = ['Ordered Domain']))
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin'], 
                initials = [[self.bin_count]], 
                minimum_values = [[1]], 
                maximum_values = [[100000]], 
                instances = [[self]], 
                #rewidget = [[True]], 
                keys = [['bin_count']], 
                box_labels = ['Number of Bins']))
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['radio'], 
                labels = [capture_targetable], 
                initials = [[self.function_of]], 
                instances = [[self]], 
                keys = [['function_of']], 
                box_labels = ['As a Function of']))
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['radio'], 
                labels = [capture_targetable], 
                initials = [[self.mean_of]], 
                instances = [[self]], 
                keys = [['mean_of']], 
                box_labels = ['Statistics of']))
        super(post_process_standard_statistics, self).set_settables(
                                    *args, from_sub = True)
