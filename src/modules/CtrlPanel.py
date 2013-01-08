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

import gtk, modules, tools

from tools   import consts, prefs, sec2str
from gettext import gettext as _

MOD_INFO = ('Control Panel', 'Control Panel', '', [], True, False, consts.MODCAT_NONE)

PREFS_DEFAULT_VOLUME = 0.65


class CtrlPanel(modules.Module):
    """ This module manages the control panel with the buttons and the slider """

    def __init__(self):
        """ Constructor """
        handlers = {
                        consts.MSG_EVT_PAUSED:           self.onPaused,
                        consts.MSG_EVT_STOPPED:          self.onStopped,
                        consts.MSG_EVT_UNPAUSED:         self.onUnpaused,
                        consts.MSG_EVT_APP_QUIT:         self.onAppQuit,
                        consts.MSG_EVT_NEW_TRACK:        self.onNewTrack,
                        consts.MSG_EVT_TRACK_MOVED:      self.onCurrentTrackMoved,
                        consts.MSG_EVT_APP_STARTED:      self.onAppStarted,
                        consts.MSG_EVT_NEW_TRACKLIST:    self.onNewTracklist,
                        consts.MSG_EVT_VOLUME_CHANGED:   self.onVolumeChanged,
                        consts.MSG_EVT_TRACK_POSITION:   self.onNewTrackPosition,
                   }

        modules.Module.__init__(self, handlers)


   # --== Message handler ==--


    def onAppStarted(self):
        """ Real initialization function, called when this module has been loaded """
        self.currTrackLength = 0
        self.sclBeingDragged = False

        # Widgets
        wTree             = prefs.getWidgetsTree()
        self.btnStop      = wTree.get_object('btn-stop')
        self.btnPlay      = wTree.get_object('btn-play')
        self.btnNext      = wTree.get_object('btn-next')
        self.btnPrev      = wTree.get_object('btn-previous')
        self.sclSeek      = wTree.get_object('scl-position')
        self.btnVolume    = wTree.get_object('btn-volume')
        self.lblElapsed   = wTree.get_object('lbl-elapsedTime')
        self.lblRemaining = wTree.get_object('lbl-remainingTime')

        # Don't show the volume button when using playbin2 and pulseaudio together (#511589)
        if not tools.isPulseAudioRunning() or prefs.getCmdLine()[0].playbin or prefs.getCmdLine()[0].volume_button:
            self.btnVolume.show()

        # Restore the volume
        volume = prefs.get(__name__, 'volume', PREFS_DEFAULT_VOLUME)
        self.btnVolume.set_value(volume)
        modules.postMsg(consts.MSG_CMD_SET_VOLUME, {'value': volume})

        # GTK handlers
        self.btnStop.connect('clicked', lambda widget: modules.postMsg(consts.MSG_CMD_STOP))
        self.btnNext.connect('clicked', lambda widget: modules.postMsg(consts.MSG_CMD_NEXT))
        self.btnPrev.connect('clicked', lambda widget: modules.postMsg(consts.MSG_CMD_PREVIOUS))
        self.btnPlay.connect('clicked', lambda widget: modules.postMsg(consts.MSG_CMD_TOGGLE_PAUSE))
        self.sclSeek.connect('change-value', self.onSeekChangingValue)
        self.sclSeek.connect('value-changed', self.onSeekValueChanged)
        self.btnVolume.connect('value-changed', self.onVolumeValueChanged)
        self.sclSeek.connect('button-press-event', self.onSeekButtonPressed)
        self.sclSeek.connect('button-release-event', self.onSeekButtonReleased)


    def onAppQuit(self):
        """ The application is about to terminate """
        prefs.set(__name__, 'volume', self.btnVolume.get_value())


    def onNewTrack(self, track):
        """ A new track is being played """
        self.btnStop.set_sensitive(True)
        self.btnPlay.set_sensitive(True)
        self.btnPlay.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_BUTTON))
        self.btnPlay.set_tooltip_text(_('Pause the current track'))

        self.currTrackLength = track.getLength()
        self.sclSeek.show()
        self.lblElapsed.show()
        self.lblRemaining.show()
        self.onNewTrackPosition(0)

        # Must be done last
        if self.currTrackLength != 0:
            self.sclSeek.set_range(0, self.currTrackLength)


    def onStopped(self):
        """ The playback has been stopped """
        self.btnStop.set_sensitive(False)
        self.btnNext.set_sensitive(False)
        self.btnPrev.set_sensitive(False)
        self.btnPlay.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON))
        self.btnPlay.set_tooltip_text(_('Play the first selected track of the playlist'))
        self.sclSeek.hide()
        self.lblElapsed.hide()
        self.lblRemaining.hide()


    def onNewTrackPosition(self, seconds):
        """ The track position has changed """
        if not self.sclBeingDragged:
            self.lblElapsed.set_label(sec2str(seconds))
            if seconds >= self.currTrackLength:
                seconds = self.currTrackLength
            self.lblRemaining.set_label(sec2str(self.currTrackLength - seconds))
            # Make sure the handler will not be called
            self.sclSeek.handler_block_by_func(self.onSeekValueChanged)
            self.sclSeek.set_value(seconds)
            self.sclSeek.handler_unblock_by_func(self.onSeekValueChanged)


    def onVolumeChanged(self, value):
        """ The volume has been changed """
        self.btnVolume.handler_block_by_func(self.onVolumeValueChanged)
        self.btnVolume.set_value(value)
        self.btnVolume.handler_unblock_by_func(self.onVolumeValueChanged)


    def onCurrentTrackMoved(self, hasPrevious, hasNext):
        """ Update previous and next buttons """
        self.btnNext.set_sensitive(hasNext)
        self.btnPrev.set_sensitive(hasPrevious)


    def onPaused(self):
        """ The playback has been paused """
        self.btnPlay.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON))
        self.btnPlay.set_tooltip_text(_('Continue playing the current track'))


    def onUnpaused(self):
        """ The playback has been unpaused """
        self.btnPlay.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_BUTTON))
        self.btnPlay.set_tooltip_text(_('Pause the current track'))


    def onNewTracklist(self, tracks, playtime):
        """ A new tracklist has been set """
        self.btnPlay.set_sensitive(playtime != 0)


    # --== GTK handlers ==--


    def onSeekValueChanged(self, range):
        """ The user has moved the seek slider """
        modules.postMsg(consts.MSG_CMD_SEEK, {'seconds': int(range.get_value())})
        self.sclBeingDragged = False


    def onSeekChangingValue(self, range, scroll, value):
        """ The user is moving the seek slider """
        self.sclBeingDragged = True

        if value >= self.currTrackLength: value = self.currTrackLength
        else:                             value = int(value)

        self.lblElapsed.set_label(sec2str(value))
        self.lblRemaining.set_label(sec2str(self.currTrackLength - value))


    def onSeekButtonPressed(self, range, event):
        """ Mouse button has been pressed over the seek slider """
        # Make left clicks act the same as middle clicks
        if event.button == 1:
            event.button = 2
            range.emit('button-press-event', event)
            return True


    def onSeekButtonReleased(self, range, event):
        """ Mouse button has been released over the seek slider """
        # Make left clicks act the same as middle clicks
        if event.button == 1:
            event.button = 2
            range.emit('button-release-event', event)
            return True


    def onVolumeValueChanged(self, button, value):
        """ The user has moved the volume slider """
        modules.postMsg(consts.MSG_CMD_SET_VOLUME, {'value': value})
