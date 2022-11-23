import re
import string
import numpy as np
from jiwer import wer, compute_measures
from difflib import SequenceMatcher

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


def generate_possible_utt_windows(snip, prev_match):
    # filter speakers
    spk_pattern = r'\w+:'

    cleaned_org_utts = [
        clean_str(t) for t in snip.curr_utterances
        if not re.search(spk_pattern, t)
    ]
    
    test_utts = cleaned_org_utts.copy()
    prefix_match = prev_match
    for i, u in enumerate(cleaned_org_utts):
        prefix_match = test_utts[i] = f'{prefix_match} {u}'.strip()
    if prev_match:
        test_utts += cleaned_org_utts.copy() + [prev_match]

    return np.array(list(set(test_utts)))

def longest_common_wseq(str1, str2):
    str1, str2 = str1.split(), str2.split()
    matcher = SequenceMatcher(None,str1,str2)
    match = matcher.find_longest_match(0, len(str1), 0, len(str2))
    return ' '.join(str1[match.a: match.a + match.size])

def is_match(text, utt, calc, hit_thres=0.9):
    def match_stats():
        # misses == left-overs
        # misses on text-end
        if num_misses_snip_utt == calc['insertions']:
            return True
        # misses on utt-end
        if num_misses_snip_utt == calc['deletions']:
            return True
        # few words different; possibly spelling
        if num_misses_snip_utt == calc['substitutions']:
            return True
        return False

    wcnt_txt = cntw_str(text)
    wcnt_utt = cntw_str(utt)
    perc_snip_utt_hit = calc['hits']/wcnt_utt
    num_misses_snip_utt = wcnt_txt - int(wcnt_utt*perc_snip_utt_hit)

    if calc['hits'] > 0 and match_stats():
        # consecutive hits match with few misses
        # aka. at-least 0.5words in utt conseq match
        len_lcs = cntw_str(longest_common_wseq(text, utt))
        if len_lcs == calc['hits'] and len_lcs/wcnt_utt > 0.5:
            return True
        
        if perc_snip_utt_hit >= hit_thres:
            # close hits match with minor spelling mistakes
            return True
        
        if calc['wer'] <= 0.25:
            # TODO check to merge with spelling mistakes
            # high error rate, probably just slightly missing
            return True
        
    return False
        
    

def get_matches(snip, text, prefix_match="", verbose=False):
    test_utts = generate_possible_utt_windows(snip, prefix_match)
    if verbose:
        print(f':::: {text}\n::::test_utts\n::::{test_utts}')
    calcs = [compute_measures(text, t) for t in test_utts]
    # print(calcs)
    # breakpoint()

    matched_utts_idx = []
    for i, (utt, calc)  in enumerate(zip(test_utts, calcs)):
        if  is_match(text, utt, calc):
            matched_utts_idx.append(i)
    
    if verbose:
        print(f':::: {calcs}')
    
    if matched_utts_idx:
        scores = [ 
            1/(calcs[i]['wer'] + 1)*calcs[i]['wip']*cntw_str(test_utts[i])
            for i in matched_utts_idx
        ]
        print(f':::: matches: {test_utts[matched_utts_idx]}')
        print(f':::: scores: {scores}')
        
        argmax_utts = matched_utts_idx[np.argmax(scores)]
        # print(calcs[argmax_utt]['mer'])
        print(f':::: top: {scores[np.argmax(scores)]} @ {test_utts[argmax_utts]}')
        breakpoint()

        return test_utts[argmax_utts]
    
    return ''

def cntw_str(_str):
    if not _str:
        return 0
    return len([w for w in _str.split(' ') if w])

def cntw_str_list(str_list):
    return np.sum([cntw_str(s) for s in str_list])


def get_text_start_point(subs_f_dir, text, verbose=False):
    text = clean_str(text)
    # TODO remove
    
    # Ensure non-null subtitles file
    if subs_f_dir.curr_subs_reader is None:
        next(subs_f_dir)
        next(subs_f_dir)
        print(f'{subs_f_dir.curr_file_idx}: {subs_f_dir.get_curr_filename()}')

        
    while True:
        
        # Ensure non-null subtitle-snippet
        curr_snip = subs_f_dir.curr_subs_reader.curr_snippet
        if not curr_snip:
            curr_snip = next(subs_f_dir.curr_subs_reader)
            
        found_sub_snip = False
        match = ""
        prev_wer = 10 # some arbitirarly large number > 1
        while True:
            match = get_matches(
                curr_snip, text, 
                prefix_match=match,
                verbose=verbose
            )
            if match:
                # TODO calculate wer if not tiny enough.. 
                # if it gets worse.. use prev..
                if verbose:
                    print(f'\n=> matched utts: {match} \n')
                    breakpoint()
                curr_wer = wer(text, match)
                # if (cntw_str(match) == cntw_str(text)) or\
                if (curr_wer >= prev_wer):
                    found_sub_snip = True
                    match = prev_match
                    break
                prev_wer = wer(text, match)
                prev_match = match

                
            curr_snip  = next(subs_f_dir.curr_subs_reader)
            if not curr_snip:
                break
            
        if found_sub_snip:
            return match
        
        if not next(subs_f_dir):
            # TODO maybe wrap!
            print(f'{subs_f_dir.curr_file_idx}: {subs_f_dir.get_curr_filename()}')
            break
        
    return None 