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

from twisted.internet import reactor, protocol
from twisted.protocols import basic
import xbmcnp
import settings

DEBUG = True

class MPD(basic.LineReceiver):
    """
    A MusicPlayerDaemon Server emulator.
    """
    
    def __init__(self):
        self.xbmc = xbmcnp.XBMCControl(settings.HOST, settings.PORT)
        self.delimiter = '\n'
        self.command_list = False
        self.command_list_ok = True
        self.command_list_response = ''
        self.playlist_id = 1
        self.playlist_dict = {0 : []}
        self.supported_commands = ['status', 'currentsong', 'pause', 'play',
                                   'next', 'previous', 'lsinfo', 'add',
                                   'deleteid', 'plchanges', 'search', 'setvol',
                                   'list', 'count', 'command_list_ok_begin',
                                   'command_list_end', 'commands',
                                   'notcommands', 'outputs', 'tagtypes',
                                   'playid']
        self.all_commands = ['add', 'addid', 'clear', 'clearerror', 'close',
                            'commands', 'consume','count', 'crossfade',
                            'currentsong', 'delete', 'deleteid',
                            'disableoutput','enableoutput', 'find', 'idle',
                            'kill', 'list', 'listall', 'listallinfo',
                            'listplaylist', 'listplaylistinfo',
                            'listplaylists', 'load', 'lsinfo', 'move','moveid',
                            'next', 'notcommands', 'outputs', 'password',
                            'pause', 'ping', 'play','playid', 'playlist',
                            'playlistadd', 'playlistclear', 'playlistdelete',
                            'playlistfind', 'playlistid', 'playlistinfo',
                            'playlistmove', 'playlistsearch','plchanges',
                            'plchangesposid', 'previous', 'random', 'rename',
                            'repeat', 'rm','save', 'search', 'seek', 'seekid',
                            'setvol', 'shuffle', 'single', 'stats', 'status',
                            'stop', 'swap', 'swapid', 'tagtypes', 'update',
                            'urlhandlers', 'volume']
        #self.plchanges(send=False)

    def _send_lists(self, datalist):
        """
        Pushes a list of information to the client.
        """
        data = ""
        for i in datalist:
            data += "%s: %s\n" % (i[0], i[1])
        self._send(data)

    def _send(self, data=""):
        """
        Pushes a simple string to the client.
        """
        if self.command_list:
            self.command_list_response += data
            if self.command_list_ok:
                self.command_list_response += "list_OK\n"
        else:
            data += "OK"
            if DEBUG:
                print "RESPONSE: %s" % data
            self.sendLine(data)

    
    def connectionMade(self):
        """
        Connection established.
        """
        self.sendLine('OK MPD 0.16.0')
    
    def lineReceived(self, data):
        """
        Receives data and takes the specified actions.

        Returns 'UNSUPPORTED REQUEST' if invalid data is received.
        """
        if DEBUG:
            print 'REQUEST: %s' % data
        
        if data == 'status':
           #print 'sending status'
            self.status()
        elif data == 'currentsong':
           #print 'sending current song'
            self.currentsong()
        elif data == 'next':
            self.next()
        elif data == 'previous':
            self.next()
        elif data == 'lsinfo':
           #print 'sending directory info'
            self.lsinfo()
        elif data.startswith('add'):
            self.add(data[5:-1])
        elif data.startswith('deleteid'):
            self.delete_id(data[9:-1])
        elif data.startswith('delete'):
            self.delete_id(data[8:-1])
        elif data.startswith('lsinfo'):
            self.lsinfo(data[8:-1])
        elif data.startswith('plchanges'):
            print data
            self.plchanges(int(data[11:-1]))
        elif data.startswith('playlistinfo'):
            self.playlistinfo(int(data[14:-1]))
        elif data.startswith('playlistid'):
            self.playlistinfo(int(data[12:-1]))
        elif data.startswith('search "album"'):
            #print "searching album..."
            self.search_album(data[16:-1])
        elif data.startswith('list album') or data.startswith('find album'):
            self.search_album(data[12:-1])
        elif data.startswith('setvol'):
            self.set_vol(data[8:-1])
        elif data == 'list "artist"' or data == "list artist":
            self.list_artists()
        elif data == 'list "genre"' or data == "list genre":
            self.list_genres()
        elif data.startswith('list "album" "artist"'):
            self.list_album_artist(data[23:-1])
        elif data == 'list "album"' or data == "list album":
            self.list_albums()
        elif data.startswith('list "date" "artist"'):
            #artist, album = [x.replace("\"", "").strip() \
            #                   for x in data[22:-2].split("\"album\"")]
            #self.list_date_artist(artist, album)
            self.list_album_date(data[41:-1])
        elif data.startswith('list "date"'):
            self.list_dates()
        elif data.startswith('count "artist"'):
            #print "sending artist stats"
            if data != 'count "artist" "Untagged"' and data != 'count "artist" ""':
                self.count_artist(data[16:-1])
            else:
                self._send_lists([['songs', 0],
                                  ['playtime', 0]])
        elif data == 'command_list_begin':
            self.command_list_ok = False
            self.command_list = True
        elif data == 'command_list_ok_begin':
            self.command_list_ok = True
            self.command_list = True
        elif data == 'command_list_end':
            self.command_list = False
            #print self.command_list_response
            self._send(self.command_list_response)
            self.command_list_response = ''
        elif data == 'commands':
            self.commands()
        elif data == 'notcommands':
            self.notcommands()
        elif data == 'outputs':
            self.outputs()
        elif data == 'tagtypes':
            self.tagtypes()
        elif data == 'stats':
            self.stats()
        elif data.startswith('playid'):
            self.playid(data[8:-1])
        elif data.startswith('pause') or data.startswith('play'):
            print 'RECEIVED %s, pausing/playing' % data
            self.playpause()
        else:
            print 'UNSUPPORTED REQUEST: %s' % data

    def playlistinfo(self, pos):
        """
        Gathers informations about the current playlist.

        Uses _send_lists() to push data to the client
        """
        try:
            playlist = self.playlist_dict[self.playlist_id]
        except:
            self.plchanges(send=False)
            playlist = self.playlist_dict[self.playlist_id]
        #ugly hack ahead!
        seperated_playlist = []
        counter = 0
        templist = []
        for i in playlist:
            templist.append(i)
            counter += 1
            if counter == 10:
                seperated_playlist.append(templist)
                templist = []
                counter = 0
        self._send_lists(seperated_playlist[pos])

    def stats(self):
        """
        Fetches library statistics from xbmc.

        Uses _send_lists() to push data to the client
        """
        artistcount, albumcount, songcount, totallength = self.xbmc.get_library_stats()
        self._send_lists([['artists', artistcount],
                          ['albums', albumcount],
                          ['songs', songcount],
                          ['uptime', 1],
                          ['playtime', 0],
                          ['db_playtime', totallength],
                          ['db_update', 1252868674]])

    def tagtypes(self):
        """
        Sends a list of supported tagtypes.

        Uses _send_lists() to push data to the client
        """
        tags = ['Artist', 'Album', 'Title', 'Track', 'Name', 'Genre', 'Date']
        templist = []
        for tag in tags:
            templist.append(['tagtype', tag])
        self._send_lists(templist)

    def commands(self):
        """
        Sends a list of supported commands.

        Uses _send_lists() to push data to the client
        """
        templist = []
        for i in self.supported_commands:
            templist.append(["command", i])
        self._send_lists(templist)

    def outputs(self):
        """
        Sends a list of configured outputs.

        Uses _send_lists() to push data to the client
        """
        templist = [['outputid', 0],
                    ['outputname', 'default detected output'],
                    ['outputenabled', 1]]
        self._send_lists(templist)
        

    def notcommands(self):
        """
        Sends a list of unsupported commands.
        
        Uses _send_lists() to push data to the client
        """
        unsupported = set(self.all_commands) ^ set(self.supported_commands)
        templist = []
        for i in unsupported:
            templist.append(['command', i])
        self._send_lists(templist)

    def set_vol(self, volume):
        """
        Sets the volume.
        """
        self.xbmc.set_volume(volume)
        self._send()

    def delete_id(self, song_id):
        """
        Deletes a song by it's specified id.
        """
        self.xbmc.remove_from_playlist(song_id)
        self.playlist_id += 1
        self._send()

    def add(self, path):
        """
        Add a specified path to the library.
        """
        self.xbmc.add_to_playlist(settings.MUSICPATH+path)
        self.playlist_id += 1
        self._send()

    def next(self):
        """
        Skip to the next song in the playlist.
        """
        self.xbmc.next()
        self._send()

    def previous(self):
        """
        Return to the previous song in the playlist.
        """
        self.xbmc.prev()
        self._send()

    def playid(self, song_id):
        """
        Get a song by it's id and play it.
        """
        self.xbmc.playid(song_id)
        self._send()    

    def playpause(self):
        """
        Toggle play or pause.
        """
        self.xbmc.playpause()
        self._send()    

    def list_dates(self):
        """
        Lists dates from all albums.

        Uses _send_lists() to push data to the client
        """
        dates = self.xbmc.list_dates()
        datelist = []
        for date in dates:
            datelist.append(['Date', date])
        self._send_lists(datelist)

    def list_album_date(self, album):
        """
        Get the specified album's date.

        Uses _send_lists() to push data to the client
        """
        date = self.xbmc.list_album_date(album)
        self._send_lists([['Date', date]])

    def list_albums(self):
        """
        Creates a list of all albums.

        Uses _send_lists() to push data to the client
        """
        albums = self.xbmc.list_albums()
        albumlist = []
        for album in albums:
            albumlist.append(['Album', album])
        self._send_lists(albumlist)

    def list_album_artist(self, artist):
        """
        Create a list of all albums from the specified artist.

        Uses _send_lists() to push data to the client
        """
        albums = self.xbmc.list_artist_albums(artist)
        albumlist = []
        for album in albums:
            albumlist.append(['Album', album])
        self._send_lists(albumlist)
        
    def count_artist(self, artist):
        """
        Returns the number of all songs in the library and the total playtime.

        Uses _send_lists() to push data to the client
        """
        count = self.xbmc.count_artist(artist)
        self._send_lists([['songs', count[0]],
                          ['playtime', count[1]]])                      

    def list_artists(self):
        """
        Fetches a list of all artists.

        Uses _send_lists() to push data to the client
        """
        artists = self.xbmc.list_artists()
        artistlist = []
        for artist in artists:
            artistlist.append(['Artist', artist])
        self._send_lists(artistlist)

    def list_genres(self):
        """
        Fetches a list of all genres.

        Uses _send_lists() to push data to the client
        """
        genres = self.xbmc.list_genres()
        genrelist = []
        for genre in genres:
            genrelist.append(['Genre', genre])
        self._send_lists(genrelist)

    def search_album(self, album):
        """
        Searches for a specified album.

        If albums have been found it uses _send_lists() to push data,
        otherwise _send() is beeing used.
        """
        if album == '':
            self._send()
        else:
            albuminfo = self.xbmc.search_album(album)
            playlistlist = []
            for info in albuminfo:
                playlistlist.append(['file', info['Path'].replace(settings.MUSICPATH, '')])
                playlistlist.append(['Time', info['Duration']])
                playlistlist.append(['Artist', info['Artist']])
                playlistlist.append(['Title', info['Title']])
                playlistlist.append(['Album', info['Album']])
                playlistlist.append(['Track', info['Track number']])
                playlistlist.append(['Date', info['Release year']])     
                playlistlist.append(['Genre', info['Genre']])
            self._send_lists(playlistlist)


    def status(self):
        """
        Returns the current status.

        If there is no song, the following information is pushed to the client:
            * Volume
            * Repeat on/off
            * Random on/off
            * Single on/off
            * Consume on/off
            * Playlist
            * Playlistlength
            * Fade on/off
            * State (play/pause/stop)
        If a song is played, this information is beeing added:
            * Song
            * Song ID
            * Time (time:duration)
            * Bitrate
            * Samplerate

        Uses _send_lists() to push data to the client
        """
        status = self.xbmc.get_np()
        volume = self.xbmc.get_volume()
        if status != None:
            if status['PlayStatus'] == 'Playing':
                state = 'play'
            else:
                state = 'pause'
            time = int(status['Time'].split(':')[0])*60 + \
                   int(status['Time'].split(':')[1])
            duration = int(status['Duration'].split(':')[0])*60 + \
                       int(status['Duration'].split(':')[1])
            self._send_lists([['volume', volume],
                        ['repeat', 0],
                        ['random', 0],
                        ['single', 0],
                        ['consume', 0],
                        ['playlist', self.playlist_id],
                        ['playlistlength', self.xbmc.get_playlist_length()],
                        ['xfade', 0],
                        ['state', state],
                        ['song', status['SongNo']],
                        ['songid', status['SongNo']],
                        ['time', '%s:%s' % (time, duration)],
                        ['bitrate', status['Bitrate']],
                        ['audio', status['Samplerate']+':24:2']])
        else:
            self._send_lists([['volume', volume],
                        ['repeat', 0],
                        ['random', 0],
                        ['single', 0],
                        ['consume', 0],
                        ['playlist', 2],
                        ['playlistlength', self.xbmc.get_playlist_length()],
                        ['xfade', 0],
                        ['state', 'stop']])

    def plchanges(self, old_playlist_id=0, send=True):
        """
        Returns a list of playlist changes.

        Uses _send_lists() to push data to the client
        """
        #set(L1) ^ set(L2)
        playlist = self.xbmc.get_current_playlist()
        playlistlist = []
        
        pos = 0
        if playlist != [None]:
            print playlist
            for song in playlist:
                playlistlist.append(['file', song['Path'].replace(settings.MUSICPATH, '')])
                playlistlist.append(['Time', song['Duration']])
                playlistlist.append(['Artist', song['Artist']])
                playlistlist.append(['Title', song['Title']])
                playlistlist.append(['Album', song['Album']])
                playlistlist.append(['Track', song['Track number']])
                playlistlist.append(['Date', song['Release year']])     
                playlistlist.append(['Genre', song['Genre']])
                playlistlist.append(['Pos', pos])
                playlistlist.append(['Id', pos])
                pos += 1
            
            self.playlist_dict[self.playlist_id] = playlistlist
            old_playlist = (tuple(info) for info in self.playlist_dict[old_playlist_id])
            diff = []
            for plinfo in playlistlist:
                if tuple(plinfo) not in old_playlist:
                    diff.append(plinfo)
            #plchanges = set(self.playlist_dict[old_playlist_id]) ^ set(playlistlist)
            if send:
                self._send_lists(diff)
        else:
            self._send()

    def currentsong(self):
        """
        Returns informations about the current song.

        If there is a song the following information is pushed via _send_lists():
            * File
            * Time
            * Artist
            * Title
            * Track
            * Genre
            * Position
            * ID
        
        Otherwise a simple 'OK' is returned via _send()
        """
        status = self.xbmc.get_np()
        if status != None:
            filepath = status['URL'].split('/')[-1:][0]
            time = int(status['Duration'].split(':')[0])*60 + \
                   int(status['Duration'].split(':')[1])
            self._send_lists([['file', filepath],
                            ['Time', time],
                            ['Artist', status['Artist']],
                            ['Title', status['Title']],
                            ['Album', status['Album']],
                            ['Track', status['Track']],
                            ['Genre', status['Genre']],
                            ['Pos', status['SongNo']],
                            ['Id', status['SongNo']]])
        else:
            self._send('OK')
    
    def lsinfo(self, path='/'):
        """
        Returns informations about the specified path.

        Uses _send_lists() to push data to the client
        """
        newpath = settings.MUSICPATH + path
        subdirs, musicfiles = self.xbmc.get_directory(newpath)
        infolist = []
        for subdir in subdirs:
            infolist.append(['directory',
                             subdir.replace(settings.MUSICPATH, '')[:-1]])
        for musicfile in musicfiles:
            infolist.append(['file', musicfile['Path'].replace(settings.MUSICPATH, '')])
            infolist.append(['Time', musicfile['Duration']])
            infolist.append(['Artist', musicfile['Artist']])
            infolist.append(['Title', musicfile['Title']])
            infolist.append(['Album', musicfile['Album']])
            infolist.append(['Track', musicfile['Track number']])
            infolist.append(['Date', musicfile['Release year']])     
            infolist.append(['Genre', musicfile['Genre']])
        self._send_lists(infolist)

if __name__ == '__main__':
    factory = protocol.ServerFactory()
    factory.protocol = MPD
    reactor.listenTCP(settings.MPD_PORT, factory)
    reactor.run()
