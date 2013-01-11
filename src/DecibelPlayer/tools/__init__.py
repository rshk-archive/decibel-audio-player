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

import os, cPickle
import gtk
from .. import constants

_dirCache = {}

def listDir(directory, listHiddenFiles=False):
    """
    Return a list of tuples (filename, path) with the given directory content
    The dircache module sorts the list of files, and either it's not needed
    or it's not sorted the way we want
    """
    if directory in _dirCache:
        cachedMTime, list = _dirCache[directory]
    else:
        cachedMTime, list = None, None

    if os.path.exists(directory):
        mTime = os.stat(directory).st_mtime
    else:
        mTime = 0

    if mTime != cachedMTime:
        ## Make sure it's readable
        ## todo: NOOOOO!! Try to read, except do stuff, etc.
        if os.access(directory, os.R_OK | os.X_OK):
            list = os.listdir(directory)
        else:
            list = []

        _dirCache[directory] = (mTime, list)

    return [
        (filename, os.path.join(directory, filename))
            for filename in list if listHiddenFiles or filename[0] != '.']


_downloadCache = {}

def cleanupDownloadCache():
    """Remove temporary downloaded files"""
    for (cachedTime, file) in _downloadCache.itervalues():
        try:
            os.remove(file)
        except:
            pass

def downloadFile(url, cacheTimeout=3600):
    """
    If the file has been in the cache for less than 'cacheTimeout' seconds,
    return the cached file
    Otherwise download the file and cache it

    Return a tuple (errorMsg, data) where data is None if an error occurred,
    errorMsg containing the error message in this case
    """
    import socket, tempfile, time, urllib2

    if url in _downloadCache:
        cachedTime, file = _downloadCache[url]
    else:
        cachedTime, file = -cacheTimeout, None

    now = int(time.time())

    # If the timeout is not exceeded, get the data from the cache
    if (now - cachedTime) <= cacheTimeout:
        try:
            input = open(file, 'rb')
            data  = input.read()
            input.close()

            return ('', data)
        except:
            # If something went wrong with the cache, proceed to download
            pass

    # Make sure to not be blocked by the request
    socket.setdefaulttimeout(constants.socketTimeout)

    try:
        # Retrieve the data
        request = urllib2.Request(url)
        stream  = urllib2.urlopen(request)
        data    = stream.read()

        # Do we need to create a new temporary file?
        if file is None:
            handle, file = tempfile.mkstemp()
            os.close(handle)

        # On first file added to the cache, we register our clean up function
        if len(_downloadCache) == 0:
            import atexit
            atexit.register(cleanupDownloadCache)

        _downloadCache[url] = (now, file)

        output = open(file, 'wb')
        output.write(data)
        output.close()


    except urllib2.HTTPError, err:
        return 'The request failed with error code %u' % err.code, None

    except:
        return 'The request failed for unknown reasons', None

    else:
        return '', data



def sec2str(seconds, alwaysShowHours=False):
    """ Return a formatted string based on the given duration in seconds """
    hours, seconds   = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds,   60)

    if alwaysShowHours or hours != 0:
        return '%u:%02u:%02u' % (hours, minutes, seconds)
    else:
        return '%u:%02u' % (minutes, seconds)


def loadGladeFile(file, root=None):
    """ Load the given Glade file and return the tree of widgets """
    builder = gtk.Builder()

    if root is None:
        builder.add_from_file(os.path.join(constants.dirRes, file))
        return builder
    else:
        builder.add_from_file(os.path.join(constants.dirRes, file))
        widget = builder.get_object(root)
        return widget, builder


def pickleLoad(file):
    """ Use cPickle to load the data structure stored in the given file """
    input = open(file, 'r')
    data  = cPickle.load(input)
    input.close()
    return data


def pickleSave(file, data):
    """ Use cPickle to save the data to the given file """
    output = open(file, 'w')
    cPickle.dump(data, output)
    output.close()


def touch(filePath):
    """ Equivalent to the Linux 'touch' command """
    #os.system('touch "%s"' % filePath)
    with open(filePath, 'wb') as f:
        f.write('')


def percentEncode(string):
    """
    Percent-encode all the bytes in the given string
    Couldn't find a Python method to do that
    """
    mask  = '%%%X' * len(string)
    bytes = tuple([ord(c) for c in string])
    return mask % bytes


def getCursorPosition():
    """ Return a tuple (x, y) """
    cursorNfo = gtk.gdk.display_get_default().get_pointer()
    return (cursorNfo[1], cursorNfo[2])


def getDefaultScreenResolution():
    """ Return the resolution of the default screen """
    return (gtk.gdk.screen_width(), gtk.gdk.screen_height())


def htmlEscape(string):
    """ Replace characters &, <, and > by their equivalent HTML code """
    output = ''

    for c in string:
        if c == '&':   output += '&amp;'
        elif c == '<': output += '&lt;'
        elif c == '>': output += '&gt;'
        else:          output += c

    return output


def splitPath(path):
    """
    Return a list composed of all the elements forming the given path
    For instance, splitPath('/some/path/foo') returns ['some', 'path', 'foo']
    """
    path       = os.path.abspath(path)
    components = []

    while True:
        head, tail = os.path.split(path)

        if tail == '':
            return [head] + components
        else:
            path       = head
            components = [tail] + components


def isPulseAudioRunning():
    """ Return whether pulseaudio is running """
    ## Kind of hack, no better solution for now
    ## todo: improve this thing! (use psutil? is it an overkill..?)
    pipe      = os.popen('ps ax')
    isRunning = False

    for line in pipe:
        if line.find('pulseaudio') != -1:
            isRunning = True
            break

    pipe.close()

    return isRunning
