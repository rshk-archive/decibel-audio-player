#!/usr/bin/env python
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

import gettext, locale, optparse, sys

import dbus
import gtk, gobject

from .gui   import mainWindow
from .tools import consts, loadGladeFile, log, prefs

def main():

    # Command line
    optparser = optparse.OptionParser(usage='Usage: %prog [options] [FILE(s)]')
    optparser.add_option('-p', '--playbin', action='store_true', default=False, help='use the playbin GStreamer component instead of playbin2')
    optparser.add_option('--multiple-instances', action='store_true', default=False, help='start a new instance even if one is already running')
    optparser.add_option('--no-glossy-cover', action='store_true', default=False, help='disable the gloss effect applied to covers')
    optparser.add_option('--volume-button', action='store_true', default=False, help='always show the volume button')

    (optOptions, optArgs) = optparser.parse_args()


    # Check whether DAP is already running?
    if not optOptions.multiple_instances:
        shouldStop  = False
        dbusSession = None

        try:
            dbusSession    = dbus.SessionBus()
            activeServices = dbusSession.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus').ListNames()

            if consts.dbusService in activeServices:
                shouldStop = True

                # Raise the window of the already running instance
                dbus.Interface(dbusSession.get_object(consts.dbusService, '/'), consts.dbusInterface).RaiseWindow()

                # Fill the current instance with the given tracks, if any
                if len(optArgs) != 0:
                    dbus.Interface(dbusSession.get_object(consts.dbusService, '/TrackList'), consts.dbusInterface).SetTracks(optArgs, True)
        except:
            pass

        if dbusSession is not None:
            dbusSession.close()

        if shouldStop:
            sys.exit(1)


    log.logger.info('Started')
    prefs.setCmdLine((optOptions, optArgs))


    # Localization
    locale.setlocale(locale.LC_ALL, '')
    gettext.textdomain(consts.appNameShort)
    gettext.bindtextdomain(consts.appNameShort, consts.dirLocale)


    # PyGTK initialization
    gobject.threads_init()
    gtk.window_set_default_icon_list(
        gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon16),
        gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon24),
        gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon32),
        gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon48),
        gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon64),
        gtk.gdk.pixbuf_new_from_file(consts.fileImgIcon128))


    # Create the GUI
    wtree  = loadGladeFile('MainWindow.ui')
    window = wtree.get_object('win-main')

    prefs.setWidgetsTree(wtree)

    # RGBA support
    try:
        colormap = window.get_screen().get_rgba_colormap()
        if colormap:
            gtk.widget_set_default_colormap(colormap)
    except:
        log.logger.info('No RGBA support (requires PyGTK 2.10+)')

    # This object takes care of the window (mainly event handlers)
    mainWindow.MainWindow(wtree, window)


    def delayedStartup():
        """
            Perform all the initialization stuff that is not mandatory to display the window
            This function should be called within the GTK main loop, once the window has been displayed
        """
        import atexit, dbus.mainloop.glib, signal
        from . import modules

        def atExit():
            """ Final function, called just before exiting the Python interpreter """
            prefs.save()
            log.logger.info('Stopped')

        def onInterrupt(window):
            """ Handler for interrupt signals e.g., Ctrl-C """
            window.hide()
            modules.postQuitMsg()

        # D-Bus
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        # Register a few handlers
        atexit.register(atExit)
        signal.signal(signal.SIGINT,  lambda sig, frame: onInterrupt(window))
        signal.signal(signal.SIGTERM, lambda sig, frame: onInterrupt(window))

        # Now we can start all modules
        gobject.idle_add(modules.postMsg, consts.MSG_EVT_APP_STARTED)

        # Immediately show the preferences the first time the application is started
        if prefs.get(__name__, 'first-time', True):
            prefs.set(__name__, 'first-time', False)
            gobject.idle_add(modules.showPreferences)


    # Let's go
    gobject.idle_add(delayedStartup)
    gtk.main()

if __name__ == '__main__':
    main()
