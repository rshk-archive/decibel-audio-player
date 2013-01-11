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
import gobject, gtk, os.path
from .. import modules, tools
from ..tools   import consts

MOD_INFO = ('Track Panel', 'Track Panel', '', [], True, False, consts.MODCAT_NONE)


class TrackPanel(modules.Module):
    """
        This module manages the panel showing information on the current track.
        This includes the thumbnail of the current cover, if the user has enabled the 'Covers' module.
    """

    def __init__(self):
        """ Constructor """
        handlers = {
                        consts.MSG_EVT_STOPPED:     self.onStopped,
                        consts.MSG_CMD_SET_COVER:   self.onSetCover,
                        consts.MSG_EVT_NEW_TRACK:   self.onNewTrack,
                        consts.MSG_EVT_APP_STARTED: self.onAppStarted,
                   }

        modules.Module.__init__(self, handlers)


    def __setTitle(self, title, length=None):
        """ Change the title of the current track """
        title = tools.htmlEscape(title)

        if length is None: self.txtTitle.set_markup('<span size="larger"><b>%s</b></span>' % title)
        else:              self.txtTitle.set_markup('<span size="larger"><b>%s</b></span>  [%s]' % (title, tools.sec2str(length)))


    def __setImage(self, imgPath):
        """
            Change the current image to imgPath.
            Use the application's icon if imgPath is None.
        """
        if imgPath is None: self.img.set_from_file(os.path.join(tools.consts.dirPix, 'cover-none.png'))
        else:               self.img.set_from_file(imgPath)


    def __showCover(self, mouseX, mouseY):
        """
            Display a popup window showing the full size cover.
            The window closes automatically when clicked or when the mouse leaves it.
        """
        # Don't do anything if there's already a cover
        if self.coverWindow is not None:
            return

        frame            = gtk.Frame()
        image            = gtk.Image()
        evtBox           = gtk.EventBox()
        self.coverWindow = gtk.Window(gtk.WINDOW_POPUP)

        # Construct the window
        image.set_from_file(self.currCoverPath)
        evtBox.add(image)
        frame.set_shadow_type(gtk.SHADOW_IN)
        frame.add(evtBox)
        self.coverWindow.add(frame)

        # Center the window around (x, y), but make sure it isn't out of the screen
        width  = image.get_pixbuf().get_width()
        height = image.get_pixbuf().get_height()

        posX = int(mouseX - (width / 2))
        posY = int(mouseY - (height / 2))

        (resoX, resoY) = tools.getDefaultScreenResolution()

        if posX < 0:               posX = 0
        elif posX + width > resoX: posX = resoX - width

        if posY < 0:                posY = 0
        elif posY + height > resoY: posY = resoY - height

        self.coverWindow.move(posX, posY)

        # Destroy the window when clicked and when the mouse leaves it
        evtBox.connect('button-press-event', self.onCoverWindowDestroy)
        evtBox.connect('leave-notify-event', self.onCoverWindowDestroy)

        self.coverWindow.show_all()


    # --== Message handlers ==--


    def onAppStarted(self):
        """ Real initialization function, called when this module has been loaded """
        # Widgets
        wTree                  = tools.prefs.getWidgetsTree()
        evtBox                 = wTree.get_object('evtbox-cover')
        self.img               = wTree.get_object('img-cover')
        self.txtMisc           = wTree.get_object('lbl-trkMisc')
        self.txtTitle          = wTree.get_object('lbl-trkTitle')
        self.imgFrame          = wTree.get_object('frm-cover')
        self.currTrack         = None
        self.coverWindow       = None
        self.coverTimerId      = None
        self.currCoverPath     = None
        self.lastMousePosition = (0, 0)
        # GTK handlers
        evtBox.connect('leave-notify-event', self.onImgMouseLeave)
        evtBox.connect('enter-notify-event', self.onImgMouseEnter)


    def onNewTrack(self, track):
        """ A new track is being played """
        self.currTrack = track

        self.__setTitle(track.getTitleOrFilename(), track.getLength())
        self.txtMisc.set_text(_('by %(artist)s\nfrom %(album)s' % {'artist': track.getArtist(), 'album': track.getExtendedAlbum()}))


    def onStopped(self):
        """ Playback has been stopped """
        self.currTrack     = None
        self.currCoverPath = None

        self.__setImage(None)
        self.__setTitle(consts.appName)
        self.txtMisc.set_text('...And Music For All\n')


    def onSetCover(self, track, pathThumbnail, pathFullSize):
        """ Set the cover that is currently displayed """
        # Must check if currTrack is not None, because '==' calls the cmp() method and this fails on None
        if self.currTrack is not None and track == self.currTrack:
            self.currCoverPath = pathFullSize
            self.__setImage(pathThumbnail)

            # Create symbolic links to these covers so that external apps can access them
            if pathFullSize is not None and pathFullSize is not None:
                ext      = os.path.splitext(pathFullSize)[1]
                extThumb = os.path.splitext(pathThumbnail)[1]

                link      = os.path.join(consts.USER_CONFIG_DIR, 'current-cover' + ext)
                linkThumb = os.path.join(consts.USER_CONFIG_DIR, 'current-cover-small' + extThumb)

                os.system('rm -f "%s"' % link)
                os.system('rm -f "%s"' % linkThumb)

                os.system('ln -s "%s" "%s"' % (pathFullSize, link))
                os.system('ln -s "%s" "%s"' % (pathThumbnail, linkThumb))


    # --== GTK handlers ==--


    def onImgMouseEnter(self, evtBox, event):
        """ The mouse is over the event box """
        if self.currCoverPath is not None and (event.x_root, event.y_root) != self.lastMousePosition:
            self.coverTimerId = gobject.timeout_add(600, self.onCoverTimerTimedOut)


    def onImgMouseLeave(self, evtBox, event):
        """ The mouse left the event box """
        self.lastMousePosition = (0, 0)
        if self.coverTimerId is not None:
            gobject.source_remove(self.coverTimerId)
            self.coverTimerId = None


    def onCoverTimerTimedOut(self):
        """ The mouse has been over the cover thumbnail during enough time """
        if self.currCoverPath is not None:
            self.__showCover(*tools.getCursorPosition())
        return False


    def onCoverWindowDestroy(self, widget, event):
        """ Destroy the cover window """
        if self.coverWindow is not None:
            self.coverWindow.destroy()
            self.coverWindow = None
            self.lastMousePosition = tools.getCursorPosition()
