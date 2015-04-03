import modular_core.fundamental as lfu
import modular_core.data.batch_target as dba

import dispy,random,time,socket,pdb

from mpi4py import MPI
def test():
    comm = MPI.COMM_WORLD
    print 'hey, im rank %d from %d running in total:' % (comm.rank,comm.size)
    comm.Barrier()
    return comm.rank

def test_DISPY(*args):
    mobj,jobdex = args

    import modular_core.fundamental as lfu
    data = lfu.mobject(name = 'jobmobj%d'%(jobdex))

    host = socket.gethostname()
    data.dispyhost = host
    data.dispyindex = jobdex
    return data

def start_cluster(cluster,args):
    jobs = []
    jobcount = len(args)
    for jobdex in range(jobcount):
        job = cluster.submit(*args[jobdex])
        time.sleep(1)
        job.id = jobdex
        jobs.append(job)
    return jobs

def cluster_setup():
    return 0

def collect_cluster(jobs):
    results = []
    for job in jobs:
        result = job()
        if result is None:print 'LIKELY EXCEPTION\n',job.exception
        else:
            host = result.dispyhost
            jobdex = result.dispyindex
            printargs = (host,job.id,job.start_time,jobdex)
            results.append(result)
            print '%s executed job %s at %s with %s'%printargs
    return results

def clusterize(ensem,arc_length):
    requiresimdata = ensem._require_simulation_data()
    cplan = ensem.cartographer_plan
    pplan = ensem.postprocess_plan
    meta = cplan.maintain_pspmap
    arc = cplan.trajectory
    arc_length = len(arc)
    max_run = arc[0].trajectory_count
    stow_needed = ensem._require_stow(max_run,arc_length)

    data_pool = dba.batch_node(metapool = meta)
    arc_dex = 0

    comm = MPI.COMM_WORLD

    while arc_dex < arc_length:
        traj_cnt,targ_cnt,capt_cnt,ptargets = ensem._run_init(arc_dex)
        if comm.rank == 0:
            dshape = (traj_cnt,targ_cnt,capt_cnt)

            if cplan.maintain_pspmap:
                #print 'should only fill metamap data as required...'
                target_traj_cnt = traj_cnt
                traj_cnt,dshape = cplan._metamap_remaining(arc_dex,traj_cnt,dshape)
                lstr = cplan._print_friendly_pspace_location(arc_dex)
                mmap = cplan.metamap
        comm.Barrier()

        if not traj_cnt == 0:
            if comm.rank == 0:
                loc_pool = dba.batch_node(metapool = meta,
                        dshape = dshape,targets = ptargets)
            cplan._move_to(arc_dex)
            ensem._run_params_to_location()

            #subtjcnt = traj_cnt
            print 'im rank %d from %d running in total:'%(comm.rank,comm.size)
            subtjcnt = traj_cnt/20
            subshape = (subtjcnt,targ_cnt,capt_cnt)
            batch = ensem._run_batch_np(subtjcnt,subshape)
            batch = 10
            print 'calling gather!'
            batches = comm.gather(batch,root = 0)
            if comm.rank == 0:
                #batches = [None]*20
                print 'gathered!'
                for batch in batches:
                    for b in batch:
                        loc_pool._trajectory(b)

                if cplan.maintain_pspmap:
                    #print 'should record metamap data...'
                    cplan._record_persistent(arc_dex,loc_pool)
                    loc_pool = mmap._recover_location(lstr)
            else:print 'im rank %d and im done:'%(comm.rank)
            comm.Barrier()
        else:
            if comm.rank == 0:
                loc_pool = mmap._recover_location(lstr,target_traj_cnt)

        arc_dex += 1
        if comm.rank == 0:
            if pplan.use_plan:
                zeroth = pplan.zeroth
                pplan._enact_processes(zeroth,loc_pool)
            
            #loc_pool = self._run_pspace_location(arc_dex,mppool,meta)

            if meta:cplan._save_metamap()
            print 'pspace locations completed:%d/%d'%(arc_dex,arc_length)
            if requiresimdata:
                data_pool._add_child(loc_pool)
                if stow_needed:data_pool._stow_child(-1)

    comm.Barrier()
    if comm.rank == 0:
        print 'i might have made it?'
        return data_pool
    else:return None

if __name__ == '__main__':
    inpmobj = lfu.mobject(name = 'ensemble?')
    inpargs = [(inpmobj,x) for x in range(10)]
    nodes = ['127.0.0.1']
    #nodes = ['127.0.0.1','192.168.4.76']
    #nodes = ['127.0.0.1','hemlock.phys.vt.edu','192.168.4.76']
    #nodes = ['hemlock.phys.vt.edu','192.168.4.76']
    #nodes = ['127.0.0.1','192.168.4.76']
    results = clusterize(nodes,test,inpargs,[])

    pdb.set_trace()


