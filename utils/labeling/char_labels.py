import numpy as np

from utils.text_normalization import remove_punctuation_and_lowercase

OPERATION_COPY = '1'
OPERATION_CAPITALIZE = '2'

def create_char_labels(original: str, normalized: str):
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

def reconstruct_from_char_labels(normalized: str, labels):
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


##
## Tests
##

assert np.array_equal(
    create_char_labels('test', 'test'), np.array([OPERATION_COPY] * 4)
), 'should create copy labels'
assert np.array_equal(
    create_char_labels('Test', 'test'),
    np.array([OPERATION_CAPITALIZE] + [OPERATION_COPY] * 3)
), 'should create capitalize labels'
assert np.array_equal(
    create_char_labels('.a', 'a'),
    np.array(['.'])
), 'should create a simple insert label'


def test_reconstruction(original: str, reconstructs_to: str):
    # Pad to allow trailing punctuation to be reconstructed
    # with "insert before" operations.
    original += ' '
    normalized = remove_punctuation_and_lowercase(original)
    labels = create_char_labels(original, normalized)

    applied = reconstruct_from_char_labels(normalized, labels)
    if applied.strip() != reconstructs_to:
        print('Reconstruction test: Got', applied, 'expected', reconstructs_to)
        assert False, "Reconstruction test failed"

test_reconstruction('test!', 'test!')
test_reconstruction('This is, a, TEST!', 'This is, a, TEST!')
test_reconstruction('Bob\'s posession. Lession?', 'Bob\'s posession. Lession?')
