
__doc__ = """fundamental functions/classes for modular"""

import modular_core.resources as mcrsrc
import modular_core.data_pools as mcdps

import re
import sys
pipe_mirror = None
#stderr = None
import time
import types
import ctypes
import importlib
import os
from pkg_resources import resource_string

lset = None
gui_pack = None
gui_library = None
label_pool = []

import traceback

import pdb

debug_filter_thresh = 10

registry_path = os.path.join(os.getcwd(), 
	'resources', 'program_registry.txt')

def using_gui(): return USING_GUI
def find_gui_pack():
	#set_gui_pack('modular_core.gui.libqtgui')
	if using_gui(): set_gui_pack('modular_core.gui.libqtgui')
	else:
		#pass
		global gui_pack; global gui_library
		gui_pack = data_container(lgm = None, lgb = None, lgd = None)
		gui_library = 'NO GUI LIBRARY'
def set_gui_pack(gui_lib):
	global gui_pack; global gui_library
	gui_pack = importlib.import_module(gui_lib)
	gui_library = gui_lib
def initialize_gui(params):
	try: application = params['application']
	except KeyError:
		print 'no application key; no initialize_gui method...'
		return
	global lset; global stdout; global stderr
	try: import libs.modular_core.libsettings as lset
	except ImportError: lset = None
	#stdout = gui_pack.lgb.console_listener(True)
	#stderr = gui_pack.lgb.console_listener(False)
	#sys.stdout = stdout
	#sys.stderr = stderr
	app = application(params, sys.argv)
	sys.exit(app.exec_())

def using_os(os_):
	if os_ == 'windows' and (sys.platform.startswith('win') or\
				sys.platform.startswith('cygwin')): return True
	elif os_ == 'mac' and sys.platform.startswith('darwin'): return True
	elif os_ == 'linux' and sys.platform.startswith('linux'): return True
	else: return False

def convert_pixel_space(width, height):
	_screensize_ = gui_pack.lgb.set_screensize()
	good_width = 1920.0
	good_height = 1080.0
	(runtime_width, runtime_height) =\
		(_screensize_.width(), _screensize_.height())
	width_conversion = runtime_width / good_width
	height_conversion = runtime_height / good_height
	w_size = width * width_conversion
	h_size = height * height_conversion
	return w_size, h_size

def debug_filter(debug_, verbosity = 0, verb_thresh = 100):
	if lset:
		check = lset.get_setting('debug_verbosity', fail_silent = True)
		if check: verb_thresh = check

	if not verbosity > verb_thresh: print str(debug_)

def show_label_pool():
	print label_pool

def clean_label_pool():
	global label_pool
	label_pool = [item for item in label_pool 
			if not item.startswith('mobj__')]

#this likely has to be persistent on an ensemble level...
def unique_label(base):
	if not base in label_pool:
		label_pool.append(base)
		return base

	else:
		try:
			label = unique_label(''.join([base, '0']))
			if label.startswith('modu__'): pdb.set_trace()
			return label

		except RuntimeError:
			print base
			pdb.set_trace()

def get_new_pool_id():
	return str(time.time())

def fill_lists(lists, fill = None):
	length = max([len(li) for li in lists])
	for li in lists:
		if len(li) < length:
			li.extend([fill]*(length - len(li)))

class interface_template_new_style(object):

	def __init__(self, *args, **kwargs):
		#self.args = args
		for key in kwargs.keys(): self.__dict__[key] = kwargs[key]

	def _q_purge_(self):
		for item in [type(di) for di in dir(self)]:
			if repr(item).count('PySide') > 0: pdb.set_trace()

	def _destroy_(self, *args, **kwargs):
		del self

class interface_template_class(interface_template_new_style):
	__doc__ = """carries information about the class of an object"""

	def __init__(self, base_class, base_tag = None, 
				visible_attributes = ['base_tag']):
		interface_template_new_style.__init__(self, 
							_class = base_class, _tag = base_tag, 
						visible_attributes = visible_attributes)

	def set_base_class(self, new_class, even_if = False):
		__doc__ = """resets the _class attribute"""
		if self._class is object or even_if:
			self._class = new_class

class modular_object_qt(object):
	__doc__ = """fundamental class used in modular"""
	rewidget_ = True
	#_p_sp_bounds_ = []
	_children_ = []
	_handles_ = []
	data = []
	visible_attributes = []

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
		if 'data' in kwargs.keys(): print kwargs['data']
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
		self.rewidget_ = True

	def impose_default(self, *args, **kwargs):
		key = args[0]; default = args[1]
		if key in kwargs.keys(): self.__dict__[key] = kwargs[key]
		else: self.__dict__[key] = default

	def to_string(self):
		return self.label

	def update_filenames(self, files):
		for key in files.keys():
			files[key] = increment_filename(files[key])

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
		'''
		for crit in relevant_crits:
			if crit.verify_pass(*args):
				return True

		if not relevant_crits:
			print 'no relevant criteria in criteria list!'
			return True

		return False
		'''
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

	def initialize(self, *args, **kwargs): pass
	def sanitize(self, *args, **kwargs):
		self.widg_dialog_templates = []
		if self.parameter_space_templates:
			self._p_sp_bounds_ = [temp.p_sp_bounds for temp in 
								self.parameter_space_templates]
			self._p_sp_increments_ = [temp.p_sp_increment for temp 
								in self.parameter_space_templates]

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
		#	lgm.interface_template_gui(
		#		))
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
			#	print 'be concerned about this'; pdb.set_trace()
			#	return self.rewidget_
			if child.rewidget(**kwargs):
				child.set_settables(*kwargs['infos'])

	def provide_axes_manager_input(self, 
			lp = True, cp = True, bp = True, 
			x_title = 'x-title', 
			y_title = 'y-title', title = 'title'):
		self.use_line_plot = lp
		self.use_color_plot = cp
		self.use_bar_plot = bp
		self.x_title = x_title
		self.y_title = y_title
		self.title = title

	def set_settables(self, *args, **kwargs):
		self.handle_widget_inheritance(*args, **kwargs)
		self.rewidget(False)
		self.widg_templates.reverse()

class data_container(object):

	def __init__(self, *args, **kwargs):
		self.args = args
		for key in kwargs.keys(): self.__dict__[key] = kwargs[key]

class plan(modular_object_qt):

	def __init__(self, *args, **kwargs):
		if not 'label' in kwargs.keys():
			kwargs['label'] = 'another plan'

		self.impose_default('use_plan', False, **kwargs)
		modular_object_qt.__init__(self, *args, **kwargs)

	def enact_plan(self, *args, **kwargs):
		pass

	def __call__(self, *args, **kwargs):
		self.enact_plan(*args, **kwargs)

class dictionary(dict):

	parent = None

	def __init__(self, *args, **kwargs):
		dict.__init__(self, args)
		self.__dict__ = self
		if not 'parent' in kwargs.keys(): parent = None
		else: parent = kwargs['parent']
		self._parent = parent

	def clean_partition(self, partition):
		for key in self.partition[partition].keys():
			if not self.partition[partition][key]:
				del self.partition[partition][key]

			elif issubclass(self.partition[partition][
							key].__class__, dictionary):
				if partition in self.partition[partition][
									key].partition.keys():
					self.partition[partition][
						key].clean_partition(partition)

	def clear_widget_templates(self, mobj):
		try: mobj.sanitize()
		except AttributeError: pass
		try: mobj.__dict__.rid_widg_templates('template owners')
		except AttributeError: pass
		except:
			debug_filter('problem ridding widgets!', 
								debug_filter_thresh)
			#print mobj, mobj.label
			pass

	def find_relevant_partition(self, partition_key = None):
		if not partition_key is None:
			return self.partition[partition_key]

		else: return self

	def rid_widg_templates_from_lists_dicts(self, run_param):
		#print 'run', run_param
		#if not run_param: pdb.set_trace()
		if isinstance(run_param, modular_object_qt):
			#print 'found a mobj', run_param
			self.clear_widget_templates(run_param)

		elif type(run_param) == types.ListType and run_param:
			for mobj_list_or_dict in run_param:
				if isinstance(mobj_list_or_dict, modular_object_qt):
					#print 'found one in a list', mobj_list_or_dict
					self.clear_widget_templates(mobj_list_or_dict)

				else:
					self.rid_widg_templates_from_lists_dicts(
											mobj_list_or_dict)

		elif (type(run_param) == types.DictionaryType or\
				isinstance(run_param, dictionary)) and run_param:
			for key in run_param.keys():
				if key is 'parent': continue
				elif isinstance(run_param.values()[0], 
									modular_object_qt):
					self.clear_widget_templates(run_param[key])
					#print 'found one in a dict', run_param[key]

				else:
					self.rid_widg_templates_from_lists_dicts(
											run_param[key])

		else:
			#print 'hopefully this dater is simple: ', run_param
			pass

	def rid_widg_templates(self, partition_key = None):
		partition = self.find_relevant_partition(
					partition_key = partition_key)
		for key in partition.keys():
			if key is 'parent': continue
			run_param = partition[key]
			if isinstance(run_param, modular_object_qt):
				self.clear_widget_templates(run_param)

			else: self.rid_widg_templates_from_lists_dicts(run_param)

	def restore_widg_templates(self, partition_key = None, 
									settable_infos = ()):
		partition = self.find_relevant_partition(
					partition_key = partition_key)
		for key in partition.keys():
			run_param = partition[key]
			if type(run_param) == types.ListType and run_param:
				if isinstance(run_param[0], modular_object_qt):
					for mobj in run_param:
						mobj.set_settables(*settable_infos)

			elif type(run_param) == types.DictionaryType and run_param:
				if isinstance(run_param.values()[0], modular_object_qt):
					for key in run_param.keys():
						run_param[key].set_settables(*settable_infos)

	def create_partition(self, key, sub_keys):
		try:
			self.partition[key] = dictionary()

		except AttributeError:
			self.partition = {}
			self.partition[key] = dictionary()

		for sub_key in sub_keys:
			self.partition[key][sub_key] = self[sub_key]

def get_modular_program_list():
	listing = [item[0] for item in parse_registry()]
	return listing

def list_program_modules(program):
	all_files_dirs = [item for item in 
		os.walk(os.path.join(os.getcwd(), 'libs', program))]
	path_files = [(item[0], [fi[3:-3] for fi in item[2] if 
		fi.startswith('lib') and not fi.startswith('__init__') and 
			not fi.endswith('.pyc')]) for item in all_files_dirs]
	return path_files

def get_data_pool_path():
	return mcdps.__path__[0]

def get_resource_path(res):
	return os.path.join(mcrsrc.__path__[0], res)

def parse_registry():
	reg_string = resource_string(__name__, 
		os.path.join('resources', 'program_registry.txt'))
	#with open(registry_path, 'r') as handle:
	reg = reg_string.split('\n')
	#reg = handle.readlines()
	reg = [line for line in reg if not line.startswith('#') 
								and not line.strip() == '']
	reg = [[pa.strip() for pa in line.split(':')] for line in reg]
	return reg

def add_program_to_registry(program_name, 
		program_run_option, program_description):
	with open(registry_path, 'r') as handle:
		reg = handle.readlines()
		comments = [line for line in reg if line.startswith('#')]
		registered = [line for line in reg if 
			not line.startswith('#') and not line.strip() == '']
		registered.append('\n'+' : '.join([program_name, 
			program_run_option, program_description]))

	with open(registry_path, 'w') as handle:
		lines = comments + ['\n\n'] + registered
		[handle.write(line) for line in lines]

def remove_program_from_registry(program_name):
	with open(registry_path, 'r') as handle:
		reg = handle.readlines()
		comments = [line for line in reg if line.startswith('#')]
		registered = [line for line in reg if 
			not line.startswith('#') and not line.strip() == '' 
			and not line.startswith(program_name)]

	with open(registry_path, 'w') as handle:
		lines = comments + ['\n\n'] + registered
		[handle.write(line) for line in lines]

def increment_filename(fi):
	if fi == '': return fi

	else:
		fi = fi.split('.')
		if len(fi) == 1:	#non-indexed filename without extension
			return '.'.join(fi + ['0'])

		else:
			try:	#no file extension but an index to increment
				dex = int(fi[-1])
				dex = str(dex + 1)
				return '.'.join(fi[:-1] + [dex])

			except ValueError:	#assume a file extension
				try:
					dex = int(fi[-2])
					dex = str(dex + 1)
					return '.'.join(fi[:-1] + [dex] + fi[-1])

				except ValueError:	#had file extension but no index
					return '.'.join(fi[:-1] + ['0'] + fi[-1])

def flatten(unflat_list):
	return [item for sublist in unflat_list for item in sublist]

def grab_mobj_by_name(name, mobj_collection):
	#print 'lfu.grabmobjbyname()'
	#print type(mobj_collection)
	if type(mobj_collection) == types.ListType:
		return grab_mobj_from_list_by_name(name, mobj_collection)

	elif type(mobj_collection) == types.DictionaryType:
		return grab_mobj_from_dict_by_name(name, mobj_collection)

def grab_mobj_from_dict_by_name(name, mobj_dict):
	return mobj_dict[name]

def grab_mobj_from_list_by_name(name, mobj_list):
	return mobj_list[[mobj.label for mobj in mobj_list].index(name)]

def grab_mobj_names(mobj_collection):
	if type(mobj_collection) == types.ListType:
		return grab_mobj_list_names(mobj_collection)

	elif type(mobj_collection) == types.DictionaryType:
		return grab_mobj_dict_names(mobj_collection)

def grab_mobj_list_names(mobj_list):
	return [mobj.label for mobj in mobj_list]

def grab_mobj_dict_names(mobj_dict):
	return [mobj_dict[key].label for key in mobj_dict.keys()]

def grab_mobj_dex_by_name(label, collection):
	try: return grab_mobj_names(collection).index(label)	
	except ValueError:
		traceback.print_exc(file=sys.stdout)
		print 'cant find mobj in collection'
		pdb.set_trace()

def lookup_pairwise(zipped, string):
	try:
		string_dex = [type(item) == types.StringType 
						for item in zipped[0]].index(True)

	except IndexError:
		print 'zipped was empty...'
		return None

	except ValueError:
		print 'zipped had to string list...'
		return None

	try:
		obj_dex = [tup[string_dex] == string 
					for tup in zipped].index(True)

	except ValueError:
		print 'zipped did not contrain string...'
		return None

	return zipped[obj_dex][string_dex - 1]

def pagify(lines, max_leng = 30):

	def validate(line):
		splits = int(len(line) / max_leng)
		for k in range(1, splits + 1):
			line = insert_substring(line, '\n', k*max_leng)

		return line

	for line in lines:
		line = validate(line)

	return '\n'.join(lines)

def intersect_lists(list1, list2):
	list1 = [item for item in list1 if item in list2]
	return list1

def insert_substring(string, substring, index):
    return string[:index] + substring + string[index:]

def line_print_mobj(mobj):
	print '-'*40
	for key in mobj.__dict__.keys():
		print key, ' : ', mobj.__dict__[key]
	
	print '-'*40

def line_print_mobj_inspection(mobj):

	def mobj_to_pairs(mobj):
		lap = [(key, mobj.__dict__[key]) for 
				key in mobj.__dict__.keys()
				if key in mobj.visible_attributes]
		fixed_lap = []
		for pair in lap:			
			if 	issubclass(pair[1].__class__, modular_object) or\
				issubclass(pair[1].__class__, interface_template):
				if pair[1].visible_attributes:
					nest = mobj_to_pairs(pair[1])
					will_insert = [('\tnested object', 
							pair[1].__class__.__name__)]
					for sub_pair in nest:
						will_insert.append(sub_pair)

					fixed_lap.extend(will_insert)

			else:
				fixed_lap.append(pair)

		return fixed_lap

	mobj_lines = ['\t' + mobj.__class__.__name__]
	mobj_attrs = mobj_to_pairs(mobj)
	mobj_lines.extend([str(attr[0]) + ' : ' + str(attr[1]) 
								for attr in mobj_attrs])
	print '-'*40
	for line in mobj_lines: print line
	print '-'*40

def uniqfy(seq):
	seen = {}
	result = []
	for item in seq:
		if item in seen: continue
		seen[item] = 1
		result.append(item)

	return result

def zip_list(target, new_list):
	if target:
		target_names = [targ.label for targ in target[0]]
		for k in range(len(target)):
			valid = [dater for dater in new_list[k] 
				if dater.label not in target_names]
			target[k].extend(valid)
	else: target.extend(new_list)

class interface_template_dependance(interface_template_new_style):

	def __init__(self, reference, linkages = [], 
			#label = 'another dependance interface template', 
			visible_attributes = ['reference', 'linkages']):
		#(inst, key, initial)
		self.reference = reference
		#[(inst, key, relevance bool, anything, else, you, need)]
		self.linkages = linkages
		#interface_template_new_style.__init__(self, label = label, 
		interface_template_new_style.__init__(self, 
			visible_attributes = visible_attributes)

	def assert_dependance(self, *args):
		for link in [link for link in self.linkages 
								if link[2] is True]:
			if link[3] == 'direct':
				self.assert_dependance_direct(
								link, *args)

			elif link[3] == 'direct_remove':
				self.assert_dependance_direct_remove(
										link, *args)

			elif link[3] == 'append_list':
				self.assert_dependance_append_list(
										link, *args)

			elif link[3] == 'append_tuples_list':
				self.assert_dependance_append_tuples_list(
											link, *args)

			elif link[3] == 'append_list_nested':
				self.assert_dependance_append_list_nested(
											link, *args)

			else:
				print 'assertion could not be parsed!', self
				pdb.set_trace()

	def assert_dependance_direct(self, *args):
		link = args[0]
		to_assert = self.reference[0].__dict__[
							self.reference[1]]
		old = self.reference[2]
		self.reference = (self.reference[0], 
				self.reference[1], to_assert)
		link[0].__dict__[link[1]] = to_assert
		try: link[0].rewidget(True)
		except: pass

	def assert_dependance_direct_remove(self, *args):
		if self.reference[2]: #should indicate self.reference[0] is a dict
			if issubclass(self.reference[0][
				self.reference[1]].__class__, 
					lfu.modular_object_qt):
				self.reference[0][self.reference[1]]._destroy_()

			else: del self.reference[0][self.reference[1]]

		else:
			obj = self.reference[0][lfu.grab_mobj_dex_by_name(
						self.reference[1], self.reference[0])]
			if issubclass(obj.__class__, lfu.modular_object_qt):
				obj._destroy_()

			else: del obj

		#try: link[0].rewidget(True)
		#except: pass

	def assert_dependance_append_list(self, *args):
		link = args[0]
		to_assert = self.reference[0].__dict__[
							self.reference[1]]
		old = self.reference[2]
		try:
			dex = link[0].__dict__[link[1]].index(old)

		except ValueError:
			self.reference = (self.reference[0], 
				self.reference[1], to_assert)
			return

		self.reference = (self.reference[0], self.reference[1], 
													to_assert)
		#nothing like the below line appears in ValueError
		# because the data at link should automatically be
		# regenerated and should then depend on self.reference
		# by design!
		link[0].__dict__[link[1]][dex] = to_assert
		try: link[0].rewidget(True)
		except: pass

	def assert_dependance_append_list_nested(self, *args):
		link = args[0]
		to_assert = self.reference[0].__dict__[
							self.reference[1]]
		old = self.reference[2]
		try:
			dex = link[0].__dict__[link[1]][link[4]].index(old)

		except ValueError:
			self.reference = (self.reference[0], 
				self.reference[1], to_assert)
			return

		self.reference = (self.reference[0], 
				self.reference[1], to_assert)
		link[0].__dict__[link[1]][link[4]][dex] = to_assert
		try: link[0].rewidget(True)
		except: pass

	def assert_dependance_append_tuples_list(self, *args):
		link = args[0]
		to_assert = self.reference[0].__dict__[
							self.reference[1]]
		old = self.reference[2]
		try:
			lookup = [tup[link[4]] for tup in 
					link[0].__dict__[link[1]]]
			dex = lookup.index(old)

		except ValueError:
			self.reference = (self.reference[0], 
				self.reference[1], to_assert)
			return

		self.reference = (self.reference[0], 
				self.reference[1], to_assert)
		list_version = [item for item in 
			link[0].__dict__[link[1]][dex]]
		list_version[link[5]] = to_assert
		link[0].__dict__[link[1]][dex] = tuple(list_version)
		try: link[0].rewidget(True)
		except: pass

	def assert_dependance_to_list(self, *args):
		link = args[0]
		print 'dependance assertion method unsupported!'
		pass

class unique_pool_item(modular_object_qt):

	def _set_(self, val):
		if not val == self._value:
			try: self.pool.remove(self._value)
			except ValueError: pass
			self._value = self.unique(val)
			self.pool.append(self._value)
			self.pool = uniqfy(self.pool)
			return True

		else: return False

	def _get_(self, *args, **kwargs):
		return self._value

	value = property(_get_, _set_, 
		'unique modular object value')

	def __init__(self, pool, initial, parent = None):
		self.pool = pool
		self._value = self.unique(initial)
		modular_object_qt.__init__(self, parent = parent)

	def __del__(self):
		self.pool.remove(self.value)

	def show_pool(self):
		print self.pool

	def clean_pool(self):
		self.pool = [item for item in self.pool 
				if not item.startswith('mobj__')]

	def unique(self, base):
		if not base in self.pool:
			self.pool.append(base)
			return base

		else:
			try:
				label = self.unique(''.join([base, '0']))
				if label.startswith('modu__'): pdb.set_trace()
				return label

			except RuntimeError:
				print base
				pdb.set_trace()

def coerce_string_bool(string):
	true_strings = ['true', 'True', 'On', 'on']
	false_strings = ['false', 'False', 'Off', 'off']
	if string in true_strings: return True
	elif string in false_strings: return False

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

if __name__ == 'modular_core.libfundamental':
	USING_GUI = True

if __name__ == '__main__':
	print 'this is a library!'




