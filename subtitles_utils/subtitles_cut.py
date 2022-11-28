import re
from typing import TypeVar, Type
from datetime import datetime
from typing import List
from .utils import prepare_txt

TIMECODE_PATTERN =\
    r'(\d{2}):(\d{2}):(\d{2}),(\d+) --> (\d{2}):(\d{2}):(\d{2}),(\d+)'
TIMESTAMP_FORMAT = "%H:%M:%S,%f"

class SubTimestamp:    
    #hours:minutes:seconds,milliseconds
    def __init__(self, subtitle_timecode=None, start_dt=None, end_dt=None):
        if subtitle_timecode:
            tss = re.search(TIMECODE_PATTERN, subtitle_timecode)
            self.start = self._create_dt(tss.group(1, 2, 3, 4))
            self.end = self._create_dt(tss.group(5, 6, 7, 8))
        else:
            self.start = start_dt
            self.end = end_dt
    
    def _create_dt(self, h_m_s_ms_tuple):
        timestamp_tuple = list(map(int, h_m_s_ms_tuple))
        return datetime(1, 1, 1, *timestamp_tuple)
    
    def __str__(self) -> str:
        return f'{self.start.strftime(TIMESTAMP_FORMAT)}' +\
            f' ---> {self.end.strftime(TIMESTAMP_FORMAT)}'
        
    def get_start(self):
        return self.start
    
    def get_end(self):
        return self.end
    
    def get_width(self):
        return self.end - self.start
    
    def __lt__(self, __o: object) -> bool:
        return (self.end < __o.start)

    def __gt__(self, __o: object) -> bool:
        return(self.start > __o.end)
    
    def __eq__(self, __o: object) -> bool:
        return self.start == __o.start and self.end == __o.end
    
    def __ne__(self, __o: object) -> bool:
        return not(self.__eq__(self, __o))
    
    def is_overlaping(self, __o: object) -> bool:
        return not self < __o and not self > __o
            
            
    
# Create a generic variable that can be 'Parent', or any subclass.
SubtitleWindow = TypeVar('SubtitleWindow', bound='SubtitleWindow')

class SubtitleSnippet:
    def __init__(self, episode_title, num, timecode, utterances):
        self.episode_title = episode_title
        self.id = num
        self.timestamp = SubTimestamp(subtitle_timecode=timecode)
        self.utts = utterances
        self.windows = self._calc_possible_utt_windows()
        self.bwins, self.ewins = self._get_begin_end_wins()
        
    def get_id(self):
        return self.id
    
    def get_timestamp(self):
        return self.timestamp
    
    def __str__(self):
        return f'{self.id}\n' +\
            f'{str(self.timestamp)}\n' +\
            "\n".join(prepare_txt(self.utts))
    
    def __repr__(self) -> str:
        return f'\nSubtitleSnippet\n{self.__str__()}\n'
    
    def __contains__(self, item: str):
        return item.lower() in ' '.join(self.utts).lower()
    
    def __len__(self):
        return len(self.utts)
    
    def _calc_possible_utt_windows(self):
        wins = []
        for i in range(len(self)):
            for k in range(i + 1, len(self) + 1):
                utt = ' '.join(self.utts[i:k])
                # s_snip, e_snip, sline_idx, eline_idx, utt
                wins.append(
                    SubtitleWindow([self], i, k-1, utt)
                )
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

    def is_overlaping(self, __o:object):
        return self.timestamp.is_overlaping(__o.timestamp)

SnippetsList = List[SubtitleSnippet]

class SubtitleWindow:
    def __init__(self, 
                 snippets: SnippetsList,
                 s_line_idx, e_line_idx, 
                 utt):
        self.snippets = snippets
        self.id = [s.id for s in self.snippets]
        self.ss = snippets[0]
        self.es = snippets[-1]
        self.sline = s_line_idx
        self.eline = e_line_idx
        self.num_lines = self._calc_num_lines()
        self.timestamp = self._calc_normal_timestamp()
        self.org_u = utt
        self.u = utt
        
    def _calc_normal_timestamp(self):
        def _portion(snippet: SubtitleSnippet, ratio):
            ts = snippet.get_timestamp()
            return ts.start + ts.get_width()*ratio
        ss = _portion(self.ss, self.sline/len(self.ss))
        es = _portion(self.es, ((self.eline + 1)/len(self.es)))
        return SubTimestamp(start_dt=ss, end_dt=es)

    def __len__(self):
        return self.num_lines
    
    def __str__(self):
        res =\
            f'TIME:       {self.timestamp} with {self.num_lines} line(s)\n' +\
            f'From line   ({self.sline})  @  snippet ({self.ss.get_id()})\n' +\
            f'To   line   ({self.eline})  @  snippet ({self.es.get_id()})\n' +\
            f'Org-Utt:    {prepare_txt(self.org_u)}\n'
        if self.org_u != self.u:
            res += f'Trans-Utt:  {prepare_txt(self.u)}\n'
        return res
    
    def __repr__(self) -> str:
        return f'\nSubtitleWindow\n{self.__str__()}\n'
    
    def __add__(self, sub_win: Type[SubtitleWindow]):
        # ensure no errs, and snippets are consecutive
        assert self.es.get_id() == sub_win.ss.get_id() - 1
        return SubtitleWindow(
            self.snippets + sub_win.snippets, 
            self.sline, sub_win.eline,
            f'{self.u} {sub_win.u}'.strip()
        )
        
    def is_starting(self):
        return self.sline == 0
    
    def is_ending(self):
        return self.eline == len(self.es) - 1
    
    def apply(self, func):
        self.u = func(self.u)
    
    def _calc_num_lines(self):
        # Sum of lines except:
        # - # lines left before sline
        # - # lines left after the eline from es
        return sum(map(len, self.snippets)) -\
                self.sline -\
                (len(self.es) - (self.eline + 1))
            
    def is_overlaping(self, __o:object):
        return self.timestamp.is_overlaping(__o.timestamp)