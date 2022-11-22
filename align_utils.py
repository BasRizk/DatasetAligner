import string
import numpy as np
from jiwer import wer, compute_measures

translator = str.maketrans(string.punctuation, ' '*len(string.punctuation))
def clean_txt(text):
    return text.translate(translator).strip()

def get_matches(snip, text):
    
    snip.curr_utterances = [clean_txt(t) for t in snip.curr_utterances]       
    print(f'\n=> {text} :::: {snip.curr_utterances}')
    calcs = [compute_measures(t, text) for t in snip.curr_utterances]
    print(calcs)

    wcnt_txt = cntw_str(text)
    matched_utts = []
    for utt, calcs  in zip(snip.curr_utterances, calcs):
        wcnt_utt = cntw_str(utt)
        if wcnt_utt == calcs['hits'] and\
            (wcnt_txt - wcnt_utt) == calcs['insertions']:
            matched_utts.append(utt)
    
    return matched_utts

def cntw_str(_str):
    return len([w for w in _str.split(' ') if w])

def cntw_str_list(str_list):
    return np.sum([cntw_str(s) for s in str_list])


def get_text_start_point(subs_f_dir, text):
    text = clean_txt(text)
    # TODO remove
    if subs_f_dir.curr_subs_reader is None:
        next(subs_f_dir)
        next(subs_f_dir)
    while True:
        print(f'{subs_f_dir.curr_file_idx}: {subs_f_dir.get_curr_filename()}')

        found_sub_snip = False
        matched_utts = []
        for snip in subs_f_dir.curr_subs_reader: 
            
            matched_utts += get_matches(snip, text)
            print(matched_utts)
            breakpoint()
            if cntw_str_list(matched_utts) == cntw_str(text):
                found_sub_snip = True
                break
            
        if found_sub_snip:
            return subs_f_dir.curr_subs_reader
        
        if not next(subs_f_dir):
            # TODO maybe wrap!
            break
    return None 