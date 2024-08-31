
import re, pathlib
import numpy as np
from enum import Enum

# Matches the Project Gutenberg (TM) book start/end headers.
gutenbergHeaderExp = re.compile(r'[\n]\*\*\* (?:START|END) OF THE [^*]+\*\*\*[\n]')
spacesExp = re.compile(r'\s+')
paragraphBreakExp = re.compile(r'[\n]{2,}')
unsupportedCharactersExp = re.compile(r'[^a-z0-9ùúûüÿàâæçéèêëïîôœ \t\n!.,?/\-\']', re.IGNORECASE)
punctuationExp = re.compile(r'[!.,"?_/\-\']')

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
    text = unsupportedCharactersExp.sub(' ', text)
    text = paragraphBreakExp.sub(' [PAR] ', text)
    text = text.replace('\n', ' ')
    text = spacesExp.sub(' ', text)
    return text.strip()

def remove_punctuation_and_lowercase(text: str)->str:
    text = punctuationExp.sub('', text)
    text = text.lower()

    # Remove repeated spaces caused by the removal of punctuation
    return spacesExp.sub(' ', text)

class Operation(Enum):
    Copy = 0
    Capitalize = 1
    InsertAndAdvance = 2

def create_labels(original: str, normalized: str):
    output = []
    
    j = 0
    i = 0
    while i < len(normalized):
        c1 = normalized[i]
        c2 = original[j]
        if c1 == c2:
            output.append([ Operation.Copy, 'x' ])
            i += 1
            j += 1
        elif c1 == c2.lower():
            output.append([ Operation.Capitalize, 'x' ])
            i += 1
            j += 1
        else:
            to_insert = ''
            while c1 != c2.lower():
                to_insert += c2
                j += 1
                c2 = original[j]
            output.append([ Operation.InsertAndAdvance, to_insert[0] ])
            i += 1
            j += 1
    
    def to_np(entry):
        operation, character = entry
        assert len(character) == 1
        return np.array([ operation.value, character ])

    return np.array(list(map(to_np, output)))

def reconstruct_from_labels(normalized: str, labels):
    num_operations, _ = labels.shape
    result = []

    for i in range(num_operations):
        operation = Operation(int(labels[i, 0]))
        arg = labels[i, 1]
        char = normalized[i]

        if type (arg) == bytes:
            arg = arg.decode('utf-8')

        if operation == Operation.Copy:
            result.append(char)
        elif operation == Operation.Capitalize:
            result.append(str(char).upper())
        elif operation == Operation.InsertAndAdvance:
            result.append(arg)
            result.append(char)
        else:
            print('Unknown operation', operation)
    
    return ''.join(result)

def load_file_data(dataPath: pathlib.Path):
    text = preprocess_text(dataPath.read_text('utf-8'))
    paragraphs = text.split(' [PAR] ')
    source = []
    dest = []
    for paragraph in paragraphs:
        # Add an additional character to separate adjacent paragraphs (prevents
        # words from running together).
        paragraph += ' '

        normalized = remove_punctuation_and_lowercase(paragraph)

        # Extend both with a special "start of sequence" character:
        normalized = '~' + normalized
        paragraph = '~' + paragraph

        source.extend(normalized)

        labels = create_labels(paragraph, normalized)
        assert labels.shape[1] == 2
        assert labels.shape[0] == len(normalized)
        dest.extend(labels)

    assert len(source) == len(dest)

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
assert np.array_equal(
    create_labels('test', 'test'), np.array([[ Operation.Copy.value, 'x' ]] * 4)
), 'should create copy labels'
assert np.array_equal(
    create_labels('Test', 'test'),
    np.array([[Operation.Capitalize.value, 'x']] + [[ Operation.Copy.value, 'x' ]] * 3)
), 'should create capitalize labels'
assert np.array_equal(
    create_labels('.a', 'a'),
    np.array([[Operation.InsertAndAdvance.value, '.']])
), 'should create a simple insert label'
assert np.array_equal(
    create_labels('.a', 'a'),
    np.array([[Operation.InsertAndAdvance.value, '.']])
), 'should create a simple insert label'

def test_reconstruction(original: str, reconstructs_to: str):
    # Pad to allow trailing punctuation to be reconstructed
    # with "insert before" operations.
    original += ' '
    normalized = remove_punctuation_and_lowercase(original)
    labels = create_labels(original, normalized)

    applied = reconstruct_from_labels(normalized, labels)
    if applied.strip() != reconstructs_to:
        print('Reconstruction test: Got', applied, 'expected', reconstructs_to)
        assert False, "Reconstruction test failed"

test_reconstruction('test!', 'test!')
test_reconstruction('This is, a, TEST!', 'This is, a, TEST!')
test_reconstruction('Bob\'s posession. Lession?', 'Bob\'s posession. Lession?')
