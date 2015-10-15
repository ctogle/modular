import modular_core.fundamental as lfu
import modular_core.settings as lset
import modular_core.ensemble as me
import modular_core.parameterspace.metamap as mmap
import modular_core.data.batch_target as dba

import modular_core.gui.libqtgui as lqg
lgm = lqg.lgm
lgd = lqg.lgd
lgb = lqg.lgb

import pdb,os,sys,time,random,multiprocessing,socket
from cStringIO import StringIO

# a ticket associates a list of requirements with a number
class ticket(lfu.mobject):

    def __init__(self,number,ensem):
        self.number = number
        self._determine(ensem)

    # using the ensemble ensem, determine the list of required 
    # parameter space location data sets
    def _determine(self,ensem):
        required = []
        cplan = ensem.cartographer_plan
        arc = cplan.trajectory
        arc_length = len(arc)
        arc_dex = 0
        while arc_dex < arc_length:
            location = cplan._print_friendly_pspace_location(arc_dex)
            numtraj = cplan.trajectory[arc_dex].trajectory_count
            required.append((numtraj,location))
            arc_dex += 1
        self.required = required

# mworker is a class which can recieve instructions realtime
#   and execute them in parallel using multiprocessing
# it creates and runs ensembles in an attempt to full a set 
#   of requests which have in common a metamap uniqueness
#
# it has two layers of communication:
#       a layer which performs some work, checks the current 
#               instructions, and either continues or stops accordingly
#       a layer which allows modification of the current instruction
#       
class mworker(lfu.mobject):

    workprocess = None
    commprocess = None
    
    commpipe = None

    status = 'new'

    def __init__(self,module,mcfgstring,metamap,*args,**kwargs):
        self.module = module
        self.mcfgstring = mcfgstring
        self.metamap = metamap
        self.tickets = []
        self.required = {}
        self.log = StringIO()
        lfu.mobject.__init__(self,*args,**kwargs)

    ##################################################################
    ### interface to a comm process to handle requests from the server
    ##################################################################

    # start a comm process
    def _open_comm(self):
        self.commpipe,commsubpipe = multiprocessing.Pipe()
        commargs = (commsubpipe,self.module,self.mcfgstring)
        self.commprocess = multiprocessing.Process(
                    target = _comm,args = commargs)
        self.commprocess.start()

    # start working on all tickets
    # NOTE: set self.mcfgstring before calling this...
    def _start(self):
        self._open_comm()
        self.commpipe.send(self.required)
        self.status = 'working'

    # stop working on all tickets
    def _kill(self):
        self.commpipe.send('kill')
        self.commprocess.join()

    # pause working on all tickets
    def _pause(self):
        self.commpipe.send('pause')
        self.status = 'paused'

    # resume working on all tickets
    def _resume(self):
        self.commpipe.send('resume')
        self.status = 'working'

    # update the reqs/rkys to reflected progress
    def _update(self):
        self.commpipe.send('provide-update')
        self.status = 'updating'
        updated = self.commpipe.recv()

        print 'must compare update results'
        print 'older'
        print self.required
        print 'newer'
        print updated

    # provide an estimate on completion time on the required list
    def _query(self):
        if self.commpipe is None:return 'unstarted'
        self.commpipe.send('query')
        self.status = 'query'
        queryreply = self.commpipe.recv()
        self.status = 'working'
        return queryreply

    # provide a one word description of current activity
    def _status(self):
        if self.commpipe is None:return 'unstarted'
        self.commpipe.send('state')
        self.status = 'statequery'
        queryreply = self.commpipe.recv()
        self.status = 'working'
        return queryreply

    ##################################################################
    ##################################################################
    ##################################################################

    ##########################################
    ### interface for the request/ticket lists
    ##########################################

    # if mmap has matching uniqueness, ensure its data is
    #   represented in self.metamap
    # NOTE: used for receiving updates to the metamap from the workprocess
    def _host_map(self,mmap):
        if not self.metamap.uniqueness == mmap.uniqueness:
            print 'worker asked to host invalid metamap!'
            raise ValueError
        for loc_str in mmap.location_strings:
            if not loc_str in self.metamap.location_strings:
                self.metamap._log(loc_str,None)
            self.metamap.entries[loc_str]._merge(mmap.entries[loc_str])

        # THE COMM PROCESS AND WORK PROCESS MUST FIND OUT ABOUT 
        # THE NEW AVAILABLE DATA
        # this is partialyl done in the newticket process

    # add a new request to the pool of requests
    # a request is the effect of running the given ensemble
    #   reduce this to a dataset for parameter space
    #   create a set of jobs for this space that link to the request
    #   the jobs can have priority associated with them
    def _new_request(self,ticketnumber,ensem):
        newticket = ticket(ticketnumber,ensem)
        self.tickets.append(newticket)
        for req in newticket.required:
            if not req[1] in self.required:
                self.required[req[1]] = ['normal',[newticket.number],[req[0]]]
            else:
                self.required[req[1]][1].append(newticket.number)
                self.required[req[1]][2].append(req[0])
        # required is a dict containing the network of pspace requirements and tickets
        # the keys are encodings of the parameter space location and the 
        #       required number of trajectories, end, and capture criteria
        return newticket

    # stop working on a particular ticket and remove it
    # NOTE: affects the subset of requests for this ticket
    def _cancel_ticket(self,ticket):

        raise NotImplemented

    # stop working on all tickets and remove them
    # NOTE: cancel each current ticket
    def _cancel_all(self):
    
        raise NotImplemented

    # stop working on a particular ticket
    # NOTE: affects the priorities of requests in the request list
    def _pause_ticket(self,ticket):

        raise NotImplemented

    # stop working on any tickets
    # NOTE: affects the priorities of requests in the request list
    def _pause_all(self):

        raise NotImplemented

    # resume working on a particular ticket
    # NOTE: affects the priorities of requests in the request list
    def _resume_ticket(self,ticket):

        raise NotImplemented

    # resume working on all paused tickets
    # NOTE: affects the priorities of requests in the request list
    def _resume_all(self):

        raise NotImplemented

    # return request results or an estimate to completion time
    # a ticket is the identifier for a request returned by self._new_request
    def _query_ticket(self,ticket):
        commquery = self._query()
        print 'need to process commquery for ticket specific info...'
        return commquery

    # return the status of all tickets
    # a ticket is the identifier for a 
    #   request returned by self._new_request
    def _query_all(self):
        commquery = self._query()
        print 'need to process commquery for all ticket specific info...'
        print '\n\tcommquery:\n',commquery,'\n'
        return commquery

    ##########################################
    ##########################################
    ##########################################

#################################################################
### extra process target functions for executing instrutions/work
#################################################################

# run in a Process
# listen for a change in instruction from the top level process
# when a change occurs, inform the workprocess
def _comm(commpipe,module,mcfgstring):
    logqueue = StringIO()
    def log(msg):
        logqueue.write('\n\t> ')
        logqueue.write(msg)
    sys.stdout = logqueue

    print 'comm waiting for required lookup...'
    creqs = commpipe.recv()
    print 'comm received required lookup...'

    print 'comm starting worker process...'
    workpipe,worksubpipe = multiprocessing.Pipe()
    workprocess = multiprocessing.Process(
        target = _work,args = (worksubpipe,module,mcfgstring))
    workprocess.start()
    workpipe.send(creqs)
    print 'comm started worker process...'

    while True:
        instr = _comm_server_poll(commpipe,workpipe,creqs)
        if instr is False:
            workpipe.send('kill')
            workprocess.join()
            break
        else:reqs = instr

        '''#
        # communicate with the server as needed
        if commpipe.poll():
            msg = commpipe.recv()
            print 'mworker comm received a server message:',msg
            if msg == 'kill':
                workpipe.send('kill')
                workprocess.join()
            #elif msg == 'log':
            elif msg == 'pause':workpipe.send('pause')
            elif msg == 'resume':workpipe.send('resume')
            elif msg == 'receive-update':
                commrequired = commpipe.recv()
                workpipe.send('receive-update')
                workpipe.send(commrequired)
            elif msg == 'provide-update':
                workpipe.send('provide-update')
                workupdate = workpipe.recv()

                print 'make ccommrequired reflect workupdate...'
                commrequired = workupdate

                commpipe.send(commrequired)
            elif msg == 'query':
                #request = commpipe.poll()
                workpipe.send('query')
                reply = workpipe.recv()
                print 'sending query reply:',reply
                commpipe.send(reply)
            elif msg == 'state':
                workpipe.send('state')
                reply = workpipe.recv()
                print 'sending statequery reply:',reply
                commpipe.send(reply)
        '''#

        # communicate with the worker as needed
        '''#
        if workpipe.poll():
            workmsg = workpipe.recv()
            print 'mworker comm received a worker message:',workmsg
            if workmsg == 'done':
                workpipe.send('okay')
                #workpipe.send(creqs)
                print 'mworker has completed its work and awaits!'
        '''#

    workpipe.close()
    sys.stdout = sys.__stdout__

# the mworker comm process polls the server for input...
def _comm_server_poll(commpipe,workpipe,creqs):
    r = commpipe.poll()
    while r:
        r = commpipe.recv()
        print 'mworker comm received a server message:',r
        if r == 'kill':return False
        #elif r == 'log':
        elif r == 'pause':workpipe.send('pause')
        elif r == 'resume':workpipe.send('resume')
        elif r == 'receive-update':
            creqs = commpipe.recv()
            workpipe.send('receive-update')
            workpipe.send(creqs)
        elif r == 'provide-update':
            workpipe.send('provide-update')
            workupdate = workpipe.recv()

            print 'make ccreqs reflect workupdate...'
            creqs = workupdate

            commpipe.send(creqs)
        elif r == 'query':
            #request = commpipe.poll()
            workpipe.send('query')
            reply = workpipe.recv()
            print 'sending query reply:',reply
            commpipe.send(reply)
        elif r == 'state':
            workpipe.send('state')
            reply = workpipe.recv()
            print 'sending statequery reply:',reply
            commpipe.send(reply)
        r = commpipe.poll()
    return creqs

# run in a Process
# perform 5 basic functions on the worker process
#   based on messages from the commpipe
#   kill, pause, resume, update, query
#   kill - end the work process
#   pause - pause work and wait for instruction
#   resume - resume work as usual
#   update - receive/provide an update on the request list
#   query - provide an eta until completion or the results
def _work(commpipe,module,mcfgstring):
    logqueue = StringIO()
    def log(msg):
        logqueue.write('\n\t> ')
        logqueue.write(msg)
    sys.stdout = logqueue

    print "\nmultithread mworker is creating resources\n"
    stime = time.time()
    emnger = me.ensemble_manager()
    ensem = _work_setup(emnger,module,mcfgstring)
    if ensem.multiprocess_plan.use_plan:
        pcnt = int(ensem.multiprocess_plan.worker_count)
        pinit = ensem._run_params_to_location
        mppool = multiprocessing.Pool(processes = pcnt,initializer = pinit)
    else:mppool = None

    # ensem must see an update for every metamap hosted by the worker object
    # the worker will effectively merge them, so they can eventually be removed
    # once the worker has successfully written what represents their union

    print "\nmultithread mworker has started working\n"

    reqs = commpipe.recv()
    rkys = reqs.keys()
    reqs['workerdata'] = {
        'reqcnt':len(rkys),
        'starttime':time.time()}

    while True:
        instr = _work_comm_poll(commpipe,reqs,rkys)
        if instr is False:break
        else:reqs,rkys = instr
        done = len(rkys) == 1
        if done:
            instr = _work_comm_wait(commpipe,reqs,rkys) 
            if instr is False:break
            else:reqs,rkys = instr
        reqs,rkys = _work_resume(commpipe,reqs,rkys,ensem,mppool)

    if mppool:
        mppool.close()
        mppool.join()
    sys.stdout = sys.__stdout__

# wait for further work or instructions from the server
# NOTE: this is called when work is complete and the worker is idle
def _work_comm_wait(commpipe,reqs,rkys):
    print 'mworker awaits further work requests',len(rkys)
    #commpipe.send('done')
    while len(rkys) <= 1:
        r = commpipe.recv()

        time.sleep(0.1)

        if r == 'kill':return False
        elif r == 'receive-update':
            print 'mworker work process receiving update...'
            reqs = commpipe.recv()
            rkys = reqs.keys()
        elif r == 'provide-update':
            print 'mworker work process providing update...'
            commpipe.send(reqs)
        elif r == 'query':
            qrep = _form_query_reply(reqs,rkys)
            commpipe.send(qrep)
        elif r == 'state':commpipe.send('done')
        else:print 'paused worker received ambiguous input:',r
    return reqs,rkys

# handle any requests from the server
# NOTE: this is called in between work jobs to 
#   see if the server has provided new instructions
def _work_comm_poll(commpipe,reqs,rkys):
    r = commpipe.poll()
    while r:
        r = commpipe.recv()
        print 'work request recv',r
        if r == 'kill':
            print 'mworker work process killed...'
            return False
        elif r == 'pause':
            reqs,rkys =_work_pause(commpipe,reqs,rkys)
        elif r == 'receive-update':
            print 'mworker work process receiving updating...'
            reqs = commpipe.recv()
            rkys = reqs.keys()
        elif r == 'provide-update':
            print 'mworker work process providing updating...'
            commpipe.send(reqs)
        elif r == 'query':
            qrep = _form_query_reply(reqs,rkys)
            commpipe.send(qrep)
        elif r == 'state':commpipe.send('working')

        r = commpipe.poll()

    return reqs,rkys

# based on priorities, choose the next job to simulate
# NOTE: should avoid selecting 'workerdata' entry
def _pick_job(reqs,rkys):
    return 1

# the effective working state of the worker
# NOTE: called when ready to perform work
def _work_resume(commpipe,reqs,rkys,ensem,mppool):
    ireq = reqs['workerdata']['reqcnt']
    jkey = _pick_job(reqs,rkys)
    wkey = rkys[jkey]
    wreq = reqs[wkey]
    ran = _work_batch(ensem,wkey,wreq,mppool)
    if ran:
        print 'mworker completed job:',ireq-len(rkys),'/',ireq
        rkys.pop(jkey)
        del reqs[wkey]
    else:
        print '_work_batch failed to run!!'
        raise RuntimeError
    return reqs,rkys

# the effective pause state of the worker
# NOTE: called when the pause signal is received
def _work_pause(commpipe,reqs,rkys):
    print 'mworker work process paused...'
    while True:
        r = commpipe.recv()
        if r == 'resume':
            print 'mworker work process resumed...'
            break
        elif r == 'kill':return
        elif r == 'receive-update':
            print 'mworker work process receiving updating...'
            reqs = commpipe.recv()
            rkys = reqs.keys()
        elif r == 'provide-update':
            print 'mworker work process providing updating...'
            commpipe.send(reqs)
        elif r == 'query':
            qrep = _form_query_reply(reqs,rkys)
            commpipe.send(qrep)
        elif r == 'state':commpipe.send('paused')
        else:print 'paused worker received ambiguous input:',r
    return reqs,rkys

# convert a number in seconds to minutes
def s_to_m(s):return s/60.0

# consider the required list to form a reply to a query
def _form_query_reply(reqs,rkys):
    print 'mworker work answering query...'
    wdata = reqs['workerdata']
    stime,sreqcnt = wdata['starttime'],wdata['reqcnt']

    ### query function?
    rtime = time.time()-stime
    frac = 1.0-float(len(rkys)-1)/float(sreqcnt)
    eta = rtime/frac

    queryreply = '\n\tquery reply : \n\t'+str(frac*100.0)
    queryreply += ' % complete with runtime:\t'+str(s_to_m(rtime))
    queryreply += '\n\testimated total run time:\t'+str(s_to_m(eta))
    queryreply += '\n\testimated remaining time:\t'+str(s_to_m(eta-rtime))
    return queryreply

# create an ensemble for a work function to use
def _work_setup(emnger,module,mcfgstring):
    ensem = emnger._add_ensemble(module = module)
    ensem._parse_mcfg(mcfgstring = mcfgstring)
    ensem.output_plan.targeted = ensem.run_params['plot_targets'][:]
    ensem.output_plan._target_settables()
    cplan = ensem.cartographer_plan
    #ensem.multiprocess_plan.use_plan = False
    ensem._run_params_to_location_prepoolinit()
    return ensem

# use an ensemble to fulfill a work request
def _work_batch(ensem,key,req,mppool = None,pfreq = 100):
    # confirm the work location is the parameter space
    goal = max(req[2])

    print '_work_batch on',key,'for',goal,'trajectories'

    cplan = ensem.cartographer_plan
    pspace = cplan.parameter_space
    ldex = cplan.metamap._confirm_location(key,goal)
    lstr = cplan._print_friendly_pspace_location(ldex)

    # determine the remaining requirements for the location
    traj_cnt,targ_cnt,capt_cnt,ptargets = ensem._run_init(ldex)
    dshape = (traj_cnt,targ_cnt,capt_cnt)
    traj_cnt,dshape = cplan._metamap_remaining(ldex,traj_cnt,dshape)
    if not traj_cnt == 0:
        loc_pool = dba.batch_node(
            metapool = True,rnum = ensem._seed(),
            dshape = dshape,targets = ptargets)
        cplan._move_to(ldex)

        if mppool:
            mppool._initializer()
            ensem._run_mpbatch(mppool,traj_cnt,loc_pool,pfreq = pfreq) 
        else:
            ensem._run_params_to_location()
            ensem._run_batch(traj_cnt,loc_pool,pfreq = pfreq)

        cplan._record_persistent(ldex,loc_pool)
        cplan._save_metamap()

        #loc_pool = mmap._recover_location(lstr)
    #else:loc_pool = mmap._recover_location(lstr,target_traj_cnt)
    return True










