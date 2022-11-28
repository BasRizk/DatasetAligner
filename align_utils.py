import jiwer
import string
import numpy as np
from difflib import SequenceMatcher
from subtitles_utils.subtitles_cut import SubtitleSnippet



def compute_measures(ground_truth, hypothesis):
    return jiwer.compute_measures(ground_truth, hypothesis)
    
def wer(ground_truth, hypothesis):
    return jiwer.wer(ground_truth, hypothesis)

translator_punc = str.maketrans(string.punctuation, ' '*len(string.punctuation))
def clean_str(_str):
    def remove_cons_dup(_str):
        tokens = _str.split()
        updated_tokens = [tokens[0]]
        for t in tokens:
            # already observed
            if t == updated_tokens[-1]:
                continue
            updated_tokens.append(t)
        return ' '.join(updated_tokens)
    _str = _str.translate(translator_punc).strip().lower()
    _str = remove_cons_dup(_str)
    return _str

def generate_possible_utt_windows(snip: SubtitleSnippet, prev_match_win):
    # filter speakers
    # spk_pattern = r'\w+:'    
    # div_utterances = []
    # for u in snip.curr_utterances:
    #     div_utterances += [utt for utt in u.split(',') if utt]
        
    wins = []
    if prev_match_win and prev_match_win.is_ending():
        for bwin in snip.bwins:
            wins.append(
                prev_match_win + bwin
            )
        wins = [prev_match_win] + wins
    wins += snip.windows
    
    wins = np.array(list(set(wins)))
    for win in wins:
        win.apply(clean_str)
    return wins

def longest_common_wseq(str1, str2):
    str1, str2 = str1.split(), str2.split()
    matcher = SequenceMatcher(None,str1,str2)
    match = matcher.find_longest_match(0, len(str1), 0, len(str2))
    return ' '.join(str1[match.a: match.a + match.size])

# Heuristics
def is_match(text, utt, calc, hit_thres=0.9, debug=False):
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
        breakpoint()
        
    if calc['hits'] > 0:
        # consecutive hits match with few misses
        # aka. at-least 0.5words in utt conseq match
        len_lcs = cntw_str(longest_common_wseq(text, utt))
        ratio_lcs_utt = len_lcs/wcnt_utt
        if len_lcs >= calc['hits']*ratio_lcs_utt and is_misses_num_match():
            return True
        
        # submatch with minor mistakes and good enough match error rate
        # good enough = thres defined below
        sub_match_text = ' '.join(text.split()[:wcnt_utt])
        if wcnt_txt >= wcnt_utt:
            thres = (wcnt_utt/wcnt_txt)*ratio_lcs_utt
            if compute_measures(utt, sub_match_text)['mer'] <= thres:
                # breakpoint()
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

def cntw_str(_str):
    if not _str:
        return 0
    return len([w for w in _str.split(' ') if w])

def cntw_str_list(str_list):
    return np.sum([cntw_str(s) for s in str_list])
