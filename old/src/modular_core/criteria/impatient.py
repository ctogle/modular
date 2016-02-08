
class criterion_impatient(cab.criterion_abstract):

    def __init__(self, *args, **kwargs):
        if not 'label' in kwargs.keys():
            kwargs['label'] = 'timeout criterion'

        if not 'base_class' in kwargs.keys():
            kwargs['base_class'] = lfu.interface_template_class(
                            criterion_impatient, 'timeout limit')

        self.impose_default('max_timeouts', 100, **kwargs)
        self.impose_default('max_last_best', 100, **kwargs)
        cab.criterion_abstract.__init__(self, *args, **kwargs)

    def to_string(self):
        return '\ttimeout limit : ' + str(self.max_timeouts)

    def initialize(self, *args, **kwargs):
        self.max_timeouts = float(self.max_timeouts)

    def verify_pass(self, *args):
        obj = args[0]
        try:
            #print 'TIMEOUTS', obj.timeouts, self.max_timeouts
            too_many_timeouts = obj.timeouts >= self.max_timeouts
            no_longer_better = obj.last_best >= self.max_last_best
            if too_many_timeouts or no_longer_better: return True

        except AttributeError:
            print   'timeout criterion applied \
                    \n to object without .timeouts'
            return True

        return False

    def set_uninheritable_settables(self, *args, **kwargs):
        self.visible_attributes = ['label', 'base_class', 
                            'bRelevant', 'max_timeouts']

    def _widget(self, *args, **kwargs):
        self.handle_widget_inheritance(*args, from_sub = False)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin'], 
                doubles = [[False]], 
                initials = [[int(self.max_timeouts)]], 
                minimum_values = [[0]], 
                maximum_values = [[sys.maxint]], 
                instances = [[self]], 
                keys = [['max_timeouts']], 
                box_labels = ['Timeout Limit']))
        criterion._widget(self, *args, from_sub = True)
