import modular_core.fundamental as lfu
import modular_core.modules.simulationmodule as smd
import modular_core.parameterspace.parameterspaces as lpsp

import modular_core.cython.writer as cwr

import modular_core.io.output as lo

import pdb,os,sys,time,re,numpy
import matplotlib.pyplot as plt
from cStringIO import StringIO

import PyDSTool as pdt

if __name__ == 'dstoolm.dstoolm':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgb = lfu.gui_pack.lgb
    lgd = lfu.gui_pack.lgd
if __name__ == '__main__':print 'dstoolm module'

###############################################################################

module_name = 'dstoolm'

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
        smd.simulation_module.__init__(self,*args,**kwargs)

    def _metamap_uniqueness(self):
        rps = self.parent.run_params
        pspace = self.parent.cartographer_plan.parameter_space
        pspace_instances = []
        if pspace:
            pspaxes = pspace.axes
            [pspace_instances.append(px.instance) for px in pspaxes]
        uniq = StringIO()

        uniq.write('||dstoolm||rxnrates{')
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

    def _set_parameters_prepoolinit(self):
        rxns  = self.parent.run_params['reactions']
        funcs = self.parent.run_params['functions']
        varis = self.parent.run_params['variables']
        specs = self.parent.run_params['species']
        ptrgs = self.parent.run_params['plot_targets'][:]

        etime = self.parent.simulation_plan._max_time()
        ctcnt = self.parent.simulation_plan._capture_count()
        ctinc = self.parent.simulation_plan._capture_increment()

        self.iconditions = {}
        self.cparameters = {}
        self.vsequations = []
        self.dsequations = {}
        self.fsequations = {}
        fsequations = {}
        cparameters = {}
        mname = 'dstoolm_model'
        domain = [0.0,etime]

        for fnkey in funcs:
            fn = funcs[fnkey]
            fsequations[fn.name] = str(fn.func_statement)
        for vrkey in varis:
            vr = varis[vrkey]
            cparameters[vr.name] = float(vr.value)

        speqns = {}
        for spkey in specs:speqns[spkey] = ''
        for rx in rxns:
            if rx.used:u = zip(*rx.used)[0]
            else:u = []
            if rx.produced:p = zip(*rx.produced)[0]
            else:p = []
            term = '*'.join([str(rx.rate)]+[x for x in u])
            for us in u:speqns[us] += '-'+term
            for ps in p:speqns[ps] += '+'+term

        for speq in speqns:
            speqn = speqns[speq]
            if speqn.startswith('+'):speqn = speqn.replace('+','',1)
            check = False
            while not check:
                check = True
                for feqn in fsequations:
                    if speqn.count(feqn) > 0:
                        feq = fsequations[feqn]
                        speqn = speqn.replace(feqn,'('+feq+')',1)
                        check = False
                        break

            check = False
            while not check:
                check = True
                for cpar in cparameters:
                    if speqn.count(cpar) > 0:
                        cpa = str(cparameters[cpar])
                        speqn = speqn.replace(cpar,'('+cpa+')',1)
                        check = False
                        break

            speqns[speq] = speqn

        for sp in speqns:
            print 'd',sp,'/dt = ',speqns[sp]
            self.iconditions[specs[sp].name] = int(specs[sp].initial)
            self.dsequations[specs[sp].name] = speqns[specs[sp].name]
            #self.vsequations.append(specs[sp].name)#??

        sargs = (mname,ptrgs,domain,ctcnt,ctinc,self.iconditions,
            self.cparameters,self.vsequations,self.dsequations,self.fsequations)
        self.sim_args = sargs

    def _set_parameters(self):
        self._set_parameters_prepoolinit()
        return

    def _reset_parameters(self):
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
    modelname,ptargs,tdomain,captcnt,captincr,icdict,pardict,vardict,varspecdict,fnspecdict = args
    dsargs = pdt.args()
    dsargs.name = modelname
    dsargs.ics = icdict
    dsargs.pars = pardict
    dsargs.tdata = tdomain
    #dsargs.vars = vardict
    dsargs.varspecs = varspecdict
    #dsargs.fnspecs = fnspecdict
    dsargs.algparams = {
        'init_step':captincr/10.0,
        'atol':0.1,
            }

    dsys = pdt.Generator.Vode_ODEsystem(dsargs)
    #dsys = pdt.Generator.Radau_ODEsystem(dsargs)
    traj = dsys.compute('demo')
    pts = traj.sample()

    rshape = (len(ptargs),captcnt)
    result = numpy.zeros(shape = rshape,dtype = numpy.float)
    result[0,:] = numpy.arange(tdomain[0],tdomain[1]+0.000000001,captincr)
    for timedx in range(result.shape[1]):
        itraj = traj(result[0,timedx])
        for targdx in range(1,result.shape[0]):
            result[targdx,timedx] = itraj[ptargs[targdx]]
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
        self._default('cytype','cdef double',**kwargs)
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
        self._default('cytype','cdef double',**kwargs)
        #self._default('cyoptions',' nogil',**kwargs)
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
        self._default('cyoptions',' nogil',**kwargs)
        cwr.function.__init__(self,*args,**kwargs)

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
        coder.write('\n\tcdef '+dtype+' '+name+'[')
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
            cytype = 'cdef double',
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

def plot(pts):
    plt.plot(pts['t'], pts['x'], label='x')
    plt.plot(pts['t'], pts['y'], label='y')
    plt.legend()
    plt.xlabel('t')
    plt.show()







