#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of xbmcpd.

# xbmcpd is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.

# xbmcpd is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with xbmcpd.  If not, see <http://www.gnu.org/licenses/>.

import urllib2
import urllib
from xbmcclient import XBMCClient

class XBMCControl(object):
    """
    Implements a simple way to control basic XBMC library functions.
    """

    
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.artistdict = {}
        self.albumdict = {}
        self.genredict = {}
        self.eventclient = XBMCClient('xbmcPD')
        self.eventclient.connect(ip, 9777)
    
    def send(self, command):
        """
        Send a command to xbmc.

        Returns a string
        """
        #print "http://%s:%s/xbmcCmds/xbmcHttp?command=%s" % (self.ip, self.port, urllib.quote(command))
        #print "http://%s:%s/xbmcCmds/xbmcHttp?command=%s" % (self.ip, self.port, urllib.quote(command.encode("utf-8")))
        xbmcconn = urllib2.urlopen('http://%s:%s/xbmcCmds/xbmcHttp?command=%s' \
                                    % (self.ip, self.port, urllib.quote(command)))
        rawtext = xbmcconn.read()
        return rawtext

    def get_np(self):
        """
        Get currently playing file.

        Returns a dictionary or None.
        """
        rawtext = self.send('GetCurrentlyPlaying()')
        infos = (point.rstrip() for point in (rawtext.split('<li>')[1:-1]))
        infodict = {}
        for info in infos:
            infokey, infovalue = info.split(':', 1)
            infodict[infokey] = infovalue
        if len(infodict) != 0:
            return infodict
        return None
        
    def get_volume(self):
        """
        Get the currently set volume.

        Returns an integer.
        """
        volume = self.send('GetVolume')
        volume = int(volume.replace('<html>\n','').replace('</html>\n', '') \
                                                  .replace('<li>', ''))
        return volume

    def get_directory(self, path):
        """
        Get directory informations.

        Returns a list of subdirectories and a list of musicfiles
        """
        subdirs = self.send('GetDirectory(%s;/)' % path)
        subdirs = subdirs.replace('<html>\n','').replace('</html>\n', '')
        subdirs = [dirtydir.strip() for dirtydir in [subdir.split(';')[0] \
                                    for subdir in subdirs.split('<li>')[1:]]]
        musicfiles = self.send('GetDirectory(%s;[music])' % path)
        musicfiles = musicfiles.replace('<html>\n','').replace('</html>\n', '')
        musicfiles = [self.get_tags_from_filename(tagfile) for tagfile in \
                      [dirtyfile.strip() for dirtyfile in [musicfile.split(';')[0] \
                      for musicfile in musicfiles.split('<li>')[1:]]]]
        return subdirs, musicfiles

    def get_tags_from_filename(self, filename):
        """
        Get tags by filename.

        Returns a dictionary
        """
        rawtext = self.send('GetTagFromFilename(%s)' % filename)
        if rawtext != None:
            infos =  (text.rstrip() for text in (rawtext.split('<li>')[1:-1]))
            infodict = {}
            for info in infos:
                infokey, infovalue = info.split(':', 1)
                infodict[infokey] = infovalue
            if len(infodict) != 0:
                infodict['Path'] = filename
                return infodict

    def get_library_stats(self):
        """
        Get library statistics.

        Returns artistcount, albumcount, songcount and total playtime
        """
        artistcount = int(self.send('querymusicdatabase(select count(*) from artist)')[22:-25])
        albumcount = int(self.send('querymusicdatabase(select count(*) from album)')[22:-25])
        songcount = int(self.send('querymusicdatabase(select count(*) from song)')[22:-25])
        totallength = int(self.send('querymusicdatabase(select sum(iDuration) from song)')[22:-25])
        return artistcount, albumcount, songcount, totallength

    def get_current_playlist(self):
        """
        Get the current playlist contents.

        Returns a list filled by each file's tags
        """
        rawtext = self.send("GetPlaylistContents(-1)")
        playlist = [text.rstrip() for text in rawtext.replace("</html>", "") \
                                                     .split("<li>")[1:]]
        return [self.get_tags_from_filename(musicfile) for musicfile in \
                [text.rstrip() for text in rawtext.replace("</html>", "") \
                                                  .split("<li>")[1:]]]

    def next(self):
        """
        Skip to the next song.
        """
        self.eventclient.send_action("XBMC.PlayerControl(Next)")
        #self.send("PlayListNext")

    def prev(self):
        """
        Return to the previous song.
        """
        self.eventclient.send_action("XBMC.PlayerControl(Previous)")

    def set_volume(self, volume):
        """
        Set the volume.
        """
        self.eventclient.send_action("XBMC.SetVolume(%s)" % volume)

    def get_playlist_length(self):
        """
        Get the playlist length.
        """
        return int(self.send("GetPlaylistLength")[11:-8])

    def search_album(self, albumname):
        """
        Search for a specified albumname.
        """
        self.list_albums()
        album_id = self.albumdict[albumname]
        song_ids = self.send("querymusicdatabase(select idPath,strFileName  from song where idAlbum = %s)" % album_id)
        song_ids = song_ids.replace('<html>\n','').replace('</html>\n', '') \
                                                  .replace("</record>", "") \
                                                  .replace("</field>", "")
        records = song_ids.split("<record>")
        paths = []
        for record in records: 
            fields = record.split("<field>")[1:]
            if len(fields) == 2:
                #INEFFICIENT!
                paths.append(self.send("querymusicdatabase(select strPath from path where idPath = %s)" % fields[0])[22:-25]+fields[1])
        return [self.get_tags_from_filename(path) for path in paths]

    def list_artists(self):
        """
        Returns a list of all artists.
        """
        if len(self.artistdict) < 1:
            artists = self.send("querymusicdatabase(select strArtist, idArtist from artist order by strArtist)")
            artists = artists.replace('<html>\n','').replace('</html>\n', '') \
                                                    .replace("</record>", "") \
                                                    .replace("</field>", "")
            records = artists.split("<record>")
            for record in records:
                fields = record.split("<field>")[1:]
                if len(fields) == 2:
                    self.artistdict[fields[0]] = fields[1]
        return self.artistdict.keys()

    def list_genres(self):
        """
        Returns a list of all genres.
        """
        if len(self.genredict) < 1:
            genres = self.send("querymusicdatabase(select strGenre, idGenre from genre order by strGenre)")
            genres = genres.replace('<html>\n','').replace('</html>\n', '') \
                                                  .replace("</record>", "") \
                                                  .replace("</field>", "")
            records = genres.split("<record>")
            for record in records:
                fields = record.split("<field>")[1:]
                if len(fields) == 2:
                    self.genredict[fields[0]] = fields[1]
        return self.genredict.keys()

    def count_artist(self, artist):
        """
        Get number of songs by the specified artist and the total duration.

        Returns number of songs, total duration
        """
        self.list_artists()
        artist_id = self.artistdict[artist]
        song_count = self.send("querymusicdatabase(select count(*) from song where idArtist =  %s)" % artist_id)[22:-25]
        duration = self.send("querymusicdatabase(select sum(iDuration) from song where idArtist = %s)" % artist_id)[22:-25]
        if song_count == "0":
            duration = 0
        return song_count, duration

    def playid(self, song_id):
        """
        Play song specified by it's id.
        """
        self.send("SetPlaylistSong(%s)" %song_id)

    def playpause(self):
        """
        Toggle play or pause.
        """
        self.eventclient.send_action("XBMC.PlayerControl(Play)")
        #self.send("pause")

    def remove_from_playlist(self, pos):
        """
        Remove a song (specified by it's position inside the playlist) from
        the playlist.
        """
        self.send("RemoveFromPlaylist(%s)" % pos)
    
    def list_artist_albums(self, artist):
        """
        Get all albums by a specified artist.

        Returns a list.
        """
        self.list_artists()
        albums = self.send("querymusicdatabase(select strAlbum from album where idArtist = %s)" % self.artistdict[artist])
        albums = albums.replace("<record><field>", "").replace("<html>","") \
                                                      .replace("</html>", "") \
                                                      .replace("\n", "")
        return albums.split("</field></record>")[:-1]

    def list_albums(self):
        """
        Get all albums inside the library.

        Returns a list
        """
        if len(self.albumdict) <1:
            albums = self.send("querymusicdatabase(select strAlbum, idAlbum from album order by strAlbum)")
            albums = albums.replace('<html>\n','').replace('</html>\n', '') \
                                                  .replace("</record>", "") \
                                                  .replace("</field>", "")
            records = albums.split("<record>")
            for record in records:
                fields = record.split("<field>")[1:]
                if len(fields) == 2:
                    self.albumdict[fields[0]] = fields[1]
        return self.albumdict.keys()

    def list_album_date(self, album):
        """
        Get the date of the specified album.

        Returns a string

        TODO: Return a nice datetime object?
        """
        self.list_albums()
        date = self.send("querymusicdatabase(select iYear from album where idAlbum =  %s)" % self.albumdict[album])[22:-25]
        return date

    def play_file(self, path):
        """
        Play the given path
        """
        self.send("PlayFile(%s)" % path)

    def add_to_playlist(self, path):
        """
        Add the given path to the playlist.
        """
        self.send("AddToPlayList(%s)" % path)

    def list_dates(self):
        """
        Get a list of dates for which albums are available.

        Returns a list.
        """
        dates = self.send("querymusicdatabase(select distinct iYear from album)")
        dates = dates.replace("<record><field>", "").replace("<html>","") \
                                                    .replace("</html>", "") \
                                                    .replace("\n", "")
        return dates.split("</field></record>")[:-1]
