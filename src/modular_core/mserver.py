import modular_core.fundamental as lfu
import modular_core.settings as lset
import modular_core.ensemble as me
import modular_core.mworker as mwk
import modular_core.parameterspace.metamap as mmap

import modular_core.gui.libqtgui as lqg
lgm = lqg.lgm
lgd = lqg.lgd
lgb = lqg.lgb

import pdb,os,sys,time,random,threading,multiprocessing,socket,select,Queue
from cStringIO import StringIO

#################################################################
### functions for hosting a set of clients
#################################################################

def _open_comm(port,mshell,buffsize,msdelim):
    ipipe,isubpipe = multiprocessing.Pipe()
    iargs = (isubpipe,port,mshell,buffsize,msdelim)
    iproc = multiprocessing.Process(target = _listen,args = iargs)
    iproc.start()
    return iproc,ipipe

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

    clients,clientaddrs,users,toremove = [],[],[],[]
    clientcnt = 0
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
            elif request == 'job':
                commpipe.send(mcfgstringqueue.getvalue())
                mcfgstringqueue.close()
                mcfgstringqueue = StringIO()
            elif request == 'who':
                print '\n\tmserver currently has',clientcnt,'clients connected'
                if clientcnt:
                    print '\t\tclient list (index,username,address):'
                    for cx in range(clientcnt):
                        print '\t\t\t',cx,' : ',users[cx],' : ',clientaddrs[cx]
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
            users.append(None)
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
                    elif data == 'ping':
                        c.send('ping!')
                    elif data.startswith('ping:'):
                        u = lfu.msplit(data)[1]
                        users[cx] = u
                        c.send('ping!')
                    elif data == 'mcfg':
                        c.settimeout(10.0)
                        mcfgstring = c.recv(10000)
                        c.settimeout(0.5)
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
                users.pop(torem)
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

class joblistenthread(threading.Thread):

    def __init__(self,queue):
        threading.Thread.__init__(self,
            target = self.keyq,args = (queue,))
        self._stop = threading.Event()
        self.daemon = True
        self.start()

    def keyq(self,q):
        while True:
            q.put(sys.stdin.read(1))
            if self._stop.is_set():
                break

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.is_set()

class mserver(lfu.mobject):

    #############################################################
    ### methods to provide an interface for use without a gui
    #############################################################

    # block and run on a timer, 
    def _accept_work(self):
        mcfgstringqueue = StringIO()

        input_queue = Queue.Queue()
        input_thread = joblistenthread(input_queue)

        last_update = time.time()
        while True:
            time.sleep(0.1)
            if time.time()-last_update > 1.0:
                sys.stdout.write('.')
                last_update = time.time()
                self.ipipe.send('job')
                mcfgstringqueue.write(self.ipipe.recv())
                mcfgs = mcfgstringqueue.getvalue()
                if mcfgs:
                    mcfgs = mcfgs.split(self.mcfgstringdelim)
                    for mcfgstring in mcfgs:
                        if not mcfgstring:continue
                        self._run_mcfgstring(mcfgstring)
                        print '\tmcfg submitted to server...'

                    mcfgstringqueue.close()
                    mcfgstringqueue = StringIO()
                else:print '\tno mcfgs have been submitted by clients'
            if not input_queue.empty():
                keyinp = input_queue.get()
                if keyinp == 'x':
                    print '\ninput:',keyinp
                    input_thread.stop()
                    input_thread.join()
                    break

    def _help(self):
        print '\n'+'#'*40+'\n\tproviding help on server shell usage...\n'+'#'*40
        print '\n\t\toptions for input:'
        print '\t\t\tquit                   : q'
        print '\t\t\thelp                   : h'
        print '\t\t\tprint server log       : l'
        print '\t\t\tinspect data sources   : i'
        print '\t\t\treceive mcfg jobs      : w'
        print '\t\t\tdismiss completed jobs : d'
        print '\t\t\tpause workers          : p'
        print '\t\t\tresume workers         : r'
        print '\t\t\tlist clients           : c'
        print '\t\t\tprint status           : s\n'
        print '#'*40+'\n\tend help...\n'+'#'*40

    def _status(self):
        self.ipipe.send('clientcount')
        clientcnt = self.ipipe.recv()
        workercnt = self.workercnt
        print '\n'+'#'*40+'\n\tproviding status of server...\n'+'#'*40
        print '\n\t',clientcnt,'clients are currently connected\n'
        print '\n\t',workercnt,'workers are currently running\n'
        print '\n\tworker query:\n'
        self._query_workers()
        print '#'*40+'\n\tend status report...\n'+'#'*40

    # _serve_socket and provide a shell to interface
    def _serve_shell(self):
        self._inspect_sources()
        self._serve_socket()
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
                self.ipipe.send('log')
                log = self.ipipe.recv()
                print '\n'+'#'*50+'\n\tserver log:\n'+'#'*50+'\n'
                print log
            elif do == 'i':self._inspect_sources()
            elif do == 'w':self._accept_work()
            elif do == 'd':self._dismiss_work()
            elif do == 'p':self._pause_workers()
            elif do == 'r':self._resume_workers()
            elif do == 'c':
                self.ipipe.send('who')
                ready = self.ipipe.recv()
            elif do == 's':self._status()

    #############################################################
    #############################################################
    #############################################################

    #############################################################
    ### methods to start/stop serving clients on tcp sockets
    #############################################################

    # serve on a socket via a gui
    def _serve_socket(self):
        self.iproc,self.ipipe = _open_comm(
            self.port,self.clientserver_mshell,
            self.buffersize,self.mcfgstringdelim)
        iready = self.ipipe.recv()

    # close the server socket
    def _close_socket(self):
        self.ipipe.send('kill')
        self.iproc.join()

    #############################################################
    #############################################################
    #############################################################

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
        self._default('workercnt',0,**kwargs)
        self._default('tickets',{},**kwargs)
        self.mnger = me.ensemble_manager()
        lfu.mobject.__init__(self,*args,**kwargs)
        self.current_tab_index = 0

    #############################################################
    #############################################################
    #############################################################

    #############################################################
    ### methods for interacting with the existing data sources
    #############################################################

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

    # inspect one data source (directory)
    # keep track of its hdf5 and pkl files
    # host any metamaps found (create an associated worker)
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

    #############################################################
    #############################################################
    #############################################################

    #############################################################
    ### methods for using mworkers
    #############################################################

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
        newworker = mwk.mworker(self.module,mcfgstring,metamap)
        self.maprings[metamap.uniqueness] = newworker
        self.workercnt += 1
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
        print 'workers are being paused...'
        for mwuq in self.maprings:
            self.maprings[mwuq]._pause()
        time.sleep(0.1)

    # resume all mworkers
    def _resume_workers(self):
        print 'workers are being resumed...'
        for mwuq in self.maprings:
            self.maprings[mwuq]._resume()
        time.sleep(0.1)

    # query all workers on their work
    def _query_workers(self):
        print 'workers are being queried...'
        if not self.maprings:print 'no workers to query...\n'
        else:
            for mwuq in self.maprings:
                self.maprings[mwuq]._query_all()
            time.sleep(0.1)

    # remove completed work from mworkers
    def _dismiss_work(self):
        print 'completed work is being dismissed...'
        if not self.maprings:print 'no workers to query...\n'
        else:
            for mwuq in self.maprings:
                mwstatus = self.maprings[mwuq]._update()
            time.sleep(0.1)

    #############################################################
    #############################################################
    #############################################################

    #############################################################
    ### methods for issuing tickets to the server
    ### each ticket will associate with one metamap, and 
    ###     with one mworker which will generate its results
    #############################################################

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
        #pdb.set_trace()
        msrc = lfu.get_mapdata_pool_path()

        worker = self._host_map(msrc,metamap)
        return self._run_ensem(worker,ensem,mcfgstring)

    # generate a ticket for a worker,ensemble,mcfgstring
    def _run_ensem(self,worker,ensem,mcfgstring):
        ticketnumber = random.randint(1000000,9000000)
        ticket = worker._new_request(ticketnumber,ensem)
        self.tickets[ticketnumber] = ticket
        self._start_worker(worker,mcfgstring)
        time.sleep(0.1)
        return ticketnumber

    #############################################################
    #############################################################
    #############################################################

    #############################################################
    ### all code to generate gui related objects
    #############################################################

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
            bindings = lgb.create_reset_widgets_wrapper(
                window,self.settings_manager.display),
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

#################################################################
#################################################################
#################################################################










