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

import modules, time

from tools   import consts, prefs
from gettext import gettext as _

MOD_INFO = ('Automatic Resume', _('Automatic Resume'), _('Automatically resume playback on startup'), [], False, False, consts.MODCAT_DECIBEL)

# Maximum time between the startup and the restoration of the last playlist
MAX_TRACKLIST_RESTORATION_DELAY = 1.5

class AutoResume(modules.Module):

    def __init__(self):
        """ Constructor """
        handlers = {
                        consts.MSG_EVT_PAUSED:         self.onPaused,
                        consts.MSG_EVT_STOPPED:        self.onStop,
                        consts.MSG_EVT_UNPAUSED:       self.onUnpaused,
                        consts.MSG_EVT_APP_QUIT:       self.onModUnloaded,
                        consts.MSG_EVT_NEW_TRACK:      self.onNewTrack,
                        consts.MSG_EVT_APP_STARTED:    self.onAppStarted,
                        consts.MSG_EVT_MOD_LOADED:     self.onModLoaded,
                        consts.MSG_EVT_MOD_UNLOADED:   self.onModUnloaded,
                        consts.MSG_EVT_NEW_TRACKLIST:  self.onNewTracklist,
                        consts.MSG_EVT_TRACK_POSITION: self.onNewTrackPosition,
                   }

        modules.Module.__init__(self, handlers)


    def tryToRestore(self, tracklist):
        """ Check whether it's possible to restore playback """
        (options, args) = prefs.getCmdLine()

        # Ignore if the user provided its own tracks on the command line
        if len(args) != 0:
            return

        # Ignore if no track was being played last time
        if not self.playing or self.currTrack is None:
            return

        # Make sure the playlist is the same one
        if len(tracklist) != len(self.currTracklist):
            return

        trackIdx = -1
        for i in xrange(len(tracklist)):
            if tracklist[i] != self.currTracklist[i]:
                return

            if tracklist[i] == self.currTrack:
                trackIdx = i

        # Once here, we know playback can be resumed
        if trackIdx != -1:
            if self.paused: modules.postMsg(consts.MSG_CMD_TRACKLIST_PLAY_PAUSE, {'idx': trackIdx, 'seconds': self.currPos})
            else:           modules.postMsg(consts.MSG_CMD_TRACKLIST_PLAY,       {'idx': trackIdx, 'seconds': self.currPos})



    # --== Message handlers ==--


    def onAppStarted(self):
        """ The application has been started """
        self.onModLoaded()
        self.startTime = time.time()


    def onModLoaded(self):
        """ The module has been loaded """
        self.startTime = 0

        self.paused        = prefs.get(__name__, 'was-paused', False)
        self.playing       = prefs.get(__name__, 'was-playing', False)
        self.currPos       = prefs.get(__name__, 'position', 0)
        self.currTrack     = prefs.get(__name__, 'track', None)
        self.currTracklist = prefs.get(__name__, 'tracklist', [])


    def onModUnloaded(self):
        """ The module is being unloaded """
        prefs.set(__name__, 'was-paused', self.paused)
        prefs.set(__name__, 'was-playing', self.playing)
        prefs.set(__name__, 'position', self.currPos)
        prefs.set(__name__, 'track', self.currTrack)
        prefs.set(__name__, 'tracklist', self.currTracklist)


    def onPaused(self):
        """ The playback has been paused """
        self.paused = True


    def onUnpaused(self):
        """ The playback has been unpaused """
        self.paused = False


    def onNewTrack(self, track):
        """ A new track is being played """
        if track is not None:
            self.paused    = False
            self.playing   = True
            self.currTrack = track


    def onStop(self):
        """ Playback has been stopped """
        self.playing = False


    def onNewTrackPosition(self, seconds):
        """ The track position has changed """
        self.currPos = seconds


    def onNewTracklist(self, tracks, playtime):
        """ A new tracklist has been set """
        if time.time() - self.startTime <= MAX_TRACKLIST_RESTORATION_DELAY:
            # Ignore the very first (empty) tracklist
            if len(tracks) != 0:
                self.tryToRestore(tracks)

                self.startTime     = 0
                self.currTracklist = tracks
        else:
            self.currTracklist = tracks
