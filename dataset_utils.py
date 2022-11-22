import pandas as pd

def DatasetTextGenerator(filepath):
    org_df = pd.read_csv(
        filepath, delimiter='\t',
        names=['speaker', 'utterance', 'class']
    )
    
    for i, utterance in org_df['utterance'].iteritems():
        yield i, utterance