import os
from tqdm import tqdm
from dataset_utils import DatasetParser
from aligner.ds_sub_aligner import DSSubAligner
from aligner.sub_sub_aligner import SubSubAligner
from subtitles_utils.subtitles_reader import SubsFileDirectory

if __name__ == "__main__":
    data_dir_prefix = 'EMORY'
    org_dataset_filepaths = [
        # "EMORY_train.txt",
        # "EMORY_dev.txt",
        "EMORY_test.txt"
    ]
    
    successfull_matches = []

    for filename in org_dataset_filepaths:    
        success_convs_file =\
            open(f'GEN_EMORY/{filename.split(".")[0]}_success.txt', mode='w', encoding='utf-8')
        failed_convs_file =\
            open(f'GEN_EMORY/{filename.split(".")[0]}_failed.txt', mode='w')

        org_data_gen =\
            DatasetParser.read_dataset(os.path.join(data_dir_prefix, filename))
        eng_subs_f_dir = SubsFileDirectory('eng_friends_subs')
        arab_subs_f_dir = SubsFileDirectory('arab_friends_subs')
        db_sub_aligner = DSSubAligner(eng_subs_f_dir)
        sub_sub_aligner = SubSubAligner(arab_subs_f_dir)
        
        for conv_df in tqdm(org_data_gen):
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
            