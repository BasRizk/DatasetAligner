import re
import jiwer
import string
import contractions
import numpy as np
from difflib import SequenceMatcher
from subtitles_utils.subtitles_cut import SubtitleSnippet



def compute_measures(ground_truth, hypothesis):
    return jiwer.compute_measures(ground_truth, hypothesis)
    
def wer(ground_truth, hypothesis):
    return jiwer.wer(ground_truth, hypothesis)


"""
Cleaning word

wsubs_pattern based on:
- https://stackoverflow.com/questions/14156473/can-you-write-a-str-replace-using-dictionary-values-in-python

"""
word_substituations = {
    "y'serious": "you serious",
    "'cause": "because",
    "y'know": "you know",
    "y's": "ys", 
    'lizzie': 'lizzy',
    'doin': 'doing',
    "c'mon": 'come on',
    "ya": 'you',
    'in a sec': 'in a second'
}

wsubs_pattern = r'\b({})\b'.format(
    '|'.join(sorted(
        re.escape(k) 
        for k in word_substituations
    ))
)

def make_defined_substitutions(_str):
    return re.sub(wsubs_pattern, lambda m: word_substituations.get(m.group(0)), _str, flags=re.IGNORECASE)
    
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
    _str = _str.lower()
    _str = contractions.fix(_str)
    _str = make_defined_substitutions(_str)
    _str = _str.translate(translator_punc).strip()
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

def cntw_str(_str):
    if not _str:
        return 0
    return len([w for w in _str.split(' ') if w])

def cntw_str_list(str_list):
    return np.sum([cntw_str(s) for s in str_list])
