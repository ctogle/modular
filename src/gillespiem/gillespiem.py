import modular_core.fundamental as lfu
import modular_core.modules.simulationmodule as smd
import modular_core.parameterspace.parameterspaces as lpsp
import modular_core.cython.writer as cwr
import modular_core.io.output as lo

import pdb,os,sys,time,re
from cStringIO import StringIO

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
        self._default('optimize_reaction_order',False,**kwargs)
        #self._default('optimize_reaction_order',True,**kwargs)
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

    def _metamap_uniqueness(self):
        rps = self.parent.run_params
        pspace = self.parent.cartographer_plan.parameter_space
        pspace_instances = []
        if pspace:
            pspaxes = pspace.axes
            [pspace_instances.append(px.instance) for px in pspaxes]
        uniq = StringIO()

        uniq.write('||gillespiem||rxnrates{')
        rxns = rps['reactions']
        if rxns:
            rnames,rrates = [r.name for r in rxns],[r.rate for r in rxns]
            rnames,rrates = zip(*sorted(zip(rnames,rrates)))
            [uniq.write('|'+rn+':'+rr+'|') for rn,rr in zip(rnames,rrates)]

        uniq.write('}||speciesinitials{')
        specs = rps['species']
        if specs:
            snames = specs.keys()
            snames = sorted(snames)
            sinits = []
            for sn in snames:
                spec = specs[sn]
                if spec in pspace_instances:si = '$'
                else:si = str(spec.initial)
                uniq.write('|'+sn+':'+si+'|')

        uniq.write('}||variablesvalues{')
        varis = rps['variables']
        if varis:
            vnames = varis.keys()
            vnames = sorted(vnames)
            for vn in vnames:
                varib = varis[vn]
                if varib in pspace_instances:vv = '$'
                else:vv = str(varib.value)
                uniq.write('|'+vn+':'+vv+'|')

        uniq.write('}||functionstatements{')
        funcs = rps['functions']
        if funcs:
            fnames = funcs.keys()
            fsts = [funcs[f].func_statement for f in fnames]
            fnames,fsts = zip(*sorted(zip(fnames,fsts)))
            [uniq.write('|'+fn+':'+str(fs)+'|') for fn,fs in zip(fnames,fsts)]

        uniq.write('}||')
        print 'metamap uniqueness:',uniq.getvalue()
        return uniq.getvalue()

    def _write_mcfg(self,mcfg_path,ensem):
        rparams = ensem.run_params
        mcfg = StringIO()
        self._write_mcfg_run_param_key(rparams,'variables',mcfg)
        self._write_mcfg_run_param_key(rparams,'functions',mcfg)
        self._write_mcfg_run_param_key(rparams,'reactions',mcfg)
        self._write_mcfg_run_param_key(rparams,'species',mcfg)
        smd.simulation_module._write_mcfg(mcfg_path,ensem,mcfg)

    def _ext_special_funcs(self):
        heavi = heaviside()
        gnoise = gauss_noise()
        return [heavi,gnoise]

    def _ext_external_signal_funcs(self):
        rcnt = len(self.parent.run_params['reactions'])
        sigfuncs = []
        for spath in signalpaths.keys():
            sargs = {
                'signalpath':spath,
                'name':signalpaths[spath][0],
                'domain':signalpaths[spath][1],
                'rxncount':rcnt,
                    }
            sigfunc = external_signal_function(**sargs)
            sigfuncs.append(sigfunc)
        return sigfuncs

    def _ext_funcs_run(self,rxnorder = None):
        ptargs = self.parent.run_params['plot_targets']
        ccnt = self.parent.simulation_plan._capture_count()
        cinc = self.parent.simulation_plan._capture_increment()
        if rxnorder is None:orderedrxns = self.parent.run_params['reactions']
        else:
            orderedrxns = self.parent.run_params['reactions']
            orderedrxns = [orderedrxns[rdx] for rdx in rxnorder]
        cplan = self.parent.cartographer_plan
        fplan = self.parent.fitting_plan
        mappspace = cplan.use_plan
        fitting = fplan.use_plan
        runargs = {}
        if mappspace or fitting:
            paxes = cplan.parameter_space.axes
            paxnames = [a.instance.name.strip() for a in paxes]
            astring = ','.join(paxnames)
            for px,ax in zip(paxnames,paxes):runargs[px] = ax
        else:astring = ''
        if fitting:astring += ',timeout = 30.0'
        rargs = {
            'argstring':astring,
            'runargs':runargs,
            'capture_count':ccnt,
            'capture_increment':cinc,
            'targets':ptargs,
            'species':self.parent.run_params['species'],
            'reactions':orderedrxns,
            'constants':self.parent.run_params['variables'],
            'functions':self.parent.run_params['functions'],
            'countreactions':self.countreactions,
            'use_timeout':fitting,
                }
        return run(**rargs)

    # this returns functions for the extension
    # NOT TO BE CONFUSED WITH RXN RATE FUNCTIONS
    def _ext_funcs(self,rxnorder = None):
        runfunc = self._ext_funcs_run(rxnorder)
        rxns = self.parent.run_params['reactions']
        funcs = self.parent.run_params['functions']
        varis = self.parent.run_params['variables']
        funcnames = funcs.keys()
        rcnt = len(rxns)
        for r in rxns:
            r.statetargets = runfunc.statetargets
            r.functionnames = funcnames
            r.variables = varis
            r.rxncount = rcnt
        for f in funcnames:
            funcs[f].statetargets = runfunc.statetargets
            funcs[f].functionnames = funcnames
            funcs[f].variables = varis
            funcs[f].rxncount = rcnt
        rxnfuncs = [rx._cython_react(x) for x,rx in enumerate(rxns)]
        rxnvalds = [rx._cython_valid(x) for x,rx in enumerate(rxns)]
        rxnvalds = [x for x in rxnvalds if not x is None]
        rxnprops = [rx._cython_propensity(x) for x,rx in enumerate(rxns)]
        rxnrates = [funcs[fu]._cython(x) for x,fu in enumerate(funcs.keys())]
        funcs = [runfunc]
        specials = self._ext_special_funcs()
        extsignals = self._ext_external_signal_funcs()
        for es in extsignals:
            es.statetargets = runfunc.statetargets
            es.argstring = 'double['+str(len(runfunc.statetargets))+'] state'
        return specials+extsignals+rxnvalds+rxnprops+rxnrates+rxnfuncs+funcs

    # these are the keywords for the eventual cython module
    def _ext_kwargs(self,rxnorder = None):
        ext_kwargs = {
            'name':self.extensionname,
            'functions':self._ext_funcs(rxnorder),
                }
        return ext_kwargs

    def _increment_extensionname(self):
        self.extensionname = self.extensionname.replace('_','.',1)
        self.extensionname = lo.increment_filename(self.extensionname)
        self.extensionname = self.extensionname.replace('.','_',1)

    def _set_parameters_prepoolinit(self):
        if not self.extensionname in sys.modules.keys():
            insttime = time.time()
            if self.optimize_reaction_order:
                print 'creating temporary extension:',self.extensionname
                self._increment_extensionname()
                self.countreactions = True
                ext_kwargs = self._ext_kwargs()
                writer = cwr.extension(**ext_kwargs)
                writer._write()
                writer._install()
                mod = writer._import()
                rcounts = mod.run()
                print 'rcounts',rcounts
                rcountmap = list(zip(*sorted(zip(rcounts,range(len(rcounts)))))[1])
                rcountmap.reverse()
                print 'rcountmap',rcountmap
            else:rcountmap = None

            print 'creating temporary extension:',self.extensionname
            self._increment_extensionname()
            self.countreactions = False
            ext_kwargs = self._ext_kwargs(rcountmap)
            writer = cwr.extension(**ext_kwargs)
            writer._write()
            writer._install()
            #self._writer = writer
            print '\ninstallation took:',time.time() - insttime,'seconds\n'
        else:print '\ninstallion was not needed...\n'
        #self.dependencies = [lfu.get_cache_path('gillespiemext_0.so')]
        self.dependencies = [lfu.get_cache_path(self.extensionname)]

    def _set_parameters(self):
        module = __import__(self.extensionname)
        cplan = self.parent.cartographer_plan
        fplan = self.parent.fitting_plan
        mappspace = cplan.use_plan
        fitting = fplan.use_plan
        if mappspace or fitting:
            paxes = cplan.parameter_space.axes
            pargs = [float(px.instance.__dict__[px.key]) for px in paxes]
        else:pargs = []
        if fitting:pargs.append(3)
        self.sim_args = [module.run]+pargs

    def _reset_parameters(self):
        if self.extensionname in sys.modules.keys():
            del sys.modules[self.extensionname]
        ensem = self.parent
        self._gui_memory()
        ensem.simulation_plan._reset_criteria_lists()
        ensem.run_params['variables'] = {}
        ensem.run_params['species'] = {}
        ensem.run_params['reactions'] = []
        ensem.run_params['functions'] = {}
        ensem.run_params['plot_targets'][:] = ['time']
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
            smd.simulation_module._panel_templates(
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
    runfunc = args[0]
    result = runfunc(*args[1:])
    return result

###############################################################################

class external_signal_function(cwr.function):

    def _code_header(self,coder):
        cshape = (self.valuecount,)
        self._carray(coder,self.name+'_domain',cshape,spacer = '\n')
        self._carray(coder,self.name+'_codomain',cshape,spacer = '\n')
        coder.write('\n')
        for dx,x in enumerate(self.extstrx):
            coder.write(self.name+'_domain['+str(dx)+'] = '+x+';')
            if dx % 5 == 0 and dx > 0:coder.write('\n')
        coder.write('\n')
        for dy,y in enumerate(self.extstry):
            coder.write(self.name+'_codomain['+str(dy)+'] = '+y+';')
            if dy % 5 == 0 and dy > 0:coder.write('\n')
        coder.write('\ncdef int '+self.name+'lastindex = 0')
        coder.write('\n'+self.cytype+' '+self.name+'('+self.argstring+')')
        coder.write(self.cyoptions+':')

    def _code_body(self,coder):
        coder.write('\n\tglobal '+self.name+'_domain')
        coder.write('\n\tglobal '+self.name+'_codomain')
        coder.write('\n\tglobal '+self.name+'lastindex')
        sdx = self.statetargets.index(self.domain)
        coder.write('\n\tcdef double xcurrent = state['+str(sdx)+']')
        coder.write('\n\tcdef double domvalue = '+self.name+'_domain')
        coder.write('['+self.name+'lastindex]')
        coder.write('\n\tcdef double codomvalue')
        coder.write('\n\twhile xcurrent > domvalue:')
        coder.write('\n\t\t'+self.name+'lastindex'+' += 1')
        coder.write('\n\t\tdomvalue = '+self.name+'_domain')
        coder.write('['+self.name+'lastindex]')
        coder.write('\n\tcodomvalue = '+self.name+'_codomain')
        coder.write('['+self.name+'lastindex-1]')
        coder.write('\n\treturn codomvalue\n')

    def __init__(self,*args,**kwargs):
        self._default('name','extsignal',**kwargs)
        self._default('domain','time',**kwargs)
        self._default('signalpath','',**kwargs)
        self._default('rxncount',0,**kwargs)
        #self._default('cytype','cdef double',**kwargs)
        self._default('cytype','cdef inline double',**kwargs)
        self._default('cyoptions',' nogil',**kwargs)
        cwr.function.__init__(self,*args,**kwargs)
        with open(self.signalpath,'r') as handle:
            signal = handle.readlines()
            self.valuecount = len(signal)
            self.extstrx = []
            self.extstry = []
            for sigdex in range(len(signal)):
                sigp = signal[sigdex].strip()
                if not ',' in sigp:continue
                coma = sigp.find(',')
                self.extstrx.append(sigp[:coma])
                self.extstry.append(sigp[coma+1:])

############################################################################### 

class gauss_noise(cwr.function):

    def _code_body(self,coder):
        coder.write('\n\tcdef double gn = numpy.random.normal(0.0,1.0)')
        coder.write('\n\treturn value + value*(gn*'+str(self.SNR)+')\n')

    def __init__(self,*args,**kwargs):
        self._default('name','gauss_noise',**kwargs)
        self._default('argstring','double value',**kwargs)
        self._default('cytype','cdef inline double',**kwargs)
        #self._default('cyoptions',' nogil',**kwargs)
        self._default('SNR',1.0,**kwargs)
        cwr.function.__init__(self,*args,**kwargs)

############################################################################### 

class heaviside(cwr.function):

    def _code_body(self,coder):
        coder.write('\n\tif value >= 0.0:return 1.0')
        coder.write('\n\telse:return 0.0\n')

    def __init__(self,*args,**kwargs):
        self._default('name','heaviside',**kwargs)
        self._default('argstring','double value',**kwargs)
        self._default('cytype','cdef inline double',**kwargs)
        self._default('cyoptions',' nogil',**kwargs)
        cwr.function.__init__(self,*args,**kwargs)

############################################################################### 

class run(cwr.function):

    def _code_body_initialize(self,coder):
        scnt = len(self.species)
        rcnt = len(self.reactions)
        vcnt = len(self.constants)
        fcnt = len(self.functions)

        dshape = (self.target_count,self.capture_count)
        sshape = (1 + scnt + vcnt + fcnt,)
        cshape = (self.target_count,)

        #coder.write('\n\tprint ')
        #for ra in self.runargs:
        #    coder.write(ra+',')
        #coder.write('\'!\'\n')

        self._nparray(coder,'data',dshape)
        self._carray(coder,'capture',cshape)
        self._carray(coder,'state',sshape)
        for sdex in range(scnt):
            sp = self.statetargets[sdex+1]
            spec = self.species[sp]
            if spec.name in self.runargs:
                send = spec.name
            else:send = str(spec.initial)
            coder.write('\n\tstate['+str(sdex+1)+'] = '+send)
        for vdex in range(vcnt):
            va = self.statetargets[vdex+scnt+1]
            const = self.constants[va]
            if const.name in self.runargs:
                vend = const.name
            else:vend = str(const.value)
            coder.write('\n\tstate['+str(vdex+scnt+1)+'] = '+vend)
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
        #coder.write('\n\tcdef float imax = float(INT_MAX)')

        coder.write('\n\tcdef int whichrxn = 0')
        coder.write('\n\tcdef int rxncount = '+str(rcnt))
        pshape = (rcnt,)
        if self.countreactions:self._nparray(coder,'reactcounts',pshape)
        self._carray(coder,'reactiontable',pshape)
        self._carray(coder,'propensities',pshape)
        for rdex in range(rcnt):
            rname = 'rxnpropensity'+str(rdex)
            coder.write('\n\tpropensities['+str(rdex)+'] = '+rname+'(state)')

        #self._nparray(coder,'tdexes',cshape,dtype = 'numpy.long')
        self._carray(coder,'tdexes',cshape,dtype = 'int')
        for tdx in range(self.target_count):
            statedex = self.statetargets.index(self.targets[tdx])
            coder.write('\n\ttdexes['+str(tdx)+'] = '+str(statedex))
        
    # THIS SHOULD PROBABLY BE ACID TESTED
    def _gibson_lookup(self,rxns,funcs):
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

            #lookups[rdx].extend(alwayses)
            for alw in alwayses:
                if funcs[rxns[alw].rate]._depends_on('time',funcs):
                    lookups[rdx].append(alw)
                    continue
                for affs in r.affected_species:
                    if funcs[rxns[alw].rate]._depends_on(affs,funcs):
                        lookups[rdx].append(alw)
                        break

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

        if self.use_timeout:
            coder.write('\n\n\tcdef float start_time = timemodule.time()')
            coder.write('\n\tcdef bint timed_out = 0')

        coder.write('\n\n\twhile capturecount < totalcaptures')
        
        if self.use_timeout:
            coder.write(' and not timed_out:')
            coder.write('\n\t\ttimed_out = (timemodule.time()-start_time) > timeout')
        else:coder.write(':')

        coder.write('\n\t\ttotalpropensity = 0.0')
        rcnt = len(self.reactions)
        for pdex in range(rcnt):
            rxn = self.reactions[pdex]
            uchecks = []
            for u in rxn.used:
                uspec,ucnt = u
                udex = rxn.statetargets.index(uspec)
                uchecks.append('state['+str(udex)+'] >= '+str(ucnt))
            if uchecks:ucheckline = '\n\t\tif '+' and '.join(uchecks)+':'
            else:ucheckline = '\n\t\t'
            '''
            coder.write('\n\tif state['+str(udex)+'] < '+str(ucnt)+':')
            coder.write('return 0')
            '''
            #if self.reactions[pdex].requires_validator:
            #    coder.write('\n\t\tif rxnvalid'+str(pdex)+'(state):')
            #else:coder.write('\n\t\t')
            coder.write(ucheckline)
            coder.write('totalpropensity = totalpropensity + ')
            coder.write('propensities['+str(pdex)+']')
            coder.write('\n\t\treactiontable['+str(pdex)+'] = totalpropensity')

        coder.write('\n\n\t\tif totalpropensity > 0.0:')
        coder.write('\n\t\t\ttpinv = 1.0/totalpropensity')
        #coder.write('\n\t\t\tfor rtabledex in range(rxncount):')
        #coder.write('\n\t\t\t\treactiontable[rtabledex] *= tpinv')
        
        coder.write('\n\t\t\tdel_t = -1.0*log(<float>random.random())*tpinv')
        #coder.write('\n\t\t\trandr = <float>random.random()')
        coder.write('\n\t\t\trandr = <float>random.random()*totalpropensity')

        coder.write('\n\t\t\tfor rtabledex in range(rxncount):')
        coder.write('\n\t\t\t\tif randr < reactiontable[rtabledex]:')
        coder.write('\n\t\t\t\t\twhichrxn = rtabledex')
        coder.write('\n\t\t\t\t\tbreak\n')

        coder.write('\n\n\t\telse:')
        coder.write('\n\t\t\tdel_t = '+str(self.capture_increment))
        coder.write('\n\t\t\twhichrxn = -1')

        coder.write('\n\n\t\tstate[0] += del_t')
        coder.write('\n\t\trealtime = state[0]')

        coder.write('\n\t\twhile lasttime < realtime')
        coder.write(' and capturecount < totalcaptures:')

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

        lookup = self._gibson_lookup(self.reactions,self.functions)
        rcnt = len(self.reactions)

        # the lookup for the null reaction is every reaction!!!
        coder.write('\n\n\t\tif whichrxn == -1:')
        for rdex in range(rcnt):
            #rname = 'rxnpropensity'+str(rdex)
            #coder.write('\n\t\t\tpropensities['+str(rdex)+'] = '+rname+'(state)')

            rxn = self.reactions[rdex]
            uchecks = []
            for u in rxn.used:
                uspec,ucnt = u
                udex = rxn.statetargets.index(uspec)
                #uchecks.append('state['+str(udex)+']')
                uline = ['(state['+str(udex)+']-'+str(x)+')' for x in range(ucnt)]
                uline[0] = uline[0].replace('-0','')
                if ucnt > 1:uline.append(str(1.0/ucnt))
                uchecks.append('*'.join(uline))

            try: ratestring = str(float(rxn.rate))
            except ValueError:
                if rxn.rate in rxn.functionnames:
                    ratestring = rxn.rate+'(state)'
                    rxn.rate_is_function = True
                else:
                    vdex = rxn.statetargets.index(rxn.rate)
                    ratestring = 'state['+str(vdex)+']'

            uchecks.append(ratestring)
            rxnpropexprsn = '*'.join(uchecks)
            coder.write('\n\t\t\tpropensities['+str(rdex)+'] = '+rxnpropexprsn)

        rwhichrxnmap = range(rcnt)
        for rdex in rwhichrxnmap:
            coder.write('\n\t\telif whichrxn == '+str(rdex)+':')
            coder.write('\n\t\t\trxn'+str(rdex)+'(state)')
            if self.countreactions:
                coder.write('\n\t\t\treactcounts['+str(rdex)+'] += 1')
            for look in lookup[rdex]:
                #rname = 'rxnpropensity'+str(look)
                #coder.write('\n\t\t\tpropensities['+str(look)+']')
                #coder.write(' = '+rname+'(state)')

                rxn = self.reactions[look]
                uchecks = []
                for u in rxn.used:
                    uspec,ucnt = u
                    udex = rxn.statetargets.index(uspec)
                    uline = ['(state['+str(udex)+']-'+str(x)+')' for x in range(ucnt)]
                    uline[0] = uline[0].replace('-0','')
                    if ucnt > 1:uline.append(str(1.0/ucnt))
                    uchecks.append('*'.join(uline))

                try: ratestring = str(float(rxn.rate))
                except ValueError:
                    if rxn.rate in rxn.functionnames:
                        ratestring = rxn.rate+'(state)'
                        rxn.rate_is_function = True
                    else:
                        vdex = rxn.statetargets.index(rxn.rate)
                        ratestring = 'state['+str(vdex)+']'

                uchecks.append(ratestring)
                rxnpropexprsn = '*'.join(uchecks)
                coder.write('\n\t\t\tpropensities['+str(look)+'] = '+rxnpropexprsn)

    def _code_body_finalize(self,coder):
        if self.use_timeout:coder.write('\n\n\tif timed_out:return None')
        if self.countreactions:
            coder.write('\n\n\treturn numpy.array')
            coder.write('(reactcounts,dtype = numpy.float)\n')
        #coder.write('\n\n\tprint \'reactcounts\',')
        #[coder.write('reactcounts['+str(k)+'],') for k in range(len(self.reactions))]
        #coder.write('"!"')
        else:coder.write('\n\n\treturn numpy.array(data,dtype = numpy.float)\n')

    def _code_body(self,coder):
        self._code_body_initialize(coder)
        self._code_body_loop(coder)
        self._code_body_finalize(coder)
        coder.write('\n'+'#'*80+'\n'*10)

    def __init__(self,*args,**kwargs):
        self._default('countreactions',False,**kwargs)
        self._default('use_timeout',False,**kwargs)
        self._default('runargs',{},**kwargs)
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
        if not 'name' in kwargs.keys():
            namemsg = 'Provide a unique name for this species:\n\t'
            nametitle = 'Name Species'
            kwargs['name'] = lfu.gather_string(namemsg,nametitle)
        self._default('name','aspecies',**kwargs)
        self._default('initial',0,**kwargs)
        pspace_axes =\
          [lpsp.pspace_axis(instance = self,key = 'initial',
              bounds = [1,10000000000],increment = 0.0,
              continuous = False,caste = int)]
        self.pspace_axes = pspace_axes
        lfu.run_parameter.__init__(self,*args,**kwargs)

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
            #argstring = 'double['+str(self.rxncount)+'] state',
            argstring = 'double['+str(len(self.statetargets))+'] state',
            cytype = 'cdef inline void',
            cyoptions = ' nogil')
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
        if True:
            print 'rxn validators are off!!',self.name
            self.requires_validator = False
            return None



        if len(self.used) == 0:
            print 'rxn does not require validator!',self.name
            self.requires_validator = False
            return None
        cy = cwr.function(
            name = 'rxnvalid'+str(dx),
            #argstring = 'double['+str(self.rxncount)+'] state',
            argstring = 'double['+str(len(self.statetargets))+'] state',
            cytype = 'cdef inline bint',
            cyoptions = ' nogil')
        cy._code_body = self._cython_valid_body
        self.requires_validator = True
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
            else:
                vdex = self.statetargets.index(self.rate)
                ratestring = 'state['+str(vdex)+']'
        coder.write('\n\treturn population * '+ratestring+'\n')

    def _cython_propensity(self,dx):
        cy = cwr.function(
            name = 'rxnpropensity'+str(dx),
            #argstring = 'double['+str(self.rxncount)+'] state',
            argstring = 'double['+str(len(self.statetargets))+'] state',
            cytype = 'cdef inline double',
            cyoptions = ' nogil')
        cy._code_body = self._cython_propensity_body
        return cy

    def __init__(self,*args,**kwargs):
        self._default('name','a reaction',**kwargs)
        self._default('rate',float(10.0),**kwargs)
        self._default('rate_is_function',False,**kwargs)
        self._default('used',[],**kwargs)
        self._default('produced',[],**kwargs)
        lfu.run_parameter.__init__(self,*args,**kwargs)

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
            initials = [[self.name],[self.rate]])
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
        if not 'name' in kwargs.keys():
            namemsg = 'Provide a unique name for this variable:\n\t'
            nametitle = 'Name Variable'
            kwargs['name'] = lfu.gather_string(namemsg,nametitle)
        self._default('name','a variable',**kwargs)
        self._default('value',1.0,**kwargs)
        pspace_axes = [
            lpsp.pspace_axis(instance = self,key = 'value',
                        bounds = [1.0/sys.float_info.max,sys.float_info.max])]
        self.pspace_axes = pspace_axes
        lfu.run_parameter.__init__(self,*args,**kwargs)

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

signalnumber = 0
signalpaths = {}
class function(lfu.run_parameter):

    def _carray(self,coder,name,shape,dtype = 'double'):
        coder.write('\n\tcdef inline '+dtype+' '+name+'[')
        coder.write(','.join([str(s) for s in shape])+']')

    def _signal_name(self,signalpath,sdomain):
        global signalnumber
        sname = 'extsignal'+str(signalnumber)
        signalpaths[signalpath] = (sname,sdomain)
        signalnumber += 1
        return sname

    def _cython_body(self,coder):
        def convert(substr):
            if substr in self.functionnames:return substr+'(state)'
            elif substr in self.variables:
                #return str(self.variables[substr].value)
                tdx = self.statetargets.index(substr)
                return 'state['+str(tdx)+']'
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
            #argstring = 'double['+str(self.rxncount)+'] state',
            argstring = 'double['+str(len(self.statetargets))+'] state',
            cytype = 'cdef inline double',
            cyoptions = ' nogil')
        cy._code_body = self._cython_body
        if self._ext_signal():
            for esig in range(self.func_statement.count('external_signal')):
                sigpath,sigdomain = self._extract_signal_path(self.func_statement)
                if sigpath in signalpaths.keys():
                    esigname = signalpaths[sigpath][0]
                else:esigname = self._signal_name(sigpath,sigdomain)
                self._fix_signal_call(
                    self.func_statement,sigpath,sigdomain,esigname)
        return cy

    def _fix_signal_call(self,funcst,sigpath,sigdomain,signame):
        s = 'external_signal'                              
        funcst = funcst.replace(s,signame,1)
        funcst = funcst.replace(sigpath+',','',1)
        self.func_statement = funcst.replace(sigdomain,'state',1)

    def _extract_signal_path(self,func_statement):
        s = 'external_signal('                              
        path = func_statement[func_statement.find(s)+len(s):]
        path = path[:path.find(')')]
        path,domain = path.split(',')
        return path,domain

    def _ext_signal(self):
        if self.func_statement.count('external_signal'):return True
        else:return False

    def _depends_on(self,spec,funcs):
        for f in funcs:
            if self.func_statement.count(f) > 0:
                deps = funcs[f]._depends_on(spec)
                if deps:return True
        return self.func_statement.count(spec) > 0

    def __init__(self,*args,**kwargs):
        if not 'name' in kwargs.keys():
            namemsg = 'Provide a unique name for this function:\n\t'
            nametitle = 'Name Function'
            kwargs['name'] = lfu.gather_string(namemsg,nametitle)
        self._default('name','a function',**kwargs)
        self._default('func_statement','',**kwargs)
        lfu.run_parameter.__init__(self,*args,**kwargs)

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










