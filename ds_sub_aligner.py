from aligner import Aligner
from align_utils import clean_str, np, get_matches
from align_utils import wer, compute_measures

class DSSubAligner(Aligner):
        
    def get_text_start_point(self, text, verbose, debug):
        text = clean_str(text) # TODO do it somewhere else
        while True:
            found_sub_snip = False
            prev_wer = np.inf
            match_win = None
            prev_match_win = None

            while self._get_cur_sub_snippet():
                # if 'Sorry. Thanks. You look good too.'.lower() in curr_snippet:
                #     debug = True
                #     verbose = True
                #     breakpoint()

                # if 'barry' in curr_snippet:
                #     breakpoint()
                    
                match_win = get_matches(
                    self._get_cur_sub_snippet(), 
                    text, prefix_match_win=match_win,
                    verbose=verbose, debug=debug
                )

                if match_win or prev_match_win:
                    if match_win:
                        curr_wer = wer(text, match_win.u)
             
                    # it did well before and now failed 
                    # (higher WER or not matching at all)
                    if prev_match_win and not match_win or\
                        curr_wer >= prev_wer:
                        found_sub_snip = True
                        match_win = prev_match_win
                        # Start next time from last matching snippet
                        self._shift_back_sub_snippet()
                        break
                    prev_wer = wer(text, match_win.u)
                    prev_match_win = match_win    
                    
                self._get_next_sub_snippet()
                
            if found_sub_snip:
                return match_win
            # else:
            #     breakpoint()
            
            if not self._get_next_subs_reader():
                break
            
        return None 
    
    def find_alignment(self, conv_df, thres=0.1, verbose=False, debug=False):
        # Start from the beginning of subtitles
        self.reset()
        matches = []        
        idx = 0
        while idx < len(conv_df):
            spk, text, emotion = conv_df.iloc[idx]
            idx += 1
            
            match = self.get_text_start_point(text, verbose=verbose, debug=debug)
            
            if match is None:
                break
            matches.append(match)

            # verify that snippets are consecutive 
            # TODO maybe consider threshold over timestamps instead of ids
            for i in range(len(matches)-1):
                # one snippet difference or exactly the same
                # TODO check batching lonely missing snippets right (higher probability)
                if matches[i].episode_title != matches[i+1].episode_title or\
                    np.min(matches[i+1].ids) - np.max(matches[i].ids) > 2:
                        
                    # start from last matching snippet in last matching episode
                    self.open_episode(
                        episode_info=matches[i+1].episode_title,
                        snippet_id=np.min(matches[i+1].ids)
                    )
                    
                    # There is a jump! probably a mistaken early access
                    # breakpoint()
                    matches = []
                    idx = 0
                    break
                    # TODO ensure shifting subsfilereader to first obeservation
                    
            
            if verbose:
                print('=> orig: ', text)
                print('==='*12, f'  {idx}  ', '==='*12)
                print('=> orig: ', text)
                print('=> match:', match)
                print('==='*30)
        
        if matches and len(matches) == len(conv_df):
            conv_df['cleaned_utt'] = conv_df['utterance'].apply(lambda m: clean_str(m))
            conv_df['match_utt'] = list(map(lambda m: m.u, matches))

            # verify wer
            err = wer(
                conv_df['cleaned_utt'].to_list(),
                conv_df['match_utt'].to_list()
            )
            if err < thres:
                return True, conv_df, matches, f'Match :: wer: {err}'
            else:
                return False, conv_df, matches, f'Non-Match :: WER is below thres: {err}'
            
        return False, conv_df, matches, 'Non-Match :: no complete consecutive matches found'