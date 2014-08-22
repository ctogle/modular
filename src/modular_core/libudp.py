import libs.modular_core.libfundamental as lfu

import socket
import thread
import time

import pdb

default_udp_port = 9999
default_buffer_size = 1024
default_socket_ip = '127.0.0.1'

class receiver(lfu.modular_object_qt):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #socket_ip = default_socket_ip
    socket_port = default_udp_port
    buffer_size = default_buffer_size
    bound = False
    parent = None

    def __init__(self, *args, **kwargs):
        if 'default_IP' in kwargs.keys():
            self.socket_ip = kwargs['default_IP']
        else: self.socket_ip = default_socket_ip
        lfu.modular_object_qt.__init__(self, *args, **kwargs)

    def listen(self, *args, **kwargs):
        thread.start_new_thread(self.open_socket, args, **kwargs)

    def handle_socket_binding(self):
        time_out = 0
        while not self.bound:
            try:
                self.sock.bind((self.socket_ip, self.socket_port))
                self.bound = True
                print 'bound', self.bound

            except:
                if time_out < 5:
                    print 'socket could not bind; retrying...'
                    time_out += 1
                    time.sleep(2)

                else:
                    print 'socket binding timed out; giving up!'
                    return False

    def open_socket(self, *args, **kwargs):
        self.handle_socket_binding()
        self._received_ = []
        while True:
            data, addr = self.sock.recvfrom(self.buffer_size)
            self._received_.append(data)
            if hasattr(self.parent, 'interpret_udp'):
                self.parent.interpret_udp(data)
            else: print 'receiver parent has no interpret_UDP method!'
            #print 'received message:', data
            time.sleep(0.5)

    def set_settables(self, *args, **kwargs):
        window = args[0]
        self.handle_widget_inheritance(*args, **kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['button_set', 'text'], 
                labels = [['Start Receiver'], None], 
                initials = [None, [self.socket_ip]], 
                tooltips = [None, ['use ipconfig \n\
                        to determine proper ip']], 
                alignments = [None, ['center']], 
                max_lengths = [None, [16]], 
                instances = [None, [self]], 
                keys = [None, ['socket_ip']], 
                bindings = [[self.listen], None]))
        lfu.modular_object_qt.set_settables(
                self, *args, from_sub = True)

class transceiver(lfu.modular_object_qt):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #socket_ip = default_socket_ip
    socket_port = default_udp_port
    buffer_size = default_buffer_size
    message = 'hello world!'

    def __init__(self, *args, **kwargs):
        if 'default_IP' in kwargs.keys():
            self.socket_ip = kwargs['default_IP']
        else: self.socket_ip = default_socket_ip
        lfu.modular_object_qt.__init__(self, *args, **kwargs)

    def speak(self, *args, **kwargs):
        if 'message' in kwargs.keys(): message = kwargs['message']
        else: message = self.message
        thread.start_new_thread(self.open_socket, (message, ))
        #is this starting many threads or are they closing?

    def open_socket(self, *args, **kwargs):
        message = args[0]
        sock_message = (message, (self.socket_ip, self.socket_port))
        self.sock.sendto(*sock_message)

    def set_settables(self, *args, **kwargs):
        window = args[0]
        self.handle_widget_inheritance(*args, **kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['button_set'], 
                labels = [['Talk To The Aether']], 
                bindings = [[self.speak]]))
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['text'], 
                initials = [[self.socket_ip]], 
                tooltips = [['use ipconfig \n\
                    to determine proper ip']], 
                alignments = [['center']], 
                #minimum_sizes = [[(150, 150)]], 
                #keep_frame = [True], 
                max_lengths = [[16]], 
                instances = [[self]], 
                keys = [['socket_ip']]))
                #bind_events = [['returnPressed', 'textEdited']]))
        lfu.modular_object_qt.set_settables(
                self, *args, from_sub = True)

if __name__ == 'libs.modular_core.libudp':
    if lfu.gui_pack is None: lfu.find_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb

if __name__ == '__main__':
    print 'this is a library!'




