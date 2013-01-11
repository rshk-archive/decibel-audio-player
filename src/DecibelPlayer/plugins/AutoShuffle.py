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

from gettext import gettext as _
import gobject
from .. import modules
from ..tools   import consts, prefs

MOD_INFO = ('Automatic Shuffle', _('Automatic Shuffle'), _('Periodically shuffle the playlist'), [], False, True, consts.MODCAT_DECIBEL)

PREFS_DFT_ENABLED     = False
PREFS_DFT_PERIODICITY = 15

class AutoShuffle(modules.Module):

    def __init__(self):
        """ Constructor """
        handlers = {
                        consts.MSG_EVT_STOPPED:      self.onStop,
                        consts.MSG_EVT_APP_QUIT:     self.onModUnloaded,
                        consts.MSG_EVT_NEW_TRACK:    self.onNewTrack,
                        consts.MSG_EVT_MOD_LOADED:   self.onModLoaded,
                        consts.MSG_EVT_APP_STARTED:  self.onModLoaded,
                        consts.MSG_EVT_MOD_UNLOADED: self.onModUnloaded,
                   }

        modules.Module.__init__(self, handlers)


    def timerFunc(self):
        """ Shuffle the playlist """
        modules.postMsg(consts.MSG_CMD_TRACKLIST_SHUFFLE)
        return True


    # --== Message handlers ==--


    def onModLoaded(self):
        """ The module has been loaded """
        self.timer       = None
        self.cfgWin      = None
        self.enabled     = prefs.get(__name__, 'enabled', PREFS_DFT_ENABLED)
        self.periodicity = prefs.get(__name__, 'periodicity', PREFS_DFT_PERIODICITY)


    def onModUnloaded(self):
        """ The module has been unloaded """
        if self.timer is not None:
            gobject.source_remove(self.timer)
            self.timer = None


    def onNewTrack(self, track):
        """ A new track is being played """
        if self.enabled and self.timer is None and track is not None:
            self.timer = gobject.timeout_add_seconds(self.periodicity * 60, self.timerFunc)


    def onStop(self):
        """ Playback has been stopped """
        if self.timer is not None:
            gobject.source_remove(self.timer)
            self.timer = None


    # --== Configuration ==--


    def configure(self, parent):
        """ Show the configuration dialog """
        if self.cfgWin is None:
            import gui.window

            self.cfgWin = gui.window.Window('AutoShuffle.ui', 'vbox1', __name__, MOD_INFO[modules.MODINFO_L10N], 340, 180)

            self.cfgWin.getWidget('btn-ok').connect('clicked', self.onBtnOk)
            self.cfgWin.getWidget('btn-help').connect('clicked', self.onBtnHelp)
            self.cfgWin.getWidget('chk-enabled').connect('toggled', self.onEnabledToggled)
            self.cfgWin.getWidget('btn-cancel').connect('clicked', lambda btn: self.cfgWin.hide())

        if not self.cfgWin.isVisible():
            self.cfgWin.getWidget('chk-enabled').set_active(self.enabled)
            self.cfgWin.getWidget('slider-periodicity').set_value(self.periodicity)
            self.cfgWin.getWidget('slider-periodicity').set_sensitive(self.enabled)

            self.cfgWin.getWidget('btn-cancel').grab_focus()

        self.cfgWin.show()


    def onEnabledToggled(self, chkEnabled):
        """ The 'enabled' checkbox has been toggled """
        self.cfgWin.getWidget('slider-periodicity').set_sensitive(chkEnabled.get_active())


    def onBtnOk(self, btn):
        """ The button 'Ok' has been pressed """
        self.enabled     = self.cfgWin.getWidget('chk-enabled').get_active()
        self.periodicity = int(self.cfgWin.getWidget('slider-periodicity').get_value())

        prefs.set(__name__, 'enabled', self.enabled)
        prefs.set(__name__, 'periodicity', self.periodicity)

        # Restart timer, periodicity may have changed
        if self.timer is not None:
            gobject.source_remove(self.timer)

            if self.enabled:
                self.timer = gobject.timeout_add_seconds(self.periodicity * 60, self.timerFunc)

        self.cfgWin.hide()


    def onBtnHelp(self, btn):
        """ Display a small help message box """
        from gui import help

        helpDlg = help.HelpDlg(MOD_INFO[modules.MODINFO_L10N])
        helpDlg.addSection(_('Description'),
                           _('When active, this module periodically shuffles the playlist. This is '
                             'useful for example to simulate a radio station with a large playlist. '
                             'This module works best when the repeat function is enabled as well.'))

        helpDlg.show(self.cfgWin)
