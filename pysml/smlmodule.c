/**
 *  Python Module to interface libsml
 *
 *  Copyright © 2017, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
 *
 *  To compile this file into a Python module, run `python setup.py build`.
 *  The compiled binary will be put into build/lib.<platform>/sml.so.
 */

#include <Python.h>

#include <sml/sml_file.h>
#include <sml/sml_transport.h>

#define MODULE_DOCSTRING "Python Module to interface libsml."


PyObject *callback;
PyThreadState *thrstate;


void transport_receiver(unsigned char *buffer, size_t buffer_len) {
    // the buffer contains the whole message, with transport escape sequences.
    // these escape sequences are stripped here.
    sml_file *file = sml_file_parse(buffer + 8, buffer_len - 16);

    PyObject *vals = NULL;

    if( file->messages_len == 3 ){
        sml_get_list_response *resp = file->messages[1]->message_body->data;

        vals = PyList_New(0);

        double current;
        PyObject *pyentry;
        sml_list *entry = resp->val_list;
        while(entry != NULL){
            if( entry->value->type ){
                current = sml_value_to_double(entry->value);
                pyentry = PyTuple_New(2);
                PyTuple_SetItem(pyentry, 0, PyString_FromStringAndSize(
                    (const char *)entry->obj_name->str, entry->obj_name->len ));
                PyTuple_SetItem(pyentry, 1, PyFloat_FromDouble( current ));
                PyList_Append(vals, pyentry);
                Py_DECREF(pyentry);
            }
            entry = entry->next;
        }
    }

    // free the malloc'd memory
    sml_file_free(file);

    if( vals != NULL ){
        PyObject *args = PyTuple_New(1);
        PyTuple_SetItem(args, 0, vals);
        PyEval_RestoreThread(thrstate); /* acquire GIL */
        PyObject_CallObject(callback, args);
        Py_DECREF(args);
        thrstate = PyEval_SaveThread(); /* release GIL */
    }
}



static PyObject* py_sml_transport_listen(PyObject* self, PyObject* args){
    int fd;
    PyObject *cb;

    if( !PyArg_ParseTuple( args, "iO", &fd, &cb ) ){
        return NULL;
    }

    if( PyCallable_Check(cb) == 0 ){
        PyErr_SetString(PyExc_TypeError, "callback needs to be callable");
        return NULL;
    }

    callback = cb;
    Py_INCREF(cb);

    thrstate = PyEval_SaveThread(); /* release GIL */
    sml_transport_listen(fd, &transport_receiver);
    PyEval_RestoreThread(thrstate); /* acquire GIL */

    Py_RETURN_TRUE;
}


/**
 *  Module initialization.
 */


static PyMethodDef smlmodule_Methods[] = {
    { "sml_transport_listen", (PyCFunction)py_sml_transport_listen, METH_VARARGS,
        "sml_transport_listen(fd, callback)\n"
        "Listen on fd and call callback with received data (loops indefinitely!)."},
    { NULL, NULL, 0, NULL }
};

#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC initsml(void){
    PyObject* module;
    module = Py_InitModule3( "sml", smlmodule_Methods, MODULE_DOCSTRING );
}


