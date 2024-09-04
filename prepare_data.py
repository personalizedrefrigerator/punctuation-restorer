
import re, pathlib
import numpy as np
from enum import Enum

# Matches the Project Gutenberg (TM) book start/end headers.
gutenbergHeaderExp = re.compile(r'[\n]+\*\*\* (?:START|END) OF THE [^*]+\*\*\*[\n]+')
spacesExp = re.compile(r'\s+')
paragraphBreakExp = re.compile(r'[\n]{2,}')
unsupportedCharactersExp = re.compile(r'[^a-z0-9ùúûüÿàâæçéèêëïîôœ \t\n.,?\-\':]', re.IGNORECASE)
punctuationExp = re.compile(r'[.,?\-\':]')

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

OPERATION_COPY = '1'
OPERATION_CAPITALIZE = '2'

def create_labels(original: str, normalized: str):
    output = []
    
    j = 0
    i = 0
    while i < len(normalized):
        c1 = normalized[i]
        c2 = original[j]
        if c1 == c2:
            output.append(OPERATION_COPY)
            i += 1
            j += 1
        elif c1 == c2.lower():
            output.append(OPERATION_CAPITALIZE)
            i += 1
            j += 1
        else:
            to_insert = ''
            while c1 != c2.lower():
                to_insert += c2
                j += 1
                c2 = original[j]
            output.append(to_insert[0])
            i += 1
            j += 1

    return np.array(output)

def reconstruct_from_labels(normalized: str, labels):
    num_operations, = labels.shape
    result = []

    for i in range(num_operations):
        operation = labels[i]
        char = normalized[i]

        if type (operation) == bytes:
            operation = operation.decode('utf-8')
        if type (char) == bytes:
            char = char.decode('utf-8')

        if operation == OPERATION_COPY:
            result.append(char)
        elif operation == OPERATION_CAPITALIZE:
            result.append(str(char).upper())
        else:
            result.append(operation)
            result.append(char)
    
    return ''.join(result)

def load_file_data(dataPath: pathlib.Path, labelMode: int = 1):
    text = preprocess_text(dataPath.read_text('utf-8').strip())
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

        if labelMode == 1: # For the v1 notebook
            labels = create_labels(paragraph, normalized)
            assert labels.shape == (len(normalized),)
            dest.extend(labels)
        elif labelMode == 2: # For the v2 notebook
            dest.extend(paragraph)

    if labelMode == 1:
        assert len(source) == len(dest)
    elif labelMode == 2:
        assert len(dest) > len(source) and len(source) > 0
    return source, dest # y, x

def load_data(dirPath: str, labelMode: int = 1):
    path = pathlib.Path(dirPath)
    source, dest = [], []

    for path in path.iterdir():
        if not path.is_file() or not path.as_posix().endswith('.txt'):
            continue
        src, dst = load_file_data(path, labelMode)
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
assert remove_punctuation_and_lowercase('Test thing? Test -- ha.') == 'test thing test ha', 'should remove punctuation'
assert np.array_equal(
    create_labels('test', 'test'), np.array([OPERATION_COPY] * 4)
), 'should create copy labels'
assert np.array_equal(
    create_labels('Test', 'test'),
    np.array([OPERATION_CAPITALIZE] + [OPERATION_COPY] * 3)
), 'should create capitalize labels'
assert np.array_equal(
    create_labels('.a', 'a'),
    np.array(['.'])
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
