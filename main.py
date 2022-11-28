import os
from dataset_utils import DatasetParser
from ds_sub_aligner import DSSubAligner
from sub_sub_aligner import SubSubAligner
from subtitles_utils.subtitles_reader import SubsFileDirectory

if __name__ == "__main__":
    data_dir_prefix = 'CoMPM\dataset\EMORY'
    org_dataset_filepaths = [
        "EMORY_train copy.txt",
        # "EMORY_dev.txt", "EMORY_test.txt"
    ]
    
    successfull_matches = []

    for filename in org_dataset_filepaths:    
        trans_convs_file = open(f'{filename.split(".")[0]}_success.txt', mode='w', encoding='utf-8')
        failed_convs_file = open(f'{filename.split(".")[0]}_failed.txt', mode='w')

        org_data_gen =\
            DatasetParser.read_dataset(os.path.join(data_dir_prefix, filename))
        eng_subs_f_dir = SubsFileDirectory('eng_friends_subs')
        arab_subs_f_dir = SubsFileDirectory('arab_friends_subs')
        db_sub_aligner = DSSubAligner(eng_subs_f_dir)
        sub_sub_aligner = SubSubAligner(arab_subs_f_dir)
        
        next(org_data_gen)
        next(org_data_gen)
        next(org_data_gen)
    
        for conv_df in org_data_gen:
            is_match, conv_df, eng_sub_matches, msg =\
                db_sub_aligner.find_alignment(
                    conv_df, verbose=False, debug=True, thres=0.2
                )
                
            print('Message:', msg)
            if is_match:
                sub_sub_matches =\
                    sub_sub_aligner.find_alignment(
                        eng_sub_matches, debug=False
                    )
                
                if sub_sub_matches:
                    DatasetParser.write_conv(
                        conv_df, trans_convs_file,
                        translation=sub_sub_matches
                    )
                    continue
                print('Error Sub-Sub Matching')
                
            DatasetParser.write_conv(conv_df, failed_convs_file)
            breakpoint()
            
        failed_convs_file.close()
            