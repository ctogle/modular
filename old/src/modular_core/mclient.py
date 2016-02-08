import modular_core.fundamental as lfu
import modular_core.settings as lset

###
import modular_core.gui.libqtgui as lqg
lgm = lqg.lgm
lgd = lqg.lgd
lgb = lqg.lgb
###

import pdb,os,sys,time,random,multiprocessing,socket,traceback

def valid_port(nport):
    if not nport:return False
    print 'checking validity of port:',nport
    try:
        port = int(nport)
        return True
    except ValueError:return False

def valid_host(nhost):
    if not nhost:return False
    print 'assuming validity of host:',nhost
    return True

# NEED A CONCEPT OF A USER FOR RELOGGING IN LATER
# NEED TO GET JOB RELATED REPLY FOR STATUS QUERY
# NEED TO BE ABLE TO LOOK AT AN MCFG IN STDOUT BEFORE SENDING

# requests can also be issued from the mservers interface
class mclient(lfu.mobject):

    def _settings(self):
        self.settings_manager.display()

    def __init__(self,*args,**kwargs):
        self.settings_manager = lset.settings_manager(
            parent = self,filename = 'mclient_settings.txt')
        self.settings = self.settings_manager.read_settings()
        defport = lset.get_setting('default_port')
        self._default('port',defport,**kwargs)
        defhost = lset.get_setting('default_host')
        self._default('host',defhost,**kwargs)
        defuser = lset.get_setting('default_user')
        self._default('user',defuser,**kwargs)
        self._default('connected',False,**kwargs)
        lfu.mobject.__init__(self,*args,**kwargs)

    def _connect(self,host,port):
        print '\t>\tmclient connecting to mserver on port:',port,'\n'
        c = socket.socket()
        try:
            c.connect((host,self.port))
            ping = self._ping(c)
            if ping:
                self.connected = True
                print '\t>\tmclient successfully connected on port:',port,'\n'
            else:print '\t>\tmclient failed to connect on port:',port,'\n'
        except socket.error:
            traceback.print_exc(file=sys.stdout)
            self.connected = False
            print '\t>\tmclient failed to connect on port:',port,'\n'
        return c

    def _disconnect(self,c):
      if self.connected:
            p = self._ping(c)
            if p:
                c.send('kill')
                c.close() 
                self.connected = False
            else:print '\t>\tserver cannot be disconnected...\n'

    def _ping(self,c):
        if not c is None:
            try:
                c.send('ping:'+self.user)
                p = c.recv(1024)
                if p == '':p = False
                return p
            except socket.error:return False
        else:return False

    def _help(self):
        print '#'*40+'\n\tproviding help on client shell usage...\n'+'#'*40
        print '\n\t\toptions for input:'
        print '\t\t\thelp                   : h'
        print '\t\t\tquit                   : q'
        print '\t\t\tconnect to             : c'
        print '\t\t\tdisconnect from server : d'
        print '\t\t\tping server            : p'
        print '\t\t\tquery job status       : s'
        print '\t\t\tset the host/port      : w'
        print '\t\t\tissue mcfg job         : r\n'
        print '#'*40+'\n\tend help...\n'+'#'*40

    def _status(self,c):
        print '#'*40+'\n\tproviding status of client...\n'+'#'*40
        print '\n\tclient is serving user:',self.user
        print '\tclient is using port:',self.port
        if self.connected:
            print '\tclient is connected to server:',self.host,'\n'
        else:print '\tclient is not connected to server:',self.host,'\n'
        print '#'*40+'\n\tend status report...\n'+'#'*40

    def _listen(self):
        print '\n\t>\tstarting mclient...\n'
        c = self._connect(self.host,self.port)
        print '\n\t>\twelcome to the mclient shell'
        print '\t>\t\tuse "h" for help...'
        while True:
            do = raw_input('\n\tmclient shell :> ')
            if   do == 'h':self._help()
            elif do == 'q':
                c = self._disconnect(c)
                break
            elif do == 'c':
                if self.connected:print '\t>\tmclient is already connected to mserver...'
                else:c = self._connect(self.host,self.port)
            elif do == 'd':
                if self.connected:c = self._disconnect(c)
                else:print '\t>\tmclient is already disconnected from mserver...'
            elif do == 'p':
                if self._ping(c):
                    self.connected = True
                    print '\t>\tclient pinged the server...'
                else:
                    self.connected = False
                    print '\t>\tclient is not connected to server!'
            elif do == 's':self._status(c)
            elif do == 'w':
                nport = raw_input('\n\tnew port? (currently:'+str(self.port)+') :> ')
                if valid_port(nport):self.port = nport
                nhost = raw_input('\n\tnew host? (currently:'+str(self.host)+') :> ')
                if valid_host(nhost):self.host = nhost
                print '\t>\tmclient port:',self.port
                print '\t>\tmclient host:',self.host
            elif do == 'r':
                ping = self._ping(c)
                if ping is False:print '\t>\tclient is not connected to server!'
                else:
                    mfi = raw_input('\n\tmcfg filename? :> ')
                    if os.path.exists(mfi):mpa = mfi
                    else:mpa = lfu.resolve_filepath(mfi)
                    if mpa is None:print '\t>\tfailed to find mcfg:',mfi
                    else:
                        with open(mpa,'r') as mh:
                            mcfgstring = mh.read()
                        c.send('mcfg')
                        c.send(mcfgstring)

        print '\t>\tmclient closing socket...'
        c = self._disconnect(c)
        print '\t>\tmclient socket closed...'
        print '\n\t>\tstopped mclient...\n'

    def get_on_close(self,window):
        def on_close():
            self._kill_workers()
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



        self._toolbars(*args,**kwargs)
        lfu.mobject._widget(self,*args,from_sub = True)










