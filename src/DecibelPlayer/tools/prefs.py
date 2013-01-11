# -*- coding: utf-8 -*-
#
# Author: Ingelrest François (Francois.Ingelrest@gmail.com)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

import os, threading
from .. import tools

__all__ = ['save', 'set', 'get', 'setCmdLine', 'getCmdLine',
           'setWidgetsTree', 'getWidgetsTree']

## Load user preferences from the disk
try:
    _usrPrefs = tools.pickleLoad(tools.consts.filePrefs)
except:
    _usrPrefs = {}

## Used to prevent concurrent calls to functions
_mutex = threading.Lock()

## Some global values shared by all the components of the application
_appGlobals = {}


def save():
    """Save user preferences to disk"""
    _mutex.acquire()
    tools.pickleSave(tools.consts.filePrefs, _usrPrefs)
    os.chmod(tools.consts.filePrefs, 0600)
    _mutex.release()

def set(module, name, value):
    """ Change the value of a preference """
    _mutex.acquire()
    _usrPrefs[module + '_' + name] = value
    _mutex.release()

def get(module, name, default=None):
    """ Retrieve the value of a preference """
    _mutex.acquire()
    try:    value = _usrPrefs[module + '_' + name]
    except: value = default
    _mutex.release()
    return value


## Command line used to start the application
def setCmdLine(cmdLine):
    _appGlobals['cmdLine'] = cmdLine
def getCmdLine():
    return _appGlobals['cmdLine']


## Main widgets' tree created by Glade
def setWidgetsTree(tree):
    _appGlobals['wTree'] = tree
def getWidgetsTree():
    return _appGlobals['wTree']
