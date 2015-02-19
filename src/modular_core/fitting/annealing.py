
class fit_routine_simulated_annealing(fit_routine):

    def __init__(self, *args, **kwargs):
        if not 'label' in kwargs.keys():
            kwargs['label'] = 'simulated annealing routine'

        if not 'base_class' in kwargs.keys():
            kwargs['base_class'] = lfu.interface_template_class(
                                object, 'simulated annealing')

        self.impose_default('cooling_curve', None, **kwargs)
        self.impose_default('max_temperature', 1000, **kwargs)
        self.impose_default('temperature', None, **kwargs)
        fit_routine.__init__(self, *args, **kwargs)

    def initialize(self, *args, **kwargs):
        if not self.cooling_curve:
            self.final_iteration =\
                self.fitted_criteria[0].max_iterations
            lam = -1.0 * np.log(self.max_temperature)/\
                                self.final_iteration
            cooling_domain = np.array(range(self.final_iteration))
            cooling_codomain = self.max_temperature*np.exp(
                                        lam*cooling_domain)
            self.cooling_curve = ldc.scalars(
                label = 'cooling curve', scalars = cooling_codomain)

        fit_routine.initialize(self, *args, **kwargs)
        self.data.extend(ldc.scalars_from_labels(
                        ['annealing temperature']))
        self.temperature = self.cooling_curve.scalars[self.iteration]
        self.parameter_space.initial_factor = self.temperature

    def iterate_genetic(self, *args, **kwargs):
        self.temperature = self.cooling_curve.scalars[self.iteration]
        rev_iter =\
            len(self.cooling_curve.scalars) - 1  - self.iteration
        self.proginy_count =\
            int(self.cooling_curve.scalars[rev_iter]) +\
                                        self.worker_count
        self.p_sp_step_factor = self.temperature
        fit_routine.iterate_genetic(self, *args, **kwargs)

    def iterate(self, *args, **kwargs):
        self.temperature = self.cooling_curve.scalars[self.iteration]
        rev_iter =\
            len(self.cooling_curve.scalars) - 1  - self.iteration
        self.proginy_count =\
            int(self.cooling_curve.scalars[rev_iter]) +\
                                        self.worker_count
        self.p_sp_step_factor = self.temperature
        fit_routine.iterate(self, *args, **kwargs)

    '''#
    def move_in_parameter_space(self, *args, **kwargs):
        self.temperature = self.cooling_curve.scalars[self.iteration]
        self.p_sp_step_factor = self.temperature
        initial_factor = self.parameter_space.initial_factor
        dims = self.parameter_space.dimensions
        self.many_steps = int(max([1, abs(random.gauss(1, 
            dims))*(self.p_sp_step_factor/initial_factor)]))
        fit_routine.move_in_parameter_space(self, *args, **kwargs)
    '''#

    def capture_plot_data(self, *args, **kwargs):
        fit_routine.capture_plot_data(self, *args, **kwargs)
        self.data[-1].scalars.append(self.temperature)

    def _widget(self, *args, **kwargs):
        self.capture_targets =\
                ['fitting iteration'] +\
                [met.label + ' measurement' 
                    for met in self.metrics] +\
                    ['annealing temperature']
        self.handle_widget_inheritance(*args, from_sub = False)
        fit_routine._widget(self, *args, from_sub = True)
