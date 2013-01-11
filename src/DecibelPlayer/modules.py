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

from __future__ import absolute_import

import os, sys, threading, traceback, warnings
from gettext import gettext as _

import gobject, gtk

from . import gui
from .tools   import consts, prefs
from .tools.log import logger
from .tools.consts import USER_PLUGINS_DIR


# Information exported by a module -- DEPRECATED!!
MODINFO_NAME=0           # Name of the module, must be unique
MODINFO_L10N=1           # Name translated into the current locale
MODINFO_DESC=2           # Description of the module, translated into the current locale
MODINFO_DEPS=3           # A list of special Python dependencies (e.g., pynotify)
MODINFO_MANDATORY=4      # True if the module cannot be disabled
MODINFO_CONFIGURABLE=5   # True if the module can be configured
MODINFO_CATEGORY=6       # Category the module belongs to

def convert_modinfo(modinfo):
    """Converts old-style to new-style MOD_INFO form plugins
    """
    if not isinstance(modinfo, tuple):
        return modinfo
    warnings.warn("Deprecated MODINFO tuple format - use dict instead")
    return {
        'name': modinfo[0],
        'l10n': modinfo[1],
        'desc': modinfo[2],
        'deps': modinfo[3],
        'mandatory': modinfo[4],
        'configurable': modinfo[5],
        'category': modinfo[6],
    }


## Values associated with a module
MOD_PMODULE = 0
'''The actual Python module object'''

MOD_CLASSNAME = 1
'''The classname of the module'''

MOD_INSTANCE = 2
'''Instance, None if not currently enabled'''

MOD_INFO = 3
'''A tuple exported by the module, see above definition'''


class LoadException(Exception):
    """ Raised when a module could not be loaded """

    def __init__(self, errMsg):
        """ Constructor """
        self.errMsg = errMsg

    def __str__(self):
        """ String representation """
        return self.errMsg


def __checkDeps(deps):
    """ Given a list of Python modules, return a list of the modules that are unavailable """
    unmetDeps = []
    for module in deps:
        try:
            __import__(module)
        except:
            unmetDeps.append(module)
    return unmetDeps


def load(name):
    """ Load the given module, may raise LoadException """
    mModulesLock.acquire()
    module = plugins[name]
    mModulesLock.release()

    # Check dependencies
    unmetDeps = __checkDeps(module[MOD_INFO][MODINFO_DEPS])
    if len(unmetDeps) != 0:
        errMsg  = _('The following Python modules are not available:')
        errMsg += '\n     * '
        errMsg += '\n     * '.join(unmetDeps)
        errMsg += '\n\n'
        errMsg += _('You must install them if you want to enable this module.')
        raise LoadException, errMsg

    # Instantiate the module
    try:
        module[MOD_INSTANCE] = getattr(module[MOD_PMODULE], module[MOD_CLASSNAME])()
        module[MOD_INSTANCE].start()

        mHandlersLock.acquire()
        if module[MOD_INSTANCE] in mHandlers[consts.MSG_EVT_MOD_LOADED]:
            module[MOD_INSTANCE].postMsg(consts.MSG_EVT_MOD_LOADED)
        mHandlersLock.release()

        logger.info('Module loaded: %s' % module[MOD_CLASSNAME])
        plugins_enabled.append(name)
        prefs.set(__name__, 'enabled_modules', plugins_enabled)
    except:
        raise LoadException, traceback.format_exc()


def unload(name):
    """ Unload the given module """
    mModulesLock.acquire()
    module               = plugins[name]
    instance             = module[MOD_INSTANCE]
    module[MOD_INSTANCE] = None
    mModulesLock.release()

    if instance is not None:
        mHandlersLock.acquire()
        instance.postMsg(consts.MSG_EVT_MOD_UNLOADED)
        for handlers in [handler for handler in mHandlers.itervalues() if instance in handler]:
            handlers.remove(instance)
        mHandlersLock.release()

        plugins_enabled.remove(name)
        logger.info('Module unloaded: %s' % module[MOD_CLASSNAME])
        prefs.set(__name__, 'enabled_modules', plugins_enabled)


def getModules():
    """ Return a copy of all known modules """
    mModulesLock.acquire()
    copy = plugins.items()
    mModulesLock.release()
    return copy


def register(module, msgList):
    """ Register the given module for all messages in the given list/tuple """
    mHandlersLock.acquire()
    for msg in msgList:
        mHandlers[msg].add(module)
    mHandlersLock.release()


def showPreferences():
    """ Show the preferences dialog box """
    from .gui import preferences as gui_preferences
    gobject.idle_add(gui_preferences.show)


def __postMsg(msg, params=None):
    """ This is the 'real' postMsg function, which must be executed in the GTK main loop """
    if params is None:
        params = {}
    mHandlersLock.acquire()
    for module in mHandlers[msg]:
        module.postMsg(msg, params)
    mHandlersLock.release()


def postMsg(msg, params=None):
    """ Post a message to the queue of modules that registered for this type of message """
    # We need to ensure that posting messages will be done by the GTK main loop
    # Otherwise, the code of threaded modules could be executed in the caller's thread, which could cause problems when calling GTK functions
    if params is None:
        params = {}
    gobject.idle_add(__postMsg, msg, params)


def __postQuitMsg():
    """ This is the 'real' postQuitMsg function, which must be executed in the GTK main loop """
    __postMsg(consts.MSG_EVT_APP_QUIT)
    for modData in plugins.itervalues():
        if modData[MOD_INSTANCE] is not None:
            modData[MOD_INSTANCE].join()
        # Don't exit the application right now, let modules do their job before
    gobject.idle_add(gtk.main_quit)


def postQuitMsg():
    """ Post a MSG_EVT_APP_QUIT in each module's queue and exit the application """
    # As with postMsg(), we need to ensure that the code will be executed by the GTK main loop
    gobject.idle_add(__postQuitMsg)


mMenuItems  = {}
mSeparator  = None
mAccelGroup = None


def __addMenuItem(label, callback, accelerator):
    """ This is the 'real' addMenuItem function, which must be executed in the GTK main loop """
    global mAccelGroup, mSeparator

    menu = prefs.getWidgetsTree().get_object('menu-edit')

    # Remove all menu items
    if len(mMenuItems) != 0:
        menu.remove(mSeparator)
        for menuitem in mMenuItems.itervalues():
            menu.remove(menuitem)

    # Create a new menu item for the module
    menuitem = gtk.MenuItem(label)
    menuitem.connect('activate', callback)
    menuitem.show()
    mMenuItems[label] = menuitem

    # Add an accelerator if needed
    if accelerator is not None:
        if mAccelGroup is None:
            mAccelGroup = gtk.AccelGroup()
            prefs.getWidgetsTree().get_object('win-main').add_accel_group(mAccelGroup)

        key, mod = gtk.accelerator_parse(accelerator)
        menuitem.add_accelerator('activate', mAccelGroup, key, mod, gtk.ACCEL_VISIBLE)

    # Create the separator?
    if mSeparator is None:
        mSeparator = gtk.SeparatorMenuItem()
        mSeparator.show()

    # Re-add items alphabetically, including the new one
    menu.insert(mSeparator, 0)
    for item in sorted(mMenuItems.items(), key = lambda item: item[0], reverse = True):
        menu.insert(item[1], 0)


def addMenuItem(label, callback, accelerator=None):
    """ Add a menu item to the 'modules' menu """
    gobject.idle_add(__addMenuItem, label, callback, accelerator)


def __delMenuItem(label):
    """ This is the 'real' delMenuItem function, which must be executed in the GTK main loop """
    # Make sure the menu item is there
    if label not in mMenuItems:
        return

    menu = prefs.getWidgetsTree().get_object('menu-edit')

    # Remove all current menu items
    menu.remove(mSeparator)
    for menuitem in mMenuItems.itervalues():
        menu.remove(menuitem)

    # Delete the given menu item
    del mMenuItems[label]

    # Re-add items if needed
    if len(mMenuItems) != 0:
        menu.insert(mSeparator, 0)
        for item in sorted(mMenuItems.items(), key = lambda item: item[0], reverse = True):
            menu.insert(item[1], 0)


def delMenuItem(label):
    """ Delete a menu item from the 'modules' menu """
    gobject.idle_add(__delMenuItem, label)


# --== Base classes for modules ==--


class ModuleBase:
    """ This class makes sure that all modules have some mandatory functions """

    def join(self):
        pass

    def start(self):
        pass

    def configure(self, parent):
        pass

    def handleMsg(self, msg, params):
        pass

    def restartRequired(self):
        gobject.idle_add(
            gui.infoMsgBox,
            None,
            _('Restart required'),
            _('You must restart the application for this modification to take effect.'))



class Module(ModuleBase):
    """ This is the base class for non-threaded modules """

    def __init__(self, handlers):
        self.handlers = handlers
        register(self, handlers.keys())

    def postMsg(self, msg, params=None):
        if params is None: params = {}
        gobject.idle_add(self.__dispatch, msg, params)

    def __dispatch(self, msg, params):
        self.handlers[msg](**params)



class ThreadedModule(threading.Thread, ModuleBase):
    """ This is the base class for threaded modules """

    def __init__(self, handlers):
        """ Constructor """
        import Queue

        # Attributes
        self.queue        = Queue.Queue(0)            # List of queued messages
        self.gtkResult    = None                      # Value returned by the function executed in the GTK loop
        self.gtkSemaphore = threading.Semaphore(0)    # Used to execute some code in the GTK loop

        # Initialization
        threading.Thread.__init__(self)

        # Add QUIT and UNLOADED messages if needed
        # These messages are required to exit the thread's loop
        if consts.MSG_EVT_APP_QUIT not in handlers:     handlers[consts.MSG_EVT_APP_QUIT]     = lambda: None
        if consts.MSG_EVT_MOD_UNLOADED not in handlers: handlers[consts.MSG_EVT_MOD_UNLOADED] = lambda: None

        self.handlers = handlers
        register(self, handlers.keys())

    def __gtkExecute(self, func):
        """ Private function, must be executed in the GTK main loop """
        self.gtkResult = func()
        self.gtkSemaphore.release()

    def gtkExecute(self, func):
        """ Execute func in the GTK main loop, and block the execution of the thread until done """
        gobject.idle_add(self.__gtkExecute, func)
        self.gtkSemaphore.acquire()
        return self.gtkResult

    def threadExecute(self, func, *args):
        """
            Schedule func(*args) to be called by the thread
            This is used to avoid func to be executed in the GTK main loop
        """
        self.postMsg(consts.MSG_CMD_THREAD_EXECUTE, (func, args))

    def postMsg(self, msg, params=None):
        """ Enqueue a message in this threads's message queue """
        if params is None: params = {}
        self.queue.put((msg, params))

    def run(self):
        """ Wait for messages and handle them """
        msg = None
        while msg != consts.MSG_EVT_APP_QUIT and msg != consts.MSG_EVT_MOD_UNLOADED:
            (msg, params) = self.queue.get(True)

            if msg == consts.MSG_CMD_THREAD_EXECUTE:
                (func, args) = params
                func(*args)
            else:
                self.handlers[msg](**params)


# --== Entry point ==--

import pkgutil, imp
import DecibelPlayer

MODULES_SEARCH_PATH = (
    os.path.join(os.path.dirname(DecibelPlayer.__file__), 'plugins'),
    USER_PLUGINS_DIR,
)


def discover_plugins():
    modules = {}
    for search_dir in MODULES_SEARCH_PATH:
        for mod in pkgutil.iter_modules([search_dir]):
            try:
                import_path = [search_dir] + sys.path
                module = imp.load_module(mod[1], *imp.find_module(mod[1], import_path))
                modules[mod[1]] = module
            except:
                #logger.exception("Module failed to load ({name})".format(name=mod[1]))
                logger.debug("Module failed to load ({name})".format(name=mod[1]))
    return modules


#mModDir         = os.path.dirname(__file__)                                    # Where modules are located
plugins        = {}                                                           # All known modules associated to an 'active' boolean
mHandlers       = dict([(msg, set()) for msg in xrange(consts.MSG_END_VALUE)]) # For each message, store the set of registered modules
mModulesLock    = threading.Lock()                                             # Protects the modules list from concurrent access
mHandlersLock   = threading.Lock()                                             # Protects the handlers list from concurrent access
plugins_enabled = prefs.get(__name__, 'enabled_modules', [])                   # List of modules currently enabled


### Find modules, instantiate those that are mandatory or that have been previously enabled by the user
#sys.path.append(mModDir)
#for file in [os.path.splitext(file)[0] for file in os.listdir(mModDir) if file.endswith('.py') and file != '__init__.py']:
#    try:
#        pModule = __import__(file)
#        modInfo = getattr(pModule, 'MOD_INFO')
#        modInfo = convert_modinfo(modInfo)
#
#        # Should it be instanciated?
#        instance = None
#        if modInfo['mandatory'] or modInfo['name'] in mEnabledModules:
#            if len(__checkDeps(modInfo[MODINFO_DEPS])) == 0:
#                instance = getattr(pModule, file)()
#                instance.start()
#                logger.info('Module loaded: %s' % file)
#            else:
#                logger.error('Unable to load module %s because of missing dependencies' % file)
#
#        # Add it to the dictionary
#        mModules[modInfo[MODINFO_NAME]] = [pModule, file, instance, modInfo]
#    except:
#        logger.error('Unable to load module %s\n\n%s' % (file, traceback.format_exc()))


## Find modules, instantiate those that are mandatory
## or that have been previously enabled by the user
for mod_id, module in discover_plugins().iteritems():
    try:
        mod_info = convert_modinfo(module.MOD_INFO)

        ## Should it be loaded?
        instance = None
        if mod_info['mandatory'] or (mod_info['name'] in plugins_enabled):
            if len(__checkDeps(mod_info[MODINFO_DEPS])) == 0:
                instance = module.PLUGIN()
                instance.start()
                logger.info('Module loaded: %s' % file)
            else:
                logger.error('Unable to load module %s because of missing dependencies' % file)

        ## Add it to the plugins list
        plugins[mod_info[MODINFO_NAME]] = [module, file, instance, mod_info]

    except:
        logger.error('Unable to load module %s\n\n%s' % (file, traceback.format_exc()))

# Remove enabled modules that are no longer available
plugins_enabled[:] = [
    module for module in plugins_enabled
        if module in plugins
]
prefs.set(
    __name__,
    'enabled_modules',
    plugins_enabled,
)
