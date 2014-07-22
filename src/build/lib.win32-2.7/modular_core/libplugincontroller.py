import libs.modular_core.libfundamental as lfu

import pdb

import imp, os

plugin_dir = os.path.join(os.getcwd(), 'libs', 'modules')
MainModule = "__init__"

def getPlugins():
	plugins = []
	possibleplugins = os.listdir(PluginFolder)
	for i in possibleplugins:
		location = os.path.join(PluginFolder, i)
		if not os.path.isdir(location) or not MainModule + ".py" in os.listdir(location):
			continue
		info = imp.find_module(MainModule, [location])
		plugins.append({"name": i, "info": info})
	return plugins

def loadPlugin(plugin):
	return imp.load_module(MainModule, *plugin["info"])

if __name__ == '__main__':
	print 'This is a library!'

if __name__ == 'libs.modular_core.libplugincontroller':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb


