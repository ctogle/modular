# distutils: language = c++

########################################################################

import numpy as np
import pdb
'''
########################################################################
# sample bindings
########################################################################

cdef extern from "src_sample/ctestlib.h":
	cdef cppclass testClass:
		testClass() except +
		int foobar
		void test()

cdef class py_testClassss:

	cdef testClass* thisptr # hold a C++ instance which we're wrapping

	def __cinit__(self):
		self.thisptr = new testClass()

	def __dealloc__(self):
		del self.thisptr

	def test(self):
		self.thisptr.test()

########################################################################

cdef extern from "src_sample/ctest.h":
	cdef int main_test() except +

cpdef int py_main_test():
	return main_test()

########################################################################

cdef extern from "src_sample/ctestlib2.h":
	cdef void test2() except +

cpdef py_test2():
	test2()

########################################################################
'''


########################################################################
# bullet 3 bindings
########################################################################

cdef extern from "src_b3/src/LinearMath/btScalar.h":
	ctypedef float btScalar

########################################################################

cdef extern from "src_b3/src/LinearMath/btVector3.h":
	cdef cppclass btVector3:
		btVector3() except +
		btVector3(btScalar, btScalar, btScalar) except +

		btScalar length()
		btVector3 normalized()
		void setValue(btScalar, btScalar, btScalar)

		btScalar[4] m_floats

cdef class pybtVector3:

	cdef btVector3 thisptr
	comps = np.zeros(4, dtype = np.float)

	def __cinit__(self, *args, **kwargs):
		if len(args) < 3: self.thisptr = btVector3()
		else:
			x_,y_,z_ = args[0],args[1],args[2]
			self.thisptr = btVector3(x_,y_,z_)
		self._copy_components_()

	def _copy_components_(self):
		self.comps[0] = self.thisptr.m_floats[0]
		self.comps[1] = self.thisptr.m_floats[1]
		self.comps[2] = self.thisptr.m_floats[2]
		self.comps[3] = self.thisptr.m_floats[3]

	def setValue(self, x, y, z):
		self.thisptr.setValue(x, y, z)
		self._copy_components_()

	def __str__(self):
		self._copy_components_()
		return 'vector3: ' + self.comps.__str__()

	def length(self):
		return self.thisptr.length()

	def normalize(self):
		self.thisptr = self.thisptr.normalized()
		self._copy_components_()

########################################################################

cdef extern from "src_b3/src/LinearMath/btTransform.h":
	cdef cppclass btTransform:
		btTransform() except +

cdef class pybtTransform:

	cdef btTransform *thisptr # hold a C++ instance which we're wrapping

	def __cinit__(self): self.thisptr = new btTransform()
	def __dealloc__(self): del self.thisptr

########################################################################
cdef extern from "src_b3/src/BulletCollision/CollisionShapes/btBoxShape.h": pass
'''
cdef extern from "src_b3/src/BulletCollision/CollisionShapes/btBoxShape.h":
	cdef cppclass btBoxShape:
		#btBoxShape() except +
		btBoxShape(btVector3) except +
		void calculateLocalInertia(btScalar, btVector3)

cdef class pybtBoxShape:

	cdef btBoxShape *thisptr # hold a C++ instance which we're wrapping
	cdef btVector3 boxHalfExtents

	def __cinit__(self):
		self.boxHalfExtents = btVector3(1,1,1)
		self.thisptr = new btBoxShape(self.boxHalfExtents)
	def __dealloc__(self): del self.thisptr
'''
########################################################################
'''
cdef extern from "src_b3/src/btBulletDynamicsCommon.h":
	cdef cppclass btRigidBody:
		btRigidBody(btRigidBody.btRigidBodyConstructionInfo) except +
		bint isInWorld()
	#cdef cppclass btRigidBodyConstructionInfo:
	#	#cdef cppclass btRigidBodyConstructionInfo:
	#		btRigidBodyConstructionInfo(btScalar, btMotionState*, btCollisionShape*, btVector3&) except +

cdef class pybtRigidBody:

	cdef btRigidBody *thisptr # hold a C++ instance which we're wrapping

	cdef btScalar mass
	cdef btVector3 localInertia
	#cdef btBoxShape colShape
	#mass = 1.0
	#localInertia = btVector3(0,0,0)
	#colShape = btBoxShape(btVector3(1,1,1))
	#colShape.calculateLocalInertia(mass,localInertia)

	#startTransform = btTransform()
	#startTransform.setIdentity()
	#startTransform.setOrigin(btVector3(
	#	btScalar(0.0),btScalar(0.0),btScalar(0.0)))

	#myMotionState = btDefaultMotionState(startTransform)

	#rbInfo = btRigidBody.btRigidBodyConstructionInfo(mass,myMotionState,colShape,localInertia)

	def __cinit__(self):
		self.mass = 1.0
		#self.localInertia = btVector(0,0,0)

		#//using motionstate is recommended, it provides interpolation capabilities, and only synchronizes 'active' objects
		#btDefaultMotionState* myMotionState = new btDefaultMotionState(startTransform);
		#btRigidBody::btRigidBodyConstructionInfo rbInfo(mass,myMotionState,colShape,localInertia);
		#btRigidBody* body = new btRigidBody(rbInfo);

		#m_dynamicsWorld->addRigidBody(body);

		#self.thisptr = new btRigidBody(self.rbInfo)
		pass

	def __dealloc__(self): del self.thisptr
	def isInWorld(self): return self.thisptr.isInWorld()
'''
########################################################################
cdef extern from "src_b3/src/BulletCollision/CollisionDispatch/btCollisionConfiguration.h": pass
'''
cdef extern from "src_b3/src/BulletCollision/CollisionDispatch/btCollisionConfiguration.h":
	cdef cppclass btDefaultCollisionConfiguration:
		btDefaultCollisionConfiguration() except +

cdef class pybtDefaultCollisionConfiguration:

	cdef btDefaultCollisionConfiguration *thisptr

	def __cinit__(self): self.thisptr = new btDefaultCollisionConfiguration()
	def __dealloc__(self): del self.thisptr
'''
########################################################################
cdef extern from "src_b3/src/BulletCollision/CollisionDispatch/btConvexPlaneCollisionAlgorithm.h": pass
cdef extern from "src_b3/src/Bullet3Common/b3AlignedAllocator.h": pass






