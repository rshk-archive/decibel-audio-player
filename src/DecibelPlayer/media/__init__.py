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

import os, traceback
from os.path import splitext

from . import playlist
from .format import monkeysaudio, asf, flac, mp3, mp4, mpc, ogg, wav, wavpack
from .track.fileTrack import FileTrack
from ..tools.log import logger


# Supported formats with associated modules
mFormats = {
    '.ac3': monkeysaudio,
    '.ape': monkeysaudio,
    '.flac': flac,
    '.m4a': mp4,
    '.mp2': mp3,
    '.mp3': mp3,
    '.mp4': mp4,
    '.mpc': mpc,
    '.oga': ogg,
    '.ogg': ogg,
    '.wav': wav,
    '.wma': asf,
    '.wv': wavpack,
}

## todo: use python-magic to determine file type, instead of extension!

def isSupported(filename):
    """Return True if the given file is a supported format"""
    try:
        return splitext(filename.lower())[1] in mFormats
    except:
        return False


def getSupportedFormats():
    """ Return a list of all formats from which tags can be extracted """
    return ['*' + ext for ext in mFormats]


def getTrackFromFile(filename):
    """
    Return a Track object, based on the tags of the given file
    The 'file' parameter must be a real file (not a playlist or a directory)
    """
    try:
        return mFormats[splitext(filename.lower())[1]].getTrack(filename)

    except:
        logger.exception('Unable to extract information from %s' % filename)
        return FileTrack(filename)


def getTracksFromFiles(files):
    """ Same as getTrackFromFile(), but works on a list of files instead of a single one """
    return [getTrackFromFile(f) for f in files]


def getTracks(filenames, sortByFilename=False, ignoreHiddenFiles=True):
    """
    Same as getTracksFromFiles(), but works for any kind of filenames
    (files, playlists, directories)

    If sortByFilename is True, files loaded from directories are sorted
    by filename instead of tags

    If ignoreHiddenFiles is True, hidden files are ignored when walking
    directories
    """
    allTracks = []

    # Directories
    for directory in [filename for filename in filenames if os.path.isdir(filename)]:
        mediaFiles, playlists = [], []
        for root, subdirs, files in os.walk(directory):
            for file in files:
               if not ignoreHiddenFiles or file[0] != '.':
                    if isSupported(file):
                        mediaFiles.append(os.path.join(root, file))
                    elif playlist.isSupported(file):
                        playlists.append(os.path.join(root, file))

        if sortByFilename:
            allTracks.extend(sorted(
                getTracksFromFiles(mediaFiles),
                lambda t1, t2: cmp(t1.getFilePath(), t2.getFilePath())))
        else:
            allTracks.extend(sorted(getTracksFromFiles(mediaFiles)))

        for pl in playlists:
            allTracks.extend(getTracksFromFiles(playlist.load(pl)))

    # Files
    tracks = getTracksFromFiles([
        filename for filename in filenames
            if os.path.isfile(filename) and isSupported(filename)
    ])

    if sortByFilename:
        allTracks.extend(sorted(tracks, key=lambda x: x.getFilePath()))

    else:
        allTracks.extend(sorted(tracks))

    # Playlists
    for pl in [filename for filename in filenames if os.path.isfile(filename) and playlist.isSupported(filename)]:
        allTracks.extend(getTracksFromFiles(playlist.load(pl)))

    return allTracks
