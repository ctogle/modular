#include <Python.h>
#include "arrayobject.h"
#include <iostream>


/* new header since this is the new entry point */
#include "FRFMC_main.h"


using namespace std;

static PyObject *WrapError;

//takes the system encoded in a string from python
//returns the data 1-1 with the labels of what it represents
// should be just like the motif for cython ->
//  same finalize_data procedure
static PyObject *simulate_wrap(PyObject *self, PyObject *args)
{
	const char *s;
	PyArg_ParseTuple(args, "s", &s);
	cout << "system_string\t" << s << "\n";


	/* this level of structure has to be parsed here...? */
	int num_targets = 3;
	int num_points = 100;


	npy_intp dim[2] = {num_targets,num_points};
	PyArrayObject *array = (PyArrayObject *) PyArray_SimpleNew(2, dim, PyArray_DOUBLE);
	double *buffer = (double*)array->data;



	/*
	 * this is the contact point between wrapper and simulation
	 * 
	 * particles is a good example module because it was written
	 *  with absolutely no prior knowledge of modular
	 * it uses an ifstream/ofstream for input/output
	 * 
	 * this is what must be effectively overridden
	 * 
	 * WIn is an ifstream ->
	 * WIn.open(InputFile.c_str());
	 * 
	 * the naivest approach:
	 *  use the system_string to create the input file
	 *  use the resultant output file to create a data array and
	 *   target list to return
	 * 
	 * call the main function passing in the filename
	 *  just as you would running the simulation stand-alone
	 * this expects the stand-alone to return an exit-status int
	 * */
	int i;
	for (i =0; i<num_targets*num_points; i++)
	{
		buffer[i] = double(i);
	}



	return PyArray_Return(array);
}

//main_wrap - need a function to call main
static PyObject *main_wrap(PyObject *self, PyObject *args)
{
	int i = 2;
	char *s;
	char* es[] = { "dummyname", "filename", NULL };
	PyArg_ParseTuple(args, "is", &i, &s);
	cout << ' i :' << i << ' s :' << s << '\n';
	mainly(i, *es);
	return NULL;
}

static PyMethodDef WrapMethods[] = {
	{"simulate", simulate_wrap, METH_VARARGS, 
					"perform simulation."},
	{"stand_alone", main_wrap, METH_VARARGS, 
		"perform simulation stand alone."},
	{NULL, NULL, 0, NULL}/* Sentinel */
};

PyMODINIT_FUNC
initgeneric_wrap(void)
{
	PyObject *m;
	m = Py_InitModule("generic_wrap", WrapMethods);
	if (m == NULL) return;
	import_array();
	WrapError = PyErr_NewException("WrapError.error", NULL, NULL);
	Py_INCREF(WrapError);
	PyModule_AddObject(m, "error", WrapError);
}




