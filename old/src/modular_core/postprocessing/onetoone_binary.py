
class post_process_1_to_1_binary_operation(post_process):

    #take a data set - choose two data mobjects and an operator
    #   make a new data mobject containing the result
    def __init__(self,*args,**kwargs):
        self._default('name','1 - 1 binary operation',**kwargs)
        self._default('valid_regimes',['per trajectory'],**kwargs)
        self._default('regime','per trajectory',**kwargs)

        self._default('use_gpu',False,**kwargs)
        self._default('input_1',None,**kwargs)
        self._default('input_2',None,**kwargs)
        self._default('domain',None,**kwargs)
        self._default('operation','+',**kwargs)
        self._default('operations',['+','-','*','/'],**kwargs)
        post_process.__init__(self,*args,**kwargs)

    def to_string(self):
        #label : one to one binary operation : 0
        inps = self._string_inputs()
        return '\t' + ' : '.join([self.label, 
            'one to one binary operation', inps])

    def grab_daters(self, *args, **kwargs):
        trajectory = args[0]
        dater_1 = lfu.grab_mobj_by_name(self.input_1, trajectory)
        dater_2 = lfu.grab_mobj_by_name(self.input_2, trajectory)
        #data = lgeo.scalars_from_labels(['_'.join(
        data = ldc.scalars_from_labels(['_'.join(
            [self.input_1, self.input_2]), self.domain])
        data[1].scalars = lfu.grab_mobj_by_name(
                        self.domain, trajectory).scalars
        return dater_1.scalars, dater_2.scalars, data

    def gpu_operation(self, *args, **kwargs):
        dater_1, dater_2, data = self.grab_daters(*args, **kwargs)
        data[0].scalars = self.mp_plan_ref.gpu_1to1_operation(
                                            dater_1, dater_2)
        return data

    def addition(self, *args, **kwargs):
        dater_1, dater_2, data = self.grab_daters(*args, **kwargs)
        data[0].scalars = [sum(pair) for pair in zip(dater_1, dater_2)]
        return data

    def subtraction(self, *args, **kwargs):
        dater_1, dater_2, data = self.grab_daters(*args, **kwargs)
        data[0].scalars = [pair[0] - pair[1] for 
                pair in zip(dater_1, dater_2)]
        return data

    def multiplication(self, *args, **kwargs):
        dater_1, dater_2, data = self.grab_daters(*args, **kwargs)
        data[0].scalars = [pair[0]*pair[1] for pair 
                        in zip(dater_1, dater_2)]
        return data

    def division(self, *args, **kwargs):
        dater_1, dater_2, data = self.grab_daters(*args, **kwargs)
        data[0].scalars =\
            [pair[0]/pair[1] if not pair[1] == 0 else None 
                        for pair in zip(dater_1, dater_2)]
        if None in data[0].scalars:
            print 'avoided zero division...'
            pdb.set_trace()

        return data

    def postproc(self, *args, **kwargs):
        if lgpu.gpu_support and self.use_gpu:
            self.mp_plan_ref.gpu_worker.initialize()
            method = self.gpu_operation
            if self.operation == '+':
                self.mp_plan_ref.gpu_worker.verify_cl_extension(
                                gpu_cl_extension = 'addition')

            if self.operation == '-':
                self.mp_plan_ref.gpu_worker.verify_cl_extension(
                                gpu_cl_extension = 'subtraction')

            if self.operation == '*':
                self.mp_plan_ref.gpu_worker.verify_cl_extension(
                                gpu_cl_extension = 'multiplication')

            if self.operation == '/':
                self.mp_plan_ref.gpu_worker.verify_cl_extension(
                                gpu_cl_extension = 'division')

        else:
            if self.operation == '+':
                method = self.addition

            if self.operation == '-':
                method = self.subtraction

            if self.operation == '*':
                method = self.multiplication

            if self.operation == '/':
                method = self.division

        kwargs['method'] = method
        post_process.postproc(self, *args, **kwargs)

    #this is a stupid hack!
    #def provide_axes_manager_input(self):
    #   post_process.provide_axes_manager_input(self)
    #   self.x_title = 'time'

    def _target_settables(self, *args, **kwargs):
        self.valid_regimes = ['per trajectory']
        self.valid_inputs = self._valid_inputs(*args, **kwargs)
        capture_targetable = self._targetables(*args, **kwargs)
        if self.input_1 is None and capture_targetable:
                self.input_1 = capture_targetable[0]

        if self.input_2 is None and capture_targetable:
                self.input_2 = capture_targetable[0]

        if self.domain is None and capture_targetable:
                self.domain = capture_targetable[0]

        self.capture_targets = ['_'.join(
            [self.input_1, self.input_2]), self.domain]
        post_process._target_settables(self, *args, **kwargs)

    def set_settables(self, *args, **kwargs):
        self.handle_widget_inheritance(*args, from_sub = False)
        capture_targetable = self._targetables(*args, **kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                panel_position = (1, 3), 
                keys = [['domain']], 
                instances = [[self]], 
                widgets = ['radio'], 
                box_labels = ['As a Function of'], 
                initials = [[self.domain]], 
                labels = [capture_targetable]))
        self.widg_templates.append(
            lgm.interface_template_gui(
                keys = [['input_2']], 
                instances = [[self]], 
                widgets = ['radio'], 
                box_labels = ['Input 2'], 
                initials = [[self.input_2]], 
                labels = [capture_targetable]))
        self.widg_templates.append(
            lgm.interface_template_gui(
                keys = [['operation']], 
                instances = [[self]], 
                widgets = ['radio'], 
                box_labels = ['Operation'], 
                initials = [[self.operation]], 
                labels = [self.operations]))
        self.widg_templates.append(
            lgm.interface_template_gui(
                keys = [['input_1']], 
                instances = [[self]], 
                widgets = ['radio'], 
                box_labels = ['Input 1'], 
                initials = [[self.input_1]], 
                labels = [capture_targetable]))
        super(post_process_1_to_1_binary_operation, 
            self).set_settables(*args, from_sub = True)
