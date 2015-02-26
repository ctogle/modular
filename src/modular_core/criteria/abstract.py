import modular_core.fundamental as lfu

import pdb,types,sys

if __name__ == 'modular_core.criteria.abstract':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'criterion abstract of modular_core'

criterion_types = {}

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

###############################################################################
### utility functions
###############################################################################

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
    crit = criterion_types[variety][0](**cargs)
    return crit

def parse_criterion_line(line,ensem,parser,procs,routs,targs):
    print 'parse criterion line:\n\t"',line,'"\n'
    crit_types = criterion_types.keys()
    spl = lfu.msplit(line)
    variety = spl[0]
    cargs = criterion_types[variety][1](spl,ensem,procs,routs)
    crit = criterion(**cargs)
    if parser == 'end_criteria':
        ensem.simulation_plan._add_end_criteria(crit = crit)
    elif parser == 'capture_criteria':
        ensem.simulation_plan._add_capture_criteria(crit = crit)

###############################################################################
###############################################################################










