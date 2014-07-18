import libs.modular_core.libfundamental as lfu
import libs.modular_core.libfiler as lf
import libs.modular_core.libgeometry as lgeo
import libs.modular_core.libiteratesystem as lis
import libs.modular_core.libsettings as lset
import libs.modular_core.libmath as lm
import libs.modular_core.libmultiprocess as lmp



import libs.world3d_simulator.lib3dworld as l3d

import libs.modules.granular_support.libodesim as los
import libs.modules.granular_support.libnavierstokes as lns

import os
import sys
import types

import pdb

if len(sys.argv) > 1 and type(sys.argv[1]) is types.StringType:
	cmd = sys.argv[1]
	if cmd.startswith('los.test('):
		eval(cmd)

	elif cmd == '3dworld':
		l3d.world3d(objs = [l3d.cell()])

pdb.set_trace()







