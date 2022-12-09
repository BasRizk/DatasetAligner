import os

from tqdm import tqdm
from dataset_utils import DatasetParser, pd
from aligner.ds_sub_aligner import DSSubAligner
from aligner.sub_sub_aligner import SubSubAligner
from subtitles_utils.subtitles_reader import SubsFileDirectory
from joblib import Parallel, delayed, parallel_backend


def split_into_batches(conversations, n_batches):
    offset = int(len(conversations)/n_batches)
    batches = []
    for batch_i in range(n_batches):
        batches.append(conversations[offset*batch_i:offset*batch_i+1])
    return batches
    
def find_save_conv_match(
        conv_df: pd.DataFrame,
        db_sub_aligner: DSSubAligner,
        sub_sub_aligner: SubSubAligner,
        success_convs_file, failed_convs_file,
        progress_bar: tqdm
    ):
    org_size = len(conv_df)
    is_match, conv_df, eng_sub_matches, msg =\
                db_sub_aligner.find_alignment(
                    conv_df, verbose=False, debug=False, thres=0.3
                )
    print('\nMessage:', msg)
    # At least 4 utterances long translation to add to dataset
    if is_match and len(conv_df) >= 4:
        sub_sub_matches =\
            sub_sub_aligner.find_alignment(
                eng_sub_matches, debug=False
            )
            
        # breakpoint()
        if sub_sub_matches is not None and len(sub_sub_matches) == len(conv_df):
            DatasetParser.write_conv(conv_df, success_convs_file, translation=sub_sub_matches)
            return
        print('Error Sub-Sub Matching')
        
    DatasetParser.write_conv(conv_df, failed_convs_file)
    progress_bar.update(1)
    
if __name__ == "__main__":
    data_dir_prefix = 'EMORY'
    org_dataset_filepaths = [
        # "EMORY_train.txt",
        "EMORY_dev.txt", 
        "EMORY_test.txt"
    ]
    
    n_jobs = os.cpu_count()
      
    for filename in org_dataset_filepaths:    
        org_data_gen = DatasetParser.read_dataset(os.path.join(data_dir_prefix, filename))

        success_convs_files = []
        failed_convs_files = []
        eng_subs_f_dirs = []
        arab_subs_f_dirs = []
        db_sub_aligners = []
        sub_sub_aligners = []
        
        for i in tqdm(range(n_jobs), desc='Init Generator and Aligners for parallel processes'):
            success_convs_files.append(
                open(f'GEN_EMORY/{filename.split(".")[0]}_success_batch_{i}.txt',
                    mode='w', encoding='utf-8')
            )
            failed_convs_files.append(
                open(f'GEN_EMORY/{filename.split(".")[0]}_failed_batch_{i}.txt', mode='w')
            )
            eng_subs_f_dirs.append(SubsFileDirectory('eng_friends_subs'))
            db_sub_aligners.append(DSSubAligner(eng_subs_f_dirs[-1]))
            arab_subs_f_dirs.append(SubsFileDirectory('arab_friends_subs'))
            sub_sub_aligners.append(SubSubAligner(arab_subs_f_dirs[-1]))
        
        pbar = tqdm('Conversations', total=len(org_data_gen))
        
            
        with parallel_backend('threading', n_jobs=2):
            executor = Parallel(require='sharedmem')
            tasks = (
                delayed(find_save_conv_match)(
                    conv_df,
                    db_sub_aligners[batch_i],
                    sub_sub_aligners[batch_i],
                    success_convs_files[batch_i],
                    failed_convs_files[batch_i],
                    pbar
                ) for batch_i, batch in enumerate(
                    split_into_batches(org_data_gen, n_jobs)
                ) for conv_df in batch
            )
            executor(tasks)
            
        for f in failed_convs_files + success_convs_files:
            f.close()
            