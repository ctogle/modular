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

    # provide an update on the request list
    def _update(self):
        self.commpipe.send('update')
        self.status = 'updating'

    # provide an estimate on completion time on the required list
    def _query(self):
        if self.commpipe is None:return 'unstarted'
        self.commpipe.send('query')
        self.status = 'query'
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
                self._log(loc_str,None)
            self.metamap.entries[loc_str]._merge(mmap.entries[loc_str])

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
    print 'comm waiting for required lookup...'
    commrequired = commpipe.recv()
    print 'comm received required lookup...'

    print 'comm starting worker process...'
    workpipe,worksubpipe = multiprocessing.Pipe()
    workprocess = multiprocessing.Process(
        target = _work,args = (worksubpipe,module,mcfgstring))
    workprocess.start()
    workpipe.send(commrequired)
    print 'comm started worker process...'

    msg = None
    while not msg == 'kill':
        # communicate with the server as needed
        if commpipe.poll():
            msg = commpipe.recv()
            print 'mworker comm received a server message:',msg
            if msg == 'kill':
                workpipe.send('kill')
                workprocess.join()
            elif msg == 'pause':workpipe.send('pause')
            elif msg == 'resume':workpipe.send('resume')
            elif msg == 'receive-update':
                commrequired = commpipe.recv()
                workpipe.send('receive-update')
                workpipe.send(commrequired)
            elif msg == 'provide-update':
                workpipe.send('provide-update')
                commrequired = commpipe.recv()
            elif msg == 'query':
                request = commpipe.poll()
                workpipe.send('query')
                reply = workpipe.recv()
                print 'sending query reply:',reply
                commpipe.send(reply)
        # communicate with the worker as needed
        elif workpipe.poll():
            workmsg = workpipe.recv()
            print 'mworker comm received a worker message:',workmsg
            if workmsg == 'complete':
                workpipe.send(commrequired)
                print 'mworker has completed its work and awaits!'
        # do nothing for a short period of time
        else:time.sleep(0.1)
    workpipe.close()

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
    print "\nmultithread mworker is creating resources\n"
    stime = time.time()
    emnger = me.ensemble_manager()
    ensem = _work_setup(emnger,module,mcfgstring)
    itime = time.time()

    print "\nmultithread mworker has started working\n"
    required = commpipe.recv()
    reqkeys = required.keys()
    ireq = len(reqkeys)
    while True:
        request = commpipe.poll()
        #print 'work request polled',request
        if request is True:
            request = commpipe.recv()
            print 'work request recv',request
            if request == 'kill':
                print 'mworker work process killed...'
                break
            elif request == 'pause':
                print 'mworker work process paused...'
                request = commpipe.recv()
                while True:
                    if request == 'resume':break
                    elif request == 'kill':return
                    elif request == 'receive-update':
                        print 'mworker work process receiving updating...'
                        required = commpipe.recv()
                        reqkeys = required.keys()
                    elif request == 'provide-update':
                        print 'mworker work process providing updating...'
                        commpipe.send(required)
                    elif request == 'query':
                        queryreply = _form_query_reply(itime,ireq,required)
                        commpipe.send(queryreply)
                    else:print 'paused worker received ambiguous input:',request
                    request = commpipe.recv()
            elif request == 'resume':
                print 'mworker work process resumed...'
            elif request == 'receive-update':
                print 'mworker work process receiving updating...'
                required = commpipe.recv()
                reqkeys = required.keys()
            elif request == 'provide-update':
                print 'mworker work process providing updating...'
                commpipe.send(required)
            elif request == 'query':
                queryreply = _form_query_reply(itime,ireq,required)
                commpipe.send(queryreply)

        complete = len(reqkeys) == 0
        if complete:
            print 'mworker awaits further work requests'
            commpipe.send('complete')

            ##### NEED A WHILE LOOP FOR THE COMPLETE STATE
            ##### NEED TO BREAK UP ALL THESE STATE FUNCTIONS...
            request = commpipe.recv()
            while True:
                if request == 'kill':return
                elif request == 'receive-update':
                    print 'mworker work process receiving updating...'
                    required = commpipe.recv()
                    reqkeys = required.keys()
                elif request == 'provide-update':
                    print 'mworker work process providing updating...'
                    commpipe.send(required)
                elif request == 'query':
                    queryreply = _form_query_reply(itime,ireq,required)
                    commpipe.send(queryreply)
                else:print 'paused worker received ambiguous input:',request
                request = commpipe.recv()
            ##### NEED A WHILE LOOP FOR THE COMPLETE STATE
            ##### NEED TO BREAK UP ALL THESE STATE FUNCTIONS...

            required = commpipe.recv()
            reqkeys = required.keys()
        else:
            # should choose the next key based on priority
            jobkeyx = 0
            workkey = reqkeys[jobkeyx]
            workreq = required[workkey]
            ran = _work_batch(ensem,workkey,workreq)
            if ran:
                print 'mworker completed job',ireq-len(reqkeys),'/',ireq
                reqkeys.pop(jobkeyx)
                del required[workkey]
            else:
                print '_work_batch failed to run!!'
                raise RuntimeError

# consider the required list to form a reply to a query
def _form_query_reply(stime,sreqcnt,reqs):
    ### query function?
    print 'mworker work answering query...'
    rtime = time.time()-stime
    rkeys = reqs.keys()
    frac = float(len(rkeys))/float(sreqcnt)
    eta = rtime/frac
    #frac = str(len(rkeys))+'/'+str(sreqcnt)
    queryreply = 'query reply : \n\t'+str(frac*100.0)
    queryreply += '% complete with runtime: '+str(rtime)
    queryreply += '\n\testimated completion time:\t'+str(eta)
    return queryreply

# create an ensemble for a work function to use
def _work_setup(emnger,module,mcfgstring):
    ensem = emnger._add_ensemble(module = module)
    ensem._parse_mcfg(mcfgstring = mcfgstring)
    ensem.output_plan.targeted = ensem.run_params['plot_targets'][:]
    ensem.output_plan._target_settables()
    cplan = ensem.cartographer_plan
    ensem.multiprocess_plan.use_plan = False
    ensem._run_params_to_location_prepoolinit()
    return ensem

# use an ensemble to fulfill a work request
def _work_batch(ensem,key,req):
    # confirm the work location is the parameter space
    goal = max(req[2])
    cplan = ensem.cartographer_plan
    pspace = cplan.parameter_space
    ldex = cplan.metamap._confirm_location(key,goal)
    lstr = cplan._print_friendly_pspace_location(ldex)

    # determine the remaining requirements for the location
    traj_cnt,targ_cnt,capt_cnt,ptargets = ensem._run_init(ldex)
    dshape = (traj_cnt,targ_cnt,capt_cnt)
    traj_cnt,dshape = cplan._metamap_remaining(ldex,traj_cnt,dshape)
    if not traj_cnt == 0:
        loc_pool = dba.batch_node(metapool = True,
                dshape = dshape,targets = ptargets)
        cplan._move_to(ldex)

        if ensem.multiprocess_plan.use_plan:mppool._initializer()
        else:ensem._run_params_to_location()
        #if mppool:ensem._run_mpbatch(mppool,traj_cnt,loc_pool)
        #else:ensem._run_batch(traj_cnt,loc_pool)
        ensem._run_batch(traj_cnt,loc_pool,pfreq = 100)

        cplan._record_persistent(ldex,loc_pool)
        cplan._save_metamap()

        #loc_pool = mmap._recover_location(lstr)
    #else:loc_pool = mmap._recover_location(lstr,target_traj_cnt)
    return True

#################################################################
#################################################################
#################################################################

#################################################################
#################################################################
#################################################################

# this is target function for a child Process
# it functions as an interface between a server and its clients
# it receives requests from clients and in some cases posts replies
# it communicates the needs of the clients to the server
# the server will communicate with clients through this process only
def _listen(commpipe,port,msh = False,buffersize = 4096,msdelim = '\n|::|\n'):
    mcfgstringqueue = StringIO()
    logqueue = StringIO()
    def log(msg):
        if not msh:print(msg)
        logqueue.write(msg)

    log('\n\t>\tmserver opening socket on port:'+str(port))
    s = socket.socket()
    s.settimeout(0.5)
    s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    s.bind(('',port))
    log('\n\t>\tmserver opened socket on port:'+str(port))

    clients = []
    clientaddrs = []
    clientcnt = 0
    toremove = []
    commpipe.send(True)
    while True:

        # handle requests from the server
        request = commpipe.poll()
        if request is True:
            request = commpipe.recv()
            log('\n\t>\tmserver request recv'+request)
            if request == 'kill':
                log('\n\t>\tmserver disconnecting clients...')
                for c in clients:c.close()
                log('\n\t>\tmserver disconnected clients...')
                break
            elif request == 'log':commpipe.send(logqueue.getvalue())
            elif request == 'job':commpipe.send(mcfgstringqueue.getvalue())
            elif request == 'who':
                print '\n\tmserver currently has',clientcnt,'clients connected'
                if clientcnt:
                    print '\t\tclient list:'
                    for cx in range(clientcnt):
                        print '\t\t\t',cx,' : ',clientaddrs[cx]
                commpipe.send('mshell')
            elif request == 'clientcount':commpipe.send(clientcnt)
            else:log('\n\t>\tinvalid mserver request:\t'+request)

        # allow new clients to connect
        try:
            s.listen(1)
            c,addr = s.accept()
            c.settimeout(0.5)
            clients.append(c)
            clientaddrs.append(addr)
            clientcnt += 1
            log('\n\t>\tconnected to client:\t'+str(addr))
        except socket.timeout:
            #print 'server polling shell...'
            pass

        # allow clients to be heard
        if clientcnt:
            for cx in range(clientcnt):
                c,addr = clients[cx],clientaddrs[cx]
                try:
                    data = c.recv(buffersize)
                    if data == 'kill':toremove.append(cx)
                    elif data == 'ping':c.send('ping!')
                    elif data == 'mcfg':
                        mcfgstring = c.recv(4096)
                        mcfgstringqueue.write(msdelim)
                        mcfgstringqueue.write(mcfgstring)
                        log('\n\t>\tmserver received mcfgstring:')
                        log(mcfgstring)
                    else:log('\n\t>\tmserver received client message:\t'+data)
                except socket.timeout:
                    #print 'server polling shell...'
                    pass

        # remove disconnected clients
        if toremove:
            toremove = sorted(toremove)
            toremove.reverse()
            while toremove:
                torem = toremove.pop(0)
                clients.pop(torem)
                caddr = clientaddrs.pop(torem)
                log('\n\t>\tmserver disconnected from mclient:\t'+str(caddr))
                clientcnt -= 1

    log('\n\t>\tmserver closing socket...')
    s.close()
    log('\n\t>\tmserver socket closed...\nmserver exiting...\n')
    log('\n\t>\t\tmserver exited...')

# mserver provides an all purpose multi-user simulation server
# 
# it maintains a persistent database so that users may 
#   share and reuse data
#
# it serves a set of clients using tcp sockets
# it uses a set of mworkers to handle the aggregate of requests
#   which have been received from clients
#
# it can be run with or without a gui
#   without a gui, a shell like interface is provided
#
# it functions as a resource manager intelligently dispersing 
# batches of work until a prioritized list of requests is fulfilled
#
# it provides additional run information such as disk usage and running 
# estimates on the completion time and realtime status updates on jobs
#
# a client does not necessarily require modular, just the ability to send
#   the appropriate tcp messages to a port bound to an mserver
#
# a request is effectively a "modular.py some.mcfg" call
#   it results in output data files from post processes
# the mserver manages requests which it may receive from clients
# requests can also be issued from the mservers interface
class mserver(lfu.mobject):

    def _settings(self):
        self.settings_manager.display()

    def _open_comm(self):
        self.instpipe,instsubpipe = multiprocessing.Pipe()
        instargs = (instsubpipe,self.port,self.clientserver_mshell,
                    self.buffersize,self.mcfgstringdelim)
        self.instprocess = multiprocessing.Process(
                    target = _listen,args = instargs)
        self.instprocess.start()

    def _help(self):
        print '#'*40+'\n\tproviding help on server shell usage...\n'+'#'*40
        print '\n\t\toptions for input:'
        print '\t\t\tquit              : q'
        print '\t\t\thelp              : h'
        print '\t\t\tprint server log  : l'
        print '\t\t\treceive mcfg jobs : r'
        print '\t\t\tlist clients      : w'
        print '\t\t\tprint status      : s\n'
        print '#'*40+'\n\tend help...\n'+'#'*40

    def _accept_work(self):
        self.instpipe.send('job')
        mcfgstrings = self.instpipe.recv()
        mcfgs = mcfgstrings.split(self.mcfgstringdelim)
        if mcfgs:
            for mcfgstring in mcfgs:

                print 'could accept work????'
                print mcfgstring
                print 'was there anything even????'

                if not mcfgstring:continue
                self._run_mcfgstring(mcfgstring)
                print '\tmcfg submitted to server...'
        else:print '\tno mcfgs have been submitted by clients'

    def _status(self):
        self.instpipe.send('clientcount')
        clientcnt = self.instpipe.recv()
        print '#'*40+'\n\tproviding status of server...\n'+'#'*40
        print '\n\t\t',clientcnt,'clients are currently connected\n'
        print '#'*40+'\n\tend status report...\n'+'#'*40

    # _serve_socket and provide a shell to interface
    def _serve_shell(self):
        self._open_comm()
        ready = self.instpipe.recv()
        print '\n\twelcome to the mserver shell'
        print '\t\tuse "h" for help...'
        while True:                        
            do = raw_input('\n\tmserver shell ::>> ')
            if   do == 'q':
                self._kill_workers()
                self._close_socket()
                break
            elif do == 'h':self._help()
            elif do == 'l':
                self.instpipe.send('log')
                log = self.instpipe.recv()
                print '\n'+'#'*50+'\n\tserver log:\n'+'#'*50+'\n'
                print log
            elif do == 'r':self._accept_work()
            elif do == 'w':
                self.instpipe.send('who')
                ready = self.instpipe.recv()
            elif do == 's':self._status()
    
    # serve on a socket via a gui
    def _serve_socket(self):
        self._open_comm()
        ready = self.instpipe.recv()

    # close the server socket
    def _close_socket(self):
        self.instpipe.send('kill')
        self.instprocess.join()

    def __init__(self,*args,**kwargs):
        self.settings_manager = lset.settings_manager(
            parent = self,filename = 'mserver_settings.txt')
        self.settings = self.settings_manager.read_settings()

        defmod = lset.get_setting('default_module')
        self._default('module',defmod,**kwargs)

        defmcfgpath = lset.get_setting('mcfg_path')
        self._default('mcfg_path',defmcfgpath,**kwargs)
        self._default('mcfg_dir',lfu.get_mcfg_path(),**kwargs)

        defport = lset.get_setting('default_port')
        self._default('port',defport,**kwargs)
        self._default('clientserver_mshell',not lfu.using_gui,**kwargs)
        self._default('buffersize',4096,**kwargs)
        self._default('mcfgstringdelim','\n~!|::|!~\n',**kwargs)


        defdatadir = lset.get_setting('default_data_directory')
        self._default('default_data_directory',defdatadir,**kwargs)

        datasources = [defdatadir,lfu.get_mapdata_pool_path()]
        self._default('data_sources',datasources,**kwargs)


        defoutpdir = lset.get_setting('default_output_directory')
        self._default('output_directory',defoutpdir,**kwargs)
        self._default('metamaps',[],**kwargs)
        self._default('maprings',{},**kwargs)
        self._default('tickets',{},**kwargs)
        self.mnger = me.ensemble_manager()
        lfu.mobject.__init__(self,*args,**kwargs)
        self.current_tab_index = 0

    # examine the contents of the data_sources
    # reset the list of metamaps to the list present
    # read each metamap and establish instances for them
    def _inspect_sources(self):
        self.hdf5files = []
        self.mpklfiles = []
        for src in self.data_sources:
            if not os.path.exists(src):
                print 'data source does not exist... :',src
            else:self._inspect_source(src)
        print 'inspected data sources and found:'
        print '\t',len(self.hdf5files),'hdf5 data files'
        print '\t',len(self.mpklfiles),'pkl data files'
        print 'now hosting',len(self.metamaps),'metamaps'

    def _inspect_source(self,src):
        print 'inspecting data...'
        dfiles = os.listdir(src)
        newhdf5files = [df for df in dfiles if df.endswith('.hdf5')]
        newmpklfiles = [df for df in dfiles if df.endswith('.pkl')]
        self.hdf5files.extend(newhdf5files)
        self.mpklfiles.extend(newmpklfiles)
        if newmpklfiles:
            for mpf in newmpklfiles:
                worker = self._host_map(src,mpf)
        print 'inspected data source and found:'
        print '\t',len(newhdf5files),'hdf5 data files'
        print '\t',len(newmpklfiles),'pkl data files'
        print 'now hosting',len(self.metamaps),'metamaps'

    # create the data to manage identity and access of a metamap
    #
    # if the maps uniqueness is new, create an mworker to maintain 
    #   the maps associated with that uniqueness
    # if the maps uniqueness is not new, ask the existing mworker 
    #   to host the new metamap
    # 
    # an mworker hosts additional maps my merging their information
    #   the datafiles must be located in the same directory
    # the mworker should be able to do something similar if told to inspect 
    #   the data directory for possible updates to the available data
    #
    def _host_map(self,msrc,mfile):
        if type(mfile) == type(''):
            meta = mmap.metamap(
                require_match = False,parent = self,
                mapfile = mfile,mapdir = msrc)
        else:meta = mfile
        if meta.uniqueness in self.maprings:
            worker = self.maprings[meta.uniqueness]
            worker._host_map(meta)
        else:
            mcfgstring = meta.mcfgstring
            if mcfgstring is None:
                print 'metamap is missing mcfgstring...'
                #pdb.set_trace()
            worker = self._new_worker(meta,mcfgstring)
        return worker

    # create a new mworker
    def _new_worker(self,metamap,mcfgstring):
        self.metamaps.append(metamap)
        newworker = mworker(self.module,mcfgstring,metamap)
        self.maprings[metamap.uniqueness] = newworker
        return newworker

    # start an mworker
    def _start_worker(self,worker,mcfgstring = None):
        if mcfgstring:worker.mcfgstring = mcfgstring
        worker._start()
        time.sleep(0.1)

    # kill all mworkers
    def _kill_workers(self):
        print 'workers are being killed...'
        for mwuq in self.maprings:
            self.maprings[mwuq]._kill()
        print 'workers have been killed...'
        time.sleep(0.1)

    # pause all mworkers
    def _pause_workers(self):
        for mwuq in self.maprings:
            self.maprings[mwuq]._pause()
        time.sleep(0.1)

    # resume all mworkers
    def _resume_workers(self):
        for mwuq in self.maprings:
            self.maprings[mwuq]._resume()
        time.sleep(0.1)

    # query all workers on their work
    def _query_workers(self):
        for mwuq in self.maprings:
            self.maprings[mwuq]._query_all()
        time.sleep(0.1)

    # run an ensemble given an mcfg
    def _run_mcfg(self,mcfg = None):
        if mcfg is None:mcfg = self.mcfg_path
        if not os.path.exists(mcfg):
            print 'unable to location mcfg file:'
            print '\t'+mcfg
        else:
            with open(mcfg,'r') as mh:mcfgstring = mh.read()
            self._run_mcfgstring(mcfgstring)

    # run an ensemble given an mcfgstring
    # determine associated metamap / create if necessary
    def _run_mcfgstring(self,mcfgstring):
        ensem = self.mnger._add_ensemble(module = self.module)
        ensem._parse_mcfg(mcfgstring = mcfgstring)
        ensem.output_plan.targeted = ensem.run_params['plot_targets'][:]
        ensem.output_plan._target_settables()
        metamap = ensem.cartographer_plan.metamap
        metamap.mcfgstring = mcfgstring

        #msrc = self.data_directory
        pdb.set_trace()

        worker = self._host_map(msrc,metamap)
        return self._run_ensem(worker,ensem,mcfgstring)

    # generate a ticket for an ensemble
    def _run_ensem(self,worker,ensem,mcfgstring):
        ticketnumber = random.randint(1000000,9000000)
        ticket = worker._new_request(ticketnumber,ensem)
        self.tickets[ticketnumber] = ticket
        self._start_worker(worker,mcfgstring)
        time.sleep(0.1)
        return ticketnumber

    def _select_mcfg(self,file_ = None):
        if not file_ and not os.path.isfile(self.mcfg_path):
            fidlg = lgd.create_dialog('Choose File','File?','file', 
                    'Modular config files (*.mcfg)',self.mcfg_dir)
            file_ = fidlg()                  
        if file_:
            self.mcfg_path = file_
            self.mcfg_text_box_ref[0].setText(self.mcfg_path)

    def _mcfg_widget(self,*args,**kwargs):
        window = args[0]
        config_text = lgm.interface_template_gui(
            layout = 'grid', 
            widg_positions = [(0, 0)],
            widg_spans = [(1, 2)], 
            widgets = ['text'], 
            handles = [(self,'mcfg_text_box_ref')], 
            keys = [['mcfg_path']], 
            instances = [[self]], 
            initials = [[self.mcfg_path]])
        config_buttons = lgm.interface_template_gui(
            widg_positions = [(1, 0),(1, 1),(2, 0)], 
            widgets = ['button_set'], 
            bindings = [[
                lgb.create_reset_widgets_wrapper(window,
                    [self._select_mcfg,self._run_mcfg])]], 
            labels = [['Run mcfg File']])
        return config_text + config_buttons

    def _data_sources_widget(self,*args,**kwargs):
        window = args[0]
        directory_templates =\
            [lgm.interface_template_gui(
                panel_scrollable = True, 
                widgets = ['directory_name_box'], 
                layout = 'horizontal', 
                keys = [['default_data_directory']], 
                instances = [[self]], 
                initials = [[self.default_data_directory,None,os.getcwd()]],
                labels = [['Choose Default Data Directory']], 
                box_labels = ['Default Data Directory'])]
        return directory_templates

    def get_on_close(self,window):
        def on_close():
            self._kill_workers()
            self._close_socket()
            window.on_close()
        return on_close

    def _toolbars(self,*args,**kwargs):
        window = args[0]
        wrench_icon = lfu.get_resource_path('wrench_icon.png')
        center_icon = lfu.get_resource_path('center.png')
        refresh = lfu.get_resource_path('refresh.png')
        quit = lfu.get_resource_path('quit.png')
        settings_ = lgb.create_action(parent = window,label = 'Settings', 
            bindings = lgb.create_reset_widgets_wrapper(window,self._settings),
            icon = wrench_icon,shortcut = 'Ctrl+Shift+S',statustip = 'Settings')
        center_ = lgb.create_action(parent = window,label = 'Center', 
            icon = center_icon,shortcut = 'Ctrl+C',statustip = 'Center Window',
            bindings = [window.on_resize,window.on_center])
        self.refresh_ = lgb.create_reset_widgets_function(window)
        update_gui_ = lgb.create_action(parent = window, 
            label = 'Refresh GUI', icon = refresh, shortcut = 'Ctrl+G', 
            bindings = self.refresh_,statustip = 'Refresh the GUI (Ctrl+G)')
        quit_ = lgb.create_action(parent = window,label = 'Quit', 
            icon = quit,shortcut = 'Ctrl+Q',statustip = 'Quit the Application',
            bindings = self.get_on_close(window))
        self.menu_templates.append(
            lgm.interface_template_gui(
                menu_labels = ['&File']*4,
                menu_actions = [settings_,center_,update_gui_,quit_]))
        self.tool_templates.append(
            lgm.interface_template_gui(
                tool_labels = ['&Tools']*4,
                tool_actions = [settings_,center_,update_gui_,quit_]))

    def _widget(self,*args,**kwargs):
        window = args[0]
        self._sanitize(*args,**kwargs)
        
        serverclient_templates = []
        config_file_box_template = self._mcfg_widget(*args,**kwargs)
        serverclient_templates.append(config_file_box_template)

        server_templates = []
        server_templates.append(
            lgm.interface_template_gui(
                layout = 'horizontal',
                widgets = ['button_set'], 
                bindings = [[self._serve_socket,
                    self._close_socket,self._accept_work]], 
                labels = [['Serve Clients On Socket',
                    'Close Server Socket','Accept Client Jobs']]))
        server_templates.append(
            lgm.interface_template_gui(
                widgets = ['button_set'], 
                bindings = [[self._query_workers]], 
                labels = [['Query Workers']]))
        server_templates.append(
            lgm.interface_template_gui(
                widgets = ['button_set'], 
                bindings = [[self._resume_workers]], 
                labels = [['Resume Workers']]))
        server_templates.append(
            lgm.interface_template_gui(
                widgets = ['button_set'], 
                bindings = [[self._pause_workers]], 
                labels = [['Pause Workers']]))
        server_templates.append(
            lgm.interface_template_gui(
                widgets = ['button_set'], 
                bindings = [[self._kill_workers]], 
                labels = [['Stop Workers']]))

        client_templates = []

        monitor_templates = []

        data_source_templates = []
        data_source_templates.append(
            lgm.interface_template_gui(
                widgets = ['button_set'], 
                bindings = [[self._inspect_sources]], 
                labels = [['Inspect Data Sources']]))
        directory_templates = self._data_sources_widget(*args,**kwargs)
        data_source_templates.append(
            lgm.interface_template_gui(
                widgets = ['panel'], 
                #panel_scrollable = True, 
                templates = [directory_templates]))

        #self.widg_templates.append(
        #    lgm.interface_template_gui(
        #        widgets = ['button_set'], 
        #        bindings = [[self._settings]], 
        #        labels = [['Change Settings']]))

        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['tab_book'], 
                handles = [(self,'tab_ref')], 
                pages = [[
                    ('ServerClient',serverclient_templates), 
                    ('Server',server_templates), 
                    ('Clients',client_templates), 
                    ('Monitor',monitor_templates), 
                    ('Data Sources',data_source_templates),
                        ]], 
                initials = [[self.current_tab_index]], 
                instances = [[self]], 
                keys = [['current_tab_index']]))
        self._toolbars(*args,**kwargs)
        lfu.mobject._widget(self,*args,from_sub = True)







