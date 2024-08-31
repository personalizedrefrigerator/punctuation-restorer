
import re, pathlib
import numpy as np

# Matches the Project Gutenberg (TM) book start/end headers.
gutenbergHeaderExp = re.compile(r'[\n]\*\*\* (?:START|END) OF THE [^*]+\*\*\*[\n]')
spacesExp = re.compile(r'\s+')
paragraphBreakExp = re.compile(r'[\n]{2,}')
unsupportedCharactersExp = re.compile(r'[^a-z0-9ùúûüÿàâæçéèêëïîôœ \t\n!.,?_/-]', re.IGNORECASE)
punctuationExp = re.compile(r'[!.,"?_/-]')

def preprocess_text(text: str)->str:
    # Remove metadata
    metadataSplit = gutenbergHeaderExp.split(text)
    if len(metadataSplit) == 3:
        text = metadataSplit[1]

    text = text.replace('“', '"')
    text = text.replace('’', '\'')
    text = text.replace('”', '"')
    text = text.replace('«', '"')
    text = text.replace('»', '"')
    # Some books use -- at the start of a line to start quotes (e.g. "Le Comte De Monte Cristo")
    text = text.replace('\n--', '\n"')
    text = unsupportedCharactersExp.sub('', text)
    text = paragraphBreakExp.sub(' [PAR] ', text)
    text = text.replace('\n', ' ')
    text = spacesExp.sub(' ', text)
    return text.strip()

def remove_punctuation_and_lowercase(text: str)->str:
    text = punctuationExp.sub(' ', text)
    text = text.lower()

    # Remove repeated spaces caused by the removal of punctuation
    return spacesExp.sub(' ', text).strip()

def load_file_data(dataPath: pathlib.Path):
    text = preprocess_text(dataPath.read_text('utf-8'))
    paragraphs = text.split(' [PAR] ')
    source = paragraphs
    dest = map(remove_punctuation_and_lowercase, paragraphs)

    return source, dest # y, x

def load_data(dirPath: str):
    path = pathlib.Path(dirPath)
    source, dest = [], []

    for path in path.iterdir():
        if not path.is_file() or not path.as_posix().endswith('.txt'):
            continue
        src, dst = load_file_data(path)
        source.extend(src)
        dest.extend(dst)
    
    return np.array(source), np.array(dest)

##
## Tests
##

assert preprocess_text('test') == 'test', 'should preprocess a single word'
assert preprocess_text('test thing') == 'test thing', 'should preserve spaces'
assert preprocess_text('test thing') == 'test thing', 'should preserve spaces'
assert preprocess_text('Test thing?') == 'Test thing?', 'should preserve punctuation'
assert preprocess_text('Test thing?\nTest...\nTest.') == 'Test thing? Test... Test.', 'should replace newlines'
assert preprocess_text('Test thing?\n\nTest...\n\n\n\nTEST.') == 'Test thing? [PAR] Test... [PAR] TEST.', 'should replace double newlines'
assert preprocess_text('Test\n*** START OF THE TEST BOOK ***\n\nTest\n\n*** END OF THE TEST BOOK ***\n\n End') == 'Test'
assert remove_punctuation_and_lowercase('Test thing? Test -- ha!') == 'test thing test ha', 'should remove punctuation'
