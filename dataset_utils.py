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
                        yield df
                        break 
        print('Finished file')
    
    @staticmethod
    def write_conv(conv_df, file, columns=['speaker', 'utterance', 'emotion']):
        for _, row in conv_df[columns].iterrows():
            file.write("\t".join(row) + "\n")
        file.write('\n')
        file.flush()