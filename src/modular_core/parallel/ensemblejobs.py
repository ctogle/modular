import modular_core.fundamental as lfu
import modular_core.parallel.mpicluster as mmcl
import modular_core.data.batch_target as dba
import modular_core.parameterspace.parameterspaces as lpsp

from mpi4py import MPI

import pdb,os,sys,numpy

###############################################################################
### ejob provides modular_core related functionality to an mjob
###############################################################################

class ejob(mmcl.mjob):

    # produce a numpy array of trajectory data
    def _runbatch(self,*args):
        ensem,trjcnt,tgcnt,cptcnt,meta = args
        dshape = (trjcnt,tgcnt,cptcnt)
        r = ensem._run_batch_np(trjcnt,dshape,pfreq = None)
        return r

    # create a loc_pool from numpy arrays in self.inputs
    def _gather_zeroth_inputs(self,ptargets = None,meta = False):
        if ptargets is None:
            ptargets = self.wargs[0].simulation_plan.plot_targets
        inputs = self.inputs
        if len(inputs) > 1:
            for i in inputs:
                if i is None:
                    return None
            ishape = inputs[0].shape
            agshape = (len(inputs)*ishape[0],ishape[1],ishape[2])
            aggregate = numpy.zeros(agshape,dtype = numpy.float)
            for idx in range(len(inputs)):
                i0 = idx*ishape[0]
                i1 = (idx+1)*ishape[0]
                if inputs[idx] is None:return None
                aggregate[i0:i1,:,:] = inputs[idx][:,:]
        else:aggregate = inputs[0]
        loc_pool = dba.batch_node(metapool = meta,
            data = aggregate,targets = ptargets)
        return loc_pool

    # perform zeroth post processes on self.inputs
    def _zeroth(self):
        ensem,trjcnt,tgcnt,cptcnt,meta = self.wargs
        ptargets = ensem.simulation_plan.plot_targets
        loc_pool = self._gather_zeroth_inputs(ptargets,meta)
        ensem.postprocess_plan._enact_zeroth_processes(loc_pool)
        #del self.inputs
        r = dba.batch_node(metapool = meta)
        for z in ensem.postprocess_plan.zeroth:
            r._add_child(z.data.children[0])
        return r

    # collect results from mjobs which perform self._zeroth
    def _aggregate(self):
        ensem,arc_length = self.wargs
        zeroth = ensem.postprocess_plan.zeroth
        zcount = len(zeroth)
        for adx in range(arc_length):
            l0p = self.inputs[adx]
            #if cplan.maintain_pspmap:
            #    mloc = l0p.metalocation
            #    mstr = mloc.location_string
            #    cplan.metamap.entries[mstr] = mloc
            #    cplan.metamap.location_strings.append(mstr)
            for zdx in range(zcount):
                zp = zeroth[zdx]
                zpdata = l0p.children[zdx]
                zp.data._add_child(zpdata)
                zp.data._stow_child(-1,v = False)

    # do all work associated with a pspace location
    # this bypasses much communication which is necessary
    # to break up work at a single pspace location
    def _run_pspace_location(self):
        r = self._runbatch(*self.wargs)
        self.inputs = [r]

        #if meta:
        #    print 'should record metamap data...'
        #    cplan = ensem.cartographer_plan
        #    cplan._record_persistent(ldex,loc_pool)

        z = self._zeroth()
        return z

    # generally expected to be called once per node before
    # running any simulations; this is when gillespiem compiles
    def _prepoolinit(self):
        #mmcl.silence()

        host = MPI.Get_processor_name()
        currcache = lfu.get_cache_path()
        if not currcache.endswith(host):
            lfu.set_cache_path(os.path.join(currcache,host))
        currcache = lfu.get_cache_path()
        if not os.path.exists(currcache):
            os.mkdir(currcache)
        #time.sleep(1)

        ensem = self.wargs[0]
        ensem._run_params_to_location_prepoolinit()
        #mmcl.vocalize()
        print 'finished prepoolinit work'

    # decide how to do work based on self.work string
    def _work(self):
        r = None
        if self.work == 'batch_run':r = self._runbatch(*self.wargs)
        elif self.work == 'zeroth':r = self._zeroth()
        elif self.work == 'gather':r = self._gather_zeroth_inputs()
        elif self.work == 'aggregate':r = self._aggregate()
        elif self.work == 'plocation':r = self._run_pspace_location()
        elif self.work == 'prepoolinit':r = self._prepoolinit()
        elif self.work == 'pass':r = None
        else:print 'UNKNOWN WORK REQUEST!',self.work
        self.result = r

###############################################################################
###############################################################################

# create an mjob which performs _prepoolinit once for each node
def setup_node_setup_mjob(ensem):
    from modular_core.ensemble import ensemble_manager
    mnger = ensemble_manager()

    mcfgstring = ensem._mcfg_string()
    anensem = mnger._add_ensemble(module = ensem.module_name)
    anensem._parse_mcfg(mcfgstring = mcfgstring)
    anensem.module.parsers = None
    anensem.multiprocess_plan.use_plan = False
    anensem.parent = None

    anensem.fitting_plan.routines = []
    anensem.fitting_plan.children = []
    anensem.run_params['fit_routines'] = []
    anensem.run_params['output_plans'] = {}

    prepoolargs = (anensem,)
    setup = ejob([],'prepoolinit',prepoolargs)
    return setup

# setup jobs for a pspace assuming break up of simulation work
def setup_pspace_mjobs(mjobs,zjobs,mnger,modname,mstring,arc,arc_dex,tpj,meta):
    anensem = mnger._add_ensemble(module = modname)
    anensem._parse_mcfg(mcfgstring = mstring)
    anensem.module.parsers = None
    anensem.multiprocess_plan.use_plan = False
    if anensem.postprocess_plan.use_plan:
        anensem.postprocess_plan._init_processes(arc)
    #
    anensem.module._increment_extensionname()
    #
    cplan = anensem.cartographer_plan
    pspace = cplan.parameter_space
    mappspace = cplan.use_plan and pspace
    if not mappspace:
        pspace = anensem.cartographer_plan._parameter_space([])
        trj = anensem.cartographer_plan.trajectory
        ntrj = anensem.num_trajectories
        lpsp.trajectory_set_counts(trj,ntrj)

    traj_cnt,targ_cnt,capt_cnt,ptargets = anensem._run_init(arc_dex)
    anensem.cartographer_plan._move_to(arc_dex)    
    anensem._run_params_to_location()
    anensem.parent = None

    brun_jcnt = traj_cnt/tpj
    remainder = traj_cnt - brun_jcnt*tpj

    print 'creating',brun_jcnt,'batch run jobs, each simulating',tpj,'trajectories'
    brun_args = (anensem,tpj,targ_cnt,capt_cnt)
    brun_mjobs = [ejob([],'batch_run',brun_args) for x in range(brun_jcnt)]
    if remainder > 0:
        brun_args = (anensem,remainder,targ_cnt,capt_cnt)
        brun_mjobs.append(ejob([],'batch_run',brun_args))
    mjobs.extend(brun_mjobs)
    print 'created',brun_jcnt,'batch run jobs, each simulating',tpj,'trajectories'

    #print 'creating',brun_jcnt,'batch run jobs, each simulating',tpj,'trajectories'
    zero_args = (anensem,traj_cnt,targ_cnt,capt_cnt,meta)
    brun_jdxs = [mjobs.index(j) for j in brun_mjobs]
    zero_mjob = ejob(brun_jdxs,'zeroth',zero_args)
    zjobs.append(zero_mjob)
    #print 'created',brun_jcnt,'batch run jobs, each simulating',tpj,'trajectories'

# create mjob hierarchy assuming fully broken up work
def setup_ensemble_mjobs(ensem,trj_per_job = None):
    comm = MPI.COMM_WORLD
    ncores = comm.size

    requiresimdata = ensem._require_simulation_data()
    pplan = ensem.postprocess_plan
    cplan = ensem.cartographer_plan
    pspace = cplan.parameter_space
    mappspace = cplan.use_plan and pspace
    if not mappspace:
        pspace = cplan._parameter_space([])
        trj,ntrj = cplan.trajectory,ensem.num_trajectories
        lpsp.trajectory_set_counts(trj,ntrj)

    meta = False

    arc = cplan.trajectory
    arc_length = len(arc)
    if pplan.use_plan:pplan._init_processes(arc)

    from modular_core.ensemble import ensemble_manager
    mnger = ensemble_manager()
    mcfgstring = ensem._mcfg_string()

    mjobs = []
    zjobs = []

    arc_dex = 0
    if trj_per_job is None:trj_per_job = traj_cnt/ncores
    #mmcl.silence()
    while arc_dex < arc_length:
        spargs = (mjobs,zjobs,mnger,ensem.module_name,
            mcfgstring,arc,arc_dex,trj_per_job,meta)
        setup_pspace_mjobs(*spargs)
        arc_dex += 1
        print 'make some jobs for this location:%d/%d'%(arc_dex,arc_length)
    #mmcl.vocalize()

    mjobs.extend(zjobs)
    aggr_args = (ensem,arc_length)
    zero_jdxs = [mjobs.index(j) for j in zjobs]
    aggr_mjob = ejob(zero_jdxs,'aggregate',aggr_args)
    aggr_mjob.root_only = True
    mjobs.append(aggr_mjob)
    return mjobs

# setup jobs for a pspace assuming NO break up of simulation work
def setup_pspace_mjob_maponly(mjobs,mnger,modname,mstring,arc,arc_dex,meta):
    anensem = mnger._add_ensemble(module = modname)
    anensem._parse_mcfg(mcfgstring = mstring)
    anensem.module.parsers = None
    anensem.multiprocess_plan.use_plan = False
    if anensem.postprocess_plan.use_plan:
        anensem.postprocess_plan._init_processes(arc)
    #
    anensem.module._increment_extensionname()
    #
    cplan = anensem.cartographer_plan
    pspace = cplan.parameter_space
    mappspace = cplan.use_plan and pspace
    if not mappspace:
        pspace = anensem.cartographer_plan._parameter_space([])
        trj = anensem.cartographer_plan.trajectory
        ntrj = anensem.num_trajectories
        lpsp.trajectory_set_counts(trj,ntrj)

    traj_cnt,targ_cnt,capt_cnt,ptargets = anensem._run_init(arc_dex)
    anensem.cartographer_plan._move_to(arc_dex)
    anensem._run_params_to_location()
    anensem.parent = None

    prun_args = (anensem,traj_cnt,targ_cnt,capt_cnt,meta)
    psploc_job = ejob([],'plocation',prun_args)
    mjobs.append(psploc_job)

# create mjob hierarchy assuming pspace map breakup of work
def setup_ensemble_mjobs_maponly(ensem):
    comm = MPI.COMM_WORLD
    ncores = comm.size

    requiresimdata = ensem._require_simulation_data()
    pplan = ensem.postprocess_plan
    cplan = ensem.cartographer_plan
    pspace = cplan.parameter_space
    mappspace = cplan.use_plan and pspace
    if not mappspace:
        pspace = cplan._parameter_space([])
        trj,ntrj = cplan.trajectory,ensem.num_trajectories
        lpsp.trajectory_set_counts(trj,ntrj)

    meta = False
    #meta = cplan.maintain_pspmap

    arc = cplan.trajectory
    arc_length = len(arc)
    if pplan.use_plan:pplan._init_processes(arc)

    from modular_core.ensemble import ensemble_manager
    mnger = ensemble_manager()
    mcfgstring = ensem._mcfg_string()

    mjobs = []
    arc_dex = 0
    #mmcl.silence()
    while arc_dex < arc_length:
        spargs = (mjobs,mnger,ensem.module_name,
                    mcfgstring,arc,arc_dex,meta)
        setup_pspace_mjob_maponly(*spargs)
        arc_dex += 1
        print 'make job for this location:%d/%d'%(arc_dex,arc_length)
    #mmcl.vocalize()

    aggr_args = (ensem,arc_length)
    pspl_jdxs = [x for x in range(arc_length)]
    aggr_mjob = ejob(pspl_jdxs,'aggregate',aggr_args)
    aggr_mjob.root_only = True
    mjobs.append(aggr_mjob)
    return mjobs

###############################################################################

def setup_pspace_fitting_mjobs(anensem,traj_cnt,tpj):
    mjobs = []
    brun_jcnt = traj_cnt/tpj
    remainder = traj_cnt - brun_jcnt*tpj

    ptargs = anensem.run_params['plot_targets']
    targ_cnt = len(ptargs)
    capt_cnt = anensem.simulation_plan._capture_count()
    meta = False

    brun_args = (anensem,tpj,targ_cnt,capt_cnt)
    brun_mjobs = [ejob([],'batch_run',brun_args) for x in range(brun_jcnt)]
    if remainder > 0:
        brun_args = (anensem,remainder,targ_cnt,capt_cnt)
        brun_mjobs.append(ejob([],'batch_run',brun_args))
    mjobs.extend(brun_mjobs)

    zero_args = (anensem,traj_cnt,targ_cnt,capt_cnt,meta)
    brun_jdxs = [x for x in range(len(mjobs))]
    if anensem.postprocess_plan.use_plan:
        zero_mjob = ejob(brun_jdxs,'zeroth',zero_args,root_only = True)
    else:zero_mjob = ejob(brun_jdxs,'gather',zero_args,root_only = True)
    mjobs.append(zero_mjob)
    return mjobs

###############################################################################

if __name__ == '__main__':
    print 'modular_core.parallel.ensemblejobs'

###############################################################################










