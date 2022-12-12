import unidecode
import pandas as pd

class DatasetParser:
    
    @staticmethod
    def split_line(file):
        line =  file.readline().strip()
        if line:
            return line.split("\t")
        return line
    
    @staticmethod
    def read_dataset(
        filepath, 
        columns=['speaker','utterance', 'emotion'],
        dropped_columns=[],
        lines_to_skip=0,
        force_unicode=True,
    ): 

        dfs = []       
        with open(filepath, encoding='utf-8') as file:
            for _ in range(lines_to_skip):
                file.readline()
                
            while True:
                line = DatasetParser.split_line(file)
                if not line:
                    # File is over
                    break
                dialog = []
                while(True):
                    if force_unicode:
                        line = [unidecode.unidecode(t) for t in line]
                    dialog.append(line)
                    line = DatasetParser.split_line(file)
                    if not line:
                        df = pd.DataFrame(
                                dialog, 
                                columns=columns
                            )
                        if dropped_columns:
                            df = df.drop(dropped_columns, axis=1)
                        dfs.append(df)
                        break 
        return dfs
    
    @staticmethod
    def write_conv(conv_df, file, columns=['speaker', 'utterance', 'emotion'], translation=None):
        if translation:
            conv_df['translation'] = translation
            columns=['speaker', 'utterance', 'translation', 'emotion']
            
        lines = ''
        for _, row in conv_df[columns].iterrows():
            lines += "\t".join(row) + "\n"
        lines += '\n'
        file.write(lines)
        file.flush()