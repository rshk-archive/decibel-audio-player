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

import modules, os, tools, traceback

from tools     import consts, prefs
from gettext   import gettext as _
from tools.log import logger


# Module information
MOD_INFO = ('Covers', _('Covers'), _('Show album covers'), [], False, True, consts.MODCAT_DECIBEL)
MOD_NAME = MOD_INFO[modules.MODINFO_NAME]

AS_API_KEY   = 'fd8dd98d26bb3f288f3e626502f9add6'   # Ingelrest François' Audioscrobbler API key
AS_TAG_START = '<image size="large">'               # The text that is right before the URL to the cover
AS_TAG_END   = '</image>'                           # The text that is right after the URL to the cover

# It seems that a non standard 'user-agent' header may cause problem, so let's cheat
USER_AGENT = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008072820 Firefox/3.0.1'

# We store both the paths to the thumbnail and to the full size image
(
    CVR_THUMB,
    CVR_FULL,
) = range(2)

# Width/height of PIL images
(
    PIL_WIDTH,
    PIL_HEIGHT,
) = range(2)

# Constants for thumbnails
THUMBNAIL_WIDTH   = 100  # Width allocated to thumbnails in the model
THUMBNAIL_HEIGHT  = 100  # Height allocated to thumbnails in the model
THUMBNAIL_OFFSETX =  11  # X-offset to render the thumbnail in the model
THUMBNAIL_OFFSETY =   3  # Y-offset to render the thumbnail in the model

# Constants for full size covers
FULLSIZE_WIDTH  = 300
FULLSIZE_HEIGHT = 300

# File formats we can read
ACCEPTED_FILE_FORMATS = {'.jpg': None, '.jpeg': None, '.png': None, '.gif': None}

# Default preferences
PREFS_DFT_DOWNLOAD_COVERS       = False
PREFS_DFT_PREFER_USER_COVERS    = True
PREFS_DFT_USER_COVER_FILENAMES  = ['cover', 'art', 'front', '*']
PREFS_DFT_SEARCH_IN_PARENT_DIRS = False

# Images for thumbnails
THUMBNAIL_GLOSS = os.path.join(consts.dirPix, 'cover-gloss.png')
THUMBNAIL_MODEL = os.path.join(consts.dirPix, 'cover-model.png')


class Covers(modules.ThreadedModule):

    def __init__(self):
        """ Constructor """
        handlers = {
                        consts.MSG_EVT_APP_QUIT:     self.onModUnloaded,
                        consts.MSG_EVT_NEW_TRACK:    self.onNewTrack,
                        consts.MSG_EVT_MOD_LOADED:   self.onModLoaded,
                        consts.MSG_EVT_APP_STARTED:  self.onModLoaded,
                        consts.MSG_EVT_MOD_UNLOADED: self.onModUnloaded,
                   }

        modules.ThreadedModule.__init__(self, handlers)


    def __resizeWithRatio(self, width, height, maxWidth, maxHeight):
        """
            Fit (width x height) into (maxWidth x maxHeight) while preserving the ratio of the original image
            If the ratios are close to each other, distort the original image to fit exactly into (maxWidth x maxHeight)

            Return a tuple (newWidth, newheight)
        """
        diffWidth  = width - maxWidth
        diffHeight = height - maxHeight

        # If the image is small enough, we don't need to scale it
        if diffWidth <= 0 and diffHeight <= 0:
            newWidth  = width
            newHeight = height
        else:
            # If the ratios are close to each other, we can afford some distortion in the original image
            ratioSrc = width / float(height)
            ratioDst = maxWidth / float(maxHeight)

            if abs(ratioSrc - ratioDst) / float(min(ratioSrc, ratioDst)) <= 0.05: keepRatio = False
            else:                                                                 keepRatio = True

            # Scale image
            if diffHeight > diffWidth:
                newHeight = maxHeight

                if keepRatio: newWidth = width * maxHeight / height
                else:         newWidth = maxWidth
            else:
                newWidth = maxWidth

                if keepRatio: newHeight = height * maxWidth / width
                else:         newHeight = maxHeight

        return (newWidth, newHeight)


    def generateFullSizeCover(self, inFile, outFile, format):
        """ Resize inFile if needed, and write it to outFile (outFile and inFile may be equal) """
        import Image

        try:
            # Open the image
            cover = Image.open(inFile)

            # Fit the image into FULLSIZE_WIDTH x FULLSIZE_HEIGHT
            (newWidth, newHeight) = self.__resizeWithRatio(cover.size[PIL_WIDTH], cover.size[PIL_HEIGHT], FULLSIZE_WIDTH, FULLSIZE_HEIGHT)

            # Resize it
            cover = cover.resize((newWidth, newHeight), Image.ANTIALIAS)

            # We're done
            cover.save(outFile, format)
        except:
            logger.error('[%s] An error occurred while generating a showable full size cover\n\n%s' % (MOD_NAME, traceback.format_exc()))


    def generateThumbnail(self, inFile, outFile, format):
        """ Generate a thumbnail from inFile (e.g., resize it) and write it to outFile (outFile and inFile may be equal) """
        import Image

        try:
            # Open the image
            cover = Image.open(inFile).convert('RGBA')

            # Fit the image into THUMBNAIL_WIDTH x THUMBNAIL_HEIGHT
            (newWidth, newHeight) = self.__resizeWithRatio(cover.size[PIL_WIDTH], cover.size[PIL_HEIGHT], THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT)

            # We need to shift the image if it doesn't fully fill the thumbnail
            if newWidth < THUMBNAIL_WIDTH: offsetX = (THUMBNAIL_WIDTH - newWidth) / 2
            else:                          offsetX = 0

            if newHeight < THUMBNAIL_HEIGHT: offsetY = (THUMBNAIL_HEIGHT - newHeight) / 2
            else:                            offsetY = 0

            # Resize the image
            cover = cover.resize((newWidth, newHeight), Image.ANTIALIAS)

            # Paste the resized cover into our model
            model = Image.open(THUMBNAIL_MODEL).convert('RGBA')
            model.paste(cover, (THUMBNAIL_OFFSETX + offsetX, THUMBNAIL_OFFSETY + offsetY), cover)
            cover = model

            # Don't apply the gloss effect if asked to
            if not prefs.getCmdLine()[0].no_glossy_cover:
                gloss = Image.open(THUMBNAIL_GLOSS).convert('RGBA')
                cover.paste(gloss, (0, 0), gloss)

            # We're done
            cover.save(outFile, format)
        except:
            logger.error('[%s] An error occurred while generating a thumbnail\n\n%s' % (MOD_NAME, traceback.format_exc()))


    def getUserCover(self, trackPath):
        """ Return the path to a cover file in trackPath, None if no cover found """
        splitPath = tools.splitPath(trackPath)

        if prefs.get(__name__, 'search-in-parent-dirs', PREFS_DFT_SEARCH_IN_PARENT_DIRS): lvls = len(splitPath)
        else:                                                                             lvls = 1

        while lvls != 0:

            # Create the path we're currently looking into
            currPath = os.path.join(*splitPath)

            # Create a dictionary with candidates
            candidates = {}
            for (file, path) in tools.listDir(currPath, True):
                (name, ext) = os.path.splitext(file.lower())
                if ext in ACCEPTED_FILE_FORMATS:
                    candidates[name] = path

            # Check each possible name using its index in the list as its priority
            for name in prefs.get(__name__, 'user-cover-filenames', PREFS_DFT_USER_COVER_FILENAMES):
                if name in candidates:
                    return candidates[name]

                if name == '*' and len(candidates) != 0:
                    return candidates.values()[0]

            # No cover found, let's go one level higher
            lvls      -= 1
            splitPath  = splitPath[:-1]

        return None


    def getFromCache(self, artist, album):
        """ Return the path to the cached cover, or None if it's not cached """
        cachePath    = os.path.join(self.cacheRootPath, str(abs(hash(artist))))
        cacheIdxPath = os.path.join(cachePath, 'INDEX')

        try:
            cacheIdx = tools.pickleLoad(cacheIdxPath)
            cover    = os.path.join(cachePath, cacheIdx[artist + album])
            if os.path.exists(cover):
                return cover
        except:
            pass

        return None


    def __getFromInternet(self, artist, album):
        """
            Try to download the cover from the Internet
            If successful, add it to the cache and return the path to it
            Otherwise, return None
        """
        import socket, urllib2

        # Make sure to not be blocked by the request
        socket.setdefaulttimeout(consts.socketTimeout)

        # Request information to Last.fm
        # Beware of UTF-8 characters: we need to percent-encode all characters
        try:
            url = 'http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key=%s&artist=%s&album=%s' % (AS_API_KEY,
                tools.percentEncode(artist), tools.percentEncode(album))
            request = urllib2.Request(url, headers = {'User-Agent': USER_AGENT})
            stream = urllib2.urlopen(request)
            data = stream.read()
        except urllib2.HTTPError, err:
            if err.code == 400:
                logger.error('[%s] No known cover for %s / %s' % (MOD_NAME, artist, album))
            else:
                logger.error('[%s] Information request failed\n\n%s' % (MOD_NAME, traceback.format_exc()))
            return None
        except:
            logger.error('[%s] Information request failed\n\n%s' % (MOD_NAME, traceback.format_exc()))
            return None

        # Extract the URL to the cover image
        malformed = True
        startIdx  = data.find(AS_TAG_START)
        endIdx    = data.find(AS_TAG_END, startIdx)
        if startIdx != -1 and endIdx != -1:
            coverURL    = data[startIdx+len(AS_TAG_START):endIdx]
            coverFormat = os.path.splitext(coverURL)[1].lower()
            if coverURL.startswith('http://') and coverFormat in ACCEPTED_FILE_FORMATS:
                malformed = False

        if malformed:
            logger.error('[%s] Received malformed data\n\n%s' % (MOD_NAME, data))
            return None

        # Download the cover image
        try:
            request = urllib2.Request(coverURL, headers = {'User-Agent': USER_AGENT})
            stream  = urllib2.urlopen(request)
            data    = stream.read()

            if len(data) < 1024:
                raise Exception, 'The cover image seems incorrect (%u bytes is too small)' % len(data)
        except:
            logger.error('[%s] Cover image request failed\n\n%s' % (MOD_NAME, traceback.format_exc()))
            return None

        # So far, so good: let's cache the image
        cachePath    = os.path.join(self.cacheRootPath, str(abs(hash(artist))))
        cacheIdxPath = os.path.join(cachePath, 'INDEX')

        if not os.path.exists(cachePath):
            os.mkdir(cachePath)

        try:    cacheIdx = tools.pickleLoad(cacheIdxPath)
        except: cacheIdx = {}

        nextInt   = len(cacheIdx) + 1
        filename  = str(nextInt) + coverFormat
        coverPath = os.path.join(cachePath, filename)

        cacheIdx[artist + album] = filename
        tools.pickleSave(cacheIdxPath, cacheIdx)

        try:
            output = open(coverPath, 'wb')
            output.write(data)
            output.close()
            return coverPath
        except:
            logger.error('[%s] Could not save the downloaded cover\n\n%s' % (MOD_NAME, traceback.format_exc()))

        return None


    def getFromInternet(self, artist, album):
        """ Wrapper for __getFromInternet(), manage blacklist """
        # If we already tried without success, don't try again
        if (artist, album) in self.coverBlacklist:
            return None

        # Otherwise, try to download the cover
        cover = self.__getFromInternet(artist, album)

        # If the download failed, blacklist the album
        if cover is None:
            self.coverBlacklist[(artist, album)] = None

        return cover


    # --== Message handlers ==--


    def onModLoaded(self):
        """ The module has been loaded """
        self.cfgWin         = None                                   # Configuration window
        self.coverMap       = {}                                     # Store covers previously requested
        self.currTrack      = None                                   # The current track being played, if any
        self.cacheRootPath  = os.path.join(consts.dirCfg, MOD_NAME)  # Local cache for Internet covers
        self.coverBlacklist = {}                                     # When a cover cannot be downloaded, avoid requesting it again

        if not os.path.exists(self.cacheRootPath):
            os.mkdir(self.cacheRootPath)


    def onModUnloaded(self):
        """ The module has been unloaded """
        if self.currTrack is not None:
            modules.postMsg(consts.MSG_CMD_SET_COVER, {'track': self.currTrack, 'pathThumbnail': None, 'pathFullSize': None})

        # Delete covers that have been generated by this module
        for covers in self.coverMap.itervalues():
            if os.path.exists(covers[CVR_THUMB]):
                os.remove(covers[CVR_THUMB])
            if os.path.exists(covers[CVR_FULL]):
                os.remove(covers[CVR_FULL])
        self.coverMap = None

        # Delete blacklist
        self.coverBlacklist = None


    def onNewTrack(self, track):
        """ A new track is being played, try to retrieve the corresponding cover """
        # Make sure we have enough information
        if track.getArtist() == consts.UNKNOWN_ARTIST or track.getAlbum() == consts.UNKNOWN_ALBUM:
            modules.postMsg(consts.MSG_CMD_SET_COVER, {'track': track, 'pathThumbnail': None, 'pathFullSize': None})
            return

        album          = track.getAlbum().lower()
        artist         = track.getArtist().lower()
        rawCover       = None
        self.currTrack = track

        # Let's see whether we already have the cover
        if (artist, album) in self.coverMap:
            covers        = self.coverMap[(artist, album)]
            pathFullSize  = covers[CVR_FULL]
            pathThumbnail = covers[CVR_THUMB]

            # Make sure the files are still there
            if os.path.exists(pathThumbnail) and os.path.exists(pathFullSize):
                modules.postMsg(consts.MSG_CMD_SET_COVER, {'track': track, 'pathThumbnail': pathThumbnail, 'pathFullSize': pathFullSize})
                return

        # Should we check for a user cover?
        if not prefs.get(__name__, 'download-covers', PREFS_DFT_DOWNLOAD_COVERS)        \
            or prefs.get(__name__, 'prefer-user-covers', PREFS_DFT_PREFER_USER_COVERS):
                rawCover = self.getUserCover(os.path.dirname(track.getFilePath()))

        # Is it in our cache?
        if rawCover is None:
            rawCover = self.getFromCache(artist, album)

        # If we still don't have a cover, maybe we can try to download it
        if rawCover is None:
            modules.postMsg(consts.MSG_CMD_SET_COVER, {'track': track, 'pathThumbnail': None, 'pathFullSize': None})

            if prefs.get(__name__, 'download-covers', PREFS_DFT_DOWNLOAD_COVERS):
                rawCover = self.getFromInternet(artist, album)

        # If we still don't have a cover, too bad
        # Otherwise, generate a thumbnail and a full size cover, and add it to our cover map
        if rawCover is not None:
            import tempfile

            thumbnail     = tempfile.mktemp() + '.png'
            fullSizeCover = tempfile.mktemp() + '.png'
            self.generateThumbnail(rawCover, thumbnail, 'PNG')
            self.generateFullSizeCover(rawCover, fullSizeCover, 'PNG')
            if os.path.exists(thumbnail) and os.path.exists(fullSizeCover):
                self.coverMap[(artist, album)] = (thumbnail, fullSizeCover)
                modules.postMsg(consts.MSG_CMD_SET_COVER, {'track': track, 'pathThumbnail': thumbnail, 'pathFullSize': fullSizeCover})
            else:
                modules.postMsg(consts.MSG_CMD_SET_COVER, {'track': track, 'pathThumbnail': None, 'pathFullSize': None})


    # --== Configuration ==--


    def configure(self, parent):
        """ Show the configuration window """
        if self.cfgWin is None:
            from gui.window import Window

            self.cfgWin = Window('Covers.ui', 'vbox1', __name__, MOD_INFO[modules.MODINFO_L10N], 320, 265)
            self.cfgWin.getWidget('btn-ok').connect('clicked', self.onBtnOk)
            self.cfgWin.getWidget('img-lastfm').set_from_file(os.path.join(consts.dirPix, 'audioscrobbler.png'))
            self.cfgWin.getWidget('btn-help').connect('clicked', self.onBtnHelp)
            self.cfgWin.getWidget('chk-downloadCovers').connect('toggled', self.onDownloadCoversToggled)
            self.cfgWin.getWidget('btn-cancel').connect('clicked', lambda btn: self.cfgWin.hide())

        if not self.cfgWin.isVisible():
            downloadCovers     = prefs.get(__name__, 'download-covers',       PREFS_DFT_DOWNLOAD_COVERS)
            preferUserCovers   = prefs.get(__name__, 'prefer-user-covers',    PREFS_DFT_PREFER_USER_COVERS)
            userCoverFilenames = prefs.get(__name__, 'user-cover-filenames',  PREFS_DFT_USER_COVER_FILENAMES)
            searchInParentDirs = prefs.get(__name__, 'search-in-parent-dirs', PREFS_DFT_SEARCH_IN_PARENT_DIRS)

            self.cfgWin.getWidget('btn-ok').grab_focus()
            self.cfgWin.getWidget('txt-filenames').set_text(', '.join(userCoverFilenames))
            self.cfgWin.getWidget('chk-downloadCovers').set_active(downloadCovers)
            self.cfgWin.getWidget('chk-preferUserCovers').set_active(preferUserCovers)
            self.cfgWin.getWidget('chk-preferUserCovers').set_sensitive(downloadCovers)
            self.cfgWin.getWidget('chk-searchInParentDirs').set_active(searchInParentDirs)

        self.cfgWin.show()


    def onBtnOk(self, btn):
        """ Save configuration """
        downloadCovers     = self.cfgWin.getWidget('chk-downloadCovers').get_active()
        preferUserCovers   = self.cfgWin.getWidget('chk-preferUserCovers').get_active()
        searchInParentDirs = self.cfgWin.getWidget('chk-searchInParentDirs').get_active()
        userCoverFilenames = [word.strip() for word in self.cfgWin.getWidget('txt-filenames').get_text().split(',')]

        prefs.set(__name__, 'download-covers',       downloadCovers)
        prefs.set(__name__, 'prefer-user-covers',    preferUserCovers)
        prefs.set(__name__, 'user-cover-filenames',  userCoverFilenames)
        prefs.set(__name__, 'search-in-parent-dirs', searchInParentDirs)

        self.cfgWin.hide()


    def onDownloadCoversToggled(self, downloadCovers):
        """ Toggle the "prefer user covers" checkbox according to the state of the "download covers" one """
        self.cfgWin.getWidget('chk-preferUserCovers').set_sensitive(downloadCovers.get_active())


    def onBtnHelp(self, btn):
        """ Display a small help message box """
        from gui import help

        helpDlg = help.HelpDlg(MOD_INFO[modules.MODINFO_L10N])
        helpDlg.addSection(_('Description'),
                           _('This module displays the cover of the album the current track comes from. Covers '
                              'may be loaded from local pictures, located in the same directory as the current '
                              'track, or may be downloaded from the Internet.'))
        helpDlg.addSection(_('User Covers'),
                           _('A user cover is a picture located in the same directory as the current track. '
                             'When specifying filenames, you do not need to provide file extensions, supported '
                             'file formats (%s) are automatically used. This module can be configured to search '
                             'for user covers in parent directories are well.' % ', '.join(ACCEPTED_FILE_FORMATS.iterkeys())))
        helpDlg.addSection(_('Internet Covers'),
                           _('Covers may be downloaded from the Internet, based on the tags of the current track. '
                             'You can ask to always prefer user covers to Internet ones. In this case, if a user '
                             'cover exists for the current track, it is used. If there is none, the cover is downloaded.'))
        helpDlg.show(self.cfgWin)
