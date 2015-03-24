import modular_core.fundamental as lfu
import modular_core.criteria.abstract as cab

import pdb,sys,os,traceback,time,types

if __name__ == 'modular_core.criteria.endcaptureplan':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'endcaptureplan of modular_core'

###############################################################################
### endcapture_plan manages capture criteria, end criteria, and plot targets
###############################################################################

class endcapture_plan(lfu.plan):

    _always_targetable_ = ['time']

    def __init__(self,*args,**kwargs):
        self._default('name','end/capture plan',**kwargs)

        self.end_criteria = []
        self.selected_end_crit = None
        self.selected_end_crit_label = None
        self.capture_criteria = []
        self.selected_capt_crit = None
        self.selected_capt_crit_label = None
        self.plot_targets = []

        lfu.plan.__init__(self,*args,**kwargs)

    def _captures_per_trajectory(self):
        tcnt = len(self.plot_targets)
        ccnt = self._capture_count()
        cpt = tcnt * ccnt
        return cpt

    def _capture_count(self):
        ccnt = int(self._max_time()/self._capture_increment())+1
        return ccnt

    def _capture_increment(self):
        cap = self.capture_criteria[0]
        return float(cap.increment)

    def _max_time(self):
        end = self.end_criteria[0]
        return float(end.max_time)

    def _sanitize(self,*args,**kwargs):
        if not ('from_sub' in kwargs.keys() and kwargs['from_sub']):
            self.widg_templates_end_criteria = []
            self.widg_templates_capture_criteria = []
            self.widg_templates_plot_targets = []
        lfu.plan._sanitize(self,*args,**kwargs)

    def _reset_criteria_lists(self):
        del self.end_criteria[:]
        del self.capture_criteria[:]
        del self.children[:]
        self._rewidget(True)

    def _add_end_criteria(self,crit = None):
        if crit is None:crit = cab.criterion(parent = self)
        else:crit.parent = self
        if crit is None:return
        self.end_criteria.append(crit)
        self.children.append(crit)
        crit._rewidget(True)
        self._rewidget(True)

    def _add_capture_criteria(self,crit = None):
        if crit is None:crit = cab.criterion(parent = self)
        else:crit.parent = self
        if crit is None:return
        self.capture_criteria.append(crit)
        self.children.append(crit)
        crit._rewidget(True)
        self._rewidget(True)

    def clear_criteria(self):
        def clear(crits):
            for crit in crits: crits.remove(crit)
        clear(self.end_criteria)
        clear(self.capture_criteria)
        self.children = []
        self._rewidget(True)

    def remove_end_criteria(self, crit = None):
        if crit: select = crit
        else: select = self.get_selected_criteria('end')
        if select:
            self.end_criteria.remove(select)
            self.children.remove(select)
        self._rewidget(True)

    def remove_capture_criteria(self, crit = None):
        if crit: select = crit
        else: select = self.get_selected_criteria('capture')
        if select:
            self.capture_criteria.remove(select)
            self.children.remove(select)
        self._rewidget(True)

    def get_selected_criteria(self, type_):
        if type_ is 'end': key = 'end_crit_selector'
        elif type_ is 'capture': key = 'capt_crit_selector'
        else: key = 'nonsense'
        if not hasattr(self, key):
            print 'no selector'; return

        try:
            select = self.__dict__[type_ + '_criteria'][
                self.__dict__[key][0].children()[1].currentIndex() - 1]
            return select

        except IndexError:
            print 'no criterion selected'; return

    def set_selected_criteria(self, dex):
        select = self.capture_criteria[dex]
        self.selected_capt_crit = select
        self._rewidget(True)

    def verify_plot_targets(self, targs):
        targets = self.parent.run_params['plot_targets']
        targets = [targ for targ in targets if targ in targs]
        self.parent.run_params['plot_targets'] = targets
        self.parent.run_params['output_plans']['Simulation']._rewidget(True)

    def _widget(self,*args,**kwargs):
        window = args[0]
        ensem = self.parent
        self._sanitize(*args,**kwargs)

        const_targs = self._always_targetable_
        targs = ensem.run_params['plot_targets']
        self.plot_targets = ensem.run_params['plot_targets']
        all_targets = lfu.uniqfy(const_targs + targs)
        plot_target_labels = all_targets
        self.verify_plot_targets(plot_target_labels)
        try: self.selected_end_crit_label = self.selected_end_crit.label
        except AttributeError: self.selected_end_crit_label = None
        try: self.selected_capt_crit_label = self.selected_capt_crit.label
        except AttributeError: self.selected_capt_crit_label = None
        self.widg_templates_end_criteria.append(
            lgm.interface_template_gui(
                layout = 'grid', 
                widg_positions = [(0, 0), (0, 2), (1, 2)], 
                widg_spans = [(3, 2), None, None], 
                grid_spacing = 10, 
                widgets = ['mobj_catalog', 'button_set'], 
                verbosities = [1,1], 
                instances = [[self.end_criteria, self], None], 
                keys = [[None, 'selected_end_crit_label'], None], 
                handles = [(self, 'end_crit_selector'), None], 
                labels = [None, ['Add End Criterion', 
                            'Remove End Criterion']], 
                initials = [[self.selected_end_crit_label], None], 
                bindings = [None, [lgb.create_reset_widgets_wrapper(
                                    window, self._add_end_criteria), 
                    lgb.create_reset_widgets_wrapper(window, 
                        self.remove_end_criteria)]]))
        self.widg_templates_capture_criteria.append(
            lgm.interface_template_gui(
                layout = 'grid', 
                widg_positions = [(0, 0), (0, 2), (1, 2)], 
                widg_spans = [(3, 2), None, None], 
                grid_spacing = 10, 
                widgets = ['mobj_catalog', 'button_set'], 
                verbosities = [1,1], 
                instances = [[self.capture_criteria, self], None], 
                keys = [[None, 'selected_capt_crit_label'], None], 
                handles = [(self, 'capt_crit_selector'), None], 
                labels = [None, ['Add Capture Criterion', 
                            'Remove Capture Criterion']], 
                initials = [[self.selected_capt_crit_label], None], 
                bindings = [None, [lgb.create_reset_widgets_wrapper(
                                window, self._add_capture_criteria), 
                    lgb.create_reset_widgets_wrapper(window, 
                        self.remove_capture_criteria)]]))
        targets_template =\
            [lgm.interface_template_gui(
                widgets = ['check_set'], 
                verbosities = [1], 
                append_instead = [True], 
                provide_master = [True], 
                instances = [[self.parent.run_params]], 
                keys = [['plot_targets']], 
                labels = [plot_target_labels])]
        self.widg_templates_plot_targets.append(
            lgm.interface_template_gui(
                widgets = ['panel'], 
                box_labels = ['Capture Targets'], 
                scrollable = [True], 
                templates = [targets_template]))
        lfu.plan._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################






'''#
class sim_system_external(object):

    # finalize_data_nontrivial will perform necessary handling for
    #  non 1-1 listed data (surfaces for example)
    # it will return a tuple of data objects - general output case
    # args = [dataobject1, ..., dataobjectN, [targetname1, ..., targetnameN]]
    # dataobject1 should be simplest data case occurring:
    #  numpy array of dimension 2, of shape (numtargets, numcaptures)
    # dataobject2 should be no simpler than the second data case:
    #  numpy array of dimension 3, of shape (x,x,x) where x is arbitrary
    # support for other data objects will be added as necessary
    def finalize_data_nontrivial(self, *args, **kwargs):

        def data_case_1(dataobj, targs, **kwargs):
            tcnt = dataobj.shape[0]
            subtargs = targs[:tcnt]
            kwargs['ignore_targets'] = targs[tcnt:]
            return self.finalize_data(dataobj, subtargs, **kwargs)

        targs = args[-1]
        final = []
        for dataobj in args[:-1]:
            if dim == 2:final.append(data_case_1(dataobj,targs))
            elif dim == 3:final.append(dataobj)
            elif dim == 4:final.append(dataobj)
            elif dim == 5:final.append(dataobj)

        return tuple(final)
'''#









