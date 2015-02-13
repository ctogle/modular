

class post_process_period_finding(post_process):

    #the **kwargs keyword dictionary is modified and passed to the 
    # superclass where elements like kwargs['base_class'] are used
    def __init__(self, *args, **kwargs):
        if not 'base_class' in kwargs.keys():
            #class is used for recasting processes as other process instances
            # second argument is a string to look up the appropriate class
            #subsequently also appears in valid_postproc_base_classes
            kwargs['base_class'] = lfu.interface_template_class(
                                        object, 'period finding')

        #provide a default label - is made unique by superclasses
        if not 'label' in kwargs.keys():
            kwargs['label'] = 'period finder'

        #this process can be run on all trajectories
        # if the parameter space is not being mapped
        #or the process can be run all each p-space location
        # this is equivalent to the first case but run once
        # on each p-space location's collection of trajectories
        if not 'valid_regimes' in kwargs.keys():
            kwargs['valid_regimes'] = ['per trajectory']

        #by default it will attempt to run on all trajectories
        if not 'regime' in kwargs.keys():
            kwargs['regime'] = 'per trajectory'

        self.window = 5
        self.period_of = None

        #always call superclass's init within modular platform
        post_process.__init__(self, *args, **kwargs)

    def to_string(self):
        #label : period finding : 0
        inps = self._string_inputs()
        return '\t' + ' : '.join([self.label, 'period finding', inps])

    def provide_axes_manager_input(self):
        self.use_line_plot = True
        self.use_color_plot = False
        self.use_voxel_plot = False
        self.use_bar_plot = False

    #the superclass actually runs the method, but here the subclass
    # points to the appropriate bound method to use
    def postproc(self, *args, **kwargs):
        if not 'fixed_time' in self.target_list:
            print 'ensemble is captureing fixed time' +\
                    '\n\tperiod-finding will be ignored'

        kwargs['method'] = self.find_period
        post_process.postproc(self, *args, **kwargs)

    #this is where the actual algorithm for period finding goes
    # args[0] will be the data set
    # at this function, the data set will always appear to be a list
    # of lists of libs.modular_core.libgeometry.scalars objects
    #each trajectory results in a list of scalars objects
    # these lists are put in a list which is what appears as args[0]
    #use pdb.set_trace() to investigate if this isn't clear
    def find_period(self, *args, **kwargs):
        time_dex = [dater.label == 'fixed_time' for 
                        dater in args[0]].index(True)
        targ_dex = [dater.label == self.period_of for 
                        dater in args[0]].index(True)
        time = args[0][time_dex]
        targ = args[0][targ_dex]
        periods, amplitudes = self.find_period_in_window(
                            time.scalars, targ.scalars)
        #data = lgeo.scalars_from_labels(self.target_list)
        data = ldc.scalars_from_labels(self.target_list)
        data[1].scalars, data[2].scalars = self.fill_in(
                    periods, amplitudes, time.scalars)
        data[0].scalars = copy(time.scalars[:len(data[1].scalars)])
        return data

    #fill in values for codomain so that it is 1 - 1 with domain
    def fill_in(self, codomain, follow, domain):
        new_codomain = []
        new_follow = []
        dom_dex = 0
        summed_periods = 0
        for value, fellow in zip(codomain, follow):
            summed_periods += value
            #print 'summed_periods', summed_periods
            while summed_periods > domain[dom_dex]:
                new_codomain.append(value)
                new_follow.append(fellow)
                dom_dex += 1

        return new_codomain, new_follow

    def find_period_in_window(self, t, x):
        w = int(self.window)
        y = morph.grey_dilation(x, size = w)
        t = t[w-1:-w]
        x = x[w-1:-w]
        y = y[w-1:-w]
        inds = np.argwhere(x==y)
        NN = inds.size
        period = np.zeros(NN - 1)
        #period = np.zeros(NN)
        amp = np.zeros(NN - 1)
        #amp = np.zeros(NN)
        for ii in range(NN - 1):
        #for ii in range(1, NN):
            xs = x[inds[ii]:inds[ii + 1]]
            #xs = x[inds[ii] - 1:inds[ii]]
            amp[ii] = 0.5 * (xs[0] + xs[-1] - 2 * np.min(xs))
            period[ii] = t[inds[ii + 1]] - t[inds[ii]]
            #period[ii] = t[inds[ii]] - t[inds[ii - 1]]
            #print np.min(xs)

        return period, amp

    def _target_settables(self, *args, **kwargs):
        self.valid_regimes = ['per trajectory']
        self.valid_inputs = self._valid_inputs(*args, **kwargs)
        capture_targetable = self.g_targetables(*args, **kwargs)
        if self.period_of is None and capture_targetable:
            self.period_of = capture_targetable[0]

        self.target_list = ['fixed_time', 
                self.period_of + ' period', 
                self.period_of + ' amplitude']
        self.capture_targets = self.target_list
        post_process._target_settables(self, *args, **kwargs)

    #this function specifies the gui for this object
    # it's a bit difficult to describe when it's called, but anything
    # which is kept up-to-date prior to running is likely kept that way
    # by this function
    #this function is only called to recalculate the widget templates
    # it is NOT called simply to make them, unless necessary
    def set_settables(self, *args, **kwargs):
        self.handle_widget_inheritance(*args, from_sub = False)
        capture_targetable = self._targetables(*args, **kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                keys = [['window']], 
                instances = [[self]], 
                #rewidget = [[True]], 
                widgets = ['text'], 
                box_labels = ['Window'], 
                initials = [[self.window]]))
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['radio'], 
                labels = [capture_targetable], 
                initials = [[self.period_of]], 
                instances = [[self]], 
                keys = [['period_of']], 
                box_labels = ['Period/Amplitude of']))
        super(post_process_period_finding, self).set_settables(
                                        *args, from_sub = True)
