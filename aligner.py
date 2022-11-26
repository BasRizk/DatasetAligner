from subtitles_utils.subtitles_cut import SubtitleSnippet
from subtitles_utils.subtitles_reader import SubsFileDirectory, SubtitlesReader

class Aligner:
    def __init__(self, subs_f_dir):
        self.subs_f_dir = subs_f_dir
        self.curr_sub_reader = self._get_cur_subs_reader()
        
        # for 1-look back in the past
        self.sub_snippet_shifted = False
        self.prev_sub_snippet = None
        
        self.curr_sub_snippet = self._get_cur_sub_snippet()
            
    def _get_subs_dir(self) -> SubsFileDirectory:
        return self.subs_f_dir
    
    def _get_cur_subs_reader(self) -> SubtitlesReader:
        # Ensure non-null subtitles file
        if self._get_subs_dir().curr_subs_reader is None:
            next(self.subs_f_dir)
            next(self.subs_f_dir)
            print(f'{self._get_subs_dir().curr_file_idx}: {self._get_subs_dir().get_curr_filename()}')
        self.curr_sub_reader = self._get_subs_dir().curr_subs_reader
        return self.curr_sub_reader
    
    def _get_next_subs_reader(self) -> SubtitlesReader:
        self.curr_subs_reader =  next(self._get_subs_dir())
        if self.curr_subs_reader:
            print(f'{self._get_subs_dir().curr_file_idx}: {self._get_subs_dir().get_curr_filename()}')
        return self.curr_subs_reader
    
    def _get_cur_sub_snippet(self) -> SubtitleSnippet:
        if self.sub_snippet_shifted:
            return self.prev_sub_snippet
        # Ensure non-null subtitle-snippet
        self.curr_sub_snippet = self._get_subs_dir().curr_subs_reader.curr_snippet
        if not self.curr_sub_snippet:
            self.curr_sub_snippet = next(self._get_subs_dir().curr_subs_reader)
        return self.curr_sub_snippet
    
    def _get_next_sub_snippet(self) -> SubtitleSnippet:
        if self.sub_snippet_shifted:
            self.sub_snippet_shifted = False
            return self._get_cur_sub_snippet()
        self.prev_sub_snippet = self.curr_sub_snippet
        self.curr_sub_snippet = next(self._get_subs_dir().curr_subs_reader)
        return self.curr_sub_snippet
    
    def _shift_back_sub_snippet(self):
        self.sub_snippet_shifted = True
        
    def open_episode(self, episode_info) -> SubtitlesReader:
        self._get_cur_subs_reader = self.subs_f_dir.open_episode(episode_info)