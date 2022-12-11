import os
import time
import queue
import threading
from tqdm import tqdm
from dataset_utils import DatasetParser, pd
from aligner.ds_sub_aligner import DSSubAligner
from aligner.sub_sub_aligner import SubSubAligner
from subtitles_utils.subtitles_reader import SubsFileDirectory


n_jobs = 4
write_thread_lock = threading.Lock()
tools_queue_lock = threading.Lock()
align_tools_queue = queue.Queue(n_jobs)

class AlignTools:
    def __init__(self):
        self.eng_subs_f_dir = SubsFileDirectory('eng_friends_subs')
        self.db_sub_aligner = DSSubAligner(self.eng_subs_f_dir)
        self.arab_subs_f_dir = SubsFileDirectory('arab_friends_subs')
        self.sub_sub_aligner = SubSubAligner(self.arab_subs_f_dir)
        
    def find_db_sub_alignment(self, conv_df, verbose, debug, thres):
        return self.db_sub_aligner.find_alignment(
            conv_df, verbose=verbose, debug=debug, thres=thres
        )
    
    def find_sub_sub_alignment(self, eng_sub_matches, debug):
        return self.sub_sub_aligner.find_alignment(
            eng_sub_matches, debug=debug
        )              
        
class AligningThread(threading.Thread):
    def __init__(self, threadID, 
            conv_df: pd.DataFrame,
            success_convs_file, failed_convs_file,
            progress_bar: tqdm
        ):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.conv_df = conv_df
        self.success_convs_file = success_convs_file
        self.failed_convs_file = failed_convs_file
        self.pbar = progress_bar
      
    def run(self):
        self.find_save_conv_match()
    
    def obtain_tools(self):
        while True:
            tools_queue_lock.acquire()
            if not align_tools_queue.empty():
                tools = align_tools_queue.get()
                tools_queue_lock.release()
                break
            tools_queue_lock.release()
            time.sleep(2)
        return tools
    
    def return_tools(self, tools):
        tools_queue_lock.acquire()    
        align_tools_queue.put(tools)
        tools_queue_lock.release()
        return True
        
    def find_save_conv_match(self):
        tools = self.obtain_tools()
        retured_tools = False
    
        # org_size = len(self.conv_df)
        is_match, conv_df, eng_sub_matches, msg =\
            tools.find_db_sub_alignment(
                self.conv_df, verbose=False, debug=False, thres=0.3
            )
        
        write_thread_lock.acquire()
        print('\nMessage:', msg)
        write_thread_lock.release()
        
        # At least 4 utterances long translation to add to dataset
        if is_match and len(conv_df) >= 4:
            sub_sub_matches =\
                tools.find_sub_sub_alignment(
                    eng_sub_matches, debug=False
                )   
            retured_tools = self.return_tools(tools)

            if sub_sub_matches is not None and len(sub_sub_matches) == len(conv_df):
                write_thread_lock.acquire()
                DatasetParser.write_conv(conv_df, self.success_convs_file, translation=sub_sub_matches)
                self.pbar.update(1)
                write_thread_lock.release()
                return
                
            write_thread_lock.acquire()
            print('Error Sub-Sub Matching')
            write_thread_lock.release()
        
        if not retured_tools:
            self.return_tools(tools)
            
        write_thread_lock.acquire()
        DatasetParser.write_conv(self.conv_df, self.failed_convs_file)
        self.pbar.update(1)
        write_thread_lock.release()


if __name__ == "__main__":
    data_dir_prefix = 'EMORY'
    org_dataset_filepaths = [
        "EMORY_train.txt",
        "EMORY_dev.txt", 
        "EMORY_test.txt"
    ]
    
    for i in tqdm(range(n_jobs), desc='Init AlignTools'):
        align_tools_queue.put_nowait(AlignTools())
    
    for filename in org_dataset_filepaths:    
        convs_list = DatasetParser.read_dataset(os.path.join(data_dir_prefix, filename))

        success_convs_file =\
            open(f'GEN_EMORY/{filename.split(".")[0]}_success.txt',
                    mode='w', encoding='utf-8')
        failed_convs_file =\
            open(f'GEN_EMORY/{filename.split(".")[0]}_failed.txt', mode='w')
            
        pbar = tqdm('Conversations', total=len(convs_list))
        
        threads = [
            AligningThread(i, conv_df, success_convs_file, failed_convs_file, pbar)
            for i, conv_df in enumerate(convs_list)
        ]
        for t in threads:
            t.start()
            
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        success_convs_file.close()
        failed_convs_file.close()
            