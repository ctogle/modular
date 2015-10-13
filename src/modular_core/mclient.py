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

# requests can also be issued from the mservers interface
class mclient(lfu.mobject):

    TCP_IP = '127.0.0.1'
    #TCP_PORT = 5005
    TCP_PORT = 12397
    BUFFER_SIZE = 128
    MESSAGE = "Hello, World!"

    def _settings(self):
        self.settings_manager.display()

    def _hw(self,c):
        c.send('hello, world!')

    def __init__(self,*args,**kwargs):
        self.settings_manager = lset.settings_manager(
            parent = self,filename = 'mclient_settings.txt')
        self.settings = self.settings_manager.read_settings()
        defport = lset.get_setting('default_port')
        self._default('port',defport,**kwargs)
        defhost = lset.get_setting('default_host')
        self._default('host',defhost,**kwargs)
        self._default('connected',False,**kwargs)
        lfu.mobject.__init__(self,*args,**kwargs)

    def _connect(self,host,port):
        print 'mclient connecting to mserver on port:',port
        c = socket.socket()
        try:
            c.connect((host,self.port))
            self._hw(c)
            self.connected = True
            print 'mclient successfully connected on port:',port
        except socket.error:
            traceback.print_exc(file=sys.stdout)
            self.connected = False
            print 'mclient failed to connect on port:',port
        return c

    def _disconnect(self,c):
      if self.connected:
            p = self._ping(c)
            if p:
                c.send('kill')
                c.close() 
                self.connected = False
            else:print 'server cannot be disconnected...'

    def _ping(self,c):
        if not c is None:
            try:
                c.send('ping')
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
        print '\n\t\tmclient status!\n',self.connected

    def _listen(self):
        c = self._connect(self.host,self.port)
        print '\n\twelcome to the mclient shell'
        print '\n\t\tuse "h" for help...'
        while True:
            do = raw_input('\n\tmclient shell:>\t')
            if   do == 'h':self._help()
            elif do == 'q':
                c = self._disconnect(c)
                break
            elif do == 'c':
                if self.connected:print 'mclient is already connected to mserver...'
                else:c = self._connect(self.host,self.port)
            elif do == 'd':
                if self.connected:c = self._disconnect(c)
                else:print 'mclient is already disconnected from mserver...'
            elif do == 'p':
                if self._ping(c):
                    self.connected = True
                    print 'client pinged the server...'
                else:
                    self.connected = False
                    print 'client is not connected to server!'
            elif do == 's':self._status(c)
            elif do == 'w':
                nport = raw_input('\n\tnew port? (currently:'+str(self.port)+'):>\t')
                if valid_port(nport):self.port = nport
                nhost = raw_input('\n\tnew host? (currently:'+str(self.host)+'):>\t')
                if valid_host(nhost):self.host = nhost
                print '\tmclient port:',self.port
                print '\tmclient host:',self.host
            elif do == 'r':
                ping = self._ping(c)
                if ping is False:print 'client is not connected to server!'
                else:
                    mfi = raw_input('\n\tmcfg filename?:>\t')

                    c.send('mcfg')
                    c.send('THE MCFGSTRING!!')

                    #if not os.path.exists(self.mcfg_path):
                    #    return
                    #with open(self.mcfg_path,'r') as mh:mcfgstring = mh.read()
                    #return mcfgstring

        print 'mclient closing socket...'
        c = self._disconnect(c)
        print 'mclient socket closed...'

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










