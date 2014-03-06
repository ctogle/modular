import libs.modular_core.libfundamental as lfu
from libs.modular_core.libfundamental import modular_object_qt as modular_object
import libs.modular_core.libsimcomponents as lsc
import libs.modular_core.libmath as lm
import libs.modular_core.libgeometry as lgeo
import libs.modular_core.libfitroutine as lfr
import libs.modular_core.libpostprocess as lpp
import libs.modular_core.libcriterion as lc

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.path as path

import types
import random
from math import log as log

import pdb

if __name__ == 'libs.modules.liblattice':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is the lattice module library!'

module_name = 'lattice'
run_param_keys = ['End Criteria', 'Capture Criteria', 'Plot Targets', ]

def set_parameters(ensem):
	ensem.run_params['plot_targets'] = ['iteration', 
		'time', 'total population', 'vertex counts']
	output_plan = ensem.run_params['output_plans']['Simulation']
	output_plan.targeted = ['iteration', 'time', 
			'total population', 'vertex counts']
	for dex in range(len(output_plan.outputs)):
		output_plan.outputs[dex] = ['iteration', 'time', 
					'total population', 'vertex counts']

	ensem.run_params['bool_expressions'] = lfu.dictionary()
	ensem.run_params['bool_expressions']['end'] = ''
	ensem.run_params['bool_expressions']['capt'] = ''
	ensem.run_params.create_partition('system', 
		[	'end_criteria', 'capture_criteria', 'plot_targets', 
										'bool_expressions'	])
	ensem.cartographer_plan.parameter_space_mobjs =\
				ensem.run_params.partition['system']
	ensem.run_params.create_partition('template owners', [])

def generate_gui_templates_qt(window, ensemble):
	panel_template_lookup = []
	plot_target_labels = ['iteration', 'time', 
		'total population', 'vertex counts']
	ensemble.simulation_plan.plot_targets = plot_target_labels
	ensemble.simulation_plan.set_settables(window, ensemble) #this may not need to be here
	sim_plan = ensemble.simulation_plan
	panel_template_lookup.append(('end_criteria', 
		lgm.interface_template_gui(
			widgets = ['panel'], 
			templates = [sim_plan.widg_templates_end_criteria]))), 
	panel_template_lookup.append(('capture_criteria', 
		lgm.interface_template_gui(
			widgets = ['panel'], 
			templates = [sim_plan.widg_templates_capture_criteria])))
	panel_template_lookup.append(('plot_targets', 
		lgm.interface_template_gui(
			widgets = ['panel'], 
			templates = [sim_plan.widg_templates_plot_targets])))
	
	return lgb.tree_book_panels_from_lookup(
		panel_template_lookup, window, ensemble)

#an instance of this object represents an independent simulation system
class sim_system(lsc.sim_system):

	#this function is here only for debugging/development
	def histogram(self):
		fig, ax = plt.subplots()

		data = [len(vertex) for vertex in self.lattice]
		n, bins = data, range(len(self.lattice)+1)

		# get the corners of the rectangles for the histogram
		left = np.array(bins[:-1])
		right = np.array(bins[1:])
		bottom = np.zeros(len(left))
		top = bottom + n

		# we need a (numrects x numsides x 2) numpy array for the path helper
		# function to build a compound path
		XY = np.array([[left,left,right,right], [bottom,top,top,bottom]]).T

		# get the Path object
		barpath = path.Path.make_compound_path_from_polys(XY)

		# make a patch out of it
		patch = patches.PathPatch(barpath, facecolor='blue', edgecolor='gray', alpha=0.8)
		ax.add_patch(patch)

		# update the view limits
		ax.set_xlim(left[0], right[-1])
		ax.set_ylim(bottom.min(), top.max())

		plt.show()

	def __init__(self, ensem = None, params = {}):
		lsc.sim_system.__init__(self, ensem = ensem, params = params)
		try:
			dex = [da.label for da in self.data].index('vertex counts')
			self.data[dex] = lgeo.bin_vectors_from_labels(
									['vertex counts'])[0]

		except ValueError: pass

		def validate_time(dex):
			return len(self.data[dex].scalers) - 10

		timedex = [dater.label for dater in self.data].index('iteration')
		self.determine_end_valid_data = (validate_time, (timedex))

		self.end_criteria[0].max_iterations = 100

	def initialize(self):
		ndimensions = 1
		self.movements = []
		self.cell_deaths = []
		self.maximum_occupants = 2
		self.xsize = 100
		self.ysize = 100
		self.zsize = 100


		#This loop executes if n dimensions equals 1
		if ndimensions == 1: 
			#Declare 1 dimensional lattice
			self.iterate_lattice = self.one_d_lattice_iterate
			#Self.lattice is instantiated as a list of empty list
			self.lattice = [[] for dex in range(self.xsize)]

			#Declare initial occupants
			self.lattice[20].append(species(20, 0 ,0, self))
			self.lattice[90].append(species(90, 0 ,0, self))
			self.lattice[80].append(species(80, 0 ,0, self))

		elif ndimensions==2:
			self.iterate_lattice=self.two_d_lattice_iterate
			self.lattice=[[[] for xdex in range(xsize)] 
							for ydex in range(ysize)]

		else:
			self.iterate_lattice=self.three_d_lattice_iterate
			self.lattice=[[[[] for xdex in range(xsize)] 
							for ydex in range(ysize)] 
							for zdex in range(zsize)]

		self.time.append(0.0)
		self.data[-1].bins = range(len(self.lattice) + 1)

	def iterate(self):
		#try:
			#
			delta_time = 1.0
			self.time.append(self.time[-1] + delta_time)
			#The following line calls one_d_lattice_iterate
			self.iterate_lattice()
			print 'system iterated', self.iteration
		#except:
		#	print 'sim_system.iterate() failed!'
		#	self.bAbort = True

	def decommission(self):
		#self.histogram()
		#pdb.set_trace()
		pass

	def one_d_lattice_iterate(self):
		#Movement and death are handled by the following loop
		#It works by iterating across each vertex, then over each 
		#occupant at each nonempty vertex.
		for vertex in self.lattice:
			#if a given vertex is nonempty the following statement executes
			if vertex:
				#self.divisions is a list of the occupants which will divide on the current iteration
				self.divisions = []
				#The following loop iterates across each occupant at a given vertex	
				for occupant in vertex:
					#The following statement executes if the occupant is 
					#in the list of cells dying on the current iteration
					if occupant in self.cell_deaths:
						#Remove cell from list
						vertex.remove(occupant)
						continue
					#The following statement executes if the occupant is 
					#in the list of cells which are slated to move
					if occupant in self.movements:
						#Remove cell fom list
						vertex.remove(occupant)
						self.movements.remove(occupant)
						#If current xposition is greater than the 
						#lattice size, print walked-off-right message 
						#and do NOT reappend to list
						if occupant.xposition >= self.xsize:
							print 'Walked off lattice to the right'
							occupant.die()
						
						#If current xposition negative, print walked-
						#off-left message and do NOT reappend to list
						elif occupant.xposition < 0:
							print 'Walked off lattice to the left'
							occupant.die()
						#If the xposition is on the interior of the 
						#lattice, 
						else:
							if occupant.xposition == self.xsize or occupant.xposition < 0:
								#pdb.set_trace()
								pass
							print '|', occupant.xposition, len(self.lattice), len(vertex)
							#If the cell's new xposition is not off the 
							#lattice, reappend it at the new site
							self.lattice[occupant.xposition].append(occupant)
		#After the loop, movements and cell deaths are redeclared to be 
		#empty
		self.movements = []
		self.cell_deaths = []
		#Cell divisions are handled by the following for loop
		#It operates just like the loop for movements and deaths
		for vertex in self.lattice:
			#The following statement executes if a given vertex is 
			#nonempty
			if vertex:
				#The list of cells slated to divide is instinatiated as 
				#empty
				self.divisions = []
				#The following loop iterates across each occupant in a 	
				#given vertex
				for occupant in vertex:
					occupant.iterate()
				#If the vertex is nonempty, call one_d_iterate_vertex on it	
				self.one_d_iterate_vertex(vertex)

	#The following function is called if a nonempty vertex is found 
	#while iterating over the lattice
	def one_d_iterate_vertex(self, vertex):
		#for each cell in the division list, append a new cell to the 
		#same location
		for division in self.divisions:
			vertex.append(species(division.xposition, 
				division.yposition, division.zposition, self))
				
		#If the number of cells at the current vertex exceeds the 
		#maximum, the following statement executes
		if len(vertex) >= self.maximum_occupants:
			#This line computes the number of cells to move from a vertex
			move_sample_size = len(vertex) - self.maximum_occupants
			#This line selects the appropriate number of cells to move,
			#and chooses randomly rather than off the top
			movers = random.sample(vertex, move_sample_size)
			#This loop moves each cell in the list of movers by calling 
			#move_left_or_right on each of them
			for mover in movers: self.move_left_or_right(mover)

	def move_left_or_right(self, mover):
		#The following if statement counts the number of cells in the 
		#vertices to the right and left for each mover
		#if mover.xposition - 1 < 0:
		if mover.xposition < 0:
			left__pop = 0
			right_pop = len(self.lattice[mover.xposition + 1])

		
		elif mover.xposition + 1 >= self.xsize:
		#elif mover.xposition >= self.xsize:
		#elif mover.xposition + 2 >= self.xsize:
			#try: left__pop = len(self.lattice[mover.xposition - 1])
			try: left__pop = len(self.lattice[mover.xposition - 8])
			except: pdb.set_trace()
			right_pop = 0

		else:
			try: left__pop = len(self.lattice[mover.xposition - 1])
			except:
				print 'left problem'
				pdb.set_trace()
			try: right_pop = len(self.lattice[mover.xposition + 1])
			except:
				print 'right problem'
				pdb.set_trace()

		#The following if statement determines a bias for the movement 
		#based on neighboring population
		if left__pop - right_pop > 0:
			bias = left__pop - right_pop
			if bias >= self.maximum_occupants: bias_bump = 0.5
			else: bias_bump = bias/self.maximum_occupants * 0.5
		
		elif right_pop - left__pop > 0:
			bias = right_pop - left__pop
			if bias >= self.maximum_occupants: bias_bump = -0.5
			else: bias_bump = bias/self.maximum_occupants * -0.5

		else: bias_bump = 0.0
		#Right is a binary number which will dermine whether the given 
		#mover moves left or right
		right = random.random() + bias_bump <= 0.5
		if right:  
			mover.xposition += 1
		else: 
			try: 
				mover.xposition -= 1
				#print mover.xposition, mover
			except mover.xposition == 101:
				print('got there')
		#else: mover.xposition -= 1
		self.movements.append(mover)

	def two_d_lattice_iterate(self): pass
	def two_d_iterate_vertex(self, vertex): pass
	def three_d_lattice_iterate(self): pass
	def three_d_iterate_vertex(self, vertex): pass

	def capture_plot_data(self):
		for k in range(len(self.parameters['plot_targets'])):
			if self.data[k].tag == 'bin_vector':
				self.data[k].counts.append(
					[len(vertex) for vertex in self.lattice])
				self.data[k].time.append(self.time[-1])

			elif self.data[k].tag == 'scaler':
				if self.data[k].label == 'time':
					self.data[k].scalers.append(
						self.__dict__[self.data[k].label][-1])

				elif self.data[k].label == 'total population':
					self.data[k].scalers.append(sum(
						[len(vertex) for vertex in self.lattice]))

				else:
					self.data[k].scalers.append(
						self.__dict__[self.data[k].label])

class species(modular_object):

	def __init__(self, x, y, z, system):
		self.xposition = x
		self.yposition = y
		self.zposition = z
		self.max_age = 1000
		self.system = system
		modular_object.__init__(self)
		self.initialize()

	def initialize(self, *args, **kwargs):
		self.divide_time = 10
		self.divide_timer = 0
		self.diffusion_probability = 0.8
		self.age_iteration = 0

	def iterate(self, *args, **kwargs):
		#print self.xposition
		self.age_iteration += 1
		if self.age_iteration == self.max_age:
			self.system.cell_deaths.append(self)
			return

		self.divide_timer += 1
		if self.divide_timer == self.divide_time:
			self.divide_timer = 0
			self.divide()

		if random.random() <= 1:
		#if random.random() <= self.diffusion_probability:
			self.system.move_left_or_right(self)

	def divide(self):
		self.system.divisions.append(self)

	def die(self):
		print self
		del self
