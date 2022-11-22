import os
from subtitles_reader import SubtitlesReader, SubsFileDirectory
from dataset_utils import DatasetTextGenerator
from align_utils import get_text_start_point        

if __name__ == "__main__":
    data_dir_prefix = 'CoMPM\dataset\EMORY'
    org_dataset_filepaths = [
        "EMORY_train.txt", "EMORY_dev.txt", "EMORY_test.txt"
    ]
    
    for filepath in org_dataset_filepaths:
        org_data_gen =\
            DatasetTextGenerator(os.path.join(data_dir_prefix, filepath))
        subs_f_dir = SubsFileDirectory('eng_friends_subs')
        
        for i, text in org_data_gen:
            subsfile_reader =\
                get_text_start_point(
                    subs_f_dir,
                    text
                )
            print(text)
            breakpoint()
            