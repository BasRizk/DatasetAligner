import sys, os
sys.path.insert(0, os.path.abspath('..'))
from subtitles_utils.subtitles_cut import SubtitleSnippet, SubtitleWindow
from subtitles_utils.utils import prepare_txt
  
from .aligner import Aligner


class SubSubAligner(Aligner):
    
    def _get_overlapping_snippets(self, sub_win: SubtitleWindow, debug):
        overlapping_matches = []
        while self._get_cur_snippet():
            # if debug:
            #     print('\n Current Snippet:\n', cur_snippet)
            
            # Get overlapping subtitle snippets
            if sub_win.is_overlaping(self._get_cur_snippet()):
                overlapping_matches.append(self._get_cur_snippet())
            elif len(overlapping_matches) > 0:
                self._shift_back_snippet()
                break
            # elif debug:
            #     breakpoint()
            
            self._get_next_snippet()
            
        return overlapping_matches
    
    def _remove_spanning_snippets(self, snippets: SubtitleSnippet):            
        if len(snippets) <= 1:
            return snippets

        kept = []
        for s1 in snippets:
            remove = True
            for s2 in snippets:
                if not s1.timestamp.is_spanning(s2.timestamp):
                    remove = False
            if not remove:
                kept.append(s1)
        return kept
    
    def _remove_non_overlapping_lines(self, sub_win:SubtitleWindow, snippets):
        kept_wins = []
        for s in snippets:
            for line, utt in enumerate(s.utts):
                line_win = SubtitleWindow([s], line, line, utt)
                if line_win.is_overlaping(sub_win):
                    kept_wins.append(line_win)
        return kept_wins
            
            
    
    
    def _get_corresponding_text(self, sub_win: SubtitleWindow, debug):
        if debug:
            print('Sub window:\n', sub_win)
            
        overlapping_snippets = self._get_overlapping_snippets(sub_win, debug)
                
        if overlapping_snippets:

            # Remove spanning snippets (Advertisement or Author..or such..) 
            overlapping_nonspanning_snippets = self._remove_spanning_snippets(overlapping_snippets)

            # Pick statements based on line numbers and number of snippets in sub_win
            overlapping_wins = self._remove_non_overlapping_lines(sub_win, overlapping_nonspanning_snippets)
            
            self.most_recent_successful_snippet = overlapping_wins[-1].es.get_id()

            # print('Non-spanning Wins:\n', overlapping_wins)                        
            matched_text = ' '.join([w.u for w in overlapping_wins])
            
            if debug:
                print('Overlapping Snippets Ids:', list(map(lambda x: x.id, overlapping_snippets)))
                print('Overlapping Non-spanning Snippets Ids:', list(map(lambda x: x.id, overlapping_snippets)))
                from subtitles_utils.utils import prepare_txt
                print('::: Original text:', prepare_txt(sub_win.u))
                print('::: Matched text:', prepare_txt(matched_text))
                breakpoint()
                
            return matched_text
        else:
            print('Failed to find any overlapping snippets with snippet; Using Org subs')
            # breakpoint()
            # Return for now the text as is in English (Assuming it refers to sounds!)
            return sub_win.u 
        
        
    
    def find_alignment(self, sub_wins, debug=False):
        # Set pointer over the relevant episode
        self.open_episode(sub_wins[0].ss.episode_title)
        text_matches = []
        self.most_recent_successful_snippet = None
        for sub_win in sub_wins:
            matched_text = self._get_corresponding_text(
                sub_win, debug=debug
            )
            # print(sub_win.u)
            # print(prepare_txt(matched_text))
            # breakpoint()
            if matched_text == sub_win.u:
                if self.most_recent_successful_snippet:
                    self.open_episode(
                        sub_win.ss.episode_title, 
                        snippet_id=self.most_recent_successful_snippet
                    )
                else:
                    break
            text_matches.append(matched_text)
         
         
        # print([prepare_txt(t) for t in text_matches])
        # breakpoint()

        print('Finished Conversation Windows')
        return text_matches