from subtitles_utils.subtitles_cut import SubtitleSnippet
from subtitles_utils.subtitles_reader import SubsFileDirectory, SubtitlesReader

class Aligner:
    def __init__(self, subs_f_dir: SubsFileDirectory, episode_info=None, snippet_id=None):
        self.subs_f_dir = subs_f_dir
        if episode_info:
            self.subs_f_dir.open_episode(episode_info, snippet_id)        
        # for 1-look back in the past
        self.sub_snippet_shifted = False
        self.prev_sub_snippet = None
                
    def _get_subs_dir(self) -> SubsFileDirectory:
        return self.subs_f_dir
    
    def _get_cur_subs_reader(self) -> SubtitlesReader:
        return self._get_subs_dir().get_cur_subs_reader()
    
    def _get_next_subs_reader(self) -> SubtitlesReader:
        next(self._get_subs_dir())
        return self._get_cur_subs_reader()
    
    def _get_cur_sub_snippet(self) -> SubtitleSnippet:
        if self.sub_snippet_shifted:
            return self.prev_sub_snippet
        return self._get_cur_subs_reader().get_cur_snippet()
    
    def _get_next_sub_snippet(self) -> SubtitleSnippet:
        if self.sub_snippet_shifted:
            self.sub_snippet_shifted = False
            return self._get_cur_sub_snippet()
        self.prev_sub_snippet = self._get_cur_sub_snippet()
        next(self._get_cur_subs_reader())
        return self._get_cur_sub_snippet()
    
    def _shift_back_sub_snippet(self):
        self.sub_snippet_shifted = True
        
    def open_episode(self, episode_info, snippet_id=None) -> SubtitlesReader:
        self.subs_f_dir.destroy()
        self.__init__(
            self.subs_f_dir, 
            episode_info=episode_info, 
            snippet_id=snippet_id
        )
    
    def reset(self):
        self.subs_f_dir.destroy()
        self.__init__(self.subs_f_dir)