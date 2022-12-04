from .aligner import Aligner
from aligner.align_utils import np, clean_str, cntw_str
from aligner.align_utils import generate_possible_utt_windows, longest_common_wseq
from aligner.align_utils import wer, compute_measures


# Heuristics
def is_match(text, utt, calc, hit_thres=0.9, allowed_extra_err=0.5,  debug=False):
    def is_misses_num_match():
        # misses == left-overs
        # misses on text-end
        if num_misses_snip_utt == calc['insertions']:
            return True
        # misses on utt-end
        if num_misses_snip_utt == calc['deletions']:
            return True
        return False
        
    wcnt_txt = cntw_str(text)
    wcnt_utt = cntw_str(utt)
    perc_snip_utt_hit = calc['hits']/wcnt_utt
    num_misses_snip_utt = wcnt_txt - int(wcnt_utt*perc_snip_utt_hit)

    if debug:
        print('Debug')
        print('Text:', text)
        print('Utt:', utt)
        breakpoint()
        
    # allowed max extra error margin & there are hits
    if wcnt_txt/wcnt_utt > allowed_extra_err and calc['hits'] > 0:
        # consecutive hits match with few misses
        # aka. at-least 0.5hits from utt matches are consecutive
        len_lcs = cntw_str(longest_common_wseq(text, utt))
        ratio_lcs_utt = len_lcs/wcnt_utt
        if len_lcs >= calc['hits']*ratio_lcs_utt and is_misses_num_match():
            return True
        
        # submatch with minor mistakes and good enough match error rate
        # good enough = thres defined below
        sub_match_text = ' '.join(text.split()[:wcnt_utt])
        if wcnt_txt >= wcnt_utt:
            thres = (wcnt_utt/wcnt_txt)*ratio_lcs_utt
            thres *= (wcnt_txt/wcnt_utt) # Experiment relative difference!
            if compute_measures(utt, sub_match_text)['mer'] <= thres:
                return True

        # close hits match with minor spelling mistakes
        if perc_snip_utt_hit >= hit_thres and is_misses_num_match():
            return True
                
        # high error rate, probably just slightly missing
        # if calc['wer'] <= 0.25 and num_misses_snip_utt == calc['substitutions']:
        #     return True
        
    return False

def get_matches(snip, text, prefix_match_win=None, verbose=False, debug=False):
    test_wins = generate_possible_utt_windows(snip, prefix_match_win)
        
    calcs = [compute_measures(text, w.u) for w in test_wins]

    matched_utts_idx = []
    for i, (win, calc)  in enumerate(zip(test_wins, calcs)):
        if  is_match(text, win.u, calc):
            matched_utts_idx.append(i)
    
    if matched_utts_idx:
        scores = [ 
            1/(calcs[i]['wer'] + 1)*calcs[i]['wip']*cntw_str(test_wins[i].u)
            for i in matched_utts_idx
        ]
        argmax_utts = matched_utts_idx[np.argmax(scores)]
        match_win = test_wins[argmax_utts]
    else:
        match_win = None
        
    if verbose:
        print('::::'*20)
        print(f':::: org: {text}')
        for i, win in enumerate(test_wins):
            print(f':::: utt: {win.u}')
            print(f':::: {[(k, round(v, 2)) for k, v in calc.items()]}')
        if matched_utts_idx:
            for win, score in zip(test_wins[matched_utts_idx], scores):
                if match_win.u == win.u:
                    print(f':::: match(score): {win.u} => ({score}) <======== top')
                else:
                    print(f':::: match(score): {win.u} => ({score})')
            print(f':::: org: {text}')
        else:
            print(f':::: matches: {test_wins[matched_utts_idx]}')
        print('::::'*20)

    if debug:
        breakpoint()
        
    return match_win


class DSSubAligner(Aligner):
    
    def is_debug_cond_sats(
            self, snippet_text=None, reg_text=None
        ):
        unsats_trues = 0
        if snippet_text is not None:
            unsats_trues += 1
            if snippet_text.lower() in self._get_cur_snippet():
                unsats_trues -= 1
        if reg_text is not None:
            unsats_trues += 1
            if reg_text.lower() in self.cur_text:
                unsats_trues -= 1
        
        return unsats_trues == 0
                    
    def get_text_start_point(self, text, verbose, debug):
        text = clean_str(text) # TODO do it somewhere else
        self.cur_text = text
        while True:
            found_sub_snip = False
            prev_wer = np.inf
            match_win = None
            prev_match_win = None

            while self._get_cur_snippet():
                # if self.is_debug_cond_sats(
                #         # snippet_text='anyone who... stands erect... So what',
                #         reg_text='stands erect'
                #     ):
                #     debug = True
                #     verbose = True    
                #     breakpoint()

                match_win = get_matches(
                    self._get_cur_snippet(), 
                    text, prefix_match_win=prev_match_win,
                    verbose=verbose, debug=debug
                )

                if match_win or prev_match_win:
                    if match_win:
                        curr_wer = wer(text, match_win.u)
             
                    # it did well before and now failed 
                    # (higher WER or not matching at all)
                    if (prev_match_win and not match_win) or\
                        curr_wer >= prev_wer:
                        found_sub_snip = True
                        match_win = prev_match_win
                        break
                    
                    # wer should be there if we get to this point
                    prev_wer = curr_wer if match_win else np.inf
                    prev_match_win = match_win    
                    
                self._get_next_snippet()
                
            if found_sub_snip:
                # Start next time from last matching snippet
                self._shift_back_snippet()
                return match_win
            # else:
            #     breakpoint()
            
            if not self._get_next_subs_reader():
                break
    
    def find_alignment(self, conv_df, thres=0.1, verbose=False, debug=False):
        # Start from the beginning of subtitles
        self.reset()
        
        best_matches = []
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
                    np.min(matches[i+1].ids) - np.max(matches[i].ids) > 1:
                    
                    # breakpoint()
                    # start from right-after recent jumping snippet
                    self.open_episode(
                        episode_info=matches[i].episode_title,
                        snippet_id=np.max(matches[i].ids) + 1
                    )
                    if len(matches) > len(best_matches):
                        best_matches = matches
                    matches = []
                    idx = 0
                    self._unshift_snippet()
                    break                    
            
            if verbose:
                print('=> orig: ', text)
                print('==='*12, f'  {idx}  ', '==='*12)
                print('=> orig: ', text)
                print('=> match:', match)
                print('==='*30)
        
        
        postfix_msgs = []
        if len(best_matches) > len(matches):
            matches = best_matches
            postfix_msgs = ['dropping snippets']
            
        if matches and len(matches) == len(conv_df):
            conv_df['cleaned_utt'] = conv_df['utterance'].apply(lambda m: clean_str(m))
            conv_df['match_utt'] = list(map(lambda m: m.u, matches))

            # breakpoint()
            # verify wer
            err = wer(
                conv_df['cleaned_utt'].to_list(),
                conv_df['match_utt'].to_list()
            )
            if err < thres:
                return True, conv_df, matches,\
                    f'Match :: WER: {err}; {"; ".join(postfix_msgs)}'
            else:
                return False, conv_df, matches,\
                    f'Non-Match :: WER is below thres: {err}; {"; ".join(postfix_msgs)}'
            
        return False, conv_df, matches, 'Non-Match :: no complete consecutive matches found'