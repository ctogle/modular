import modular_core.libfundamental as lfu

import pdb,types,sys

if __name__ == 'modular_core.criteria.libcriterion':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'libcriterion of modular_core'

###############################################################################
### a criterion is a glorified function which tests some condition
###############################################################################

class criterion_abstract(lfu.run_parameter):

    #ABSTRACT
    def __init__(self,*args,**kwargs):
        self._default('use',True,**kwargs)
        lfu.run_parameter.__init__(self,*args,**kwargs)

    def __call__(self,*args,**kwargs):
        return not self.use or self._verify_pass(*args,**kwargs)

    def _verify_pass(self,*args,**kwargs):
        print 'abstract criterion always passes'
        return True

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                panel_position = (2, 0), 
                widgets = ['check_set'], 
                append_instead = [False],
                instances = [[self]], 
                keys = [['use']], 
                labels = [['Use This Criterion']]))
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['text'], 
                keys = [['name']], 
                instances = [[self]], 
                initials = [[self.name]], 
                box_labels = ['Criterion Name']))
        lfu.run_parameter._widget(self,*args,from_sub = True)

class criterion_iteration(criterion_abstract):

    def __init__(self,*args,**kwargs):
        self._default('name','iteration criterion',**kwargs)
        self._default('max_iterations',1000,**kwargs)
        criterion_abstract.__init__(self,*args,**kwargs)

    def _sim_string(self):
        return 'iteration>=' + str(self.max_iterations)

    def _string(self):
        return '\titeration limit : ' + str(self.max_iterations)

    def _initialize(self,*args,**kwargs):
        self.max_iterations = float(self.max_iterations)

    def _verify_pass(self,*args):
        mobji = args[0].iteration
        verif = mobji >= self.max_iterations
        return verif

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,from_sub = False)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin'], 
                doubles = [[False]], 
                initials = [[int(self.max_iterations)]], 
                minimum_values = [[0]], 
                maximum_values = [[sys.maxint]], 
                instances = [[self]], 
                keys = [['max_iterations']], 
                box_labels = ['Iteration Limit']))
        criterion_abstract._widget(self,*args,from_sub = True)

class criterion_sim_time(criterion_abstract):

    def __init__(self,*args,**kwargs):
        self._default('name','simulation time criterion',**kwargs)
        self._default('max_time',100.0,**kwargs)
        criterion_abstract.__init__(self,*args,**kwargs)

    def _sim_string(self):
        return 'time>=' + str(self.max_time)

    def _string(self):
        return '\ttime limit : ' + str(self.max_time)

    def _initialize(self,*args,**kwargs):
        self.max_time = float(self.max_time)

    def _verify_pass(self,*args):
        mobjt = args[0].time[-1]
        return self.max_time <= mobjt

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,from_sub = False)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin'], 
                doubles = [[True]], 
                initials = [[float(self.max_time)]], 
                minimum_values = [[0.0]], 
                maximum_values = [[sys.float_info.max]], 
                instances = [[self]], 
                keys = [['max_time']], 
                box_labels = ['Max Simulation Time']))
        criterion_abstract._widget(self,*args,from_sub = True)

class criterion_increment(criterion_abstract):

    def __init__(self,*args,**kwargs):
        self._default('name','increment criterion',**kwargs)
        self._default('increment',10.0,**kwargs)
        self._default('target','time',**kwargs)
        self._default('targets',['iteration','time'],**kwargs)
        criterion_abstract.__init__(self,*args,**kwargs)

    def _sim_string(self):
        return 'increment:' + self.target + ':' + str(self.increment)

    def _string(self):
        strr = '\t' + self.target + ' increment : ' + str(self.increment)
        return strr

    def _initialize(self,*args,**kwargs):
        self.increment = float(self.increment)
        if self.target == 'time':self._last_value = self._last_value_list
        if self.target == 'iteration':self._last_value = self._last_value_value
        self.targetdex = [dater.label == self.target 
                for dater in system.data].index(True)

    def _last_value_value(self,system):
        last_value = system.__dict__[self.key]
        return last_value

    def _last_value_list(self,system):
        last_value = system.__dict__[self.key][-1]
        return last_value

    def _verify_pass(self,*args):
        mobj = args[0]
        last_value = self.find_last_value(mobj)
        last_captured_value = mobj.data[self.targetdex].scalars[-1]
        return abs(last_value - last_captured_value) >= self.increment

    def _widget(self,*args,**kwargs):
        window = args[0]
        self._sanitize(*args,from_sub = False)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin'], 
                doubles = [[True]], 
                initials = [[float(self.increment)]], 
                minimum_values = [[0.0]], 
                maximum_values = [[sys.float_info.max]], 
                instances = [[self]], 
                keys = [['increment']], 
                box_labels = ['Increment']))
        self.widg_templates.append(
            lgm.interface_template_gui(
                panel_position = (1, 1), 
                widgets = ['radio'], 
                labels = [self.targets], 
                initials = [[self.target]], 
                instances = [[self]], 
                keys = [['target']], 
                box_labels = ['Target to Check']))
        criterion_abstract._widget(self,*args,from_sub = True)

criterion_types = {                                                    
    'iteration limit':criterion_iteration, 
    'time limit':criterion_sim_time, 
    'increment':criterion_increment,
        }

# prompt user for criterion type if needed and create
def criterion(variety = None,**cargs):
    opts = criterion_types.keys()
    if variety is None:
        if lfu.using_gui:
            variety = lgd.create_dialog(
                title = 'Choose Criterion Type',
                options = opts,variety = 'radioinput')
        else:
            crequest = 'enter a criterion type:\n\t'
            for op in opts:crequest += op + '\n\t'
            crequest += '\n'
            variety = raw_input(crequest)
    if not variety in opts:
        print 'unrecognized criterion type:',variety
        return
    crit = criterion_types[variety](**cargs)
    return crit

def parse_criterion_line(line,ensem,parser,procs,routs,targs):
    print 'parse criterion line:\n\t"',line,'"\n'
    crit_types = criterion_types.keys()
    spl = [l.strip() for l in line.split(':')]
    scnt = len(spl)
    variety = spl[0]
    cargs = {'variety':variety}
    if scnt > 1:
        if variety == 'time limit':cargs['max_time'] = spl[1]
        elif variety == 'iteration limit':cargs['max_iterations'] = spl[1]
        elif variety == 'increment':
            cargs['increment'] = spl[1]
            if scnt > 2: cargs['target'] = spl[2]

        '''#
        elif crit_type._tag == 'capture limit':
            crit.max_captures = split[1]
        elif crit_type._tag == 'species count':
            crit.spec_count_target = split[1]
            if len(split) > 2: crit.key = split[2]
        '''#

    crit = criterion(**cargs)
    if parser == 'end_criteria':
        ensem.simulation_plan._add_end_criteria(crit = crit)
    elif parser == 'capture_criteria':
        ensem.simulation_plan._add_capture_criteria(crit = crit)

###############################################################################







###############################################################################
###############################################################################
###############################################################################

class criterion_capture_count(criterion_abstract):

    def __init__(self, parent = None, max_captures = 100.0, 
            label = 'capture limit criterion', visible_attributes =\
            ['label', 'bRelevant', 'max_captures']):
        criterion_abstract.__init__(self,parent = parent,label = label)
        self.max_captures = max_captures

    def to_string(self):
        return '\tcapture limit : ' + str(self.max_captures)

    def initialize(self, *args, **kwargs):
        self.max_captures = int(self.max_captures)

    def verify_pass(self, system):
        try:
            if len(system.data[0].scalars) >= self.max_captures:
                print 'criterion: passed capture count limit'
                return True

            return False

        except IndexError:
            print 'capture count criterion with no capture targets!'
            return True

    def set_uninheritable_settables(self, *args, **kwargs):
        self.visible_attributes = ['label','bRelevant','max_captures']
        #this has to be overridden even if this class lacks
        # its own uninheritable settables

    def set_settables(self, *args, **kwargs):
        self.handle_widget_inheritance(*args, from_sub = False)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin'], 
                doubles = [[False]], 
                initials = [[int(self.max_captures)]], 
                minimum_values = [[0]], 
                maximum_values = [[sys.maxint]], 
                instances = [[self]], 
                keys = [['max_captures']], 
                box_labels = ['Capture Count Limit']))
        criterion_abstract._widget(self,*args,from_sub = True)


class trajectory_criterion(criterion_abstract):

    #ABSTRACT
    def __init__(self, *args, **kwargs):
        if not 'label' in kwargs.keys():
            kwargs['label'] = 'trajectory criterion'
        criterion_abstract.__init__(self, *args, **kwargs)

    def _verify_pass(self, trajectory):
        print 'abstract trajectory criterion base class always passes'
        return True

    #def set_settables(self, *args, **kwargs):
    #   self.handle_widget_inheritance(*args, from_sub = False)
        #self.widg_templates.append(
        #   lgm.interface_template_gui())
    #   criterion.set_settables(self, *args, from_sub = True)

class trajectory_criterion_ceiling(trajectory_criterion):

    def __init__(self, *args, **kwargs):
        self.impose_default('ceiling', 2500, **kwargs)
        self.impose_default('target', None, **kwargs)
        trajectory_criterion.__init__(self, *args, **kwargs)
        self._children_ = []

    def _verify_pass(self, trajectory):
        
        pdb.set_trace()
        return False

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,from_sub = False)
        capture_targetable = kwargs['capture_targetable']
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['radio'], 
                labels = [capture_targetable], 
                initials = [[self.target]], 
                instances = [[self]], 
                keys = [['target']], 
                box_labels = ['Target']))
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin'], 
                doubles = [[False]], 
                initials = [[int(self.ceiling)]], 
                minimum_values = [[0]], 
                maximum_values = [[sys.maxint]], 
                instances = [[self]], 
                keys = [['ceiling']], 
                box_labels = ['Ceiling Limit']))
        trajectory_criterion._widget(self,*args,from_sub = True)




