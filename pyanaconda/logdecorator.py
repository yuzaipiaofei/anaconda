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
from decorator import decorator
import pdb
import copy
import time
import types
import sys
import traceback

def do_log_thingy(tracepoint, level, fmt, *args):
    """ this is a fake logger """
    argstr = fmt % args
    print("%s %s.%d: %s" % (time.asctime(), tracepoint, level, argstr))

def ingress_egress_logger(func, obj, *args, **kwargs):
    """ A simple logger to log entry and exit of functions / methods """
    if func and hasattr(func, '_tracelevel'):
        level = obj._tracelevel
    if obj and hasattr(obj, '_tracelevel'):
        level = obj._tracelevel
    else:
        # XXX FIXME: figure out a good default level
        level = 1

    funcname = "%s.%s"  % (func.__module__, func.__qualname__)

    newargs = copy.copy(args)
    for k,v in kwargs.items():
        newargs.append("%s=%s" % (k,v))
    argstr = ",".join(newargs)

    do_log_thingy("ingress", level, "%s(%s)" % (funcname, argstr))
    ret = func(obj, *args, **kwargs)
    do_log_thingy("egress", level, "%s() = %s" % (funcname, ret))
    return ret

def tracepoint(name):
    """ Decorator to add a tracepoint type to an object."""
    def run_func_with_logger_set(func):
        setattr(func, '_tracepoint', name)
        return func
    return run_func_with_logger_set

class LogFunction(object):
    """ This class provides a callable to log some data """

    def __init__(self, tracepoint=None):
        self._tracepoint = tracepoint

    # XXX this should use our real log formatter instead
    def __call__(self, level, msg, *args):
        # this is probably the default tracepoint, but maybe not.  
        tracepoint = self._tracepoint
        if tracepoint == None:
            # it is the default, which means we need to find if our
            # function or object have a non-default value
            try:
                raise Exception
            except Exception:
                stuff = sys.exc_info()
            namespace = stuff[2].tb_frame.f_back.f_locals
            if "self" in namespace:
                obj = namespace['self']
                funcname = stuff[2].tb_frame.f_back.f_code.co_name
                func = getattr(obj, funcname)
            else:
                obj = None
                func = None
            if hasattr(func, '_tracepoint'):
                tracepoint = func._tracepoint
            if tracepoint is None and hasattr(obj, '_tracepoint'):
                tracepoint = obj._tracepoint
            # but on the output side we use "default".
            if tracepoint is None:
                tracepoint = "default"
        if tracepoint != "squelch":
            return do_log_thingy(tracepoint, level, msg, *args)

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        else:
            return LogFunction(tracepoint=name)

class LoggedObject(type):
    """ This class object provides you with a metaclass you can use in your
    classes to get logging set up with easy defaults
    """
    def __new__(cls, name, bases, nmspc):
        for k, v in nmspc.items():
            if isinstance(v, types.FunctionType):
                v = decorator(ingress_egress_logger, v)
                nmspc[k] = v

        # We use "None" rather than "default" here so that if somebody /sets/
        # something to default, we won't override it with something with lower
        # precedence.
        tracepoint = nmspc.setdefault("_tracepoint", None)
        nmspc['log'] = LogFunction(tracepoint)
        return type.__new__(cls, name, bases, nmspc)

log = LogFunction()

@tracepoint("zoom")
class Foo(metaclass=LoggedObject):
    def __init__(self):
        self.log(1, "this should be log level type zoom")
        print('1')

    @tracepoint("baz")
    def foo(self):
        self.log(3, "this should be log type baz")
        print('2')

    def zonk(self):
        self.log.debug(3, "this should be log type debug")
        print('3')
        return 0

class Bar(metaclass=LoggedObject):
    def __init__(self):
        self.log(9, "this should be log type default")

@tracepoint("incorrect")
class Baz(metaclass=LoggedObject):
    @tracepoint("default")
    def __init__(self):
        self.log(4, "this should be log type default")

    def zonk(self):
        self.log(5,"this should be log type incorrect")

@tracepoint("maybe")
def bullshit():
    log(4, "does this even work?  maybe...")

x = Foo()
x.foo()
x.zonk()

y = Bar()

z = Baz()
z.zonk()
