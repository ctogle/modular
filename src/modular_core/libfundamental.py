
__doc__ = '''fundamental functions/classes of modular_core'''

import pdb,os,sys,types,appdirs,importlib

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

    def _string(self):
        info = [self.tag,self.name,str(self._id)]
        return ' : '.join(info)

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

    def _sanitize(self,*args,**kwargs):
        if not ('from_sub' in kwargs.keys() and kwargs['from_sub']):
            self.pspace_templates = []
            self.widg_templates = []
            self.menu_templates = []
            self.tool_templates = []
            for handle in self.widg_handles:
                handle[0].__dict__[handle[1]] = None
            self.widg_handles = []
            self._rewidget(True)

    def _rewidget(self,rw = None,**kwargs):
        if rw is None:
            self._rewidget_children(**kwargs)
            return self.rewidget
        else:
            self.rewidget = rw
            if self.rewidget and not self.parent is None:
                if not self.parent.rewidget:
                    self.parent._rewidget(self.rewidget)

    def _rewidget_children(self, *args, **kwargs):
        for child in self.children:
            if child._rewidget(**kwargs):
                child._widget(*kwargs['infos'])

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self._rewidget(False)
        self.widg_templates.reverse()

# plan is a glorified function which inherits from mobject
class plan(mobject):

    def __init__(self,*args,**kwargs):
        self._default('name','aplan',**kwargs)
        self._default('use_plan', False, **kwargs)
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
    def __init__(self, *args, **kwargs):
        self.args = args
        for key in kwargs.keys():
            self.__dict__[key] = kwargs[key]

# resolve full resource path from resource filename
def get_resource_path(res = None):
    rpath = os.path.join(appdirs.user_config_dir(),'modular_resources')
    if res is None: return rpath
    else: return os.path.join(rpath,res)

# return path to a safe place to store temporary data
def get_data_pool_path():
    return os.path.join(appdirs.user_data_dir(),'modular_data_pools')

# return default directory for mcfgs
def get_mcfg_path():
    lset = sys.modules['modular_core.libsettings']
    mpath = lset.get_setting('mcfg_path')
    if not mpath is None and not os.path.exists(mpath):
        print 'invalid default mcfg path - using working directory'
        mpath = os.getcwd()
    return mpath

# return default directory for output
def get_output_path():
    lset = sys.modules['modular_core.libsettings']
    opath = lset.get_setting('default_output_path')
    if not opath is None and not os.path.exists(opath):
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

# return whether or not the current os is os_
def using_os(os_):
    if os_ == 'windows' and (sys.platform.startswith('win') or\
                sys.platform.startswith('cygwin')): return True
    elif os_ == 'mac' and sys.platform.startswith('darwin'): return True
    elif os_ == 'linux' and sys.platform.startswith('linux'): return True
    else: return False

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
    return mobj_list[[mobj.label for mobj in mobj_list].index(name)]

# retrieve mobject names from dict/list of mobjects
def grab_mobj_names(mobj_collection):
    if type(mobj_collection) == types.ListType:
        return grab_mobj_list_names(mobj_collection)
    elif type(mobj_collection) == types.DictionaryType:
        return grab_mobj_dict_names(mobj_collection)

def grab_mobj_list_names(mobj_list):
    return [mobj.label for mobj in mobj_list]

def grab_mobj_dict_names(mobj_dict):
    return [mobj_dict[key].label for key in mobj_dict.keys()]

# identify mobject by index in dict/list of mobjects
def grab_mobj_index_by_name(name,collection):
    mobject_names = grab_mobj_names(collection)
    which = None
    for mnd in range(len(mobject_names)):
        if mobject_names[mnd] == name:
            return which

###############################################################################
### simulation module functions
###############################################################################

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
    while not input_ == 'q':
        print 'you may add or remove modules from the registry'
        print 'currently there are', mod_count, 'modules available'
        print 'they are:'
        for mod in mods: print '\t', mod
        print '\n-a <module> will attempt to add module <module>'
        print '-r <module> will attempt to remove module <module>\n'
        input_ = raw_input('\n:::: ').strip()
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
        elif not input_ == 'q':
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
    if pack is None:pack = 'modular_core.gui.libqtgui'
    gui_pack = importlib.import_module(pack)

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
if __name__ == 'modular_core.libfundamental':pass
if __name__ == '__main__':print 'libfundamental of modular_core'
###############################################################################










###############################################################################

class modular_object_qt________(object):
    __doc__ = """fundamental class used in modular"""
    rewidget_ = True
    _p_sp_bounds_ = []
    _children_ = []
    _handles_ = []
    data = []
    visible_attributes = []

    def _display_interface_(self, mason):
        lgb = gui_pack.lgb
        self.set_settables()
        self.panel = lgb.create_scroll_area(
            lgb.create_panel(self.widg_templates, mason))
        if hasattr(self, '_geometry_'): geometry = self._geometry_
        else: geometry = (150, 120, 384, 512)
        self.panel.setGeometry(*geometry)
        self.panel.show()

    def _examine_(self): pdb.set_trace()

    def _restore_label_pool_(self):
        for child in self._children_:
            if hasattr(child, '_children_'):
                child._restore_label_pool_()

        try:
            if not self.label is 'mobj__':
                self._label = unique_label(self.label)
                label_pool.append(self.label)

        except: pdb.set_trace()

    def _set_label_(self, value):
        global label_pool
        if not value == self._label and not value.startswith('mobj__'):
            try: label_pool.remove(self._label)
            except ValueError: pass
            self._label = unique_label(value)
            label_pool.append(self._label)
            label_pool = uniqfy(label_pool)
            return True

        else: return False

    def _get_label_(self): return self._label
    label = property(_get_label_, _set_label_, 
        'assumed unique modular object label')

    def _destroy_(self, *args, **kwargs):
        #print 'destroyed', self
        global label_pool
        for child in self._children_:
            if child is self: pdb.set_trace()
            child._destroy_()
        if hasattr(self, '_label') and self._label in label_pool:
            label_pool.remove(self._label)

        label_pool = uniqfy(label_pool)
        del self

    def _q_purge_(self):
        for child in self._children_: child._q_purge_()
        for item in [type(di) for di in dir(self)]:
            if repr(item).count('PySide') > 0: pdb.set_trace()

    def change_settings(self):
        if hasattr(self, 'settings_manager'):
            self.settings_manager.display()

    def __init__(self, *args, **kwargs):
        #if 'label' in kwargs.keys(): label = kwargs['label']
        #else: label = self.label
        if 'label' in kwargs.keys() and\
                not kwargs['label'].startswith('mobj__'):
            self._label = unique_label(kwargs['label'])

        else: self._label = 'mobj__'
        self.impose_default('parent', None, **kwargs)
        self.impose_default('data', [], **kwargs)
        if 'visible_attributes' in kwargs.keys():
            self.visible_attributes = kwargs['visible_attributes']

        if 'base_class' in kwargs.keys():
            base_class = kwargs['base_class']

        else: base_class = None
        if base_class is None:
            self.base_class = interface_template_class(
                    self.__class__, '__modu_object__')

        else: self.base_class = base_class
        self.set_base_class()
        if 'valid_base_classes' in kwargs.keys():
            valid_base_classes = kwargs['valid_base_classes']

        else: valid_base_classes = None
        if valid_base_classes is None:
            self.valid_base_classes = [self.base_class]

        else: self.valid_base_classes = valid_base_classes
        self.impose_default('parameter_space_templates', [], **kwargs)
        self._store_p_sp_temp_data_()   
        self.rewidget_ = True

    def impose_default(self, *args, **kwargs):
        key = args[0]; default = args[1]
        if key in kwargs.keys(): self.__dict__[key] = kwargs[key]
        else: self.__dict__[key] = default

    def to_string(self):
        return self.label

    #def update_filenames(self, files):
    #   for key in files.keys():
    #       files[key] = increment_filename(files[key])

    def set_base_class(self, new_class = None, even_if = False):
        if new_class is not None:
            self.base_class.set_base_class(new_class, even_if)

        else: self.base_class.set_base_class(self.__class__, even_if)

    def recast(self, new_base_class, base_example = None):
        self.__class__ = new_base_class
        self.base_class._class = self.__class__
        if base_example is None:
            base_example = self.base_class._class(label = 'mobj__')
            if isinstance(base_example.__dict__, dictionary):
                dictionary_version = dictionary()
                for key in self.__dict__:
                    dictionary_version[key] = self.__dict__[key]

                self.__dict__ = dictionary_version
                self.__dict__.partition =\
                    base_example.__dict__.partition

        self.base_class._tag = base_example.base_class._tag
        for key in base_example.__dict__.keys():
            if not hasattr(self, key):
                self.__dict__[key] = base_example.__dict__[key]

    def verify_criteria_list(self, crits, *args):
        relevant_crits = [crit for crit in crits if crit.bRelevant]
        passes = [crit.verify_pass(*args) for crit in relevant_crits]
        return True in passes

    def verify_criteria_list_boolean(self, crits, *args, **kwargs):
        bool_expression = kwargs['bool_expression']
        if bool_expression == '' or bool_expression == None:
            return self.verify_criteria_list(crits, *args)

        expr = bool_expression.split(' ')
        reserved = ['(', ')', '+', '|', '!']
        crit_vars = [ex for ex in expr if ex not in reserved]
        crit_refs = {}
        for var in crit_vars:
            crit_refs[var] = grab_mobj_by_name(var, crits)

        for ex, dex in zip(expr, range(len(expr))):
            if ex not in reserved:
                expr[dex] = str(crit_refs[ex].verify_pass(*args))

            elif ex == '+': expr[dex] = 'and'
            elif ex == '|': expr[dex] = 'or'
            elif ex == '!': expr[dex] = 'not'

        expr = ' '.join(expr)
        return eval(expr)

    def __setattr__(self, attr, value):
        if attr is 'label': self._set_label_(value)
        else: object.__setattr__(self, attr, value)

    def __getattr__(self, name):
        #try: getattribute = super(modular_object_qt, self).__getattr__
        #getattribute = super(modular_object_qt, self).__getattr__
        #except AttributeError: print 'lfu issue...', name, self
        if not name.startswith('__') or not name.endswith('__'):
            if name is 'label':
                try: return self._get_label_()
                except:
                    print 'the most unholiest of errors...', self
                    raise AttributeError(name)

            try: return getattr(self, '__dict__')[name]
            except KeyError: raise AttributeError(name)

        #return getattribute(name)
        return super(modular_object_qt, self).__getattr__(name)

    def __getstate__(self): return self.__dict__
    def __setstate__(self, d):
        self.__dict__ = dictionary()
        self.__dict__.update(d)

    def _store_p_sp_temp_data_(self):
        if self.parameter_space_templates:
            self._p_sp_bounds_ = [temp.p_sp_bounds for temp in 
                                self.parameter_space_templates]
            self._p_sp_increments_ = [temp.p_sp_increment for temp 
                                in self.parameter_space_templates]

    def initialize(self, *args, **kwargs): pass
    def sanitize(self, *args, **kwargs):
        self.widg_dialog_templates = []
        self._store_p_sp_temp_data_()
        self.parameter_space_templates = []
        self.widg_templates = []
        self.menu_templates = []
        self.tool_templates = []
        for handle in self._handles_:
            handle[0].__dict__[handle[1]] = None
        self._handles_ = []
        self.rewidget(True)

    def set_uninheritable_settables(self, *args, **kwargs):
        '''
        #add a text box widget for self.label
        #self.widg_templates.append(
        #   lgm.interface_template_gui(
        #       ))
        '''
        pass

    #this now handles set_settables for each child mobject
    #assigning their widg_templates is still the subclass' responsibility
    def handle_widget_inheritance(self, *args, **kwargs):
        #tells a superclass if it should clear its templates
        # based on weather its been subclassed or not
        #  to prevent the ignorant superclass from 
        #   clearing the subclasses templates
        def should_sanitize(**kwargs):
            try: return not kwargs['from_sub']
            except KeyError: return True

        if should_sanitize(**kwargs):
            self.sanitize(*args, **kwargs)
            self.set_uninheritable_settables(*args, **kwargs)

    def rewidget(self, *args, **kwargs):
        #pass a boolean to set, pass nothing to get
        try:
            if type(args[0]) is types.BooleanType:
                self.rewidget_ = args[0]
                if hasattr(self, 'parent') and self.rewidget_:
                    if self.parent is not None:
                        if not self.parent.rewidget_:
                            self.parent.rewidget(self.rewidget_)

            else: print 'unrecognized argument for rewidget; ignoring'

        except IndexError:
            self.rewidget__children_(**kwargs)
            return self.rewidget_

    def rewidget__children_(self, *args, **kwargs):
        for child in self._children_:
            #if self is child:
            #   print 'be concerned about this'; pdb.set_trace()
            #   return self.rewidget_
            if child.rewidget(**kwargs):
                child.set_settables(*kwargs['infos'])

    def provide_axes_manager_input(self, 
            lp = True, cp = True, bp = True, vp = True, 
            x_title = 'x-title', 
            y_title = 'y-title', title = 'title'):
        self.use_line_plot = lp
        self.use_color_plot = cp
        self.use_bar_plot = bp
        self.use_voxel_plot = vp
        self.x_title = x_title
        self.y_title = y_title
        self.title = title

    def set_pspace_settables(self, *args, **kwargs):
        if using_gui():
            #this should probably turn on more than one axis...
            self.parameter_space_templates[0].set_settables(
                                            *args, **kwargs)

    def set_settables(self, *args, **kwargs):
        self.handle_widget_inheritance(*args, **kwargs)
        self.rewidget(False)
        self.widg_templates.reverse()






