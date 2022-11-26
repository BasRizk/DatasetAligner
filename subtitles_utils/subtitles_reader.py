import os
import re
from natsort import natsorted
from .subtitles_cut import SubtitleSnippet
                
class SubtitlesReader:
    def __init__(self, filepath, episode_info):
        self.filepath = filepath
        self.episode_info = episode_info
        self.file = open(filepath, encoding='utf_8')
        self.curr_snippet = None
        self.gen = self._generator()
        
    def __iter__(self):
        return self
    
    def __next__(self):
        return next(self.gen)
    
    # subs_file_lines_generator
    def _generator(self) -> SubtitleSnippet:
        while True:
            lines = self.read_until(end='')
            if lines is None:
                break
            snip_id = int(re.sub(r'[^0-9]', '', lines[0]))
            snip_ts = lines[1]
            snip_utts = lines[2:]
            self.curr_snippet =\
                SubtitleSnippet(self.episode_info, snip_id, snip_ts, snip_utts)
            yield self.curr_snippet
        self.destroy()
        
    def reset(self):
        try:
            self.destroy()
        except:
            print('File was never opened')
        finally:
            self.file = open(self.filepath)
        
    def destroy(self):
        self.file.close()
    
    def read_until(self, end=''):
        lines = []
        while True:
            line = self.file.readline().strip()
            if line == end:
                break
            lines.append(line)
        if len(lines) > 0:
            return lines
        return None
    
    def get_curr_snippet_num(self):
        return self.curr_snippet.get_id()
    
    def get_curr_timestamp(self):
        return f'{self.curr_snippet.get_id()}'
    
    def get_curr_utterances(self):
        return self.curr_snippet.utts
    
    def get_filename(self):
        return os.path.basename(self.filepath)
    
        
class SubtitleFilenamePatternUndefined(Exception):
    """Raised when the subtitle filename pattern not defined in regex"""
    pass
    
class SubsFileDirectory:
    
    def __init__(
            self,
            parent_dir='eng_friends_subs',
            episode_name_regex=[
                r'.+s(\d+)e(\d+).+',
                r'.+?(\d+)x(\d+).+'
            ]
        ):
        self.parent_dir = parent_dir
        self.episode_name_regex = episode_name_regex
        self.init_filepathes()
        self.dictionarize_episodes()
        self.curr_subs_reader = None
        self.curr_file_idx = None
        self.gen = self._generator()
    
    def init_filepathes(self):
        self.subs_filepathes = []
        subs_dir = os.walk(self.parent_dir)
        # ignore folders pathes
        ignored = next(subs_dir)
        for path, _, filename_list  in subs_dir:
            for filename in filename_list:
                self.subs_filepathes.append(os.path.join(path, filename))
        self.subs_filepathes = natsorted(self.subs_filepathes)
        
    def dictionarize_episodes(self):
        def get_season_episode_num(filename):
            try:
                for pattern in self.episode_name_regex:
                        regex_app = re.search(pattern, filename)
                        if regex_app:
                            return regex_app.groups()
            except:
                breakpoint()
            return None
                
        self.episode_to_filepath = {}
        for i, filename in enumerate(self.get_subs_filenames()):
            try:
                season, episode = get_season_episode_num(filename)
                self.episode_to_filepath[(season, episode)] = self.subs_filepathes[i]     
            except:
                breakpoint()
                raise SubtitleFilenamePatternUndefined
        
        self.filepath_to_episode = {
            v:k for k, v in self.episode_to_filepath.items()
        }
        
        
    def __iter__(self):
        return self
    
    def __next__(self):
        return next(self.gen)
    
    def _generator(self):
        for i, filepath in enumerate(self.subs_filepathes):
            if self.curr_subs_reader:
                self.curr_subs_reader.destroy()
            self.curr_subs_reader = SubtitlesReader(
                filepath, self.filepath_to_episode[filepath]
            )
            self.curr_file_idx = i
            yield self.curr_subs_reader
            
    def get_subs_filenames(self):
        return [os.path.basename(p) for p in self.subs_filepathes]
            
    def get_curr_filename(self):
        return self.curr_subs_reader.get_filename()
    
    
    def open_episode(self, episode_info):
        if self.curr_subs_reader:
            self.curr_subs_reader.destroy()
        self.curr_subs_reader = SubtitlesReader(
            self.episode_to_filepath[episode_info], episode_info
        )
        return self.curr_subs_reader