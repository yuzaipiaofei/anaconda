/*
 * PYDBCS (an string Python C-extension-type wrapper for WIDESTR)
 * Copyright (C) 2000  Adrian D. Havill
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 * 
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Adrian D. Havill can be reached at havill@redhat.com or by mailing
 * to:
 *     Red Hat Japan
 *     Sotokanda 3-14-10
 *     Chiyoda-ku, Tokyo-to
 *     JAPAN  101-0021
 */

#include <assert.h>
#include <ctype.h>
#include <limits.h>
#include <locale.h>

#include "Python.h"
#include "widestr.h"
#include "pydbcs.h"

typedef struct {
  PyObject_HEAD
  int rw;
  wide_str *s;
} DBCS_type;

static const size_t default_inc = 32;

static int is_DBCS_type(PyObject *);
static DBCS_type *instantiate(size_t, wide_enc, int);
static DBCS_type *duplicate(DBCS_type *);
static const char *enc_to_mbs(wide_enc);
static wide_str *obj_to_str(PyObject *, size_t, wide_enc);
static unsigned *list_to_array(PyObject *);
static PyObject *new_string(PyObject *, PyObject *, PyObject *, int);

static PyObject *DBCSww(DBCS_type *, PyObject *, PyObject *);

static void DBCSdealloc(DBCS_type *);
static int DBCSprint(DBCS_type *, FILE *, int);
static PyObject *DBCSgetattr(DBCS_type *, char *);
static int DBCSsetattr(DBCS_type *, char *, PyObject *);
static int DBCScompare(DBCS_type *, DBCS_type *);
static PyObject *DBCSrepr(DBCS_type *);
static long DBCShash(DBCS_type *);
static PyObject *DBCScall(DBCS_type *, PyObject *, PyObject *);
static PyObject *DBCSstr(DBCS_type *);

static int DBCSlength(DBCS_type *);
static PyObject *DBCSconcat(DBCS_type *, PyObject *);
static PyObject *DBCSrepeat(DBCS_type *, int);
static PyObject *DBCSitem(DBCS_type *, int);
static PyObject *DBCSslice(DBCS_type *, int, int);
static int DBCSassign_item(DBCS_type *, int, PyObject *);
static int DBCSassign_slice(DBCS_type *, int, int, PyObject *);

static PyObject *DBCSstring(PyObject *, PyObject *, PyObject *);
static PyObject *DBCSstrbuf(PyObject *, PyObject *, PyObject *);
static PyObject *DBCSenc(PyObject *, PyObject *);
static PyObject *DBCSinc(PyObject *, PyObject *);

static PySequenceMethods DBCSr_sequence_methods = {
  (inquiry)          DBCSlength,          /* sq_length    "len(x)"     */
  (binaryfunc)       DBCSconcat,          /* sq_concat    "x + y"      */
  (intargfunc)       DBCSrepeat,          /* sq_repeat    "x * n"      */
  (intargfunc)       DBCSitem,            /* sq_item      "x[i]        */
  (intintargfunc)    DBCSslice            /* sq_slice     "x[i:j]"     */
};

static PySequenceMethods DBCSrw_sequence_methods = {
  (inquiry)          DBCSlength,          /* sq_length    "len(x)"     */
  (binaryfunc)       DBCSconcat,          /* sq_concat    "x + y"      */
  (intargfunc)       DBCSrepeat,          /* sq_repeat    "x * n"      */
  (intargfunc)       DBCSitem,            /* sq_item      "x[i]        */
  (intintargfunc)    DBCSslice,           /* sq_slice     "x[i:j]"     */
  (intobjargproc)    DBCSassign_item,     /* sq_ass_item  "x[i] = v"   */
  (intintobjargproc) DBCSassign_slice     /* sq_ass_slice "x[i:j] = v" */
};

static PyTypeObject DBCSr = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                             /* ob_size */
  "String" ,                     /* tp_name */
  sizeof(DBCS_type),             /* tp_basicsize */
  0,                             /* tp_itemsize */
  (destructor)  DBCSdealloc,     /* tp_dealloc  ref-count==0  */
  (printfunc)   DBCSprint,       /* tp_print    "print x"     */
  (getattrfunc) DBCSgetattr,     /* tp_getattr  "x.attr"      */
  (setattrfunc) NULL,            /* tp_setattr  "x.attr = v"  */
  (cmpfunc)     DBCScompare,     /* tp_compare  "x > y"       */
  (reprfunc)    DBCSrepr,        /* tp_repr     `x`           */
  NULL,                          /* tp_as_number   +,-,*,/,%,&,>>,pow */
  &DBCSr_sequence_methods,       /* tp_as_sequence +,[i],[i:j],len,   */
  NULL,                          /* tp_as_mapping  [key], len, ...    */
  (hashfunc)     DBCShash,       /* tp_hash     "dict[x]" */
  (ternaryfunc)  DBCScall,       /* tp_call     "x()"     */
  (reprfunc)     DBCSstr,        /* tp_str      "str(x)"  */
  (getattrofunc) NULL,           /* tp_getattro           */
  (setattrofunc) NULL,           /* tp_setattro           */
  NULL,                          /* tp_as_buffer */
  0,                             /* feature flags */
  STRING_INST_DOC 
};

static PyTypeObject DBCSrw = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                             /* ob_size */
  "StringBuffer",                /* tp_name */
  sizeof(DBCS_type),             /* tp_basicsize */
  0,                             /* tp_itemsize */
  (destructor)  DBCSdealloc,     /* tp_dealloc  ref-count==0  */
  (printfunc)   DBCSprint,       /* tp_print    "print x"     */
  (getattrfunc) DBCSgetattr,     /* tp_getattr  "x.attr"      */
  (setattrfunc) DBCSsetattr,     /* tp_setattr  "x.attr = v"  */
  (cmpfunc)     DBCScompare,     /* tp_compare  "x > y"       */
  (reprfunc)    DBCSrepr,        /* tp_repr     `x`           */
  NULL,                          /* tp_as_number   +,-,*,/,%,&,>>,pow */
  &DBCSrw_sequence_methods,      /* tp_as_sequence +,[i],[i:j],len,   */
  NULL,                          /* tp_as_mapping  [key], len, ...    */
  (hashfunc)     NULL,           /* tp_hash     "dict[x]" */
  (ternaryfunc)  DBCScall,       /* tp_call     "x()"     */
  (reprfunc)     DBCSstr,        /* tp_str      "str(x)"  */
  (getattrofunc) NULL,           /* tp_getattro           */
  (setattrofunc) NULL,           /* tp_setattro           */
  NULL,                          /* tp_as_buffer */
  0,                             /* feature flags */
  STRINGBUFFER_INST_DOC 
};

static struct PyMethodDef DBCS_methods[] = {
  {"wordwrap", (PyCFunction) DBCSww,
               METH_VARARGS|METH_KEYWORDS, DBCS_WW_METHOD_DOC },
  {NULL}
};

static int
is_DBCS_type (PyObject *v) {
  return NULL != v && (v->ob_type == &DBCSr || v->ob_type == &DBCSrw);
}

static DBCS_type *
instantiate (size_t inc, wide_enc enc, int rw) {
  DBCS_type *obj;
  wide_str *wcs;

  if (NULL == (wcs = malloc(sizeof(wide_str)))) return NULL;
  if (NULL == (obj = PyObject_NEW(DBCS_type, rw ? &DBCSrw : &DBCSr))) {
    free(wcs);
    return NULL;
  }
  obj->rw = rw;
  obj->s = wide_init_str(wcs, inc, enc);
  return obj;
}

static DBCS_type *
duplicate (DBCS_type *orig) {
  DBCS_type *obj;
  wide_str *s;

  if (NULL == orig) return NULL;
  if (NULL == (s = wide_clone_str(orig->s))) {
    PyErr_NoMemory();
    return NULL;
  }
  obj = PyObject_NEW(DBCS_type, orig->rw ? &DBCSrw : &DBCSr);
  if (NULL == obj) {
    wide_alloc_str(s, 0);
    Py_Free(s);
    return NULL;
  }
  obj->s = s;
  obj->rw = orig->rw;
  return obj;
}

static const char *
enc_to_mbs (wide_enc enc) {
  const char *s;

  switch (enc) {
  case wide_utf_8:      s = "utf-8"; break;
  case wide_euc_cn:     s = "euc-cn"; break;
  case wide_euc_tw:     s = "euc-tw"; break;
  case wide_euc_jp:     s = "euc-jp"; break;
  case wide_euc_kr:     s = "euc-kr"; break;
  case wide_euc_kp:     s = "euc-kp"; break;
  case wide_euc_vn:     s = "euc-vn"; break;
  case wide_iso_8859_1: s = "iso-8859-1"; break;
  default: s = NULL;
  }
  return s;
}

static wide_str *
obj_to_str (PyObject *obj, size_t inc, wide_enc enc) {
  wide_str *wcs;

  wcs = wide_init_str(Py_Malloc(sizeof(wide_str)), inc, enc);
  if (NULL == wcs) return NULL;
  if (NULL != obj && Py_None != obj) {
    if (is_DBCS_type(obj)) {
      DBCS_type *s;

      s = (DBCS_type *) obj;
      if (wide_get_enc(s->s) != enc) {
        PyErr_SetString(PyExc_TypeError, "dbcs must be the same encoding");
	goto cleanup;
      }
      wcs = wide_get_str(wcs, s->s, 0, wide_get_len(s->s));
      if (NULL == wcs) goto cleanup;
    }
    else if (PyString_Check(obj)) {
      const char *mbs;

      mbs = PyString_AS_STRING(obj);
      if (NULL == wide_conv_mbs(wcs, mbs)) goto cleanup;
    }
    else if (PyInt_Check(obj) || PyLong_Check(obj)) {
      long c;

      c = PyInt_Check(obj) ? PyInt_AS_LONG(obj) : PyLong_AsLong(obj);
      if (c > USHRT_MAX || c < 0 || !wide_check_char(c, enc)) {
        PyErr_SetString(PyExc_ValueError, "invalid character for encoding");
	goto cleanup;
      }
      if (NULL == wide_ins_char(wcs, (wide_char) c, 0)) goto cleanup;
    }
    else if (PyList_Check(obj)) {
      int len, i;
      wide_str *x;

      len = PyList_GET_SIZE(obj);
      for (i = 0; i < len; i++) {
	x = obj_to_str(PyList_GET_ITEM(obj, i), inc, enc);
	if (NULL == x) goto cleanup;
	if (NULL == wide_ins_str(wcs, x, wide_get_len(wcs))) goto cleanup;
	if (NULL == wide_alloc_str(x, 0)) goto cleanup;
        Py_Free(x);
      }
    }
    else if (NULL != obj) {
      PyErr_SetString(PyExc_TypeError, "can't convert to a dbcs");
      goto cleanup;
    }
  }
  return wcs;
cleanup:
  if (NULL != wcs) {
    wide_alloc_str(wcs, 0);
    Py_Free(wcs);
  }
  if (!PyErr_Occurred())
    PyErr_NoMemory();
  return NULL;
}

static unsigned *
list_to_array (PyObject *obj) {
  unsigned *list;
  size_t len, i;

  assert(NULL != obj);

  len = PyList_GET_SIZE(obj);
  if (NULL == (list = Py_Malloc(sizeof(unsigned) * (len + 1)))) return NULL;
  for (i = 0; i < len; i++) {
    PyObject *item;
    long j;

    item = PyList_GET_ITEM(obj, i);
    if (!PyInt_Check(item)) {
      PyErr_SetString(PyExc_TypeError, "list items must be integers");
      Py_Free(list);
      return NULL;
    }
    j = PyInt_AS_LONG(item);
    if (j > UINT_MAX || j == PyInt_GetMax())
      j = UINT_MAX;
    list[i] = (unsigned) j;
  }
  list[i] = 0;
  return list;
}

static PyObject *
new_string (PyObject *self, PyObject *args, PyObject *keywds, int w) {
  const char *x = NULL, *y;
  wide_enc enc;
  int inc = default_inc;
  PyObject *obj = NULL;
  static char *kwlist[] = { "s", "enc", "inc", "mutable", NULL };

  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|Ozii", kwlist,
      &obj, &x, &inc, &w))
    return NULL;
  if ((NULL == x || '\0' == *x) && is_DBCS_type(obj)) {
    DBCS_type *s;

    s = (DBCS_type *) obj;
    enc = wide_get_enc(s->s);
  }
  else {
    if (NULL == x || '\0' == *x) {
      const char *l, *variant;

      if (NULL == (l = setlocale(LC_CTYPE, NULL)))
        l == "C";
      variant = strrchr(l, '.');
      if (NULL != variant && strncasecmp(variant, ".utf", 4) == 0)
        x = "utf-8";
      else if (strncasecmp(l, "zh", 2) == 0 && strlen(l) > 2) {
        if (strncasecmp(l + 3, "TW", 2) == 0)
          x = "euc-tw";
        else if (strncasecmp(l + 3, "HK", 2) == 0)
          x = "euc-tw";
        else x = "euc-cn"; /* XXX: Singapore (SG) is simplified, yes? */
      }
      else if (strncasecmp(l, "ja", 2) == 0)
        x = "euc-jp";
      else if (strncasecmp(l, "ko", 2) == 0 && strlen(l) > 2)
        x = strncasecmp(l + 3, "KR", 2) == 0 ? "euc-kr" : "euc-kp";
      else if (strncasecmp(l, "vi", 2) == 0)
        x = "euc-vn";
      else x = "iso-8859-1";
    }
    for (enc = (wide_enc) 0; NULL != (y = enc_to_mbs(enc)); enc++)
      if (strcasecmp(x, y) == 0)
        break;
    if (NULL == y) {
      PyErr_SetString(PyExc_ValueError, "unknown/unsupported encoding");
      return NULL;
    }
  }
  if (inc < 0) {
    PyErr_SetString(PyExc_ValueError, "inc cannot be negative");
    return NULL;
  }
  if (NULL == (self = (PyObject *) instantiate(inc, enc, w))) return NULL;
  if (NULL != obj) {
    wide_str *s;

    if (NULL == (s = obj_to_str(obj, inc, enc))) {
      Py_DECREF(self);
      return NULL;
    }
    ((DBCS_type *) self)->s = s;
  }
  return self;
}

/**************************************************************************/
/******                                                              ******/
/******                             METHODS                          ******/
/******                                                              ******/
/**************************************************************************/

static PyObject *
DBCSww (DBCS_type *self, PyObject *args, PyObject *keywds) {
  DBCS_type *d;
  PyObject *margin, *htab = NULL, *vtab = NULL;
  wide_fmt fmt = { 0 };
  int strip = 0, ff = 0;
  static char *kwlist[] = { "margin", "strip", "htab", "vtab", "ff", NULL };

  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O!|iO!O!i", kwlist,
      &PyList_Type, &margin, &strip, &PyList_Type, &htab, &PyList_Type,
      &vtab, &ff))
    return NULL;
  if (NULL == (d = duplicate(self))) return NULL;
  if (NULL != margin) {
    if (NULL == (fmt.margin = list_to_array(margin))) goto cleanup;
  }
  else fmt.margin = NULL;
  if (NULL != htab) {
    if (NULL == (fmt.h_tab = list_to_array(htab))) goto cleanup;
  }
  else fmt.h_tab = NULL;
  if (NULL != vtab) {
    if (NULL == (fmt.v_tab = list_to_array(vtab))) goto cleanup;
  }
  else fmt.h_tab = NULL;
  fmt.reformat = strip;
  if (ff < 0) {
    PyErr_SetString(PyExc_ValueError, "page length must not be negative");
    goto cleanup;
  }
  else if (ff > INT_MAX || ff == PyInt_GetMax())
    ff = UINT_MAX;
  if (NULL == wide_fmt_str(d->s, &fmt)) goto cleanup;
  Py_Free(fmt.margin);
  Py_Free(fmt.h_tab);
  Py_Free(fmt.v_tab);
  return (PyObject *) d;
cleanup:
  Py_DECREF(d);
  PyErr_NoMemory();
  Py_Free(fmt.margin);
  Py_Free(fmt.h_tab);
  Py_Free(fmt.v_tab);
  return NULL;
}
  

/**************************************************************************/
/******                                                              ******/
/******                       STANDARD OPERATIONS                    ******/
/******                                                              ******/
/**************************************************************************/
 
static void
DBCSdealloc (DBCS_type *self) {
  wide_alloc_str(self->s, 0);
  free(self->s);
  PyMem_DEL(self);
}

static int
DBCSprint (DBCS_type *self, FILE *stream, int flags) {
  const char *expr;

  expr = self->ob_type->tp_name;
  wide_debug_str(stream, self->s, flags & Py_PRINT_RAW, expr, NULL, 0);
  return 0;
}

static PyObject *
DBCSgetattr (DBCS_type *self, char *attr) {
  assert(NULL != attr);

  if (strcmp(attr, "mutable") == 0) return PyInt_FromLong(self->rw);
  else if (strcmp(attr, "len") == 0) {
    size_t len;

    len = wide_get_len(self->s);
    if (len > PyInt_GetMax()) len = PyInt_GetMax();
    return PyInt_FromLong((long) len);
  }
  else if (strcmp(attr, "s") == 0) {
    PyObject *list;
    size_t i, len;

    len = wide_get_len(self->s);
    if (NULL == (list = PyList_New(len))) return NULL;
    for (i = 0; i < len; i++) {
      PyObject *obj;

      if (NULL == (obj = PyInt_FromLong(wide_get_char(self->s, (int) i)))) {
	Py_DECREF(list);
	return NULL;
      }
      if (NULL == PyList_SET_ITEM(list, (int) i, obj)) {
	Py_DECREF(obj);
	Py_DECREF(list);
	return NULL;
      }
    }
    return list;
  }
  else if (strcmp(attr, "enc") == 0)
    return PyString_FromString(enc_to_mbs(wide_get_enc(self->s)));
  else if (strcmp(attr, "__members__") == 0)
    return Py_BuildValue("[s,s,s,s]", "len", "enc", "s", "mutable");
  return Py_FindMethod(DBCS_methods, (PyObject *) self, attr);
}

static int
DBCSsetattr (DBCS_type *self, char *attr, PyObject *obj) {
  assert(NULL != attr);

  if (strcmp(attr, "enc") == 0 || strcmp(attr, "mutable") == 0) {
    PyErr_SetString(PyExc_AttributeError, "read-only attribute");
    return -1;
  }
  else if (strcmp(attr, "s") == 0) {
    wide_str *s, *old;

    s = obj_to_str(obj, wide_get_inc(self->s), wide_get_enc(self->s));
    if (NULL == s) {
      PyErr_NoMemory();
      return -1;
    }
    old = self->s;
    self->s = s;
    if (NULL == wide_alloc_str(old, 0)) {
      PyErr_NoMemory();
      return -1;
    }
    return 0;
  }
  else if (strcmp(attr, "len") == 0) {
    size_t old_len, last, n;
    long new_len;

    if (PyInt_Check(obj))
      new_len = PyInt_AS_LONG(obj);
    else if (PyLong_Check(obj))
      new_len = PyLong_AsLong(obj);
    else {
      PyErr_BadArgument();
      return -1;
    }
    old_len = wide_get_len(self->s);
    if (new_len > old_len || new_len < 0) {
      PyErr_SetString(PyExc_ValueError, "0 <= new_len <= old_len");
      return -1;
    }
    n = old_len - (size_t) new_len;
    last = old_len - n;
    if (NULL == wide_del_str(self->s, last, n)) {
      PyErr_NoMemory();
      return -1;
    }
  }
  else {
    PyErr_SetString(PyExc_AttributeError, attr);
    return -1;
  }
  return 0;
}

static int
DBCScompare (DBCS_type *self, DBCS_type *obj) {
  assert(NULL != self);
  assert(NULL != obj);

  return wide_cmp_str(self->s, obj->s);
}


static PyObject *
DBCSrepr (DBCS_type *self) {
  char s[48];
  const char *enc;
  PyObject *obj;
  size_t i, len, inc;
  int ascii;

  if (NULL == (obj = PyString_FromString(""))) return NULL;
  enc = enc_to_mbs(wide_get_enc(self->s));
  inc = wide_get_inc(self->s);
  snprintf(s, sizeof(s), "dbcs.%s([", self->rw ? "StringBuffer" : "String");
  if (NULL == (obj = PyString_FromString(s))) return NULL;
  for (i = 0, len = wide_get_len(self->s), ascii = 0; i < len; i++) {
    unsigned short c;
    const char *prefix, *suffix;
    int last;

    c = wide_get_char(self->s, i);
    last = i + 1 >= len;
    if (c < 0x80 && '\'' != c && '\\' != c && isprint(c)) {
      prefix = ascii ? "" : "'";
      suffix = last && ascii ? "'" : "";
      snprintf(s, sizeof(s), "%s%c%s", prefix, (char) c, suffix);
      ascii = 1;
    }
    else {
      prefix = ascii ? "'," : "";
      suffix = last ? "" : ",";
      snprintf(s, sizeof(s), "%s0x%hX%s", prefix, c, suffix);
      ascii = 0;
    }
    PyString_ConcatAndDel(&obj, PyString_FromString(s));
    if (NULL == obj) return NULL;
  }
  snprintf(s, sizeof(s), "],'%s',%zu)", enc, inc);
  PyString_ConcatAndDel(&obj, PyString_FromString(s));
  return obj;
}

static long
DBCShash (DBCS_type *self) {
  return (long) wide_hash_str(self->s);
}

static PyObject *
DBCScall (DBCS_type *self, PyObject *one, PyObject *two) {
  PyErr_SetNone(PyExc_NotImplementedError);
  return NULL;
}

static PyObject *
DBCSstr (DBCS_type *self) {
  unsigned char *s;
  PyObject *obj;

  s = wide_conv_wcs(NULL, self->s);
  if (NULL == s) return NULL;
  obj = PyString_FromString(s);
  free(s);
  return obj;
}

/**************************************************************************/
/******                                                              ******/
/******                        SEQUENCE METHODS                      ******/
/******                                                              ******/
/**************************************************************************/
 
static int
DBCSlength (DBCS_type *self) {
  return wide_get_len(self->s);
}

static PyObject *
DBCSconcat (DBCS_type *self, PyObject *obj) {
  DBCS_type *d;
  wide_str *s;
  size_t pos;

  if (NULL == (d = duplicate(self))) return NULL;
  pos = wide_get_len(d->s);
  s = obj_to_str(obj, wide_get_inc(self->s), wide_get_enc(self->s));
  if (NULL == wide_ins_str(d->s, s, pos)) {
    Py_DECREF(d);
    PyErr_NoMemory();
    return NULL;
  }
  wide_alloc_str(s, 0);
  Py_Free(s);
  return (PyObject *) d;
}

static PyObject *
DBCSrepeat (DBCS_type *self, int n) {
  DBCS_type *obj;

  obj = instantiate(wide_get_inc(self->s), wide_get_enc(self->s), self->rw);
  if (NULL == obj) return NULL;
  if (n > 0) {
    int i;
    size_t pos, len;

    if (NULL == wide_alloc_str(obj->s, wide_get_len(self->s) * n)) {
      Py_DECREF(obj);
      PyErr_NoMemory();
      return NULL;
    }
    len = wide_get_len(self->s);
    for (i = 0, pos = 0; i < n; i++, pos += len) {
      if (NULL == wide_ins_str(obj->s, self->s, pos)) {
        Py_DECREF(obj);
        PyErr_NoMemory();
        return NULL;
      }
    }
  }
  return (PyObject *) obj;
}

static PyObject *
DBCSitem (DBCS_type *self, int index) {
  if (index < 0 || index >= wide_get_len(self->s)) {
    PyErr_SetNone(PyExc_IndexError);
    return NULL;
  }
  return DBCSslice(self, index, index + 1);
}

static PyObject *
DBCSslice (DBCS_type *self, int i, int j) {
  DBCS_type *s;
  size_t len;

  len = wide_get_len(self->s);
  if (j > len)
    j = len;
  s = instantiate(wide_get_inc(self->s), wide_get_enc(self->s), self->rw);
  if (NULL == s) return NULL;
  if (i < j && i < len) {
    len = j - i;
    if (NULL == wide_get_str(s->s, self->s, i, len)) {
      Py_DECREF(s);
      PyErr_NoMemory();
      return NULL;
    }
  }
  return (PyObject *) s;
}

static int
DBCSassign_item (DBCS_type *self, int index, PyObject *obj) {
  if (index < 0 || index >= wide_get_len(self->s)) {
    PyErr_SetNone(PyExc_IndexError);
    return -1;
  }
  return DBCSassign_slice(self, index, index + 1, obj);
}

static int
DBCSassign_slice (DBCS_type *self, int i, int j, PyObject *obj) {
  wide_str *s;
  size_t len;

  assert(self->rw);

  len = wide_get_len(self->s);
  if (j > len)
    j = len;
  s = obj_to_str(obj, wide_get_inc(self->s), wide_get_enc(self->s));
  if (i <= j && i < len) {
    if (NULL == wide_del_str(self->s, i, j - i)) {
      PyErr_NoMemory();
      return -1;
    }
    if (NULL == wide_ins_str(self->s, s, i)) {
      PyErr_NoMemory();
      return -1;
    }
  }
  wide_alloc_str(s, 0);
  Py_Free(s);
  return 0;
}

/**************************************************************************/
/******                                                              ******/
/******                          MODULE LOGIC                        ******/
/******                                                              ******/
/**************************************************************************/

static PyObject *
DBCSstring (PyObject *self, PyObject *args, PyObject *keywds) {
  return new_string(self, args, keywds, 0);
}

static PyObject *
DBCSstrbuf (PyObject *self, PyObject *args, PyObject *keywds) {
  return new_string(self, args, keywds, 1);
}

static PyObject *
DBCSenc (PyObject *self, PyObject *args) {
  const char *enc;
  PyObject *list, *s;
  wide_enc i;

  if (!PyArg_ParseTuple(args, "")) return NULL;
  if (NULL == (list = PyList_New(0))) return NULL;
    for (i = (wide_enc) 0; NULL != (enc = enc_to_mbs(i)); i++) {
      if (NULL == (s = PyString_FromString(enc))) return NULL;
      if (-1 == PyList_Append(list, s)) {
        Py_DECREF(list);
	return NULL;
      }
    }
  return (PyObject *) list;
}

static PyObject *
DBCSinc (PyObject *self, PyObject *args) {
  if (!PyArg_ParseTuple(args, "")) return NULL;
  return (PyObject *) PyInt_FromLong(default_inc);
}

static struct PyMethodDef DBCS_functions[] = {
  {"String", (PyCFunction) DBCSstring,
             METH_VARARGS|METH_KEYWORDS, DBCS_MOD_STR_F_DOC },
  {"StringBuffer", (PyCFunction) DBCSstrbuf,
                   METH_VARARGS|METH_KEYWORDS, DBCS_MOD_STRBUF_F_DOC },
  {"Encodings", DBCSenc, METH_VARARGS, DBCS_MOD_ENC_F_DOC },
  {"Increment", DBCSinc, METH_VARARGS, DBCS_MOD_INC_F_DOC },
  {NULL}
};

void
initdbcs() {
  Py_InitModule3("dbcs", DBCS_functions, DBCS_MOD_DOC);
  if (PyErr_Occurred())
    Py_FatalError("can't initialize module dbcs");
}
