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

import gobject, gtk, modules, os.path

from tools     import consts, prefs
from gettext   import gettext as _
from tools.log import logger

MOD_INFO = ('Desktop Notification', _('Desktop Notification'), _('Display a desktop notification on track change'), ['pynotify'], False, True, consts.MODCAT_DESKTOP)


# Default preferences
PREFS_DEFAULT_BODY       = 'by {artist} on {album} ({playlist_pos} / {playlist_len})'
PREFS_DEFAULT_TITLE      = '{title}  [{duration_str}]'
PREFS_DEFAULT_TIMEOUT    = 10
PREFS_DEFAULT_SKIP_TRACK = False


class DesktopNotification(modules.Module):

    def __init__(self):
        """ Constructor """
        handlers = {
                        consts.MSG_EVT_STOPPED:      self.hideNotification,
                        consts.MSG_EVT_APP_QUIT:     self.hideNotification,
                        consts.MSG_EVT_NEW_TRACK:    self.onNewTrack,
                        consts.MSG_CMD_SET_COVER:    self.onSetCover,
                        consts.MSG_EVT_MOD_LOADED:   self.onModLoaded,
                        consts.MSG_EVT_TRACK_MOVED:  self.onCurrentTrackMoved,
                        consts.MSG_EVT_APP_STARTED:  self.onModLoaded,
                        consts.MSG_EVT_MOD_UNLOADED: self.hideNotification,
                   }

        modules.Module.__init__(self, handlers)


    def hideNotification(self):
        """ Hide the notification """
        self.currTrack = None
        self.currCover = None

        if self.timeout is not None:
            gobject.source_remove(self.timeout)
            self.timeout = None

        if self.notif is not None:
            self.notif.close()


    def __createNotification(self, title, body, icon):
        """ Create the Notification object """
        import pynotify

        if not pynotify.init(consts.appNameShort):
            logger.error('[%s] Initialization of pynotify failed' % MOD_INFO[modules.MODINFO_NAME])

        self.notif = pynotify.Notification(title, body, icon)
        self.notif.set_urgency(pynotify.URGENCY_LOW)
        self.notif.set_timeout(prefs.get(__name__, 'timeout', PREFS_DEFAULT_TIMEOUT) * 1000)

        if prefs.get(__name__, 'skip-track', PREFS_DEFAULT_SKIP_TRACK):
            self.notif.add_action('stop', _('Skip track'), self.onSkipTrack)


    def showNotification(self):
        """ Show the notification based on the current track """
        self.timeout = None

        # Can this happen?
        if self.currTrack is None:
            return False

        # Contents
        body  = self.currTrack.formatHTMLSafe(prefs.get(__name__, 'body',  PREFS_DEFAULT_BODY))
        title = self.currTrack.format(prefs.get(__name__, 'title', PREFS_DEFAULT_TITLE))

        # Icon
        if self.currCover is None: img = os.path.join(consts.dirPix, 'decibel-audio-player-64.png')
        else:                      img = self.currCover

        if os.path.isfile(img): icon = 'file://' + img
        else:                   icon = gtk.STOCK_DIALOG_INFO

        # Create / Update the notification and show it
        if self.notif is None: self.__createNotification(title, body, icon)
        else:                  self.notif.update(title, body, icon)

        self.notif.show()

        return False


    def onSkipTrack(self, notification, action):
        """ The user wants to skip the current track """
        if self.hasNext: modules.postMsg(consts.MSG_CMD_NEXT)
        else:            modules.postMsg(consts.MSG_CMD_STOP)


    # --== Message handlers ==--


    def onModLoaded(self):
        """ The module has been loaded """
        self.notif     = None
        self.cfgWin    = None
        self.hasNext   = False
        self.timeout   = None
        self.currTrack = None
        self.currCover = None


    def onNewTrack(self, track):
        """ A new track is being played """
        self.currCover = None
        self.currTrack = track

        if self.timeout is not None:
            gobject.source_remove(self.timeout)

        # Wait a bit for the cover to be set (if any)
        self.timeout = gobject.timeout_add(500, self.showNotification)


    def onSetCover(self, track, pathThumbnail, pathFullSize):
        """ The cover for the given track """
        # We must check first whether currTrack is not None, because '==' calls the cmp() method and this fails on None
        if self.currTrack is not None and track == self.currTrack:
            self.currCover = pathThumbnail


    def onCurrentTrackMoved(self, hasNext, hasPrevious):
        """ The position of the current track has changed """
        self.hasNext = hasNext


    # --== Configuration ==--


    def configure(self, parent):
        """ Show the configuration window """
        if self.cfgWin is None:
            import gui, pynotify

            # Create the window
            self.cfgWin = gui.window.Window('DesktopNotification.ui', 'vbox1', __name__, MOD_INFO[modules.MODINFO_L10N], 355, 345)
            self.cfgWin.getWidget('btn-ok').connect('clicked', self.onBtnOk)
            self.cfgWin.getWidget('btn-help').connect('clicked', self.onBtnHelp)
            self.cfgWin.getWidget('btn-cancel').connect('clicked', lambda btn: self.cfgWin.hide())

            # Disable the 'Skip track' button if the server doesn't support buttons in notifications
            if 'actions' not in pynotify.get_server_caps():
                self.cfgWin.getWidget('chk-skipTrack').set_sensitive(False)

        if not self.cfgWin.isVisible():
            self.cfgWin.getWidget('txt-title').set_text(prefs.get(__name__, 'title', PREFS_DEFAULT_TITLE))
            self.cfgWin.getWidget('spn-duration').set_value(prefs.get(__name__, 'timeout', PREFS_DEFAULT_TIMEOUT))
            self.cfgWin.getWidget('txt-body').get_buffer().set_text(prefs.get(__name__, 'body', PREFS_DEFAULT_BODY))
            self.cfgWin.getWidget('chk-skipTrack').set_active(prefs.get(__name__, 'skip-track', PREFS_DEFAULT_SKIP_TRACK))
            self.cfgWin.getWidget('btn-ok').grab_focus()

        self.cfgWin.show()


    def onBtnOk(self, btn):
        """ Save new preferences """
        # Skipping tracks
        newSkipTrack = self.cfgWin.getWidget('chk-skipTrack').get_active()
        oldSkipTrack = prefs.get(__name__, 'skip-track', PREFS_DEFAULT_SKIP_TRACK)
        prefs.set(__name__, 'skip-track', newSkipTrack)

        if oldSkipTrack != newSkipTrack and self.notif is not None:
            if newSkipTrack: self.notif.add_action('stop', _('Skip track'), self.onSkipTrack)
            else:            self.notif.clear_actions()

        # Timeout
        newTimeout = int(self.cfgWin.getWidget('spn-duration').get_value())
        oldTimeout = prefs.get(__name__, 'timeout', PREFS_DEFAULT_TIMEOUT)

        prefs.set(__name__, 'timeout', newTimeout)

        if oldTimeout != newTimeout and self.notif is not None:
            self.notif.set_timeout(newTimeout * 1000)

        # Other preferences
        prefs.set(__name__, 'title', self.cfgWin.getWidget('txt-title').get_text())
        (start, end) = self.cfgWin.getWidget('txt-body').get_buffer().get_bounds()
        prefs.set(__name__, 'body', self.cfgWin.getWidget('txt-body').get_buffer().get_text(start, end))
        self.cfgWin.hide()


    def onBtnHelp(self, btn):
        """ Display a small help message box """
        import gui, media

        helpDlg = gui.help.HelpDlg(MOD_INFO[modules.MODINFO_L10N])
        helpDlg.addSection(_('Description'),
                           _('This module displays a small popup window on your desktop when a new track starts.'))
        helpDlg.addSection(_('Customizing the Notification'),
                           _('You can change the title and the body of the notification to any text you want. Before displaying '
                             'the popup window, fields of the form {field} are replaced by their corresponding value. '
                             'Available fields are:\n\n') + media.track.getFormatSpecialFields(False))
        helpDlg.addSection(_('Markup'),
                           _('You can use the Pango markup language to format the text. More information on that language is '
                             'available on the following web page:') + '\n\nhttp://www.pygtk.org/pygtk2reference/pango-markup-language.html')
        helpDlg.show(self.cfgWin)
