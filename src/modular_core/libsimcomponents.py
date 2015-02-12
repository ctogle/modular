import modular_core as mc
import modular_core.libfundamental as lfu
import modular_core.libmodcomponents as lmc
import modular_core.libgeometry as lgeo
import modular_core.libmultiprocess as lmp
import modular_core.libsettings as lset

try: import modular_core.libworkerthreads as lwt
except ImportError:
    print 'multithreaded ensembles are disabled without QtCore...'
    lwt = None

import modular_core.io.liboutput as lo
import modular_core.io.libfiler as lf
import modular_core.criteria.libcriterion as lc
import modular_core.fitting.libfitroutine as lfr
import modular_core.data.libdatacontrol as ldc
import modular_core.postprocessing.libpostprocess as lpp

import pstats, cProfile, StringIO

from copy import deepcopy as copy
import os
import sys
import traceback
import types
import time
from math import sqrt as sqrt
import numpy as np
import importlib as imp

import pdb

if __name__ == 'modular_core.libsimcomponents':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'libsimcomponents of modular_core'

class simulation_plan(lfu.plan):

    _always_targetable_ = ['iteration','time']

    def __init__(self,*args,**kwargs):
        self._default('name','simulation plan',**kwargs)

        self.end_criteria = []
        self.selected_end_crit = None
        self.selected_end_crit_label = None
        self.capture_criteria = []
        self.selected_capt_crit = None
        self.selected_capt_crit_label = None
        self.plot_targets = []

        lfu.plan.__init__(self,*args,**kwargs)

    def _sanitize(self,*args,**kwargs):
        self.widg_templates_end_criteria = []
        self.widg_templates_capture_criteria = []
        self.widg_templates_plot_targets = []
        lfu.plan._sanitize(self,*args,**kwargs)

    def _reset_criteria_lists(self):
        del self.end_criteria[:]
        del self.capture_criteria[:]
        del self.children[:]
        self._rewidget(True)

    def add_end_criteria(self,crit = None):
        if crit is None:
            new = lc.criterion_sim_time(parent = self)
        else:
            new = crit
            new.parent = self

        self.end_criteria.append(new)
        self.children.append(new)
        self._rewidget(True)

    def add_capture_criteria(self,crit = None):
        if crit is None:
            new = lc.criterion_increment(parent = self)
        else:
            new = crit
            new.parent = self

        self.capture_criteria.append(new)
        self.children.append(new)
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
            select._destroy_()

        self.rewidget(True)

    def remove_capture_criteria(self, crit = None):
        if crit: select = crit
        else: select = self.get_selected_criteria('capture')
        if select:
            self.capture_criteria.remove(select)
            self.children.remove(select)
            select._destroy_()

        self.rewidget(True)

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
        #ensem = args[1]
        self._sanitize(*args,**kwargs)
        const_targs = self._always_targetable_
        targs = ensem.run_params['plot_targets']
        self.plot_targets = ensem.run_params['plot_targets']
        #all_targets = list(set(targs) | set(const_targs))
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
                verbosities = [3, 1], 
                instances = [[self.end_criteria, self], None], 
                keys = [[None, 'selected_end_crit_label'], None], 
                handles = [(self, 'end_crit_selector'), None], 
                labels = [None, ['Add End Criterion', 
                            'Remove End Criterion']], 
                initials = [[self.selected_end_crit_label], None], 
                bindings = [None, [lgb.create_reset_widgets_wrapper(
                                    window, self.add_end_criteria), 
                    lgb.create_reset_widgets_wrapper(window, 
                        self.remove_end_criteria)]]))
        self.widg_templates_capture_criteria.append(
            lgm.interface_template_gui(
                layout = 'grid', 
                widg_positions = [(0, 0), (0, 2), (1, 2)], 
                widg_spans = [(3, 2), None, None], 
                grid_spacing = 10, 
                widgets = ['mobj_catalog', 'button_set'], 
                verbosities = [3, 1], 
                instances = [[self.capture_criteria, self], None], 
                keys = [[None, 'selected_capt_crit_label'], None], 
                handles = [(self, 'capt_crit_selector'), None], 
                labels = [None, ['Add Capture Criterion', 
                            'Remove Capture Criterion']], 
                initials = [[self.selected_capt_crit_label], None], 
                bindings = [None, [lgb.create_reset_widgets_wrapper(
                                window, self.add_capture_criteria), 
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
                #labels = [self.plot_targets])]
        self.widg_templates_plot_targets.append(
            lgm.interface_template_gui(
                widgets = ['panel'], 
                box_labels = ['Capture Targets'], 
                scrollable = [True], 
                templates = [targets_template]))
        lfu.plan._widget(self, *args, from_sub = True)







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









