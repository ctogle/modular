### libfundamental is importable from anywhere in modular
import pdb,os,sys,traceback,time,types,appdirs,importlib,copy
import numpy as np

###############################################################################
### mobject is the base class of modular_core
###############################################################################

mobjects = [0]
def mobject_id():
    lastid = mobjects[-1]
    return lastid + 1

def mobject_name():
    lastid = mobjects[-1]
    return '__mobject_' + str(lastid)

class mobject(object):

    # represent the mobject as a string
    def _string(self):
        info = [self.tag,self.name,str(self._id)]
        return ' : '.join(info)

    # add attribute prop if it is not already an attribute
    #  use kwargs[prop] if present, defv if not
    def _default(self,prop,defv,**kwargs):
        if not prop in self.__dict__.keys():
            if prop in kwargs.keys():propval = kwargs[prop]
            else:propval = defv
            self.__dict__[prop] = propval

    def __init__(self,*args,**kwargs):
        # _id is unique and never changes
        self._default('_id',None,**kwargs)
        if self._id is None:self._id = mobject_id()
        elif self._id in mobjects.keys():self._id = mobject_id()
        mobjects.append(self._id)
        # name is user chosen
        self._default('name',None,**kwargs)
        if self.name is None:self.name = mobject_name()
        # tag is not; implicitly groups mobjects
        self._default('tag','mobject',**kwargs)
        self._default('parent',None,**kwargs)
        self._default('children',[],**kwargs)
        self._default('rewidget',True,**kwargs)

        self.widg_handles = []

    # display this mobjects widgets in a separate window
    def _display(self,mason,geometry = (150,120,384,512),templates = None):
        if templates is None:templates = self.widg_dialog_templates
        lgb = gui_pack.lgb
        gear_icon = get_resource_path('gear.png')
        self.panel = lgb.create_scroll_area(
            lgb.create_panel(templates,mason))
        self.panel.setWindowIcon(lgb.create_icon(gear_icon))
        self.panel.setGeometry(*geometry)
        for temp in self.widg_dialog_templates:
            if hasattr(temp,'panel_label'):
                self.panel.setWindowTitle(temp.panel_label)
                break
        self.panel.show()

    # remove all pkl/mp offenseive object references
    # this is required for multithreading the gui and saving ensembles
    def _sanitize(self,*args,**kwargs):
        if not ('from_sub' in kwargs.keys() and kwargs['from_sub']):
            self.panel = None
            self.widg_dialog_templates = []
            self.widg_templates = []
            self.menu_templates = []
            self.tool_templates = []
            for handle in self.widg_handles:
                handle[0].__dict__[handle[1]] = None
            self.widg_handles = []
            self._rewidget(True)
            if ('propagate' in kwargs.keys() and kwargs['propagate']):
                for c in self.children:c._sanitize(*args,**kwargs)

    # set whether this mobject needs its widgets remade
    # supports the mobject hierarchy
    def _rewidget(self,rw = None,**kwargs):
        if rw is None:
            self._rewidget_children(**kwargs)
            return self.rewidget
        else:
            self.rewidget = rw
            if self.rewidget and not self.parent is None:
                if not self.parent.rewidget:
                    self.parent._rewidget(self.rewidget)

    # helper function for mobject hierarchy support
    def _rewidget_children(self,*args,**kwargs):
        for child in self.children:
            if child._rewidget(**kwargs):
                child._widget(*kwargs['infos'])

    # recalculate the mobjects widget related information
    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self._rewidget(False)
        self.widg_templates.reverse()

# plan is a glorified function which inherits from mobject
class plan(mobject):

    def __init__(self,*args,**kwargs):
        self._default('name','aplan',**kwargs)
        self._default('use_plan',False,**kwargs)
        mobject.__init__(self,*args,**kwargs)

    def _enact(self,*args,**kwargs):pass

    def __call__(self,*args,**kwargs):
        return self._enact(*args,**kwargs)

###############################################################################
###############################################################################

###############################################################################
### utility classes/functions
###############################################################################

# inspecfic container for any sort of information
class data_container(object):

    def _default(self,prop,defv,**kwargs):
        if not prop in self.__dict__.keys():
            if prop in kwargs.keys():propval = kwargs[prop]
            else:propval = defv
            self.__dict__[prop] = propval

    def __init__(self, *args, **kwargs):
        self.args = args
        for key in kwargs.keys():
            self.__dict__[key] = kwargs[key]

def gather_string(msg,title):
    if using_gui:
        stringdlg = gui_pack.lgd.create_dialog(
            title = title,message = msg,variety = 'input')
        string = stringdlg()
    else:string = raw_input(msg)
    return string

user_cache_path = None
default_cache_path = os.path.join(appdirs.user_cache_dir(),'modular_cache')
# resolve full cached resource path from resource filename
def get_cache_path(res = None):
    if user_cache_path is None:cpath = default_cache_path
    else:cpath = user_cache_path
    if res is None:return cpath
    else:return os.path.join(cpath,res)
sys.path.append(get_cache_path())

# change the user cache path, modifying sys.path as needed
def set_cache_path(cpath = None):
    global user_cache_path
    current = get_cache_path()
    if current in sys.path:sys.path.remove(current)
    if not cpath is None:user_cache_path = cpath
    sys.path.append(get_cache_path())
    if not os.path.exists(get_cache_path()):
        os.mkdir(get_cache_path())

# resolve full resource path from resource filename
def get_resource_path(res = None):
    rpath = os.path.join(appdirs.user_config_dir(),'modular_resources')
    if res is None: return rpath
    else: return os.path.join(rpath,res)

user_data_pool_path = None
default_data_pool_path = os.path.join(
    appdirs.user_data_dir(),'modular_data_pools')
# return path to a safe place to store temporary data
def get_data_pool_path():
    if user_data_pool_path is None:dpath = default_data_pool_path
    else:dpath = user_data_pool_path
    return dpath

# return path to a safe place to store persistent pspace mapping data
def get_mapdata_pool_path():
    return os.path.join(get_data_pool_path(),'mapdata')

# return default directory for mcfgs
def get_mcfg_path():
    lset = sys.modules['modular_core.settings']
    mpath = lset.get_setting('mcfg_path')
    if not mpath is None and not os.path.exists(mpath):
        print 'invalid default mcfg path - using working directory'
        mpath = os.getcwd()
    return mpath

# return default directory for output
def get_output_path():
    lset = sys.modules['modular_core.settings']
    opath = lset.get_setting('default_output_path')
    if opath is None or not os.path.exists(opath):
        print 'invalid default output path - using working directory'
        opath = os.getcwd()
    return opath

# attempt to locate a file by looking in the cwd recursively
def resolve_filepath(filename, isdir = False):
    def dir_check(root, dirs, files):
        for dir_ in dirs:
            if dir_ == filename:
                found = os.path.abspath(os.path.join(root, dir_))
                return found
    def fil_check(root, dirs, files):
        for name in files:
            if name == filename:
                found = os.path.abspath(os.path.join(root, name))
                return found
    if isdir: check = dir_check
    else: check = fil_check
    for root, dirs, files in os.walk(os.getcwd()):
        found = check(root, dirs, files)
        if found: return found

logfile = get_resource_path('mlog.txt')
if not os.path.isfile(logfile):
    with open(logfile,'w') as log:
        log.write('\n\n\n'+'='*80+'\nmodular log\n'+'='*80+'\n\n\n')
        stimepretty = time.strftime(
            '%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        log.write('\tstarted:'+stimepretty+'\n\n\n')

# either raise a notification dialog or notify on the command line
# require use to press something to continue
def complain(msg):
    if using_gui:
        complaint = gui_pack.lgd.message_dialog(None,msg,'Problem')
    else:
        print '\nProblem:\n\t'+msg
        raw_input('\n')

# log the last traceback or a provided message
def log(msg = None,trace = True):
    if msg is None:
        if trace:
            with open(logfile,'a') as log:
                traceback.print_exc(file = log)
            return
        else:msg = '\n...null-log...\n'
    with open(logfile,'a') as log:log.write(msg)

# return whether or not the current os is os_
def using_os(os_):
    if os_ == 'windows' and (sys.platform.startswith('win') or\
                sys.platform.startswith('cygwin')): return True
    elif os_ == 'mac' and sys.platform.startswith('darwin'): return True
    elif os_ == 'linux' and sys.platform.startswith('linux'): return True
    else: return False

def nearest_index(num,vals):
    if num > vals[-1]:return len(vals)-1
    elif num < vals[0]:return 0
    delts = [abs(val-num) for val in vals]
    where = delts.index(min(delts))
    return where

def nearest(num,vals):
    where = nearest_index(num,vals)
    found = vals[where]
    return found

# return True if floats a,b are within 10**-20 of one another
def near(a,b):
    if abs(a-b) < 10**-20:return True
    else:return False

orders = [10**k for k in [val - 20 for val in range(40)]]
def coerce_float_magnitude(fl):
    return nearest(fl,orders)

def order_span(x0,x1):
    t0 = orders.index(nearest(x0,orders))
    t1 = orders.index(nearest(x1,orders))
    span = orders[t0:t1+1]
    return span

# divide each element by the max of a list, if its valid
def normalize(values,r = None):
    if not values:return values
    m = max(values)
    if m == 0:return values
    normed = [val/m for val in values]
    if not r is None:
        normed = [np.round(n,r) for n in normed]
    return normed

# keep the value val bounded by bot and top
def clamp(val,bot,top):
    if val < bot: return bot
    elif val > top: return top
    else: return val

# keep the value val bounded by bot and top by wrapping around
def clamp_periodic(val, min_, max_):
    period = max_ - min_
    while val < min_: val += period
    while val > max_: val -= period
    else: return val

# break an input string by delimiter de and strip results
def msplit(st,de = ':'):
    return [l.strip() for l in st.split(de)]

def parse_range_di(rng):
    interval = float(rng[rng.rfind(';')+1:])
    front = float(rng[:rng.find('-')])
    back = float(rng[rng.find('-')+1:rng.find(';')])

    #pdb.set_trace()

    return np.linspace(front,back,interval)

def parse_range_dni(rng):
    interval = 1.0
    front = float(rng[:rng.find('-')])
    back = float(rng[rng.find('-')+1:])+1.0
    return np.linspace(front,back,interval)

def parse_range_ndni(rng):
    return [float(v) for v in msplit(rng,',')]

# turn an mcfg string representing a 
#   set of values into an array of floats
#   accepts several formats:
#     x - y ; z       #from x to y with z values
#     x - y           #from x to y with int(y-x) values
#     x,y,...,z       #from x to z with all values specified in between
#     x - y ; log ; z
def parse_range(rng):
    if '-' in rng and ';' in rng:return parse_range_di(rng)
    elif '-' in rng and not ';' in rng:return parse_range_dni(rng)
    elif not '-' in rng and not ';' in rng:return parse_range_ndni(rng)
    else:print 'unsupported parse_range input format:',rng

# return a list of all things found in a list of lists of things
def flatten(unflat_list):
    return [item for sublist in unflat_list for item in sublist]

# return a copy of seq without duplicates; preserves order
def uniqfy(seq):
    seen = {}
    result = []
    for item in seq:
        if item in seen: continue
        seen[item] = 1
        result.append(item)
    return result

# modify the lists in lists in place so that they 
# are all of equal length to the longest
def fill_lists(lists, fill = None):
    length = max([len(li) for li in lists])
    for li in lists:
        if len(li) < length:
            li.extend([fill]*(length - len(li)))

# translate various strings to bools
def coerce_string_bool(string):
    true_strings = ['true', 'True', 'On', 'on']
    false_strings = ['false', 'False', 'Off', 'off']
    string = string.strip()
    if string in true_strings: return True
    elif string in false_strings: return False

# convert width,height to a size that should looks good
def convert_pixel_space(width,height,screensize = None):
    if screensize is None:screensize = gui_pack.lgb.screensize()
    good_width = 1920.0
    good_height = 1080.0
    (runtime_width, runtime_height) =\
        (screensize.width(),screensize.height())
    width_conversion = runtime_width / good_width
    height_conversion = runtime_height / good_height
    w_size = width * width_conversion
    h_size = height * height_conversion
    return w_size, h_size

# break up a very long string into a paragraph
def pagify(lines, max_leng = 30):
    def validate(line):
        splits = int(len(line) / max_leng)
        for k in range(1, splits + 1):
            line = insert_substring(line, '\n', k*max_leng)
        return line
    for line in lines:line = validate(line)
    return '\n'.join(lines)

# return a list of elements found in both list1 and list2
def intersect_lists(list1,list2):
    list1 = [item for item in list1 if item in list2]
    return uniqfy(list1)

# insert substring into string as position index
def insert_substring(string, substring, index):
    return string[:index] + substring + string[index:]

# retrieve a mobject from a dict/list given its name
def grab_mobj_by_name(name,mobj_collection):
    if type(mobj_collection) == types.ListType:
        return grab_mobj_from_list_by_name(name, mobj_collection)
    elif type(mobj_collection) == types.DictionaryType:
        return grab_mobj_from_dict_by_name(name, mobj_collection)

def grab_mobj_from_dict_by_name(name,mobj_dict):
    return mobj_dict[name]

def grab_mobj_from_list_by_name(name,mobj_list):
    return mobj_list[[mobj.name for mobj in mobj_list].index(name)]

# retrieve mobject names from dict/list of mobjects
def grab_mobj_names(mobj_collection):
    if type(mobj_collection) == types.ListType:
        return grab_mobj_list_names(mobj_collection)
    elif type(mobj_collection) == types.DictionaryType:
        return grab_mobj_dict_names(mobj_collection)

def grab_mobj_list_names(mobj_list):
    return [mobj.name for mobj in mobj_list]

def grab_mobj_dict_names(mobj_dict):
    return [mobj_dict[key].name for key in mobj_dict.keys()]

# identify mobject by index in dict/list of mobjects
def grab_mobj_index_by_name(name,collection):
    mobject_names = grab_mobj_names(collection)
    which = None
    for mnd in range(len(mobject_names)):
        if mobject_names[mnd] == name:
            return which

###############################################################################
### simulation module classes/functions
###############################################################################

# a run_parameter is any input to a simulation
###  it gets parameter space support, gui support, parsing support
class run_parameter(mobject):

    def __init__(self,*args,**kwargs):
        self._default('pspace_axes',[],**kwargs)
        mobject.__init__(self,*args,**kwargs)

    # should be called on each run parameter before running the simulation
    def _initialize(self,*args,**kwargs):pass

    # return a string representing this parameter in a simulation format
    #  expectation that simulation may require encoding as string
    #     this is what happens in stringchemical
    def _sim_string(self,*args,**kwargs):return ''

    # return a string representing this parameter in an mcfg format
    def _string(self,*args,**kwargs):return '\n'

    # a run_parameter treats its pspace_axes as children
    def _rewidget_children(self,*args,**kwargs):
        for pax in self.pspace_axes:
            if pax._rewidget(**kwargs):
                pax._widget(*kwargs['infos'])
        mobject._rewidget_children(self,*args,**kwargs)

# read the list of installed/registered simulation modules
def list_simulation_modules():
    listing = [item for item in parse_module_registry()]
    return listing

# return list of module information
def parse_module_registry():
    reg_path = get_resource_path('module_registry.txt')
    with open(reg_path, 'r') as handle:reg = handle.readlines()
    reg = [line for line in reg if 
        not line.startswith('#') and not line.strip() == '']
    reg = [[pa.strip() for pa in line.split(':')] for line in reg]
    return reg

# test whether mod is valid as a modular plugin
def is_module_valid(mod):
    try: mo = __import__(mod)
    except ImportError:
        print 'module', mod, 'is not installed!'
        return False
    if not hasattr(mo,'main'):
        print 'module',mod,'is missing "main" namespace'
        return False
    if not hasattr(mo.main,'module_name'):
        print 'module',mod,'is missing "module_name" attribute'
        return False
    return True

# add a simulation module to the module registry
def add_module_to_registry(module_name):
    print 'mrp', mod_registry_path
    if is_module_valid(module_name):
        with open(mod_registry_path, 'r') as handle:
            reg = handle.readlines()
            comments = [line for line in reg if line.startswith('#')]
            registered = [line for line in reg if 
                not line.startswith('#') and not line.strip() == '']
            registered.append('\n' + module_name)
        with open(mod_registry_path, 'w') as handle:
            lines = comments + ['\n\n'] + registered
            [handle.write(line) for line in lines]
        return True     
    else: return False

# remove a simulation module from the module registry
def remove_module_from_registry(module_name):
    with open(mod_registry_path, 'r') as handle:
        reg = handle.readlines()
        if not module_name in reg:
            print 'module', module_name, 'not found in registry!'
            return False
        comments = [line for line in reg if line.startswith('#')]
        registered = [line for line in reg if 
            not line.startswith('#') and not line.strip() == '' 
            and not line.startswith(module_name)]
    with open(mod_registry_path, 'w') as handle:
        lines = comments + ['\n\n'] + registered
        [handle.write(line) for line in lines]
    return True

# command line interface for loading/unloading simulation modules
def handle_modules():
    mods = [m[0] for m in parse_module_registry()]
    mod_count = len(mods)
    input_ = ':'
    while not input_ == '-q':
        print 'you may add or remove modules from the registry'
        print 'currently there are', mod_count, 'modules available'
        print 'they are:'
        for mod in mods: print '\t', mod
        print '\n-a <module> : attempt to add module <module>'
        print '-r <module> : attempt to remove module <module>'
        print '\n-q          : quit'
        input_ = raw_input(':::: ').strip()
        if input_.startswith('-a '):
            mod = input_[3:]
            added = add_module_to_registry(mod)
            print '-'*50
            if added: print '\nmodule', mod, 'was successfully added\n'
            else: print '\nmodule', mod, 'could not be added...\n'
            print '-'*50
        elif input_.startswith('-r '):
            mod = input_[3:]
            removed = remove_module_from_registry(mod)
            print '-'*50
            if removed: print '\nmodule', mod, 'was successfully removed\n'
            else: print '\nmodule', mod, 'could not be removed...\n'
            print '-'*50
        elif not input_ == '-q':
            print '-'*50,'\ninput not recognized... :',input_,'\n'+'-'*50
        mods = [m[0] for m in parse_module_registry()]
    print '\n\tfinished editing module registry!\n\n'

###############################################################################
###############################################################################

gui_pack = None
using_gui = False

# set global reference to a gui_pack
def set_gui_pack(pack = None):
    global gui_pack
    packed = issubclass(gui_pack.__class__,data_container)
    #notpacked = issubclass(gui_pack.__class__,data_container) or pack is None
    #if pack is None:
    if not packed or not pack is None:
	if using_gui:
            if pack is None:pack = 'modular_core.gui.libqtgui'
    	    gui_pack = importlib.import_module(pack)
    	else:gui_pack = data_container(lgm = None,lgb = None,lgd = None,lgq = None)

    #notpacked = issubclass(gui_pack.__class__,data_container) or pack is None
    #if notpacked and using_gui:
    #    if pack is None:pack = 'modular_core.gui.libqtgui'
    #    gui_pack = importlib.import_module(pack)
    #else:gui_pack = data_container(lgm = None,lgb = None,lgd = None,lgq = None)

# set global reference to gui_pack if it is None
def check_gui_pack():
    global gui_pack
    if gui_pack is None:
        set_gui_pack()

###############################################################################
###############################################################################

core_settings_path = get_resource_path('modular_settings.txt')
mod_registry_path = get_resource_path('module_registry.txt')

###############################################################################
if __name__ == 'modular_core.fundamental':pass
if __name__ == '__main__':print 'libfundamental of modular_core'
###############################################################################










