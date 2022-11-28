import os
import re
from natsort import natsorted
from .subtitles_cut import SubtitleSnippet
                
# TODO read all lines and keep track
class SubtitlesReader:
    def __init__(self, filepath, episode_info):
        self.filepath = filepath
        self.episode_info = episode_info
        self.file = open(filepath, encoding='utf_8')
        self.gen = self._generator()
        self.cur_snippet = self.__next__()
    
    def __str__(self):
        return f'Episode-Title: {self.episode_info}\n' +\
            f'Current Snippet:\n{self.cur_snippet}'
        
    def __repr__(self) -> str:
        return f'SubtitleReader\n {self.__str__()}'
    
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
            self.cur_snippet =\
                SubtitleSnippet(self.episode_info, snip_id, snip_ts, snip_utts)
            yield self.cur_snippet
        self.destroy()
        self.cur_snippet = None
        yield self.cur_snippet
    
    def get_cur_snippet(self):
        return self.cur_snippet
    
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
    
    def get_cur_snippet_num(self):
        return self.cur_snippet.get_id()
    
    def get_curr_timestamp(self):
        return f'{self.cur_snippet.get_id()}'
    
    def get_curr_utterances(self):
        return self.cur_snippet.utts
    
    def get_filename(self):
        return os.path.basename(self.filepath)
    
    def reset(self):
        try:
            self.destroy()
        except:
            print('File was never opened')
        finally:
            self.file = open(self.filepath)
        
    def destroy(self):
        self.file.close()

    def shift_to_snippet(self, snippet_id):
        if self.get_cur_snippet_num() > snippet_id:
            self.reset()
        while True:
            cur_snip_id = self.get_cur_snippet_num()
            if cur_snip_id == snippet_id:
                break
            self.__next__()
            
        
    
        
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
        self.cur_file_idx = 0
        self.gen = self._generator()
        next(self.gen)
    
    def __str__(self):
        return f'Parent: {self.parent_dir}\n' +\
            f'Current File Idx: {self.cur_file_idx}\n' +\
            f'Current File:\n {self.subreaders[self.cur_file_idx]}' +\
            f'Episode: {self.subreaders[self.cur_file_idx].episode_info}'

    def __repr__(self) -> str:
        return f'SubsFileDirector\n {self.__str__()}'
    
    def destroy(self):
        if self.subreaders:
            for subreader in self.subreaders:
                subreader.destroy()
        self.__init__(self.parent_dir, self.episode_name_regex)
    
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
                        regex_app = re.search(pattern, filename.lower())
                        if regex_app:
                            return regex_app.groups()
            except:
                breakpoint()
            return None
                
        self.subreaders = []
        self.episode_to_idx = {}
        for idx, filename in enumerate(self.get_subs_filenames()):
            try:
                episode_title = get_season_episode_num(filename)
                filepath = self.subs_filepathes[idx]
                subsreader = SubtitlesReader(filepath, episode_title)   
                self.subreaders.append(subsreader)
                self.episode_to_idx[episode_title] = idx
            except:
                breakpoint()
                raise SubtitleFilenamePatternUndefined
        
    def __iter__(self):
        return self
    
    def __next__(self):
        return next(self.gen)
    
    def get_cur_subs_reader(self):
        if self.cur_file_idx >= len(self.subreaders):
            return None
        return self.subreaders[self.cur_file_idx]
    
    def _generator(self):
        while self.get_cur_subs_reader():
            yield self.subreaders[self.cur_file_idx]
            self.cur_file_idx += 1
        yield None

    def open_episode(self, episode_info, snippet_id=None):
        self.cur_file_idx = self.episode_to_idx[episode_info]
        cur_subs_reader = self.subreaders[self.cur_file_idx]
        if snippet_id:
            cur_subs_reader.shift_to_snippet(snippet_id)
        return cur_subs_reader
    
    def get_subs_filenames(self):
        return [os.path.basename(p) for p in self.subs_filepathes]
            
    def get_curr_filename(self):
        return self.subreaders[self.cur_file_idx].get_filename()
    
    
