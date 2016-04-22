#!/usr/bin/python3
#
# Copyright 2016 Red Hat, Inc.  All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#  Peter Jones <pjones@redhat.com>
#
from functools import wraps
from decorator import decorator
import pdb
import copy
import time
import types
import sys
import traceback

def log(tracetype, level, fmt, *args):
    argstr = fmt % args
    print("%s %s.%d: %s" % (time.asctime(), tracetype, level, argstr))

def ingress_egress_logger(func, obj, *args, **kwargs):
    if func and hasattr(func, '_tracelevel'):
        level = obj._tracelevel
    if obj and hasattr(obj, '_tracelevel'):
        level = obj._tracelevel
    else:
        # XXX FIXME: figure out a good default level
        level = 1

    objname = "%s.%s"  % (func.__module__, func.__qualname__)
    if obj:
        funcname = objname
    else:
        funcname = "%s.%s" % (func.__module__, func.__name__)

    newargs = copy.copy(args)
    for k,v in kwargs.items():
        newargs.append("%s=%s" % (k,v))
    argstr = ",".join(newargs)

    log("ingress", level, "%s(%s)" % (funcname, argstr))
    if not obj:
        obj = func.__new__(func, *args, **kwargs)
        return_obj = True
        func.__init__(obj, *args, **kwargs)
        ret = obj
    else:
        ret = func(obj, *args, **kwargs)
    log("egress", level, "%s() = %s" % (funcname, ret))
    return ret

def tracetype(name):
    """ Decorator to add a tracepoint type to an object."""
    def run_func_with_logger_set(func):
        setattr(func, '_tracepoint', name)
        return func
    return run_func_with_logger_set

class LogFunction(object):
    def __init__(self, tracepoint):
        self._tracepoint = tracepoint

    # XXX this should use our real log formatter instead
    def __call__(self, level, msg, *args):
        tracepoint = self._tracepoint
        try:
            raise Exception
        except Exception:
            stuff = sys.exc_info()
        obj = stuff[2].tb_frame.f_back.f_locals['self']
        funcname = stuff[2].tb_frame.f_back.f_code.co_name
        func = getattr(obj, funcname)
        if hasattr(func, '_tracepoint'):
            tracepoint = func._tracepoint
        return log(tracepoint, level, msg, *args)

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        else:
            return LogFunction(tracepoint=name)

class LoggedObject(type):
    def __new__(cls, name, bases, nmspc):
        for k, v in nmspc.items():
            if isinstance(v, types.FunctionType):
                v = decorator(ingress_egress_logger, v)
                nmspc[k] = v

        tracepoint = nmspc.setdefault("_tracepoint", "default")
        nmspc['log'] = LogFunction(tracepoint)
        return type.__new__(cls, name, bases, nmspc)

@tracetype("baz")
class Foo(metaclass=LoggedObject):
    def __init__(self):
        print('1')

    @tracetype("baz")
    def foo(self):
        self.log(3, "I have no mouth and I must scream")
        print('2')

    def zonk(self):
        self.log.debug(3, "I have no mouth and I must scream")
        print('3')
        return 0

x = Foo()
x.foo()
x.zonk()

pdb.set_trace()
pass
