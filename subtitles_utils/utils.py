import unicodedata
import arabic_reshaper
import numpy as np

"""
Return fixed RTL (ex. Arabic) text for terminal
Source:
https://stackoverflow.com/questions/41243215/how-to-print-arabic-text-correctly-in-python
"""
def prepare_rtl(text_to_be_reshaped):
    reshaped_text = arabic_reshaper.reshape(text_to_be_reshaped)
    rev_text = reshaped_text[::-1]  # slice backwards 
    return rev_text

"""
Reverse text if RTL language (Arabic, Persian) found
Source:
https://stackoverflow.com/questions/49346329/check-if-a-string-contains-characters-other-than-persian-arabic-characters-in-py
"""
def prepare_txt(text, rtl_languages=['arabic', 'persian']):
    def is_rtl_char(c):
        name = unicodedata.name(c).lower()
        for l in rtl_languages:
            if l in name:
                return True
        return False
    
    if isinstance(text, list):
        texts = []
        for t in text:
            texts.append(
                prepare_txt(t, rtl_languages)
            )
        return texts
    
    rtl_chars = False
    for c in text:
        if is_rtl_char(c):
            rtl_chars = True
            continue
    if rtl_chars:
        return prepare_rtl(text)
    return text
    