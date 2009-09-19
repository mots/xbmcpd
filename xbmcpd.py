#!/usr/bin/python
# -*- coding: utf-8 -*-

#This file is part of xbmcpd.

#xbmcpd is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 2 of the License, or
#(at your option) any later version.

#xbmcpd is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with xbmcpd.  If not, see <http://www.gnu.org/licenses/>.

from twisted.internet import reactor, protocol
from twisted.protocols import basic
import xbmcnp
from pprint import pprint


MUSICPATH = "smb://hda/Music/"
DEBUG = False

class MPD(basic.LineReceiver):
    def __init__(self):
        self.xbmc = xbmcnp.XBMCControl("xbmc", "1337")
        self.delimiter = "\n"
        self.command_list = False
        self.command_list_ok = True
        self.command_list_response = ""
        self.playlist_id = 1
        self.playlist_dict = {0 : []}
        self.supported_commands = ["status", "currentsong", "pause", "play", "next", "previous",
                                   "lsinfo", "add", "deleteid", "plchanges", "search", "setvol",
                                   "list", "count", "command_list_ok_begin", "command_list_end",
                                    "commands", "notcommands", "outputs", "tagtypes"]
        self.all_commands = ['add', 'addid', 'clear', 'clearerror', 'close', 'commands', 'consume',
                             'count', 'crossfade', 'currentsong', 'delete', 'deleteid', 'disableoutput',
                             'enableoutput', 'find', 'idle', 'kill', 'list', 'listall', 'listallinfo',
                             'listplaylist', 'listplaylistinfo', 'listplaylists', 'load', 'lsinfo', 'move',
                             'moveid', 'next', 'notcommands', 'outputs', 'password', 'pause', 'ping', 'play',
                             'playid', 'playlist', 'playlistadd', 'playlistclear', 'playlistdelete',
                             'playlistfind', 'playlistid', 'playlistinfo', 'playlistmove', 'playlistsearch',
                             'plchanges', 'plchangesposid', 'previous', 'random', 'rename', 'repeat', 'rm',
                             'save', 'search', 'seek', 'seekid', 'setvol', 'shuffle', 'single', 'stats', 'status',
                             'stop', 'swap', 'swapid', 'tagtypes', 'update', 'urlhandlers', 'volume']
      #  self.plchanges(send=False)

    
    def connectionMade(self):
        self.sendLine("OK MPD 0.16.0")
    
    def lineReceived(self, data):
        if DEBUG:
            print "REQUEST: %s" %data
        if data == "status":
           # print "sending status"
            self.status()
        elif data == "currentsong":
           # print "sending current song"
            self.currentsong()
        elif data == "next":
            self.next()
        elif data == "previous":
            self.next()
        elif data == "lsinfo":
           # print "sending directory info"
            self.lsinfo()
        elif data.startswith("add"):
            self.add(data[5:-1])
        elif data.startswith("deleteid"):
            self.delete_id(data[9:-1])
        elif data.startswith("delete"):
            self.delete_id(data[8:-1])
        elif data.startswith("lsinfo"):
            self.lsinfo(data[8:-1])
        elif data.startswith("plchanges"):
            print data
            self.plchanges(int(data[11:-1]))
        elif data.startswith("playlistinfo"):
            self.playlistinfo(int(data[14:-1]))
        elif data.startswith("playlistid"):
            self.playlistinfo(int(data[12:-1]))
        elif data.startswith("search \"album\""):
          #  print "searching album..."
            self.search_album(data[16:-1])
        elif data.startswith("list album") or data.startswith("find album"):
            self.search_album(data[12:-1])
        elif data.startswith("setvol"):
            self.set_vol(data[8:-1])
        elif data == "list \"artist\"" or data == "list artist":
            self.list_artists()
        elif data == "list \"genre\"" or data == "list genre":
            self.list_genres()
        elif data.startswith("list \"album\" \"artist\""):
            self.list_album_artist(data[23:-1])
        elif data == "list \"album\"" or data ==  "list album":
            self.list_albums()
        elif data.startswith("list \"date\" \"artist\""):
           # artist, album = [x.replace("\"", "").strip() for x in data[22:-2].split("\"album\"")]
     #       self.list_date_artist(artist, album)
            self.list_album_date(data[41:-1])
        elif data.startswith("list \"date\""):
            self.list_dates()
        elif data.startswith("count \"artist\""):
         #   print "sending artist stats"
            if data != "count \"artist\" \"Untagged\"" and data != "count \"artist\" \"\"":
                self.count_artist(data[16:-1])
            else:
                self._send_lists([["songs", 0],
                                  ["playtime", 0]])
        elif data == "command_list_begin":
            self.command_list_ok = False
            self.command_list = True
        elif data == "command_list_ok_begin":
            self.command_list_ok = True
            self.command_list = True
        elif data == "command_list_end":
            self.command_list = False
#            print self.command_list_response
            self._send(self.command_list_response)
            self.command_list_response = ""
        elif data == "commands":
            self.commands()
        elif data == "notcommands":
            self.notcommands()
        elif data == "outputs":
            self.outputs()
        elif data == "tagtypes":
            self.tagtypes()
        elif data == "stats":
            self.stats()
        elif data.startswith("pause") or data.startswith("play"):
            print "RECEIVED %s, pausing/playing" %data
            self.playpause()
        else:
            print "UNSUPPORTED REQUEST: %s" %data

    def playlistinfo(self, pos):
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
            counter+=1
            if counter == 10:
                seperated_playlist.append(templist)
                templist = []
                counter = 0
        self._send_lists(seperated_playlist[pos])

    def stats(self):
        artistcount, albumcount, songcount, totallength = self.xbmc.get_library_stats()
        self._send_lists([["artists", artistcount],
                          ["albums", albumcount],
                          ["songs", songcount],
                          ["uptime", 1],
                          ["playtime", 0],
                          ["db_playtime", totallength],
                          ["db_update", 1252868674]])

    def tagtypes(self):
        tags = ["Artist", "Album", "Title", "Track", "Name",
                "Genre", "Date"]
        templist = []
        for tag in tags:
            templist.append(["tagtype", tag])
        self._send_lists(templist)

    def commands(self):
        templist = []
        for i in self.supported_commands:
            templist.append(["command", i])
        self._send_lists(templist)

    def outputs(self):
        templist = [["outputid", 0],
                    ["outputname", "default detected output"],
                    ["outputenabled", 1]]
        self._send_lists(templist)
        

    def notcommands(self):
        unsupported = set(self.all_commands) ^ set(self.supported_commands)
        templist = []
        for i in unsupported:
            templist.append(["command", i])
        self._send_lists(templist)

    def set_vol(self, volume):
        self.xbmc.set_volume(volume)
        self._send()

    def delete_id(self, song_id):
        self.xbmc.remove_from_playlist(song_id)
        self.playlist_id += 1
        self._send()

    def add(self, path):
        self.xbmc.add_to_playlist(MUSICPATH+path)
        self.playlist_id += 1
        self._send()

    def next(self):
        self.xbmc.next()
        self._send()

    def previous(self):
        self.xbmc.prev()
        self._send()

    def playpause(self):
        self.xbmc.playpause()
        self._send()    

    def list_dates(self):
        dates = self.xbmc.list_dates()
        datelist = []
        for date in dates:
            datelist.append(["Date", date])
        self._send_lists(datelist)

    def list_album_date(self, album):
        date = self.xbmc.list_album_date(album)
        self._send_lists([["Date", date]])

    def list_albums(self):
        albums = self.xbmc.list_albums()
        albumlist = []
        for album in albums:
            albumlist.append(["Album", album])
        self._send_lists(albumlist)

    def list_album_artist(self, artist):
        albums = self.xbmc.list_artist_albums(artist)
        albumlist = []
        for album in albums:
            albumlist.append(["Album", album])
        self._send_lists(albumlist)
        
    def count_artist(self, artist):
        count = self.xbmc.count_artist(artist)
        self._send_lists([["songs", count[0]],
                          ["playtime", count[1]]])                      

    def list_artists(self):
        artistlist = self.xbmc.list_artists()
        templist = []
        for i in artistlist:
            templist.append(["Artist", i])
        self._send_lists(templist)

    def list_genres(self):
        genrelist = self.xbmc.list_genres()
        templist = []
        for i in genrelist:
            templist.append(["Artist", i])
        self._send_lists(templist)

    def search_album(self, album):
        if album == "":
            self._send()
        else:
            albuminfo = self.xbmc.search_album(album)
            playlistlist = []
            pos = 0
            for i in albuminfo:
                playlistlist.append(["file", i["Path"].replace(MUSICPATH, "")])
                playlistlist.append(["Time", i["Duration"]])
                playlistlist.append(["Artist", i["Artist"]])
                playlistlist.append(["Title", i["Title"]])
                playlistlist.append(["Album", i["Album"]])
                playlistlist.append(["Track", i["Track number"]])
                playlistlist.append(["Date", i["Release year"]])     
                playlistlist.append(["Genre", i["Genre"]])
                pos += 1
            self._send_lists(playlistlist)


    def status(self):
        status = self.xbmc.get_np()
        volume = self.xbmc.get_volume()
        if status != None:
            if status["PlayStatus"] == "Playing":
                state = "play"
            else:
                state = "pause"
            time = int(status["Time"].split(":")[0])*60 + int(status["Time"].split(":")[1])
            duration = int(status["Duration"].split(":")[0])*60 + int(status["Duration"].split(":")[1])
            self._send_lists([["volume", volume],
                        ["repeat", 0],
                        ["random", 0],
                        ["single", 0],
                        ["consume", 0],
                        ["playlist", self.playlist_id],
                        ["playlistlength", self.xbmc.get_playlist_length()],
                        ["xfade", 0],
                        ["state", state],
                        ["song", status["SongNo"]],
                        ["songid", status["SongNo"]],
                        ["time", "%s:%s" % (time, duration)],
                        ["bitrate", status["Bitrate"]],
                        ["audio", status["Samplerate"]+":24:2"]])
        else:
            self._send_lists([["volume", volume],
                        ["repeat", 0],
                        ["random", 0],
                        ["single", 0],
                        ["consume", 0],
                        ["playlist", 2],
                        ["playlistlength", self.xbmc.get_playlist_length()],
                        ["xfade", 0],
                        ["state", "stop"]])

    def plchanges(self, old_playlist = 0, send=True):
#      set(L1) ^ set(L2)
        playlist = self.xbmc.get_current_playlist()
        
        playlistlist = []

        pos = 0
        for i in playlist:
            playlistlist.append(["file", i["Path"].replace(MUSICPATH, "")])
            playlistlist.append(["Time", i["Duration"]])
            playlistlist.append(["Artist", i["Artist"]])
            playlistlist.append(["Title", i["Title"]])
            playlistlist.append(["Album", i["Album"]])
            playlistlist.append(["Track", i["Track number"]])
            playlistlist.append(["Date", i["Release year"]])     
            playlistlist.append(["Genre", i["Genre"]])
            playlistlist.append(["Pos", pos])
            playlistlist.append(["Id", pos])
            pos += 1
        self.playlist_dict[self.playlist_id] = playlistlist
        s = (tuple(x) for x in self.playlist_dict[old_playlist])
        diff = []
        for x in playlistlist:
            if tuple(x) not in s:
                diff.append(x)
        #plchanges = set(self.playlist_dict[old_playlist]) ^ set(playlistlist)
        if send:
            self._send_lists(diff)

    def currentsong(self):
        status = self.xbmc.get_np()
        if status != None:
            file = status["URL"].split("/")[-1:][0]
            time = int(status["Duration"].split(":")[0])*60 + int(status["Duration"].split(":")[1])
            self._send_lists([["file", file],
                            ["Time", time],
                            ["Artist", status["Artist"]],
                            ["Title", status["Title"]],
                            ["Album", status["Album"]],
                            ["Track", status["Track"]],
                            ["Genre", status["Genre"]],
                            ["Pos", status["SongNo"]],
                            ["Id", status["SongNo"]]])
        else:
           self._send("OK")
    
    def lsinfo(self, path="/"):
        newpath = MUSICPATH + path
        subdirs, musicfiles = self.xbmc.get_directory(newpath)
        infolist = []
        for i in subdirs:
            infolist.append(["directory", i.replace(MUSICPATH, "")[:-1]])
        for i in musicfiles:
            infolist.append(["file", i["Path"].replace(MUSICPATH, "")])
            infolist.append(["Time", i["Duration"]])
            infolist.append(["Artist", i["Artist"]])
            infolist.append(["Title", i["Title"]])
            infolist.append(["Album", i["Album"]])
            infolist.append(["Track", i["Track number"]])
            infolist.append(["Date", i["Release year"]])     
            infolist.append(["Genre", i["Genre"]])
        self._send_lists(infolist)
        

    def _send_lists(self, datalist):
        data = ""
        for i in datalist:
            data += "%s: %s\n" %(i[0], i[1])
        self._send(data)

    def _send(self, data=""):
        if self.command_list:
            self.command_list_response += data
            if self.command_list_ok:
                self.command_list_response += "list_OK\n"
        else:
            data += "OK"
            if DEBUG:
                print "RESPONSE: %s" %data
            self.sendLine(data)


def main():
    factory = protocol.ServerFactory()
    factory.protocol = MPD
    reactor.listenTCP(6601, factory)
    reactor.run()

if __name__ == '__main__':
    main()
