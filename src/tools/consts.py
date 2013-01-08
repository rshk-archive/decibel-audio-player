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

import gtk, os.path, random, time

from gettext import gettext as _

# --- Not a constant, but it fits well here
random.seed(int(time.time()))


# --- Miscellaneous
socketTimeout = 10


# --- Strings
appName      = 'Decibel Audio Player'
appVersion   = '1.09'
appNameShort = 'decibel-audio-player'


# --- URLs
urlMain = 'http://decibel.silent-blade.org'
urlHelp = 'http://decibel.silent-blade.org/index.php?n=Main.Help'


# --- Directories
dirBaseUsr = os.path.expanduser('~')
dirBaseCfg = os.path.join(dirBaseUsr, '.config')
dirBaseSrc = os.path.join(os.path.dirname(__file__), '..')

dirRes = os.path.join(dirBaseSrc, '..', 'res')
dirDoc = os.path.join(dirBaseSrc, '..', 'doc')
dirPix = os.path.join(dirBaseSrc, '..', 'pix')
dirCfg = os.path.join(dirBaseCfg, appNameShort)
dirLog = os.path.join(dirCfg, 'Logs')

dirLocale = os.path.join(dirBaseSrc, '..', 'locale')
if not os.path.isdir(dirLocale) :
    dirLocale = os.path.join(dirBaseSrc, '..', '..', 'locale')

# Make sure the config directory exists
if not os.path.exists(dirBaseCfg):
    os.mkdir(dirBaseCfg)

if not os.path.exists(dirCfg):
    os.mkdir(dirCfg)

# Make sure the log directory exists
if not os.path.exists(dirLog): os.mkdir(dirLog)


# --- Icons
fileImgIcon16  = os.path.join(dirPix, 'decibel-audio-player-16.png')
fileImgIcon24  = os.path.join(dirPix, 'decibel-audio-player-24.png')
fileImgIcon32  = os.path.join(dirPix, 'decibel-audio-player-32.png')
fileImgIcon48  = os.path.join(dirPix, 'decibel-audio-player-48.png')
fileImgIcon64  = os.path.join(dirPix, 'decibel-audio-player-64.png')
fileImgIcon128 = os.path.join(dirPix, 'decibel-audio-player-128.png')

fileImgStar16 = os.path.join(dirPix, 'star-16.png')

fileImgCatAll      = os.path.join(dirPix, 'category-all.png')
fileImgCatDesktop  = os.path.join(dirPix, 'category-desktop.png')
fileImgCatDecibel  = os.path.join(dirPix, 'category-decibel.png')
fileImgCatExplorer = os.path.join(dirPix, 'category-explorer.png')
fileImgCatInternet = os.path.join(dirPix, 'category-internet.png')


# --- Files
fileLog     = os.path.join(dirLog, 'log')
filePrefs   = os.path.join(dirCfg, 'prefs.txt')
fileLicense = os.path.join(dirDoc, 'LICENCE')


# --- DBus constants
dbusService   = 'org.mpris.dap'
dbusInterface = 'org.freedesktop.MediaPlayer'


# --- Tracks
UNKNOWN_DATE         = 0
UNKNOWN_GENRE        = _('Unknown Genre')
UNKNOWN_TITLE        = _('Unknown Title')
UNKNOWN_ALBUM        = _('Unknown Album')
UNKNOWN_ARTIST       = _('Unknown Artist')
UNKNOWN_LENGTH       = 0
UNKNOWN_BITRATE      = 0
UNKNOWN_ENC_MODE     = 0
UNKNOWN_MB_TRACKID   = 0
UNKNOWN_DISC_NUMBER  = 0
UNKNOWN_SAMPLE_RATE  = 0
UNKNOWN_TRACK_NUMBER = 0
UNKNOWN_ALBUM_ARTIST = _('Unknown Album Artist')


# --- Drag'n'Drop
(
    DND_URI,          # From another application (e.g., from Nautilus)
    DND_DAP_URI,      # Inside DAP when tags are not known (e.g., from the FileExplorer)
    DND_DAP_TRACKS    # Inside DAP when tags are already known (e.g., from the Library)
) = range(3)

DND_TARGETS = {
                DND_URI:        ('text/uri-list',   0,                   DND_URI),
                DND_DAP_URI:    ('dap/uri-list',    gtk.TARGET_SAME_APP, DND_DAP_URI),
                DND_DAP_TRACKS: ('dap/tracks-list', gtk.TARGET_SAME_APP, DND_DAP_TRACKS)
              }


# --- View modes
# --- Don't change the order!
(
    VIEW_MODE_FULL,
    VIEW_MODE_LEAN,
    VIEW_MODE_MINI,
    VIEW_MODE_PLAYLIST,
    VIEW_MODE_NETBOOK,
) = range(5)


# -- Categories a module can belong to
(
    MODCAT_NONE,
    MODCAT_DECIBEL,
    MODCAT_DESKTOP,
    MODCAT_INTERNET,
    MODCAT_EXPLORER,
) = range(5)


# --- Message that can be sent/received by modules
# --- A message is always associated with a (potentially empty) dictionnary containing its parameters
(
    # --== COMMANDS ==--

    # GStreamer player
    MSG_CMD_PLAY,                 # Play a resource                            Parameters: 'uri', 'forced'
    MSG_CMD_STOP,                 # Stop playing                               Parameters:
    MSG_CMD_SEEK,                 # Jump to a position                         Parameters: 'seconds'
    MSG_CMD_STEP,                 # Step back or forth                         Parameters: 'seconds'
    MSG_CMD_SET_VOLUME,           # Change the volume                          Parameters: 'value'
    MSG_CMD_BUFFER,               # Buffer a file                              Parameters: 'filename'
    MSG_CMD_TOGGLE_PAUSE,         # Toggle play/pause                          Parameters:
    MSG_CMD_ENABLE_EQZ,           # Enable the equalizer                       Parameters:
    MSG_CMD_SET_EQZ_LVLS,         # Set the levels of the 10-bands equalizer   Parameters: 'lvls'
    MSG_CMD_ENABLE_RG,            # Enable ReplayGain                          Parameters:
    MSG_CMD_SET_CD_SPEED,         # Change drive speed when reading a CD       Parameters: 'speed'

    # Tracklist
    MSG_CMD_NEXT,                 # Play the next track                            Parameters:
    MSG_CMD_PREVIOUS,             # Play the previous track                        Parameters:
    MSG_CMD_TRACKLIST_SET,        # Replace tracklist                              Parameters: 'tracks', 'playNow'
    MSG_CMD_TRACKLIST_ADD,        # Extend tracklist                               Parameters: 'tracks', 'playNow'
    MSG_CMD_TRACKLIST_DEL,        # Remove a track                                 Parameters: 'idx'
    MSG_CMD_TRACKLIST_CLR,        # Clear tracklist                                Parameters:
    MSG_CMD_TRACKLIST_PLAY,       # Play the given track                           Parameters: 'idx', 'seconds'
    MSG_CMD_TRACKLIST_REPEAT,     # Set/Unset the repeat function                  Parameters: 'repeat'
    MSG_CMD_TRACKLIST_SHUFFLE,    # Shuffle the tracklist                          Parameters:
    MSG_CMD_TRACKLIST_PLAY_PAUSE, # Play the given track and pause immediately     Parameters: 'idx', 'seconds'

    # Explorers
    MSG_CMD_EXPLORER_ADD,         # Add a new explorer    Parameters: 'modName', 'expName', 'icon', 'widget'
    MSG_CMD_EXPLORER_REMOVE,      # Remove an explorer    Parameters: 'modName', 'expName'
    MSG_CMD_EXPLORER_RENAME,      # Rename an explorer    Parameters: 'modName', 'expName', 'newExpName'

    # Covers
    MSG_CMD_SET_COVER,            # Cover file for the given track     Parameters: 'track', 'pathThumbnail', 'pathFullSize'

    # Misc
    MSG_CMD_THREAD_EXECUTE,       # An *internal* command for threaded modules     Parameters: N/A


    # --== EVENTS ==--

    # Current track
    MSG_EVT_PAUSED,               # Paused                                             Parameters:
    MSG_EVT_STOPPED,              # Stopped                                            Parameters:
    MSG_EVT_UNPAUSED,             # Unpaused                                           Parameters:
    MSG_EVT_NEW_TRACK,            # The current track has changed                      Parameters: 'track'
    MSG_EVT_NEED_BUFFER,          # The next track should be buffered                  Parameters:
    MSG_EVT_TRACK_POSITION,       # New position in the current track                  Parameters: 'seconds'
    MSG_EVT_TRACK_ENDED_OK,       # The current track has ended                        Parameters:
    MSG_EVT_TRACK_ENDED_ERROR,    # The current track has ended because of an error    Parameters:

    # GStreamer player
    MSG_EVT_VOLUME_CHANGED,       # The volume has changed   Parameters: 'value'

    # Tracklist
    MSG_EVT_TRACK_MOVED,          # The position of the current track has changed    Parameters: 'hasPrevious', 'hasNext'
    MSG_EVT_NEW_TRACKLIST,        # A new tracklist has been set                     Parameters: 'tracks', 'playtime'
    MSG_EVT_REPEAT_CHANGED,       # The repeat function has been enabled/disabled    Parameters: 'repeat'
    MSG_EVT_TRACKLIST_NEW_SEL,    # The tracklist has a new set of selected tracks   Parameters: 'tracks'

    # Application
    MSG_EVT_APP_QUIT,             # The application is quitting         Parameters:
    MSG_EVT_APP_STARTED,          # The application has just started    Parameters:

    # Modules
    MSG_EVT_MOD_LOADED,           # The module has been loaded by request of the user      Parameters:
    MSG_EVT_MOD_UNLOADED,         # The module has been unloaded by request of the user    Parameters:

    # Explorer manager
    MSG_EVT_EXPLORER_CHANGED,     # A new explorer has been selected    Parameters: 'modName', 'expName'

    # End value
    MSG_END_VALUE
) = range(45)
