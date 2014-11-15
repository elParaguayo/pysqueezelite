import subprocess
import multiprocessing
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pylms.server import Server
from pylms.player import Player
from ssdp.ssdp import discover
#import ssdp

class PySqueezeliteError(Exception):
    pass

class PySqueezelite(object):
    """A small wrapper for launching squeezelite from within python scripts.

    Optional keyword arguments:
      path: path to squeezelite (defaults to /usr/bin/squeezelite)
      plname: name of player
      mac: mac address
      server: ipaddress of LMS (if not set, squeezelite will use discovery)
      args: other command line args to pass to squeezelite.
      lmsport: LMS server port (default 9000)
      telnetport: port for telnet communication to LMS (default 9090)

    Will raise SqueezeliteError if unable to locate squeezelite at given
    path.

    Will also raise error if no server and lms port are set and the scripts
    cannot locate the server using ssdp discovery.

    Methods:
      start: starts the squeezelite process
      kill: terminate the squeezelite process
      connect: connects to the LMS server to get track info
      get_player_info: retrieve additional player attributes
      play_pause: toggle the playback
      stop: stop playback
      next_track: play next track in playlist
      prev_track: play previous track in playlist

    Properties:
      track_title: track name
      track_artist: artist name
      track_album: album name
      track_duration: length of track
      track_time: time elapsed
    """

    def __init__(self, path="/usr/bin/squeezelite", 
                 plname="Squeezelite",
                 mac="12:34:56:78:90:AB",
                 server=None,
                 args=None,
                 lmsport=9000,
                 telnetport=9090):

        # Set relevant constants for this player
        self.path = path
        self.playername = plname
        self.mac = mac
        self.server = server
        self.args = args
        self.lmsport=lmsport
        self.telnetport=telnetport

        # Check if squeezelite can be found and alert user if not
        if not os.path.isfile(self.path):
            raise PySqueezeliteError("Can't find "
                                   "squeezelite at {}".format(self.path))

    def start(self):
        """Launches the squeezelite player."""

        if not self.server:
            self.server = self.__discover_server()

        self.connect(self.server, self.telnetport)

        # Default command. "-z" flag daemonises process.
        command = [self.path, "-z"]

        # Set player name
        if self.playername:
            command += ["-n", self.playername]

        # Set MAC address
        if self.mac:
            command += ["-m", self.mac]

        # Set server address
        if self.server:
            command += ["-s", self.server]

        # Add other args
        if self.args:
            command += [self.args]

        # Launch player
        subprocess.call(command)


    def kill(self):
        """Kills all instances of squeezelite found on the machine."""

        # Get the PIDs of all matching processes
        pids = subprocess.check_output(["pidof", self.path]).strip()

        # Loop through and kill them!
        for pid in pids.split(" "):
            subprocess.call(["kill", "-9", pid])

    def __discover_server(self):
        self.devices = [x for x in discover("ssdp:all") if x]
        
        self.matches = [x.ip for x in self.devices if x.port == self.lmsport]

        if len(self.matches) > 1:
            raise PySqueezeliteError("Multiple servers found on "
                                     "port {}. Need to set server ip address "
                                     "when calling "
                                     "PySqueezelite.".format(self.lmsport))
        elif len(self.matches) == 0:
            raise PySqueezeliteError("No servers found on "
                                     "port {}. Please check LMS is "
                                     "running and the correct "
                                     "port has been set.".format(self.lmsport))            
        else:
            return self.matches[0]

    def connect(self, hostname="localhost", port=9090):
        self.sc = Server(hostname=hostname, port=port)
        self.sc.connect()
        self.player = self.sc.get_player(self.mac)


    def get_player_info(self, info):

        if not self.player:
            self.connect

        if hasattr(self.player, info):
            return getattr(self.player, info)()
        else:
            return None

    def play_pause(self):
        self.player.toggle()

    def stop(self):
        self.player.stop()

    def next_track(self):
        self.player.next()

    def prev_track(self):
        self.player.prev()

    @property 
    def track_title(self):

        return self.get_player_info("get_track_title")

    @property 
    def track_artist(self):

        return self.get_player_info("get_track_artist")

    @property 
    def track_album(self):

        return self.get_player_info("get_track_album")

    @property 
    def track_duration(self):

        return self.get_player_info("get_track_duration")

    @property   
    def track_time(self):

        return self.get_player_info("get_time_elapsed")



