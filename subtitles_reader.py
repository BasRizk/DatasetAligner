import os
from natsort import natsorted

class SubtitleSnippet:
    def __init__(self, num, ts, utts):
        self.curr_snippet_num = num
        self.curr_timestamp = ts
        self.curr_utterances = utts
    
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
            self.curr_snippet =\
                SubtitleSnippet(lines[0], lines[1], lines[2:])
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