import os
from subtitles_reader import SubtitlesReader, SubsFileDirectory
from dataset_utils import DatasetParser
from align_utils import Aligner        

if __name__ == "__main__":
    data_dir_prefix = 'CoMPM\dataset\EMORY'
    org_dataset_filepaths = [
        "EMORY_train copy.txt", "EMORY_dev.txt", "EMORY_test.txt"
    ]
    
    for filepath in org_dataset_filepaths:
        org_data_gen =\
            DatasetParser.read_dataset(os.path.join(data_dir_prefix, filepath))
        subs_f_dir = SubsFileDirectory('eng_friends_subs')
        aligner = Aligner(subs_f_dir)
                
        for conv_df in org_data_gen:
            matched_subs = aligner.find_alignment(conv_df)
            # TODO save matched subs snips

        # out_file.close()
            