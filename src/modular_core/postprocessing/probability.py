

class post_process_measure_probability(post_process):

    def __init__(self, *args, **kwargs):
        if not 'base_class' in kwargs.keys():
            kwargs['base_class'] = lfu.interface_template_class(
                                        object, 'probability')

        if not 'label' in kwargs.keys():
            kwargs['label'] = 'probability measurement'

        if not 'valid_regimes' in kwargs.keys():
            kwargs['valid_regimes'] = ['all trajectories', 
                                'by parameter space']

        if not 'regime' in kwargs.keys():
            kwargs['regime'] = 'all trajectories'

        self.probability_criterion =\
            lc.trajectory_criterion_ceiling(parent = self)
        post_process.__init__(self, *args, **kwargs)
        self.children = [self.probability_criterion]

    def _string(self):
        inps = self._string_inputs()
        return '\t' + ' : '.join([self.name, 'probability', inps])

    def postproc(self, *args, **kwargs):
        kwargs['method'] = self.measure_probability
        post_process.postproc(self, *args, **kwargs)

    def measure_probability(self, *args, **kwargs):
        passes = 0.0
        for traj in args[0]:
            if self.probability_criterion(traj): passes += 1.0
        #data = lgeo.scalars_from_labels(['probability'])
        data = ldc.scalars_from_labels(['probability'])
        data[0].scalars = [passes/len(args[0])]
        return data

    def _target_settables(self,*args,**kwargs):
        self.valid_regimes = ['all trajectories','by parameter space']
        self.valid_inputs = self._valid_inputs(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        self.capture_targets = ['probability']
        post_process._target_settables(self, *args, **kwargs)

    def set_settables(self, *args, **kwargs):
        self.handle_widget_inheritance(*args, from_sub = False)
        capture_targetable = self._targetables(*args, **kwargs)
        kwargs['capture_targetable'] = capture_targetable
        self.probability_criterion.set_settables(*args, **kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['panel'], 
                templates = [self.probability_criterion.widg_templates]))
        super(post_process_measure_probability, self).set_settables(
                                            *args, from_sub = True)
