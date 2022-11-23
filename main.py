import os
from subtitles_reader import SubtitlesReader, SubsFileDirectory
from dataset_utils import DatasetTextGenerator
from align_utils import get_text_start_point        

if __name__ == "__main__":
    data_dir_prefix = 'CoMPM\dataset\EMORY'
    org_dataset_filepaths = [
        "EMORY_train copy.txt", "EMORY_dev.txt", "EMORY_test.txt"
    ]
    
    out_file = open('sample.out', mode='w')
    for filepath in org_dataset_filepaths:
        org_data_gen =\
            DatasetTextGenerator(os.path.join(data_dir_prefix, filepath))
        subs_f_dir = SubsFileDirectory('eng_friends_subs')
        
        verbose = False
        for i, text in org_data_gen:
            print('orig: ', text)
            # if 'absolutely' in text.lower():
            verbose = True
            match =\
                get_text_start_point(
                    subs_f_dir,
                    text,
                    verbose=verbose
                )
            # verbose = False
            print('=> orig: ', text)
            print('=> match:', match)
            out_file.write(text + '\n')
            out_file.write(match + '\n\n')
            out_file.flush()
            
            # breakpoint()
        out_file.close()
            