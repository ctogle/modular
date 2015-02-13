
class post_process_slice_from_trajectory(post_process):

    def __init__(self, *args, **kwargs):
    #def __init__(self, label = 'slice from trajectory', 
    #       capture_targets = [], dater_ids = None, 
    #       slice_dex = 0, regime = 'per trajectory', 
    #       base_class = None, valid_regimes = ['per trajectory']):
        #if base_class is None:
        #   base_class = lfu.interface_template_class(
        #           object, 'slice from trajectory')

        if not 'base_class' in kwargs.keys():
            kwargs['base_class'] = lfu.interface_template_class(
                                object, 'slice from trajectory')

        if not 'label' in kwargs.keys():
            kwargs['label'] = 'slices'

        if not 'valid_regimes' in kwargs.keys():
            kwargs['valid_regimes'] = ['per trajectory']

        if not 'regime' in kwargs.keys():
            kwargs['regime'] = 'per trajectory'

        self._default('dater_ids', None, **kwargs)
        self._default('slice_dex', -1, **kwargs)
    #   post_process.__init__(self, label = label, regime = regime, 
    #       base_class = base_class, valid_regimes = valid_regimes, 
    #       capture_targets = capture_targets)
        post_process.__init__(self, *args, **kwargs)

    def to_string(self):
        #slices : slice from trajectory : 1 : all : -1
        inps = self._string_inputs()
        phrase = 'all'
        slice_dex = str(self.slice_dex)
        return '\t' + ' : '.join([self.label, 'slice from trajectory', 
                                    inps, phrase, slice_dex])

    def provide_axes_manager_input(self):
        self.use_line_plot = True
        self.use_color_plot = False
        self.use_voxel_plot = False
        self.use_bar_plot = False

    def postproc(self, *args, **kwargs):
        kwargs['method'] = self.slice_from_trajectory
        post_process.postproc(self, *args, **kwargs)

    def slice_from_trajectory(self, *args, **kwargs):
        trajectory = args[0]
        #data = lgeo.scalars_from_labels([label 
        data = ldc.scalars_from_labels([label 
                for label in self.dater_ids])
        for dater in data:
            try:
                sub_traj = lfu.grab_mobj_by_name(
                        dater.label, trajectory)

            except ValueError: continue
            if self.slice_dex.count(':') == 0:
                dater.scalars = [sub_traj.scalars[int(self.slice_dex)]]

            else:
                col_dex = self.slice_dex.index(':')
                slice_1 = int(self.slice_dex[:col_dex])
                slice_2 = int(self.slice_dex[col_dex:])
                dater.scalars = sub_traj.scalars[slice_1:slice_2]

        return data

    def _target_settables(self, *args, **kwargs):
        self.valid_regimes = ['per trajectory']

        self.valid_inputs = self._valid_inputs(*args, **kwargs)
        capture_targetable = self._targetables(*args, **kwargs)
        if self.dater_ids is None:
            self.dater_ids = []

        #is this why output plans require one more update all the time it seems?
        self.capture_targets = self.dater_ids       

        self.output.targeted = [targ for targ in self.output.targeted #is this necessary?
                                    if targ in self.capture_targets]

        post_process._target_settables(self, *args, **kwargs)

    def set_settables(self, *args, **kwargs):
        self.handle_widget_inheritance(*args, from_sub = False)
        capture_targetable = self._targetables(*args, **kwargs)
        #use a spin widget to select a location in the domain
        #   or a text box to support true slicing
        self.widg_templates.append(
            lgm.interface_template_gui(
                keys = [['slice_dex']], 
                instances = [[self]], 
                #rewidget = [[True]], 
                widgets = ['text'], 
                box_labels = ['Slice Index'], 
                initials = [[self.slice_dex]]))
        self.widg_templates.append(
            lgm.interface_template_gui(
                keys = [['dater_ids']], 
                instances = [[self]], 
                #rewidget = [[True]], 
                widgets = ['check_set'], 
                box_labels = ['To Slice'], 
                append_instead = [True], 
                provide_master = [True], 
                labels = [capture_targetable]))
        super(post_process_slice_from_trajectory, 
            self).set_settables(*args, from_sub = True)
