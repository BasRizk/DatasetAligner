from aligner import Aligner
from align_utils import clean_str, np, get_matches
from align_utils import wer, compute_measures
from subtitles_utils.subtitles_cut import SubtitleSnippet, SubtitleWindow

        
class SubSubAligner(Aligner):
    
    def _get_overlapping_snippets(self, sub_win: SubtitleWindow, debug):
        overlapping_matches = []
        while True:
            cur_snippet = self._get_cur_sub_snippet()
            # if debug:
            #     print('\n Current Snippet:\n', cur_snippet)
            
            # Get overlapping subtitle snippets
            if sub_win.timestamp.is_overlaping(cur_snippet.timestamp):
                overlapping_matches.append(cur_snippet)
            elif len(overlapping_matches) > 0:
                self._shift_back_sub_snippet()
                break
            else:
                breakpoint()
            
            if not self._get_next_sub_snippet():
                break
        return overlapping_matches
    def _get_corresponding_text(self, sub_win: SubtitleWindow, debug):
        if debug:
            print('Sub window:\n', sub_win)
            
        overlapping_snippets = self._get_overlapping_snippets(sub_win, debug)
            
        if overlapping_snippets:
            # TODO Pick statements based on line numbers and number of snippets in sub_win
            print('Overlapping Snippets Ids:', list(map(lambda x: x.id, overlapping_snippets)))
            breakpoint()
        else:
            return None 
        
        
    
    def find_alignment(self, sub_wins, debug=False):
        # Set pointer over the relevant episode
        self.open_episode(sub_wins[0].ss.episode_title)

        text_matches = []
        for sub_win in sub_wins:
            matched_text = self._get_corresponding_text(
                sub_win, debug=debug
            )
            text_matches.append(matched_text)
        print('Finished Conversation Windows')
        return text_matches