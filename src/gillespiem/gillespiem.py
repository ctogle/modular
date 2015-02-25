import modular_core.libfundamental as lfu
import modular_core.simulationmodule as smd
import modular_core.parameterspaces as lpsp
import modular_core.cython.writer as cwr
import modular_core.io.liboutput as lo

import pdb,os,sys,time,re

if __name__ == 'gillespiem.gillespiem':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgb = lfu.gui_pack.lgb
    lgd = lfu.gui_pack.lgd
if __name__ == '__main__':print 'gillespiem module'

###############################################################################

module_name = 'gillespiem'

class simulation_module(smd.simulation_module):

    def _parse_variable(self,li,ensem,parser,procs,routs,targs):
        spl = lfu.msplit(li)
        name,value = spl
        varib = variable(name = name,value = value)
        return name,varib

    def _parse_function(self,li,ensem,parser,procs,routs,targs):
        spl = lfu.msplit(li)
        name,value = spl
        func = function(name = name,func_statement = value)
        return name,func

    def _parse_reaction(self,li,ensem,parser,procs,routs,targs):
        spl = lfu.msplit(li)
        rxn,lab = spl

        rxnspl = rxn.split(' ')
        arrows = ['<->','->','<-']
        for a in arrows:
            if a in rxnspl:
                divider = rxnspl.index(a)

        def stoch(side):
            sdxs = [num*2 for num in range(len(side)/2)]
            read = [(side[k + 1],int(side[k])) for k in sdxs]
            return read

        if rxnspl[divider] == '<->':
            r1,r2 = rxnspl[divider - 1],rxnspl[divider + 1]
            left  = [item for item in data[:divider-1] if not item == '+']
            right = [item for item in data[divider+2:] if not item == '+']
            left = stoch(left)
            right = stoch(right)
            rxn1 = reaction(name = lab+'1',rate = r1,used = left,produced = right)
            rxn2 = reaction(name = lab+'2',rate = r2,used = right,produced = left)
            return [rxn1,rxn2]

        elif rxnspl[divider] == '->':
            r1 = rxnspl[divider - 1]
            left  = [item for item in rxnspl[:divider-1] if not item == '+']
            right = [item for item in rxnspl[divider+1:] if not item == '+']
            left = stoch(left)
            right = stoch(right)
            rxn = reaction(name = lab,rate = r1,used = left,produced = right)
            return rxn

        elif data[divider] == '<-':
            r1 = rxnspl[divider + 1]
            left  = [item for item in rxnspl[:divider] if not item == '+']
            right = [item for item in rxnspl[divider+2:] if not item == '+']
            left = stoch(left)
            right = stoch(right)
            rxn = reaction(name = lab,rate = r1,used = right,produced = left)
            return rxn

    def _parse_species(self,li,ensem,parser,procs,routs,targs):
        spl = lfu.msplit(li)
        spec,value = spl
        new = species(name = spec,initial = value)
        return spec, new

    def __init__(self,*args,**kwargs):
        self.run_parameter_keys.extend(
            ['Variables','Functions','Reactions','Species'])
        self.parse_types.extend(
            ['variables','functions','reactions','species'])
        self.parse_funcs.extend(
            [self._parse_variable,self._parse_function, 
            self._parse_reaction,self._parse_species])
        self.simulation = simulate
        self.extensionname = 'gillespiemext'
        smd.simulation_module.__init__(self,*args,**kwargs)

    def _write_mcfg(self,mcfg_path,ensem):
        rparams = ensem.run_params
        mcfg = StringIO()
        self._write_mcfg_run_param_key(rparams,'variables',mcfg)
        self._write_mcfg_run_param_key(rparams,'functions',mcfg)
        self._write_mcfg_run_param_key(rparams,'reactions',mcfg)
        self._write_mcfg_run_param_key(rparams,'species',mcfg)
        lmc.simulation_module._write_mcfg(mcfg_path,ensem,mcfg)

    def _ext_special_funcs(self):
        heavi = heaviside()
        gnoise = gauss_noise()
        return [heavi,gnoise]

    def _ext_funcs_run(self):
        ptargs = self.parent.run_params['plot_targets']
        end = self.parent.run_params['end_criteria'][0]
        cap = self.parent.run_params['capture_criteria'][0]
        ccnt = int(float(end.max_time)/float(cap.increment))+1
        rargs = {
            'capture_count':ccnt,
            'capture_increment':cap.increment,
            'targets':ptargs,
            'species':self.parent.run_params['species'],
            'reactions':self.parent.run_params['reactions'],
            'constants':self.parent.run_params['variables'],
            'functions':self.parent.run_params['functions'],
                }
        return run(**rargs)

    # this returns functions for the extension
    # NOT TO BE CONFUSED WITH RXN RATE FUNCTIONS
    def _ext_funcs(self):
        runfunc = self._ext_funcs_run()
        rxns = self.parent.run_params['reactions']
        funcs = self.parent.run_params['functions']
        varis = self.parent.run_params['variables']
        funcnames = funcs.keys()
        for r in rxns:
            r.statetargets = runfunc.statetargets
            r.functionnames = funcnames
            r.variables = varis
        for f in funcnames:
            funcs[f].statetargets = runfunc.statetargets
            funcs[f].functionnames = funcnames
            funcs[f].variables = varis
        rxnfuncs = [rx._cython_react(x) for x,rx in enumerate(rxns)]
        rxnvalds = [rx._cython_valid(x) for x,rx in enumerate(rxns)]
        rxnprops = [rx._cython_propensity(x) for x,rx in enumerate(rxns)]
        rxnrates = [funcs[fu]._cython(x) for x,fu in enumerate(funcs.keys())]
        funcs = [runfunc]
        specials = self._ext_special_funcs()
        return specials + rxnvalds + rxnprops + rxnrates + rxnfuncs + funcs

    # these are the keywords for the eventual cython module
    def _ext_kwargs(self):
        ext_kwargs = {
            'name':self.extensionname,
            'functions':self._ext_funcs(),
                }
        return ext_kwargs

    def _set_parameters_prepoolinit(self):
        insttime = time.time()
        print 'creating temporary extension:',self.extensionname
        self.extensionname = self.extensionname.replace('_','.',1)
        self.extensionname = lo.increment_filename(self.extensionname)
        self.extensionname = self.extensionname.replace('.','_',1)
        ext_kwargs = self._ext_kwargs()
        writer = cwr.extension(**ext_kwargs)
        writer._write()
        writer._install()
        #print 'the code!\n',writer.code
        print '\ninstallation took:',time.time() - insttime,'seconds\n'

    def _set_parameters(self):
        module = __import__(self.extensionname)
        self.sim_args = (module.run,)

    def _reset_parameters(self):
        ensem = self.parent
        self._gui_memory()
        ensem.simulation_plan._reset_criteria_lists()
        ensem.run_params['variables'] = {}
        ensem.run_params['species'] = {}
        ensem.run_params['reactions'] = []
        ensem.run_params['functions'] = {}
        ensem.run_params['plot_targets'] = ['time']
        ensem.postprocess_plan._reset_process_list()
        output_plan = ensem.run_params['output_plans']['Simulation']
        output_plan.targeted = ['time']
        for w in output_plan.writers:w.targeted = ['time']

    def _gui_memory(self):
        self.module_memory = [
            lfu.data_container(selected_output_plan = 'Simulation', 
                selected_variable = 'None',selected_function = 'None', 
                selected_reaction = 'None',selected_species = 'None')]

    def _run_param_template(self,window,ensem,base,
                mobjname,key,handle_key,memory_key):
        new = (key,lgm.generate_add_remove_select_inspect_box_template(
            window = window,key = key,parent = ensem,
            labels = ['Add ' + mobjname,'Remove ' + mobjname], 
            wheres = [ensem.children,ensem.run_params[key]],
            selector_handle = (self.module_memory[0],handle_key),
            memory_handle = (self.module_memory[0],memory_key), 
            base_class = base))
        return new

    def _panel_templates(self,*args,**kwargs):
        window = args[0]
        ensem = args[1]
        self._gui_memory()
        plot_target_labels = ['time'] +\
            ensem.run_params['species'].keys() +\
            ensem.run_params['variables'].keys() +\
            ensem.run_params['functions'].keys()
        panel_template_lookup =\
            lmc.simulation_module._panel_templates(
                self,window,ensem,plot_target_labels)
        vargs = (window,ensem,variable,
            'Variable','variables','variable_selector','selected_variable')
        fargs = (window,ensem,function,
            'Function','functions','function_selector','selected_function')
        rargs = (window,ensem,reaction,
            'Reaction','reactions','reaction_selector','selected_reaction')
        sargs = (window,ensem,species,
            'Species','species','species_selector','selected_species')
        panel_template_lookup.append(self._run_param_template(*vargs))
        panel_template_lookup.append(self._run_param_template(*fargs))
        panel_template_lookup.append(self._run_param_template(*rargs))
        panel_template_lookup.append(self._run_param_template(*sargs))
        return panel_template_lookup

###############################################################################

# this must be a single argument function because of map_async
def simulate(args):
    #import pyximport; pyximport.install(reload_support = True)
    #from gillespiemext import run as runfunc
    #from gillespiemext import *
    runfunc = args[0]
    result = runfunc()
    #result = run()
    return result

############################################################################### 

class gauss_noise(cwr.function):

    def _code_body(self,coder):
        coder.write('\n\tcdef double gn = numpy.random.normal(0.0,1.0)')
        coder.write('\n\treturn value + value*(gn*'+str(self.SNR)+')\n')

    def __init__(self,*args,**kwargs):
        self._default('name','gauss_noise',**kwargs)
        self._default('argstring','double value',**kwargs)
        self._default('cytype','cdef double',**kwargs)
        self._default('SNR',1.0,**kwargs)
        cwr.function.__init__(self,*args,**kwargs)

############################################################################### 

class heaviside(cwr.function):

    def _code_body(self,coder):
        coder.write('\n\tif value > 0.0:return 1.0')
        coder.write('\n\telse:return 0.0\n')

    def __init__(self,*args,**kwargs):
        self._default('name','heaviside',**kwargs)
        self._default('argstring','double value',**kwargs)
        self._default('cytype','cdef double',**kwargs)
        cwr.function.__init__(self,*args,**kwargs)

############################################################################### 

class run(cwr.function):

    def _nparray(self,coder,name,shape,dtype = 'numpy.double'):
        predtype = dtype[dtype.find('.')+1:]
        coder.write('\n\tcdef '+predtype+' [')
        coder.write(','.join([':']*len(shape))+'] '+name+' = ')
        coder.write('zeros('+str(shape)+',dtype = '+dtype+')')

    def _code_body_initialize(self,coder):
        scnt = len(self.species)
        rcnt = len(self.reactions)
        vcnt = len(self.constants)
        fcnt = len(self.functions)

        #coder.write('\n\truniform = random.random')
        coder.write('\n\tzeros = numpy.zeros')

        dshape = (self.target_count,self.capture_count)
        sshape = (1 + scnt + vcnt + fcnt,)
        cshape = (self.target_count,)
        #coder.write('\n\tdata = zeros('+str(dshape)+',dtype = numpy.float)')
        self._nparray(coder,'data',dshape)
        self._nparray(coder,'capture',cshape)
        self._nparray(coder,'state',sshape)
        for sdex in range(scnt):
            sp = self.statetargets[sdex+1]
            sinit = self.species[sp].initial
            coder.write('\n\tstate['+str(sdex+1)+'] = '+str(sinit))
        for vdex in range(vcnt):
            va = self.statetargets[vdex+scnt+1]
            vval = self.constants[va].value
            coder.write('\n\tstate['+str(vdex+sdex+1)+'] = '+str(vval))
        for fdex in range(fcnt):
            fu = self.statetargets[fdex+vcnt+scnt+1]
            funame = self.functions[fu].name
            coder.write('\n\t'+funame+'(state)')

        coder.write('\n\tcdef int totalcaptures = '+str(self.capture_count))
        coder.write('\n\tcdef int capturecount = 0')
        coder.write('\n\tcdef int rtabledex')
        coder.write('\n\tcdef int tdex')
        coder.write('\n\tcdef int cdex')
        coder.write('\n\tcdef double totalpropensity')
        coder.write('\n\tcdef double tpinv')
        coder.write('\n\tcdef double time = 0.0')
        coder.write('\n\tcdef double lasttime = 0.0')
        coder.write('\n\tcdef double realtime = 0.0')
        coder.write('\n\tcdef double del_t = 0.0')
        coder.write('\n\tcdef double randr')
        coder.write('\n\tcdef float imax = float(INT_MAX)')

        coder.write('\n\tcdef int whichrxn = 0')
        coder.write('\n\tcdef int rxncount = '+str(rcnt))
        pshape = (rcnt,)
        self._nparray(coder,'reactiontable',pshape)
        self._nparray(coder,'propensities',pshape)
        for rdex in range(rcnt):
            rname = 'rxnpropensity'+str(rdex)
            coder.write('\n\tpropensities['+str(rdex)+'] = '+rname+'(state)')

        self._nparray(coder,'tdexes',cshape,dtype = 'numpy.long')
        for tdx in range(self.target_count):
            statedex = self.statetargets.index(self.targets[tdx])
            coder.write('\n\ttdexes['+str(tdx)+'] = '+str(statedex))
        
    # THIS SHOULD PROBABLY BE ACID TESTED
    def _gibson_lookup(self,rxns):
        rcnt = len(rxns)
        alwayses = [d for d in range(rcnt) if rxns[d].rate_is_function]
        lookups = [[] for r in rxns]
        for rdx in range(rcnt):
            # enumerate the species affected by rxns[rdx]
            r = rxns[rdx]
            r.affected_species = []
            for p in r.produced:
                found = False
                for u in r.used:
                    if u[0] == p[0]:
                        found = True
                        if not u[1] == p[1] and not p[0] in r.affected_species:
                            r.affected_species.append(p[0])
                if not found and not p[0] in r.affected_species:
                    r.affected_species.append(p[0])
            for u in r.used:
                found = False
                for p in r.produced:
                    if p[0] == u[0]:
                        found = True
                        if not p[1] == u[1] and not u[0] in r.affected_species:
                            r.affected_species.append(u[0])
                if not found and not u[0] in r.affected_species:
                    r.affected_species.append(u[0])
            #print 'rxn',r.name,r.affected_species
            lookups[rdx].extend(alwayses)
            for rdx2 in range(rcnt):
                r2 = rxns[rdx2]
                for u2 in r2.used:
                    if u2[0] in r.affected_species:
                        if not rdx2 in lookups[rdx]:
                            lookups[rdx].append(rdx2)
        return lookups

    def _code_body_loop(self,coder):
        scnt = len(self.species)
        rcnt = len(self.reactions)
        vcnt = len(self.constants)
        fcnt = len(self.functions)

        coder.write('\n\n\twhile capturecount < totalcaptures:')
        coder.write('\n\t\ttotalpropensity = 0.0')
        rcnt = len(self.reactions)
        for pdex in range(rcnt):
            coder.write('\n\t\tif rxnvalid'+str(pdex)+'(state):')
            coder.write('totalpropensity = totalpropensity + ')
            coder.write('propensities['+str(pdex)+']')
            coder.write('\n\t\treactiontable['+str(pdex)+'] = totalpropensity')

        coder.write('\n\n\t\tif totalpropensity > 0.0:')
        coder.write('\n\t\t\ttpinv = 1.0/totalpropensity')
        coder.write('\n\t\t\tfor rtabledex in range(rxncount):')
        coder.write('\n\t\t\t\treactiontable[rtabledex] *= tpinv')
        #coder.write('\n\t\t\tdel_t = -1.0*log(<float>runiform())*tpinv')
        #coder.write('\n\t\t\tdel_t = -1.0*log(rand()/float(INT_MAX))*tpinv')
        coder.write('\n\t\t\tdel_t = -1.0*log(rand()/imax)*tpinv')

        #coder.write('\n\t\t\trandr = runiform()')
        coder.write('\n\t\t\trandr = rand()/float(INT_MAX)')
        coder.write('\n\t\t\tfor rtabledex in range(rxncount):')
        coder.write('\n\t\t\t\tif randr < reactiontable[rtabledex]:')
        coder.write('\n\t\t\t\t\twhichrxn = rtabledex')
        coder.write('\n\t\t\t\t\tbreak\n')

        coder.write('\n\n\t\telse:')
        coder.write('\n\t\t\tdel_t = '+str(self.capture_increment))
        coder.write('\n\t\t\twhichrxn = -1')

        coder.write('\n\n\t\tstate[0] += del_t')
        coder.write('\n\t\trealtime = state[0]')
        coder.write('\n\t\twhile lasttime < realtime and')
        coder.write(' capturecount < totalcaptures:')
        coder.write('\n\t\t\tstate[0] = lasttime')
        coder.write('\n\t\t\tlasttime += '+str(self.capture_increment))

        coder.write('\n')
        for fdex in range(fcnt):
            fu = self.statetargets[fdex+vcnt+scnt+1]
            funame = self.functions[fu].name
            coder.write('\n\t\t\t'+funame+'(state)')

        coder.write('\n\n\t\t\tfor cdex in range('+str(self.target_count)+'):')
        coder.write('\n\t\t\t\tdata[cdex,capturecount] = state[tdexes[cdex]]')
        coder.write('\n\t\t\tcapturecount += 1')
        coder.write('\n\t\tstate[0] = realtime')

        lookup = self._gibson_lookup(self.reactions)
        rcnt = len(self.reactions)
        # the lookup for the null reaction is every reaction!!!
        coder.write('\n\n\t\tif whichrxn == -1:')
        for rdex in range(rcnt):
            rname = 'rxnpropensity'+str(rdex)
            coder.write('\n\t\t\tpropensities['+str(rdex)+'] = '+rname+'(state)')

        for rdex in range(rcnt):
            coder.write('\n\t\telif whichrxn == '+str(rdex)+':')
            coder.write('\n\t\t\trxn'+str(rdex)+'(state)')
            for look in lookup[rdex]:
                rname = 'rxnpropensity'+str(look)
                coder.write('\n\t\t\tpropensities['+str(look)+']')
                coder.write(' = '+rname+'(state)')

    def _code_body_finalize(self,coder):
        coder.write('\n\n\treturn numpy.array(data,dtype = numpy.float)\n')

    def _code_body(self,coder):
        self._code_body_initialize(coder)
        self._code_body_loop(coder)
        self._code_body_finalize(coder)
        coder.write('\n'+'#'*80+'\n'*10)

    def __init__(self,*args,**kwargs):
        self._default('name','run',**kwargs)
        self._default('cytype','cpdef',**kwargs)
        self._default('capture_count',100,**kwargs)
        self._default('capture_increment',1,**kwargs)
        self._default('targets',['time'],**kwargs)
        self._default('species',[],**kwargs)
        self._default('reactions',[],**kwargs)
        self._default('constants',[],**kwargs)
        self._default('functions',[],**kwargs)
        self.target_count = len(self.targets)
        cwr.function.__init__(self,*args,**kwargs)
        self.statetargets = ['time'] +\
            lfu.grab_mobj_names(self.species) +\
            lfu.grab_mobj_names(self.constants) +\
            lfu.grab_mobj_names(self.functions)

#################################################################################

class species(lfu.run_parameter):

    def __init__(self,*args,**kwargs):
        self._default('name','aspecies',**kwargs)
        self._default('initial',0,**kwargs)
        pspace_axes =\
          [lpsp.pspace_axis(instance = self,key = 'initial',
              bounds = [0,10000000000],increment = 1,continuous = False)]
        self.pspace_axes = pspace_axes
        lfu.run_parameter.__init__(self,*args,**kwargs)

    def _sim_string(self):
        return self.name + ':' + str(lfu.clamp(int(self.initial),0,sys.maxint))

    def _string(self):
        return '\t' + self.name + ' : ' + str(self.initial)

    def _widget(self,*args,**kwargs):
        window = args[0]
        ensem = args[1]
        self._sanitize(*args,**kwargs)
        cartographer_support = lgm.cartographer_mason(window)
        self.widg_templates.append(
            lgm.interface_template_gui(
                mason = cartographer_support, 
                widgets = ['spin'], 
                instances = [[self]], 
                keys = [['initial']], 
                minimum_values = [[0]], 
                maximum_values = [[sys.maxint]], 
                initials = [[self.initial]], 
                box_labels = ['Initial Count'], 
                parameter_space_templates =\
                    [self.pspace_axes[0]]))
        self.widg_templates.append(
            lgm.interface_template_gui(
                keys = [['name']], 
                minimum_sizes = [[(150,50)]], 
                read_only = [True],
                instances = [[self]], 
                widgets = ['text'], 
                box_labels = ['Species Name']))
        lfu.run_parameter._widget(self,*args,from_sub = True)

################################################################################

class reaction(lfu.run_parameter):

    def _cython_react_body(self,coder):
        for u in self.used:
            uspec,ucnt = u
            udex = self.statetargets.index(uspec)
            coder.write('\n\tstate['+str(udex)+'] -= '+str(ucnt))
        for p in self.produced:
            pspec,pcnt = p
            pdex = self.statetargets.index(pspec)
            coder.write('\n\tstate['+str(pdex)+'] += '+str(pcnt))
        coder.write('\n')

    def _cython_react(self,dx):
        cy = cwr.function(
            name = 'rxn'+str(dx),
            argstring = 'double [:] state',
            cytype = 'cdef void')
        cy._code_body = self._cython_react_body
        return cy

    def _cython_valid_body(self,coder):
        for u in self.used:
            uspec,ucnt = u
            udex = self.statetargets.index(uspec)
            coder.write('\n\tif state['+str(udex)+'] < '+str(ucnt)+':')
            coder.write('return 0')
        coder.write('\n\treturn 1\n')

    def _cython_valid(self,dx):
        cy = cwr.function(
            name = 'rxnvalid'+str(dx),
            argstring = 'double [:] state',
            cytype = 'cdef bint')
        cy._code_body = self._cython_valid_body
        return cy

    def _cython_propensity_body(self,coder):
        coder.write('\n\tcdef double scnt')
        coder.write('\n\tcdef double population = 1.0')
        for u in self.used:
            uspec,ucnt = u
            udex = self.statetargets.index(uspec)
            coder.write('\n\tscnt = state['+str(udex)+']')
            for x in range(ucnt):
                subt = '' if x == 0 else ' - '+str(x)
                coder.write('\n\tpopulation *= scnt'+subt)
            if ucnt > 1:coder.write('\n\tpopulation /= '+str(ucnt))
        try: ratestring = str(float(self.rate))
        except ValueError:
            if self.rate in self.functionnames:
                ratestring = self.rate+'(state)'
                self.rate_is_function = True
            else:ratestring = str(self.variables[self.rate].value)
        coder.write('\n\treturn population * '+ratestring+'\n')
        # do i need to round down if extremely small??

    def _cython_propensity(self,dx):
        cy = cwr.function(
            name = 'rxnpropensity'+str(dx),
            argstring = 'double [:] state',
            cytype = 'cdef double')
        cy._code_body = self._cython_propensity_body
        return cy

    def __init__(self,*args,**kwargs):
        self._default('name','a reaction',**kwargs)
        self._default('rate',float(10.0),**kwargs)
        self._default('rate_is_function',False,**kwargs)
        self._default('used',[],**kwargs)
        self._default('produced',[],**kwargs)
        pspace_axes =\
            [lpsp.pspace_axis(instance = self,key = 'rate',
                bounds = [0.0000000000001,100000000000.0], 
                continuous = True)]
        self.pspace_axes = pspace_axes
        lfu.run_parameter.__init__(self,*args,**kwargs)

    def _sim_string(self):
        def spec(agent):return '(' + str(agent[1]) + ')' + agent[0]
        def side(agents):return '+'.join([spec(a) for a in agents])
        return side(self.used)+'->'+str(self.rate)+'->'+side(self.produced)

    def _string(self):
        def _string_agents(agents):
            if not agents: return 'nothing'
            else: return ' '.join([str(a) for a in lfu.flatten(agents)])
        used_line = agents_to_line(self.used)
        produced_line = agents_to_line(self.produced)
        rxn_string = ' '.join([used_line,str(self.rate),'->',produced_line])
        rxn_string = '\t' + rxn_string + ' : ' + self.label
        return rxn_string

    def _widget(self,*args,**kwargs):
        window = args[0]
        ensem = args[1]
        spec_list = ensem.run_params['species'].keys()
        self.used = [u for u in self.used if u[0] in spec_list]
        self.produced = [p for p in self.produced if p[0] in spec_list]
        cartographer_support = lgm.cartographer_mason(window)
        self._sanitize(*args,**kwargs)
        left_template = lgm.interface_template_gui(
            panel_position = (0, 2), 
            mason = cartographer_support, 
            layout = 'vertical', 
            keys = [['name'],['rate']], 
            instances = [[self],[self]], 
            widgets = ['text','text'], 
            minimum_sizes = [[(400,100)],[(100,100)]], 
            box_labels = ['Reaction Name','Reaction Rate'], 
            initials = [[self.name],[self.rate]], 
            parameter_space_templates = [None,self.pspace_axes[0]])
        agents_template = lgm.interface_template_gui(
            panel_position = (0, 0), 
            layout = 'horizontal', 
            widgets = ['check_spin_list','check_spin_list'], 
            keys = [['used'],['produced']], 
            instances = [[self],[self]], 
            labels = [spec_list,spec_list],
            box_labels = ['Reagents','Products'])
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['splitter'], 
                orientations = [['horizontal']], 
                templates = [[left_template,agents_template]]))
        lfu.run_parameter._widget(self,*args,from_sub = True)
        
################################################################################

class variable(lfu.run_parameter):
  
    def __init__(self,*args,**kwargs):
        self._default('name','a variable',**kwargs)
        self._default('value',1.0,**kwargs)
        pspace_axes = [
            lpsp.pspace_axis(instance = self,key = 'value',
                        bounds = [0.0,sys.float_info.max])]
        self.pspace_axes = pspace_axes
        lfu.run_parameter.__init__(self,*args,**kwargs)

    def _sim_string(self):
        return self.name + ':' + str(self.value)

    def _string(self):
        return '\t' + self.name + ' : ' + str(self.value)

    def _widget(self,*args,**kwargs):
        window = args[0]
        cartographer_support = lgm.cartographer_mason(window)
        self._sanitize(*args,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['spin'], 
                doubles = [[True]], 
                initials = [[float(self.value)]], 
                instances = [[self]], 
                keys = [['value']], 
                box_labels = ['Variable Value'], 
                mason = cartographer_support, 
                parameter_space_templates =\
                    [self.pspace_axes[0]]))
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['text'], 
                read_only = [True],
                keys = [['name']], 
                instances = [[self]], 
                initials = [[self.name]], 
                box_labels = ['Variable Name']))
        lfu.run_parameter._widget(self,*args,from_sub = True)

################################################################################

class function(lfu.run_parameter):

    def _cython_body(self,coder):
        def convert(substr):
            if substr in self.functionnames:return substr+'(state)'
            elif substr in self.variables:
                return str(self.variables[substr].value)
            elif substr in self.statetargets:
                tdx = self.statetargets.index(substr)
                return 'state['+str(tdx)+']'
            else:return substr
        fsplit = re.split('(\W)',self.func_statement)
        fstrng = ''.join([convert(substr) for substr in fsplit])
        coder.write('\n\tcdef double val = '+fstrng)
        doffset = len(self.statetargets) - len(self.functionnames)
        selfdex = self.functionnames.index(self.name)+doffset
        coder.write('\n\tstate['+str(selfdex)+'] = val')
        coder.write('\n\treturn val\n')

    def _cython(self,dx):
        cy = cwr.function(
            name = self.name,
            argstring = 'double [:] state',
            cytype = 'cdef double')
        cy._code_body = self._cython_body
        return cy

    def __init__(self,*args,**kwargs):
        self._default('name','a function',**kwargs)
        self._default('func_statement','',**kwargs)
        lfu.run_parameter.__init__(self,*args,**kwargs)

    # modifies sim_string for ext_signal support
    #   THIS NEEDS MORE CLEANUP
    def _sim_string_ext_signal(self,afunc):
        extcnt = afunc.count('external_signal')
        fixed = []
        for exts in range(extcnt):
            leads = afunc.find('external_signal(')
            subfunc = afunc[leads+16:]
            presig = afunc[:leads+16]
            postsig = subfunc[subfunc.find('&'):]
            filename = subfunc[:subfunc.find(postsig)]
            with open(filename,'r') as handle:
                extlines = [l.strip() for l in handle.readlines()]

            extstrx = StringIO()
            extstry = StringIO()
            for eline in extlines:
                eline = eline.strip()
                if not eline.count(',') > 0: continue
                elx,ely = eline.split(',')
                extstrx.write(str(elx));extstrx.write('$')
                extstry.write(str(ely));extstry.write('$')

            fixhash = '%#%'
            extstrx.write('@')
            fixval = extstrx.getvalue() + extstry.getvalue()
            fixed.append((fixhash,fixval))
            afunc = presig + fixhash + postsig
            for fix in fixed: afunc = afunc.replace(fix[0],fix[1])
        return afunc

    def _sim_string(self):
        sysstr = self.name + '=' + self.func_statement.replace(',','&')
        return self._sim_string_ext_signal(sysstr)

    def _string(self):
        return '\t' + self.name + ' : ' + self.func_statement

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self.widg_templates.append(
            lgm.interface_template_gui(
                keys = [['func_statement']], 
                instances = [[self]], 
                widgets = ['text'], 
                minimum_sizes = [[(200,75)]], 
                box_labels = ['Function Statement'], 
                initials = [[self.func_statement]]))
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['text'], 
                keys = [['name']], 
                read_only = [True],
                instances = [[self]], 
                initials = [[self.name]], 
                box_labels = ['Function Name']))
        lfu.run_parameter._widget(self,*args,from_sub = True)

################################################################################
################################################################################










