import modular_core.fundamental as lfu
import modular_core.data.batch_target as dba
import modular_core.parameterspace.parameterspaces as lpsp
import modular_core.io.liboutput as lo
import modular_core.io.pkl as pk

import pdb,os,sys,types,time,random

if __name__ == 'modular_core.fitting.routine_abstract':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'routine_abstract of modular_core'

routine_types = {}

###############################################################################
###
###############################################################################

class routine_abstract(lfu.mobject):

    def __init__(self,*args,**kwargs):
        self._default('name','a routine',**kwargs)
        self._default('max_undos',10000,**kwargs)
        self._default('max_runtime',60.0,**kwargs)
        self._default('max_iteration',1000.0,**kwargs)
        self._default('max_last_best',10000,**kwargs)
        self._default('simulations_per_iteration',1,**kwargs)
        self._default('parameter_space',None,**kwargs)
        self._default('pspace_source','cartographer',**kwargs)
        self._default('input_data_path',None,**kwargs)
        self._default('capture_targets',[],**kwargs)
        oname = self.name + ' output'
        self.output = lo.output_plan(name = oname,
                parent = self,flat_data = False)
        self.children = [self.output]
        lfu.mobject.__init__(self,*args,**kwargs)

    def _finished(self):
        overiter = self.iteration + 1 >= self.max_iteration
        overtime = time.time() - self.starttime >= self.max_runtime
        overundo = self.undos > self.max_undos
        overlbst = (self.iteration - self.best_capture) > self.max_last_best
        done = overiter or overtime or overundo or overlbst
        if done:
            print 'oi,',overiter,',ot,',overtime,',ou,',overundo,',ol,',overlbst
        return done

    def _record_position(self,pspace):
        psp_position = pspace._position()
        self.psp_trajectory.append(psp_position)

    def _parameter_space(self):
        cplan = self.parent.parent.cartographer_plan
        if self.pspace_source == 'cartographer':
            pspace = cplan.parameter_space
        elif self.pspace_source == 'magnitude':
            axes = cplan.parameter_space.axes
            pspace = lpsp.magnitude_space(axes)
        elif self.pspace_source == 'decimated':
            axes = cplan.parameter_space.axes
            mspace = lpsp.magnitude_space(axes)
            pspace = lpsp.decimated_space(mspace.axes)
        self.parameter_space = pspace
        self.parameter_space.steps = []

    def _iterate(self,ensem,pspace):
        ensem._run_params_to_location()

        traj_cnt = self.simulations_per_iteration
        capt_cnt = ensem.simulation_plan._capture_count()
        ptargets = ensem.run_params['plot_targets']
        targ_cnt = len(ptargets)
        meta = False

        dshape = (traj_cnt,targ_cnt,capt_cnt)
        loc_pool = dba.batch_node(metapool = meta,
                dshape = dshape,targets = ptargets)
        ran = ensem._run_batch(traj_cnt,loc_pool,pfreq = None)
        return loc_pool,ran

    # consider a measurement, undo or keep step?
    def _accept_step(self,information,ran):
        return True

    def _feedback(self,information,ran,pspace):
        undo = not self._accept_step(information,ran)
        self._pspace_move(pspace,undo)

    def _movement_factor(self):
        return 1.0

    def _pspace_move(self,pspace,undo = False):
        factor = self._movement_factor()
        if undo:
            if self.capture > 0:self.undos += 1
            pspace._undo_step()
            dims = pspace.dimensions
            #many_steps = int(max([1,abs(random.gauss(dims,dims))]))
            many_steps = int(max([1,abs(random.gauss(dims/2.0,dims/2.0))]))
            pspace._proportional_step(factor,many_steps)
        else:
            creep = 2.0
            pspace._biased_step(factor/creep)

    def _capture(self,data,pspace):
        if not data.children:split = data._split()
        else:split = data
        #if not self.iteration % 100 == 0 and not self.best and self.capture:
        if not self.best and self.capture:
            split._stow_children(v = False)
            return
        print 'routine captured at iteration:',self.iteration
        if self.best:self.best_capture = self.capture
        self.capture += 1
        self._record_position(pspace)
        for sch in split.children:
            self.data._add_child(sch)
            self.data._stow_child(-1,v = False)

    # subclasses can use input data if the want
    # sets the input_data attribute to the opened data node
    def _open_data(self,dpath):
        idata = pk.load_pkl_object(dpath)

        ### THIS IS CURRENTLY UNUSED.... IT PROBABLY SHOULD BE USED....
        ptargets = self.parent.parent.simulation_plan.plot_targets
        itargets = [d.name for d in idata.data]
        aliases = {}
        for ak,rk in zip(itargets,ptargets):
            aliases[ak] = rk
        ### THIS IS CURRENTLY UNUSED.... IT PROBABLY SHOULD BE USED....

        dshape = (len(idata.data),len(idata.data[0].data))
        targets = [d.name for d in idata.data]
        idatanode = dba.batch_node(dshape = dshape,targets = targets)
        for fdx in range(dshape[0]):
            idatanode.data[fdx,:] = idata.data[fdx].data[:]
        self.input_data = idatanode

    def _initialize(self,*args,**kwargs):
        print 'initialize routine',self.name
        meta = False
        self.data = dba.batch_node(metapool = meta)

        ensem = self.parent.parent
        ensem._run_params_to_location_prepoolinit()
        if self.parameter_space is None:
            self._parameter_space()
        pspace = self.parameter_space
        pspace._lock_singular_axes()
        self.psp_trajectory = []
        self.iteration = 0
        self.capture = 0
        self.best_capture = 0
        self.undos = 0
        self.best = False

        if not self.input_data_path is None:
            self._open_data(self.input_data_path)

    def _run(self,*args,**kwargs):
        self.starttime = time.time()
        ensem = self.parent.parent
        pspace = self.parameter_space
        abort = False
        while not abort and not self._finished():
            information,ran = self._iterate(ensem,pspace)
            if ran is True:
                self._feedback(information,ran,pspace)
                self._capture(information,pspace)
            elif ran is False:abort = True
            else:
                self._feedback(information,ran,pspace)
                information._stow(v = False)
            if self.capture > 0:self.iteration += 1

    def _finalize(self,*args,**kwargs):
        print 'finializing routine',self.name,'...'
        self.data._dupe_child(self.best_capture)
        ensem = self.parent.parent
        traj = self.psp_trajectory
        traj.append(traj[self.best_capture])
        pspace = self.parameter_space
        ensem._output_trajectory_key(traj,pspace)
        print 'routine best captured at plot:',self.best_capture
        print 'pspace location',traj[-1].location

    def _targetables(self,*args,**kwargs):
        ptargs = self.parent.parent.simulation_plan.plot_targets
        return ptargs

    def _target_settables(self,*args,**kwargs):pass

###############################################################################
###############################################################################

###############################################################################
### utility functions
###############################################################################

# query the user (dialog or command line) for a routine type
def gather_routine_type():
    opts = routine_types.keys()
    if lfu.using_gui:
        variety = lgd.create_dialog(
            title = 'Choose Fitting Routine Type',
            options = opts,variety = 'radioinput')
    else:
        rrequest = 'enter a routine type:\n\t'
        for op in opts:rrequest += op + '\n\t'
        rrequest += '\n'
        variety = raw_input(rrequest)
    return variety

# query the user (dialog or command line) for a routine name
def gather_routine_name():
    namemsg = 'Provide a unique name for this fitting routine:\n\t'
    name = lfu.gather_string(msg = namemsg,title = 'Name Fitting Routine')
    return name

# prompt user for routine type if needed and create
def routine(variety = None,name = None,**rargs):
    opts = routine_types.keys()
    if variety is None:variety = gather_routine_type()
    if not variety in opts:
        print 'unrecognized routine type:',variety
        return
    if name is None:name = gather_routine_name()
    if not name is None:
        rout = routine_types[variety][0](name = name,**rargs)
        return rout
    print 'routine name was invalid:',str(name)

# parse one mcfg line into a fitting routine and add to ensems plan
def parse_routine_line(line,ensem,parser,procs,routs,targs):
    print 'parse routine line:\n\t"',line,'"\n'
    rout_types = routine_types.keys()
    spl = lfu.msplit(line)
    variety = spl[1]
    rargs = routine_types[variety][1](spl,ensem,procs,routs)
    rout = routine(**rargs)
    routs.append(rout)
    ensem.fitting_plan._add_routine(new = rout)
    if lfu.using_gui:rout._widget(0,ensem)
    else:rout._target_settables(0,ensem)

# turn the comma separated int list into an input_regime
def parse_routine_line_inputs(inputs,procs,routs):

    pdb.set_trace()
    # STILL ORIENTED FOR PROCESSES...

    ips = [int(v) for v in lfu.msplit(inputs,',')]
    reg = []
    for inp in ips:
        if inp == 0:reg.append('simulation')
        elif inp <= len(procs):reg.append(procs[inp - 1].name)
    return reg

###############################################################################
###############################################################################

# a fitting routine is a glorified feedback loop
# an mcfg specifies a model which implicits a starting location
# a parameter space should be specified as well
# this includes the range of every axis
# this can generate a coarse grained hyper-dimensional lattice
# covering the whole space with a predictable number of points
# some work is done for each location resulting in some output
# this can be one sim, many sims, and any postprocess hierarchy thereof
# this packet of information can be associated with an pspace location
# generate a hierarchy of stowed nodes as the lattice is decimated and explored
# after a batch of locations are explored, a feedback process considers the 
# currently aggregated stowed data packets to decide what parts of the lattice
# are worth exploring further
# this feedback loop should allow for user intervention/selection or automation

# must be able to close modular, reopen or open some explorer app to select
# lattice nodes and recall the data from them
# could be able to add more data as well?

###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################







#TRASH#BELOW###################################################################



class fit_routine(lfu.mobject):

    def initialize(self, *args, **kwargs):

        def affi_weights(leng):
            x = np.linspace(0, leng, leng)
            b = 5.0
            m = -4.0/x[-1]
            y = m*x + b
            return y

        if self.regime == 'coarse-magnitude':
            self.use_mean_fitting = False
            self.parameter_space, valid =\
                lgeo.generate_coarse_parameter_space_from_fine(
                        self.parameter_space, magnitudes = True)
            if not valid:
                traceback.print_exc(file=sys.stdout)
                lgd.message_dialog(None, 
                    'P-Spaced couldnt be coarsened!', 'Problem')

        elif self.regime == 'coarse-decimate':
            self.use_mean_fitting = False
            self.parameter_space, valid =\
                lgeo.generate_coarse_parameter_space_from_fine(
                        self.parameter_space, decimates = True)
            if not valid:
                traceback.print_exc(file=sys.stdout)
                lgd.message_dialog(None, 
                    'P-Spaced couldnt be coarsened!', 'Problem')

        elif self.regime == 'fine': pass
        print '\tstarted fit routine', self.label, 'regime', self.regime
        self.parameter_space.set_start_position()
        for metric in self.metrics:
            metric.initialize(self, *args, **kwargs)
        self.data = ldc.scalars_from_labels(['fitting iteration'] +\
                [met.label + ' measurement' for met in self.metrics])

    def iterate(self, *args, **kwargs):
        self.iteration += 1
        run_func = args[0]
        worker_pool = args[2]
        display = self.iteration % self.display_frequency == 0
        if display:
            print ' '.join(['\niteration:', str(self.iteration), 
                        'temperature:', str(self.temperature)])

        current_position = self.parameter_space.get_current_position()
        argu = (self.ensemble, self.data_to_fit_to, 
            self.target_key, self.domain_weights, 
            self.parameter_space, current_position, 
                            self.metric_rulers, 0)
        kwds = {'timeout': self.max_sim_wait_time}
        if self.use_mean_fitting:
            processor_count = self.worker_count
            measurements = []
            dex0 = 0
            while dex0 < self.proginy_count:
                check_time = time.time()
                runs_left = self.proginy_count - dex0
                if runs_left >= processor_count: 
                    runs_this_round = processor_count

                else: runs_this_round = runs_left % processor_count
                dex0 += runs_this_round

                worker_pool._initializer()

                result = worker_pool.map_async(run_func, 
                        [(argu, kwds)]*runs_this_round, 
                        callback = measurements.extend)
                result.wait()
                print 'multicore reported...', ' location: ', dex0

            measurements = [meas for meas in measurements 
                                    if not meas is False]
            if not measurements: measurements = False
            else:
                measurements = [np.mean(measure) for 
                    measure in zip(*measurements)]

        else:
            self.ensemble.set_run_params_to_location()
            measurements = run_func((argu, kwds))
        if measurements is False:
            print 'no valid measurements...undoing...'
            self.timeouts += 1
            self.move_in_parameter_space(bypass = True)
            return False

        for dex, met in enumerate(self.metrics):
            met.data[0].scalars.append(measurements[dex])
            met.check_best(display)

        if self.metrics[self.prime_metric].best_flag:
            self.last_best = 0

        else: self.last_best += 1
        self.capture_plot_data()
        self.p_sp_trajectory.append(current_position)
        self.move_in_parameter_space()
        return True


    def impose_coarse_result_to_p_space(self):

        def locate(num, vals):
            delts = [abs(val - num) for val in vals]
            where = delts.index(min(delts))
            found = vals[where]
            return found

        fine_space = self.ensemble.cartographer_plan.parameter_space
        print 'fine p-space modified by coarse p-space'
        print '\tbefore'
        for sub in fine_space.subspaces:
            print sub.label
            print sub.inst.__dict__[sub.key], sub.increment, sub.bounds

        orders = [10**k for k in [val - 20 for val in range(40)]]
        for spdex, finesp, subsp in zip(range(len(fine_space.subspaces)), 
                fine_space.subspaces, self.parameter_space.subspaces):
            wheres = range(len(subsp.scalars))
            best_val = float(self.p_sp_trajectory[
                self.best_fits[self.prime_metric][0]][spdex][-1])
            delts = [abs(val - best_val) for val in subsp.scalars]
            where = delts.index(min(delts))
            finesp.move_to(best_val)
            cut = int(len(wheres) / 6)
            print 'THE CUT', cut

            #if len(wheres) >= 4:
            if cut > 0:
                if where in wheres[2*cut:-2*cut]:
                    keep = subsp.scalars[cut:-cut]

                elif where in wheres[:-2*cut]:
                    keep = subsp.scalars[:-cut]

                elif where in wheres[2*cut:]:
                    keep = subsp.scalars[cut:]

                else: keep = subsp.scalars[:]

            else:
                print 'CUT IS ZERO', cut
                if self.regime.endswith('decimate'):
                    pdb.set_trace()

                elif self.regime.endswith('magnitude'):
                    current = subsp.scalars[where]
                    if current in orders[:2]:
                        left = orders[0]
                        right = orders[4]
                        print 'PINNED', left, right

                    elif current in orders[-2:]:
                        left = orders[-5]
                        right = orders[-1]
                        print 'PINNED', left, right

                    else:
                        left = locate(current/100.0, orders)
                        right = locate(current*100.0, orders)

                    if left < finesp.perma_bounds[0]:
                        left = locate(finesp.perma_bounds[0], orders)
                        right = orders[orders.index(left) + 5]
                        print 'out of bounds left', left, right

                    if right > finesp.perma_bounds[1]:
                        right = locate(finesp.perma_bounds[1], orders)
                        left = orders[orders.index(right) - 5]
                        print 'out of bounds right', left, right

                    keep = [left, right]
                    print 'slid from', subsp.scalars[wheres[0]:wheres[-1]+1], 'to', keep

                else:
                    print 'WHAT SHOULD HAPPEN HERE??'
                    pdb.set_trace()

            finesp.bounds = [keep[0], keep[-1]]

        print '\tafter'
        for sub in fine_space.subspaces:
            print sub.label
            print sub.inst.__dict__[sub.key], sub.increment, sub.bounds



 
