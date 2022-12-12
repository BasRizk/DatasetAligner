import os
from tqdm import tqdm
from dataset_utils import DatasetParser
from aligner.ds_sub_aligner import DSSubAligner
from aligner.sub_sub_aligner import SubSubAligner
from subtitles_utils.subtitles_reader import SubsFileDirectory

if __name__ == "__main__":

    subtitles_a_dir = 'subtitles/eng_friends_subs'
    subtitles_b_dir = 'subtitles/arab_friends_subs'

    data_dir_prefix = 'datasets/MELD/multi'
    generation_folder = f"datasets_generated/BI_{'_'.join(data_dir_prefix.split('/')[1:])}"
    if not os.path.exists(generation_folder):
        os.mkdir(generation_folder)
        
    org_dataset_filepaths = [
        # "EMORY_train.txt",
        # "EMORY_dev.txt",
        # "EMORY_test.txt",
        "MELD_dev.txt"
    ]
    
    data_columns=['speaker','utterance', 'emotion']
    dropped_data_columns=[]
    data_lines_to_skip=0
    
    if 'MELD' in data_dir_prefix:
        data_columns=['speaker','utterance', 'emotion', 'sentiment']
        dropped_data_columns=['sentiment']
        data_lines_to_skip=2

    successfull_matches = []

    for filename in org_dataset_filepaths:    
        success_convs_file =\
            open(f'{generation_folder}/{filename.split(".")[0]}_success.txt', mode='w', encoding='utf-8')
        failed_convs_file =\
            open(f'{generation_folder}/{filename.split(".")[0]}_failed.txt', mode='w')

        convs_list =\
            DatasetParser.read_dataset(
                os.path.join(data_dir_prefix, filename),
                columns=data_columns,
                dropped_columns=dropped_data_columns,
                lines_to_skip=data_lines_to_skip,
            )

        eng_subs_f_dir = SubsFileDirectory(subtitles_a_dir)
        arab_subs_f_dir = SubsFileDirectory(subtitles_b_dir)
        db_sub_aligner = DSSubAligner(eng_subs_f_dir)
        sub_sub_aligner = SubSubAligner(arab_subs_f_dir)
        
        for conv_df in tqdm(convs_list):
            is_match, conv_df, eng_sub_matches, msg =\
                db_sub_aligner.find_alignment(
                    conv_df, verbose=False, debug=False, thres=0.3
                )
            
            print('\nMessage:', msg)
            if is_match:
                sub_sub_matches =\
                    sub_sub_aligner.find_alignment(
                        eng_sub_matches, debug=False
                    )
                
                if sub_sub_matches is not None and len(sub_sub_matches) == len(conv_df):
                    DatasetParser.write_conv(
                        conv_df, success_convs_file,
                        translation=sub_sub_matches
                    )
                    continue
                print('Error Sub-Sub Matching')
                
            DatasetParser.write_conv(conv_df, failed_convs_file)
            # breakpoint()
            
        success_convs_file.close()
        failed_convs_file.close()
            