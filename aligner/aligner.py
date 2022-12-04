from subtitles_utils.subtitles_cut import SubtitleSnippet
from subtitles_utils.subtitles_reader import SubsFileDirectory, SubtitlesReader

class Aligner:
    def __init__(self, subs_f_dir: SubsFileDirectory, episode_info=None, snippet_id=None):
        self.subs_f_dir = subs_f_dir
        if episode_info:
            self.subs_f_dir.open_episode(episode_info, snippet_id=snippet_id)        
        # for 1-look back in the past
        self.snippet_shifted = False
        self.prev_snippet = None
                
    def _get_subs_dir(self) -> SubsFileDirectory:
        return self.subs_f_dir
    
    def _get_cur_subs_reader(self) -> SubtitlesReader:
        return self._get_subs_dir().get_cur_subs_reader()
    
    def _get_next_subs_reader(self) -> SubtitlesReader:
        next(self._get_subs_dir())
        return self._get_cur_subs_reader()
    
    def _get_cur_snippet(self) -> SubtitleSnippet:
        if self.snippet_shifted:
            return self.prev_snippet
        return self._get_cur_subs_reader().get_cur_snippet()
    
    def _get_next_snippet(self) -> SubtitleSnippet:
        if self.snippet_shifted:
            self.snippet_shifted = False
            return self._get_cur_snippet()
        self.prev_snippet = self._get_cur_snippet()
        next(self._get_cur_subs_reader())
        return self._get_cur_snippet()
    
    def _shift_back_snippet(self):
        self.snippet_shifted = True
        
    def _unshift_snippet(self):
        self.snippet_shifted = False
        
    def open_episode(self, episode_info, snippet_id=None) -> SubtitlesReader:
        self.subs_f_dir.open_episode(episode_info, snippet_id=snippet_id)
    
    def reset(self):
        self.subs_f_dir.reset()
        self._unshift_snippet()