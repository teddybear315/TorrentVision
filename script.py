import subprocess
import time
from enum import Enum
import keyboard
import threading
import sys, os, time
import json
import random

class VideoFile:
    path:str
    name:str
    tag:str
    duration:int
    def __init__(self, path:str, name:str, tag:str):
        self.path = path
        self.name = name
        self.tag = tag
        self.get_duration()
    def get_duration(self):
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                "format=duration", "-of",
                                "default=noprint_wrappers=1:nokey=1", self.path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        self.duration:int = float(result.stdout).__round__()
        

class Movie:
    path:str
    name:str
    tag:str
    duration:int
    HD:bool
    def __init__(self, path:str, name:str, tag:str, HD:bool):
        self.HD = HD
        self.path = path
        self.name = name
        self.tag = tag
        self.get_duration()
    def __init__(self, json:dict, tag:str):
        self.HD = json["HD"]
        self.path = json["path"]
        self.name = json["name"]
        self.tag = tag
        self.get_duration()
    def get_duration(self):
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                "format=duration", "-of",
                                "default=noprint_wrappers=1:nokey=1", self.path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        self.duration:int = float(result.stdout).__round__()


class Season:
    episodes:list[VideoFile]
    HD:bool
    def __init__(self, episodes, HD):
        self.episodes = episodes
        self.HD = HD


class Show:
    seasons:list[Season]
    name:str
    def __init__(self, name, seasons):
        self.name = name
        self.seasons = seasons


class ChannelMode(Enum):
    MOVIES=1
    SHOWS=2


class ShuffleMode(Enum):
    OFF=0
    SHUFFLE_FILES=1
    SHUFFLE_GROUPS=2


class Channel:
    ffmpeg_proc:subprocess.Popen | None = None
    mode:ChannelMode = ChannelMode.SHOWS
    quit:bool = False
    kill:bool = False # kill file thread
    live:bool = False
    debug:bool = False
    shuffle_mode:ShuffleMode = ShuffleMode.OFF

    startGroup:int #season
    startFile:int
    startMins:int
    startSecs:int
    id:int
    started:int = 0
    elapsed:int = 0
    remain:int = 0
    files_thread:threading.Thread
    loop = 0
    # stream_thread:threading.Thread

    playlist: list[VideoFile] | list[Movie] = []
    shows:list[Show] = []
    all_seasons:list[Season] = []
    all_episodes:list[VideoFile] | list[Movie] = []
    current_playlist_i = 0
    current_start_time:int
    dir=""
    playlist_path = "./playlist.txt"
    url = "rtmp://localhost:1935/"
    def __init__(self, config_path, debug):
            
        # Read the JSON file
        file =  open(config_path, 'r')
        json_data = file.read()
        chan_data = json.loads(json_data)
        file.flush()
        file.close()

        self.debug = debug

        # Load data
        self.id = chan_data["channel"]
        self.dir = f"./channels/{self.id}"
        self.playlist_path = f"{self.dir}/playlist.txt"
        self.playlist = []
        self.mode = ChannelMode.MOVIES if chan_data["type"] == "movies" else ChannelMode.SHOWS
        self.shuffle_mode = ShuffleMode.OFF if chan_data["shuffle"] in ["off",False] else ShuffleMode.SHUFFLE_FILES if chan_data["shuffle"] in ["files","all",True] else ShuffleMode.SHUFFLE_GROUPS

        # Load playlist data
        if self.mode == ChannelMode.MOVIES:
            m = 0
            for movie_data in chan_data["movies"]:
                m+=1
                if self.debug: print(movie_data["path"])
                self.all_episodes.append(Movie(movie_data,f"M{m}"))
        elif self.mode == ChannelMode.SHOWS:
            for show_data in chan_data["shows"]:
                title = show_data["name"]
                seasons = []
                s = 0
                for season_data in show_data["seasons"]:
                    s+=1
                    e=0
                    print(f"Loading {title} Season {s} from {season_data['path']}")
                    episodes = []
                    for filename in os.listdir(season_data['path']):
                        e+=1
                        if self.debug: print(filename)
                        fp = os.path.join(season_data['path'], filename)
                        if len(os.listdir(season_data['path'])) == 1:
                            episode = VideoFile(fp,filename[:-4],f"M{e}")
                        else:
                            try:
                                tag,ep_title = filename[len(title):].split(" ", 1)
                            except: ep_title = filename
                            episode = VideoFile(fp,ep_title[:-4], tag)
                        if self.shuffle_mode == ShuffleMode.SHUFFLE_FILES: self.all_episodes.append(episode) 
                        else: episodes.append(episode)
                    if self.shuffle_mode == ShuffleMode.SHUFFLE_GROUPS: self.all_seasons.append(Season(episodes, season_data["HD"]))
                    else: seasons.append(Season(episodes, season_data["HD"]))
                if self.shuffle_mode == ShuffleMode.OFF: self.shows.append(Show(title, seasons))
            if self.shuffle_mode == ShuffleMode.OFF:
                for show in self.shows:
                    for season in show.seasons:
                        for episode in season.episodes:
                            self.all_episodes.append(episode)

        # Generate Playlist
        self.playlist = []
        if self.shuffle_mode != ShuffleMode.OFF:            
            if self.shuffle_mode == ShuffleMode.SHUFFLE_FILES:
                self.playlist = self.all_episodes
                random.shuffle(self.playlist)
            elif self.shuffle_mode == ShuffleMode.SHUFFLE_GROUPS:
                shuff_seasons = self.all_seasons
                random.shuffle(shuff_seasons)
                for season in shuff_seasons:
                    for episode in season.episodes:
                        self.playlist.append(episode)
        else: self.playlist = self.all_episodes
        
        # File Setup
        try:
            os.makedirs(self.dir)
            with open(f"{self.dir}/ep.txt", "w+") as f_ep: f_ep.flush()
            with open(f"{self.dir}/title.txt", "w+") as f_title: f_title.flush()
            with open(f"{self.dir}/duration.txt", "w+") as f_duration: f_duration.flush()
            with open(f"{self.dir}/elapsed.txt", "w+") as f_elapsed: f_elapsed.flush()
            with open(f"{self.dir}/remain.txt", "w+") as f_remain: f_remain.flush()
            with open(self.playlist_path, "w+") as f_play: f_play.flush()
        except: print("File setup not required")
        # Fill Playlist File
        self.fill_playlist()

        self.url = 'rtmp://localhost:1935/Channel/'+str(self.id)
    def kill_file_thread(self, reset:bool=False):
        self.kill = True
        self.files_thread.join()
        try:
            os.remove(f"{self.dir}/ep.txt")
            os.remove(f"{self.dir}/title.txt")
            os.remove(f"{self.dir}/duration.txt")
            os.remove(f"{self.dir}/elapsed.txt")
            os.remove(f"{self.dir}/remain.txt")
            os.remove(self.playlist_path)
            os.remove(self.dir)
        except: print("Error deleting files")
        if reset: self.kill = False
    def start_stream(self):
        
        if self.shuffle_mode != ShuffleMode.OFF:
            # Make playlist file
            self.fill_playlist()

        if self.shuffle_mode != ShuffleMode.OFF:
            command = [ 'ffmpeg', '-hide_banner', '-re', '-f', 'concat', '-safe', '0', '-i', self.playlist_path,                        '-c:v', 'h264_nvenc', '-b:v', '4096k', '-bufsize', '8M', '-preset', 'fast', '-pix_fmt', 'yuv420p', '-g', '60', '-c:a', 'aac', '-b:a', '160k', '-f', 'flv', self.url, '-rtmp_live', '1']
        else:
            command = [ 'ffmpeg', '-hide_banner', '-re', '-f', 'concat', '-safe', '0', '-i', self.playlist_path, '-vf', 'loop=1:1:0',   '-c:v', 'h264_nvenc', '-b:v', '4096k', '-bufsize', '8M', '-preset', 'fast', '-pix_fmt', 'yuv420p', '-g', '60', '-c:a', 'aac', '-b:a', '160k', '-f', 'flv', self.url, '-rtmp_live', '1']
        
        if self.debug: self.ffmpeg_proc = subprocess.run(command, ) | subprocess.Popen(command)
        else: self.ffmpeg_proc = subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
        
        keyboard.add_hotkey("ctrl+q", self.m_quit, suppress=True, trigger_on_release=True)
        print("Press CTRL+Q to exit")
        self.live = True
        self.started = int(time.time())
        self.current_start_time = self.started

        self.files_thread = threading.Thread(None, self.update_files, name=f"C{self.id}: File Updater")
        self.files_thread.start()
        self.ffmpeg_proc.wait()
        if self.shuffle_mode != ShuffleMode.OFF: self.m_quit()
        else:
            keyboard.remove_hotkey("ctrl+q")
            try: self.ffmpeg_proc.terminate()
            except: print("No FFMPEG Process")
            self.live = False
            self.quit = True
            self.kill_file_thread()
            
    def m_quit(self):
        keyboard.remove_hotkey("ctrl+q")
        try: self.ffmpeg_proc.terminate()
        except: print("No FFMPEG Process")
        self.live = False
        self.quit = True
        self.kill_file_thread()
        if self.shuffle_mode != ShuffleMode.OFF: self.generate_playlist()
    def fill_playlist(self):
        self.clear_playlist()
        with open(self.playlist_path, "a") as playlist_file:
            for episode in self.playlist:
                    episode.path.replace('\'', '\\\'')
                    playlist_file.write(f"file \'{episode.path}\'\n")
    def clear_playlist(self):
        try:
            os.remove(self.playlist_path)
            with open(self.playlist_path, "w+") as f_ep: f_ep.flush()
        except: 
            print("ERROR! Playlist not emptied!")
    def generate_playlist(self, clear:bool=False):
        if clear:self.clear_playlist()
        if self.shuffle_mode == ShuffleMode.SHUFFLE_FILES:
            self.playlist = self.all_episodes
            random.shuffle(self.playlist)
        elif self.shuffle_mode == ShuffleMode.SHUFFLE_GROUPS:
            shuff_seasons = self.all_seasons
            random.shuffle(shuff_seasons)
            for season in shuff_seasons:
                for episode in season.episodes:
                    self.playlist.append(episode)
    def update_files(self):
        while self.started == 0: pass
        with open(f"{self.dir}/ep.txt", "w+") as f_ep:
            f_ep.write(self.playlist[self.get_current_playlist_index()].tag) 
        with open(f"./channels/{self.id}/title.txt", "w+") as f_title:
            f_title.write(self.playlist[self.get_current_playlist_index()].name) 
        with open(f"./channels/{self.id}/duration.txt", "w+") as f_duration:
            f_duration.write(str(self.playlist[self.get_current_playlist_index()].duration)) 
        while not self.kill:
            if self.get_current_playlist_index() != self.current_playlist_i:
                print(f"Finished {self.playlist[self.current_playlist_i].name}\n")
                self.current_playlist_i = self.get_current_playlist_index()
                self.current_start_time = int(time.time())
            self.elapsed = int(time.time())-self.current_start_time
            self.remain = self.playlist[self.get_current_playlist_index()].duration-self.elapsed
            with open(f"./channels/{self.id}/elapsed.txt", "w+") as f_elapsed:
                f_elapsed.write(str(self.elapsed))
            with open(f"./channels/{self.id}/remain.txt", "w+") as f_remain:
                f_remain.write(str(self.remain))
            eS = round(self.elapsed)%60
            eM = round((round(self.elapsed)-eS)/60)
            dS = round(self.playlist[self.get_current_playlist_index()].duration)%60
            dM = round((round(self.playlist[self.get_current_playlist_index()].duration)-round(self.playlist[self.get_current_playlist_index()].duration)%60)/60)
            dH = round((dM-dM%60)/60)
            if not self.debug:
                if dH:
                    eH = round((eM-eM%60)/60)
                    print(f"Streaming {self.playlist[self.get_current_playlist_index()].name} | {str(eH).zfill(2)}h{str(eM%60).zfill(2)}m{str(eS).zfill(2)}s/{str(dH).zfill(2)}h{str(dM%60).zfill(2)}m{str(dS).zfill(2)}s", end='\r')
                else:
                    print(f"Streaming {self.playlist[self.get_current_playlist_index()].name} | {str(eM).zfill(2)}m{str(eS).zfill(2)}s/{str(dM).zfill(2)}m{str(dS).zfill(2)}s", end='\r')
            time.sleep(0.5)
    
    def get_current_playlist_index(self):
        current_time = time.time()
        passed_time = self.playlist[0].duration
        for vid in range(len(self.playlist)):
            if current_time-self.started > passed_time: 
                passed_time+=self.playlist[vid].duration
                continue
            elif self.started == 0: return 0
            else: return vid

def main():
    json_path = ""
    debug = False
    
    if len(sys.argv) == 1:
        json_path = input("Please enter a channel file:")
    else:
        args = sys.argv[1:]
        for arg in args:
            if arg == "-d":
                debug = True
                print(f"[debug] {arg}")
                continue
            param = arg.split('=')[0][1:].lower()
            val = arg.split('=')[1]
            if param == 'c': json_path = val
    channel = Channel(json_path, debug)
    if channel.shuffle_mode != ShuffleMode.OFF:
        while not channel.quit: channel.start_stream()
    else: channel.start_stream()

if __name__ == "__main__": main()