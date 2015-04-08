import modular_core.fundamental as lfu
import modular_core.settings as lset

import modular_core.postprocessing.process_abstract as pra
import modular_core.data.batch_target as dba
import modular_core.io.liboutput as lo

import pdb,types,time,math,os,sys,traceback
import numpy as np
#np.seterr(divide = 'raise')

if __name__ == 'modular_core.postprocessing.processplan':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'processplan of modular_core'

###############################################################################
### post_process_plan manages post_processes
###############################################################################

class post_process_plan(lfu.plan):

    def __init__(self,*args,**kwargs):
        self._default('name','post process plan',**kwargs)
        self._default('processes',[],**kwargs)
        use = lset.get_setting('postprocessing')
        self._default('use_plan',use,**kwargs)
        fit = lset.get_setting('fitting_aware')
        self._default('fitting_aware',fit,**kwargs)
        self._default('display_children',False,**kwargs)
        self._default('always_sourceable',[],**kwargs)
        self._default('selected_process',None,**kwargs)
        lfu.plan.__init__(self,*args,**kwargs)
        self.current_tab_index = 0

    # reset the data attribute and determine if a process is 0th
    def _init_processes(self,ptraj,meta = False):
        zeroth = []
        for process in self.processes:
            process.data = dba.batch_node(metapool = meta)
            if 'simulation' in process.input_regime:
                zeroth.append(process)
        self.zeroth = zeroth
        self.psp_trajectory = ptraj
        return zeroth

    # run process proc
    def _enact_process(self,proc,pool):
        print 'performing post process:',proc.name
        stime = time.time()
        ptraj = self.psp_trajectory
        method = proc.__getattribute__[proc.method]
        if proc.regime == 'per trajectory':
            #if not pool.children:
            #    proxy = dba.batch_node(targets = pool.targets)
            #    proxy._add_child(pool)
            #    pool = proxy
            #    #pool = pool._split_self()
            for pchild in pool.children:
                pchild._recover(v = False)
                presult = method(pchild,ptraj)
                #presult = proc.method(pchild,ptraj)
                pchild._stow(v = False)
                proc.data._add_child(presult)
                proc.data._stow_child(-1,v = False)
        elif proc.regime == 'all trajectories':
            presult = method(pchild,ptraj)
            #presult = proc.method(pool,ptraj)
            proc.data._add_child(presult)
            proc.data._stow_child(-1,v = False)
        print 'process regime:',proc.regime
        runtime = time.time() - stime
        print 'finished post process:',proc.name,'in',runtime

    # for node pool run processes procs and append to each
    # procs' result
    def _enact_processes(self,procs,pool):
        ptraj = self.psp_trajectory
        pool._recover(v = False)
        for process in procs:self._enact_process(process,pool)
        pool._stow(v = False)

    # for each 0th process, recursively call consuming processes
    def _walk_processes(self):
        ptraj = self.psp_trajectory
        zeroth = self.zeroth
        ran = zeroth[:]
        toberun = [p for p in self.processes if not p in zeroth]
        while toberun:
            rannames = [r.name for r in ran]
            readytorun = []
            readypools = []
            for tbr in toberun:
                ready = True
                readypool = dba.batch_node()
                for inp in tbr.input_regime:
                    if not inp in rannames:
                        ready = False
                        break
                    else:
                        which = lfu.grab_mobj_by_name(inp,ran)
                        readypool.children.extend(which.data.children)
                if ready:
                    readytorun.append(tbr)
                    readypools.append(readypool)
            for rp,rpool in zip(readytorun,readypools):
                rpool._recover(v = False)
                self._enact_process(rp,rpool)
                rpool._stow(v = False)
                ran.append(rp)
                toberun.remove(rp)

    # perform processes, measure time, return data pool
    # for each pspace location, iterate over 0th level processes
    #  each process calls those which consume it
    #
    #  processes form a bethe network...
    def _enact(self,*args,**kwargs):
        pool = args[1]
        cplan = self.parent.cartographer_plan
        if cplan.use_plan:psp_trajectory = cplan.trajectory
        else:psp_trajectory = None
        zeroth = self._init_processes(psp_trajectory)
        if cplan.use_plan:
            for psp_dex in range(len(psp_trajectory)):
                childpool = pool.children[psp_dex]
                self._enact_processes(zeroth,childpool)
        else:self._enact_processes(zeroth,pool)
        self._walk_processes()
        return pool

    # aggregate the data of all post processes
    def _data(self):
        dpool = dba.batch_node()
        [dpool._add_child(p.data) for p in self.processes]
        return dpool

    # reset children and processes
    def _reset_process_list(self):
        del self.processes[:]
        del self.children[:]

    # add new post process; default to meanfields
    def _add_process(self,new = None):
        if new is None:new = pra.post_process(parent = self)
        if new is None:return
        new.fitting_aware = self.fitting_aware
        new.always_sourceable = self.always_sourceable
        new.parent = self

        if hasattr(self.parent,'run_params'):
            ops = self.parent.run_params['output_plans']
            ops[new.name+' output'] = new.output

        self.processes.append(new)
        self.children.append(new)
        self.parent.module._rewidget(True)
        self._rewidget(True)

    # remove selected post process
    def _del_process(self,selected = None):
        if selected is None:selected = self._selected()
        if selected:
            self.processes.remove(selected)
            self.children.remove(selected)
            if hasattr(self.parent,'run_params'):
                ops = self.parent.run_params['output_plans']
                del ops[selected.name+' output']
        self._rewidget(True)

    # shift a process up in the post process hierarchy
    def _process_up(self):
        select = self._selected()
        if select:
            select_dex = lfu.grab_mobj_dex_by_name(
                select.name,self.processes)
            self.processes.pop(select_dex)
            self.processes.insert(select_dex - 1, select)
            self._rewidget_processes()

    # shift a process down in the post process hierarchy
    def _process_down(self):
        select = self._selected()
        if select:
            select_dex = lfu.grab_mobj_dex_by_name(
                select.name,self.processes)
            self.processes.pop(select_dex)
            self.processes.insert(select_dex + 1, select)
            self._rewidget_processes()

    # propagate rewidg to children processes
    def _rewidget_processes(self,rewidg = True):
        for p in self.processes:p._rewidget(rewidg)

    # return the currently selected post process if there is one
    def _selected(self):
        if not hasattr(self,'process_selector'):print 'no selector'; return
        selector = self.process_selector[0].layout().itemAt(0).widget()
        dex = selector.currentIndex()-1
        if dex in range(len(self.processes)):
            return self.processes[dex]

    # make sure children can see ensemble...
    def _rewidget_children(self,*args,**kwargs):
        infos = (kwargs['infos'],self.parent)
        for child in self.children:
            if child._rewidget(**kwargs):
                child._widget(*infos)

    def _tab_book_pages(self,*args,**kwargs):
        pages = []
        for proc in self.processes:
            proc._widget(*args,**kwargs)
            pp_page = lgm.interface_template_gui(
                widgets = ['panel'], 
                scrollable = [True], 
                templates = [proc.widg_templates])
            pages.append((proc.name,[pp_page]))
        return pages

    def _widget(self,*args,**kwargs):
        window = args[0]
        select_label = self.selected_process
        self._sanitize(*args,**kwargs)
        primary_template = lgm.interface_template_gui(
            layout = 'grid', 
            grid_spacing = 10, 
            widg_positions = [(0,0),(0,2),(1,2),(2,2),(3,2),(4,2)], 
            widg_spans = [(3,2)]+[None]*5, 
            widgets = ['mobj_catalog','button_set'], 
            verbosities = [1,1], 
            instances = [[self.processes,self],None], 
            keys = [[None,'selected_process'],None], 
            handles = [(self,'process_selector'),None], 
            labels = [None,
                ['Add Post Process','Remove Post Process', 
                'Move Up In Hierarchy','Move Down In Hierarchy']], 
            initials = [[select_label],None], 
            bindings = [None,
                [lgb.create_reset_widgets_wrapper(window,self._add_process),
                lgb.create_reset_widgets_wrapper(window,self._del_process), 
                lgb.create_reset_widgets_wrapper(window,self._process_up), 
                lgb.create_reset_widgets_wrapper(window,self._process_down)]])
        if self.display_children:
            childrens_template = lgm.interface_template_gui(
                widgets = ['tab_book'], 
                verbosities = [0], 
                pages = [self._tab_book_pages(*args,**kwargs)], 
                initials = [[self.current_tab_index]], 
                handles = [(self, 'tab_ref')], 
                instances = [[self]], 
                keys = [['current_tab_index']])
            split_template = lgm.interface_template_gui(
                widgets = ['splitter'], 
                orientations = [['horizontal']], 
                templates = [[primary_template,childrens_template]])
            self.widg_templates.append(split_template)
        else: self.widg_templates.append(primary_template)
        lfu.plan._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################










