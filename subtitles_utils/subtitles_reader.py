import os
import re
from natsort import natsorted
from .subtitles_cut import SubtitleSnippet
                
class SubtitlesReader:
    def __init__(self, filepath, episode_info):
        self._filepath = filepath
        self._episode_info = episode_info
        self._snippets = self.read_snippets()    
        self._cur_snippet_idx = 0
        self._gen = self._generator()
        next(self._gen)
        
    def shift_to_snippet(self, snippet_id):
        # snippet_id is 1-based accoridng to SRT format
        self._cur_snippet_idx = snippet_id - 1
        self._gen = self._generator()
        next(self._gen)
        
    def reset(self):
        self.shift_to_snippet(1)
        
    def read_snippets(self):
        self.file = open(self._filepath, encoding='utf_8')
        snip_id = 1
        snippets = []
        while True:
            lines = self.read_until(end='')
            if lines is None:
                break
            snip_num = int(re.sub(r'[^0-9]', '', lines[0]))
            snip_ts = lines[1]
            snip_utts = lines[2:]
            isSkip = sum(['♪' in u for u in snip_utts])
            if not isSkip:
                snippets.append(
                    SubtitleSnippet(self._episode_info, snip_num, snip_id, snip_ts, snip_utts)
                )
                snip_id += 1
        self.file.close()
        return snippets
   
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
    
    def __str__(self):
        return f'Episode-Title: {self._episode_info}\n' +\
            f'Current Snippet:\n{self._snippets[self._cur_snippet_idx]}'
        
    def __repr__(self) -> str:
        return f'SubtitleReader\n {self.__str__()}'
    
    def __iter__(self):
        return self
    
    def __next__(self):
        return next(self._gen)

    def get_cur_snippet(self):
        if self._cur_snippet_idx >= len(self._snippets):
            return None
        return self._snippets[self._cur_snippet_idx]
    
    # subs_file_lines_generator
    def _generator(self) -> SubtitleSnippet:
        while self.get_cur_snippet():
            yield self._snippets[self._cur_snippet_idx]
            self._cur_snippet_idx += 1
        yield None
        
    def get_episode_info(self):
        return self._episode_info

    def get_cur_snippet_num(self):
        return self.get_cur_snippet().get_id()
    
    def get_curr_timestamp(self):
        return f'{self.get_cur_snippet().get_timestamp()}'
    
    def get_curr_utterances(self):
        return self.get_cur_snippet().utts
    
    def get_filename(self):
        return os.path.basename(self._filepath)
    
    
    
        
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
    
    def reset(self):
        self.cur_file_idx = 0
        self.gen = self._generator()
        next(self.gen)
        for subreader in self.subreaders:
            subreader.reset()

    def __str__(self):
        return f'Parent: {self.parent_dir}\n' +\
            f'Current File Idx: {self.cur_file_idx}\n' +\
            f'Current File:\n {self.subreaders[self.cur_file_idx]}' +\
            f'Episode: {self.subreaders[self.cur_file_idx].get_episode_info()}'

    def __repr__(self) -> str:
        return f'SubsFileDirector\n {self.__str__()}'
    
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