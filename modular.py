#!python
import modular_core.libfundamental as lfu

import argparse

def run_gui(options):
    lfu.set_gui_pack('modular_core.gui.libqtgui_modular')
    lfu.gui_pack.initialize()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--modules', action = "store_true", 
            default = False, help = 'load/unload modules')
    options = parser.parse_args()
    if options.modules:lfu.handle_modules()
    else:run_gui(options)






