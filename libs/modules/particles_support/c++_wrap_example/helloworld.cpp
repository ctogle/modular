#include <Python.h>
#include <iostream>

using namespace std;

int simulate(const char * system_string)
{
	return 1000;
}





static PyObject *WrapError;

static PyObject *
simulate_wrap(PyObject *self, PyObject *args)
{
	const char *command;
	int sts;

	if (!PyArg_ParseTuple(args, "s", &command))
		return NULL;

	sts = simulate(command);
	if (sts < 0)
	{
		PyErr_SetString(WrapError, "simulate command failed");
		return NULL;
	}

	return PyLong_FromLong(sts);
}

static PyMethodDef WrapMethods[] = {
	{"simulate",  simulate_wrap, METH_VARARGS, "perform simulation."},
	{NULL, NULL, 0, NULL}/* Sentinel */
};

PyMODINIT_FUNC
inithelloworld(void)
{
	PyObject *m;
	m = Py_InitModule("helloworld", WrapMethods);
	if (m == NULL) return;

	WrapError = PyErr_NewException("WrapError.error", NULL, NULL);
	Py_INCREF(WrapError);
	PyModule_AddObject(m, "error", WrapError);
}




