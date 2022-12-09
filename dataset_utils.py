import pandas as pd
    
class DatasetParser:
    
    @staticmethod
    def split_line(file):
        line =  file.readline().strip()
        if line:
            return line.split("\t")
        return line
    
    @staticmethod
    def read_dataset(filepath): 
        dfs = []       
        with open(filepath) as file:
            while True:
                line = DatasetParser.split_line(file)
                if not line:
                    # File is over
                    break
                dialog = []
                while(True):
                    dialog.append(line)
                    line = DatasetParser.split_line(file)
                    if not line:
                        df = pd.DataFrame(
                                dialog, 
                                columns=['speaker','utterance', 'emotion']
                            )
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