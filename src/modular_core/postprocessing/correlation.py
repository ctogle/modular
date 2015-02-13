

class post_process_correlation_values(post_process):

    def __init__(self, *args, **kwargs):
    #def __init__(self, label = 'another correlation', ordered = True, 
    #       target_1 = None, target_2 = None, function_of = None, 
    #       bin_count = 10, fill_value = -100.0, 
    #       regime = 'all trajectories', base_class = None, 
    #       capture_targets = [], input_regime = ['simulation'], 
    #       valid_inputs = ['simulation'], 
    #       valid_regimes = ['all trajectories', 
    #                       'by parameter space']):
                            #'by parameter space', 
                            #   'manual grouping']):

        if not 'base_class' in kwargs.keys():
            kwargs['base_class'] = lfu.interface_template_class(
                                        object, 'correlation')

        if not 'label' in kwargs.keys():
            kwargs['label'] = 'correlation'

        if not 'valid_regimes' in kwargs.keys():
            kwargs['valid_regimes'] = ['all trajectories', 
                                'by parameter space']

        if not 'regime' in kwargs.keys():
            kwargs['regime'] = 'all trajectories'

        self._default('target_1', None, **kwargs)
        self._default('target_2', None, **kwargs)
        self._default('function_of', None, **kwargs)
        self._default('bin_count', 100, **kwargs)
        self._default('ordered', True, **kwargs)
        self._default('fill_value', -100.0, **kwargs)
        #post_process.__init__(self, label = label, regime = regime, 
        #   base_class = base_class, valid_regimes = valid_regimes, 
        #   input_regime = input_regime, valid_inputs = valid_inputs, 
        #   capture_targets = capture_targets)
        post_process.__init__(self, *args, **kwargs)

    def to_string(self):
        #x, y correlation : correlation : 0 : x and y of time : 10 : ordered
        inps = self.string_inputs()
        phrase = ' of '.join([' and '.join(
            [self.target_1, self.target_2]), 
                self.function_of])
        bins = str(self.bin_count)
        if self.ordered: ordered = 'ordered'
        else: ordered = 'unordered'
        return '\t' + ' : '.join([self.label, 'correlation', 
                        inps, phrase, bins, ordered])

    def provide_axes_manager_input(self):
        self.use_line_plot = True
        self.use_color_plot = False
        self.use_voxel_plot = False
        self.use_bar_plot = False

    def postproc(self, *args, **kwargs):
        kwargs['method'] = self.correlate
        post_process.postproc(self, *args, **kwargs)

    def correlate(self, *args, **kwargs):

        def verify(val):
            if math.isnan(val): return self.fill_value
            else: return val

        bin_axes, targ_1_axes = select_for_binning(
            args[0], self.function_of, self.target_1)
        bin_axes, targ_2_axes = select_for_binning(
            args[0], self.function_of, self.target_2)
        bins, vals_1 = bin_scalars(bin_axes, targ_1_axes, 
                            self.bin_count, self.ordered)
        bins, vals_2 = bin_scalars(bin_axes, targ_2_axes, 
                            self.bin_count, self.ordered)
        correlations, p_values = zip(*[correl_coeff(val_1, val_2) 
                        for val_1, val_2 in zip(vals_1, vals_2)])
        #data = lgeo.scalars_from_labels([self.function_of, 
        data = ldc.scalars_from_labels([self.function_of, 
            'correlation coefficients', 'correlation p-value'])
        data[0].scalars = bins
        data[1].scalars = [verify(val) for val in correlations]
        data[2].scalars = [verify(val) for val in p_values]
        return data

    def _target_settables(self, *args, **kwargs):
        self.valid_regimes = ['all trajectories', 
            #'by parameter space', 'manual grouping']
            'by parameter space']
        self.valid_inputs = self._valid_inputs(*args, **kwargs)
        capture_targetable = self._targetables(*args, **kwargs)
        if self.target_1 is None:
            if capture_targetable:
                self.target_1 = capture_targetable[0]

        if self.target_2 is None:
            if capture_targetable:
                self.target_2 = capture_targetable[0]

        if self.function_of is None:
            if capture_targetable:
                self.function_of = capture_targetable[0]

        self.capture_targets = [self.function_of, 
            'correlation coefficients', 'correlation p-value']
        post_process._target_settables(self, *args, **kwargs)

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                panel_position = (1, 3), 
                instances = [[self]], 
                keys = [['ordered']], 
                labels = [['Domain is Ordered']], 
                append_instead = [False], 
                widgets = ['check_set'], 
                box_labels = ['Ordered Domain']))
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin'], 
                instances = [[self]], 
                keys = [['bin_count']], 
                initials = [[self.bin_count]], 
                minimum_values = [[1]], 
                maximum_values = [[100000]], 
                box_labels = ['Number of Bins']))
        self.widg_templates.append(
            lgm.interface_template_gui(
                keys = [['function_of']], 
                instances = [[self]], 
                widgets = ['radio'], 
                panel_label = 'As a Function of', 
                initials = [[self.function_of]], 
                labels = [capture_targetable]))
        self.widg_templates.append(
            lgm.interface_template_gui(
                layout = 'horizontal', 
                keys = [['target_1'], ['target_2']], 
                instances = [[self], [self]], 
                widgets = ['radio', 'radio'], 
                panel_label = 'Correlation of', 
                initials = [[self.target_1], [self.target_2]], 
                labels = [capture_targetable, capture_targetable], 
                box_labels = ['Target 1', 'Target 2']))
        super(post_process_correlation_values, self).set_settables(
                                            *args, from_sub = True)

