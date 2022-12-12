# DatasetAligner
Generating variant of **TV-shows based labelled data-set** in **language B** from original dataset in **language A** based off **subtitles** files in both languages.

> The generation of this variant of the data-set is created based subtitles two consecutive alignments. First of which is between the given TV show based data-set (**e.g.** EmoryNLP based on FRIENDS), and **Subtitles A**, which is in the language of the data-set (**e.g.** English). The second alignment is based between **Subtitles A** matched windows, and **Subtitles B**, which is in a different language (**e.g.** Arabic).

## Instructions to Run
### `main.py`
Uses the configuration mentioned and utilized `aligner` modules `ds_sub_aligner` and `sub_sub_aligner` to find matchings for conversations and write them in `dataset_generated` folder.

#### Parameters:
  - `-subtitles_a_dir` Subtitles A Dir (Same language as Dataset); Gotta be in subtitles directory (default: `eng_friends_subs`)
  - `-subtitles_b_dir` Subtitles A Dir (Of language to be generated); Gotta be in subtitles directory (default: `arab_friends_subs`)
  - `-data_dir_prefix` Data Directory Prefix; Gotta be in datasets director (default: `EMORY`)
  - `-dataset_filenames` (default: `EMORY_train.txt EMORY_dev.txt EMORY_test.txt`)
  - `-data_columns` List of columns to generate based on the dataset (default: `speaker utterance emotion`) 
  - `-dropped_columns` List of columns to drop to fit the intent of this aligner (default: ``)
  - `-data_lines_to_skip` Num of lines to skip from the dataset file (default: `0`)
  - `-force_unicode` Force unicode over dataset files (default: `True`)
  - `-j` Num of threads to run concurrently (default: `os.cpu_count()-1`)

## Structure
- `aligner`
  - `ds_sub_aligner.py`: 
  > Responsible for finding matched windows based on best alignment score of the text of a conversation from Labeled Dataset with same language (A) subtitles.
  - `sub_sub_aligner.py`:
  > Responsible for finding matching text based on best alignments of matched windows found by `ds_sub_aligner.py` with language (B) subtitles lines. Alignments now here are solely based on overlapping timestamps with little cleaning around and that seem to do the job just fine.
- `subtitles_utils`
  - `subtitles_cut.py`
    - `SubTimestamp`: Subtitle Timestamp
    - `SubtitleSnippet`: Corresponds to a unit of Subtitles SRT files (Defined below)
    - `SubtitleWindow`: Stretchable unit to define and compare with text to compute best accuracy (Defined below).
  - `subtitles_reader.py`
    - `SubtitlesReader`: SRT Subtitle File Reader that goes over the file `SubtitleSnippet` at a time.
    - `SubsFileDirectory`: Subtitles Files Directory reader that goes through the files of a TV show by `SubtitlesReader`.


## Explanation
### Defined Units
Here is a list of the definitions of the defined units, employed in our methodology, and referred to in the explanation in the following subsections:

1. **Subtitle Snippet** is unit consisting of one or more than one line broken by line breaks, corresponding to what referred to as a line based on SubRip Subtitle file (SRT) format with a number and a starting and ending timestamps.

2. **Subtitle Window** is a grouping over some lines of one or more subtitles snippets, and it start and end timestamps are calculated based on the starting and ending snippets timestamps, relative to the amount of lines taken from them.

### Data-set-Subtitles Matching
We find alignments between the Labeled Data-set conversations with Subtitles A by finding the best matched subtitle window at a time iterating over the episodes SRT files. The windows size start at line level which is possibly a subset of a Snippet, and are allowed to grow as long as there is a matching based on heuristics and improvement in overall similarity score between this new larger version of the window, and original text. 

The heuristics taken into account are generally based on common similarity measurement metrics which are used in Automatic Speech Recognition evaluations such as Word Error Rates (WER), Match Error Rates (MER), and counts of insertions, deletions and substitutions using [JIWER](https://pypi.org/project/jiwer/) library. The reason behind that is that the nature of the problem observes the same obstacle faced in Speech Recognition, as some utterances might be intentionally, or mistakenly dropped by the human-translator in the subtitle or vice-versa, as possibly it was not clearly identified in the spoken conversation.

### Subtitles-Subtitles Alignment
Following obtaining the matching subtitle windows of a conversation in the labelled data-set achieved, those windows are aligned on the basis of timestamps overlaps with a practical experimental threshold set at $0.25$ seconds overlap. 

