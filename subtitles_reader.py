import os
import re
from natsort import natsorted
from typing import TypeVar, Type

# Create a generic variable that can be 'Parent', or any subclass.
SubtitleWindow = TypeVar('SubtitleWindow', bound='SubtitleWindow')

class SubtitleWindow:
    def __init__(self, 
                 s_snip, e_snip, 
                 s_line_idx, e_line_idx, 
                 utt):
        self.ss = s_snip
        self.es = e_snip
        self.sline = s_line_idx
        self.eline = e_line_idx
        self.org_u = utt
        self.u = utt

    def __str__(self):
        res =\
            f'From line ({self.sline})  @  snippet ({self.ss.get_id()})\n' +\
            f'To   line ({self.eline})  @  snippet ({self.es.get_id()})\n' +\
            f'Org-Utt: {self.org_u}\n'
        if self.org_u != self.u:
            res += f'Trans-Utt: {self.u}\n'
        return res
    
    def __add__(self, sub_win: Type[SubtitleWindow]):
        # ensure no errs, and snippets are consecutive
        assert self.es.get_id() == sub_win.ss.get_id() - 1
        return SubtitleWindow(
            self.ss, sub_win.es, 
            self.sline, sub_win.eline,
            f'{self.u} {sub_win.u}'.strip()
        )
        
    def is_starting(self):
        return self.sline == 0
    
    def is_ending(self):
        return self.eline == len(self.es) - 1
    
    def apply(self, func):
        self.u = func(self.u)
    
        
        
class SubtitleSnippet:
    def __init__(self, num, ts, utts):
        self.curr_snippet_num = num
        self.curr_timestamp = ts
        self.curr_utterances = utts
        self.windows = self._calc_possible_utt_windows()
        self.bwins, self.ewins = self._get_begin_end_wins()
        
    def get_id(self):
        return self.curr_snippet_num
    
    def __str__(self):
        return f'{self.curr_snippet_num}\n' +\
            f'{self.curr_timestamp}\n' +\
            "\n".join(self.curr_utterances)
            
    def __contains__(self, item: str):
        return item.lower() in ' '.join(self.curr_utterances).lower()
    
    # def __add__(self, snippet):
    #     return SubtitleSnippet(
    #         (self.curr_snippet_num, snippet.curr_snippet_num),
    #         (self.curr_timestamp, snippet.curr_timestamp),
    #         self.curr_utterances + snippet.curr_utterances
    #     )
    
    def __len__(self):
        return len(self.curr_utterances)
    
    def _calc_possible_utt_windows(self):
        wins = []
        for i in range(len(self)):
            for k in range(i + 1, len(self) + 1):
                utt = ' '.join(self.curr_utterances[i:k])
                # s_snip, e_snip, sline_idx, eline_idx, utt
                wins.append(
                    SubtitleWindow(self, self, i, k-1, utt)
                )
                # TODO include timestamp also
        return wins
    
    def _get_begin_end_wins(self):
        begining_windows = []
        ending_windows = []
        for win in self.windows:
            if win.is_starting():
                begining_windows.append(win)
            if win.is_ending():
                ending_windows.append(win)
        return begining_windows, ending_windows

# class SnippetsWindowGroup:
#     def __init__(self, snippets):
#         self.snippets = snippets

#     def __len__(self):
#         return len(self.snippets)
    
#     def __add__(self, snippet):
#         self.snippets.append(snippet)
#         # TODO make sure they are sorted
    
                
    # def get_possible_snippets_win(self):
        
    #     def _merge_cons(snippets: List(SubtitleSnippet)):
    #         if len(snippets) == 1:
    #             return snippets[0].windows
            
    #         if len(snippets) == 2:
    #             merged_wins = []
    #             for win1 in snippets[0].ewins:
    #                 ssid1, _, sline_idx1, _, u1 = win1
    #                 for win2 in snippets[1].bwins:
    #                     _, esid2, _, eline_idx2, u2 = win2
    #                     merged_wins.append(
    #                         (ssid1, esid2, sline_idx1, eline_idx2, f'{u1} {u2}')
    #                     )
    #             return merged_wins
            
    #         merges = []
    #         for i in range(len(snippets)):
    #             for k in range(i + 1, len(snippets) + 1):    
    #                 merges.append(_merge_cons(snippets[i:k]))
                    
                    
                       
                       
    #     wins = []
    #     for i in range(len(self)):
    #         for k in range(i + 1, len(self) + 1):
    #             conseq_snippets = self.snippets[i:k]
    #             # TODO include timestamp also
    #     return wins

                
class SubtitlesReader:
    def __init__(self, filepath):
        self.filepath = filepath
        self.file = open(filepath)
        self.curr_snippet = None
        self.gen = self._generator()
        
    def __iter__(self):
        return self
    
    def __next__(self):
        return next(self.gen)
    
    # subs_file_lines_generator
    def _generator(self) -> SubtitleSnippet:
        while True:
            lines = self.read_until(end='')
            if lines is None:
                break
            snip_id = int(re.sub(r'[^0-9]', '', lines[0]))
            snip_ts = lines[1]
            snip_utts = lines[2:]
            self.curr_snippet =\
                SubtitleSnippet(snip_id, snip_ts, snip_utts)
            yield self.curr_snippet
        self.destroy()
        
    def reset(self):
        try:
            self.destroy()
        except:
            print('File was never opened')
        finally:
            self.file = open(self.filepath)
        
    def destroy(self):
        self.file.close()
    
    def read_until(self, end=''):
        lines = []
        while True:
            line = self.file.readline().strip()
            if line == end:
                break
            lines.append(line)
        if len(lines) > 0:
            return lines
        return None
    
    def get_curr_snippet_num(self):
        return self.curr_snippet.curr_snippet_num
    
    def get_curr_timestamp(self):
        return self.curr_snippet.curr_timestamp
    
    def get_curr_utterances(self):
        return self.curr_snippet.curr_utterances
        
    
class SubsFileDirectory:
    
    def __init__(self, parent_dir='eng_friends_subs'):
        self.parent_dir = parent_dir
        self.init_filepathes()
        self.curr_subs_reader = None
        self.curr_file_idx = None
        self.gen = self._generator()
    
    def init_filepathes(self):
        self.subs_filepathes = []
        subs_dir = os.walk(self.parent_dir)
        # ignore folders pathes
        ignored = next(subs_dir)
        for path, _, filename_list  in subs_dir:
            for filename in filename_list:
                self.subs_filepathes.append(os.path.join(path, filename))
        self.subs_filepathes = natsorted(self.subs_filepathes)
        
    def __iter__(self):
        return self
    
    def __next__(self):
        return next(self.gen)
    
    def _generator(self):
        for i, filepath in enumerate(self.subs_filepathes):
            self.curr_subs_reader = SubtitlesReader(filepath)
            self.curr_file_idx = i
            yield self.curr_subs_reader
            
    def get_subs_filenames(self):
        return [os.path.basename(p) for p in self.subs_filepathes]
            
    def get_curr_filename(self):
        return os.path.basename(self.curr_subs_reader.filepath)