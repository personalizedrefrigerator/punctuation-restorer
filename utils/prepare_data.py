
import pathlib
import numpy as np
from enum import Enum

from utils.text_normalization import normalize_text, remove_punctuation_and_lowercase
from utils.labeling.char_labels import create_char_labels


class LabelMode(Enum):
    LetterTransforms = 1
    WordTransforms = 2


def load_file_data(dataPath: pathlib.Path, labelMode: LabelMode = LabelMode.LetterTransforms):
    text = normalize_text(dataPath.read_text('utf-8').strip())
    paragraphs = text.split(' [PAR] ')
    source = []
    dest = []
    for paragraph in paragraphs:
        # Avoid extremely short paragraphs -- these are likely to be less useful
        if len(paragraph.strip()) < 4:
            continue

        # Add an additional character to separate adjacent paragraphs (prevents
        # words from running together).
        paragraph += ' '

        normalized = remove_punctuation_and_lowercase(paragraph)

        # Extend both with a special "start of sequence" character:
        normalized = '~' + normalized
        paragraph = '~' + paragraph

        source.extend(normalized)

        if labelMode == LabelMode.LetterTransforms: # For the v1 notebook
            labels = create_char_labels(paragraph, normalized)
            assert labels.shape == (len(normalized),)
            dest.extend(labels)
        elif labelMode == LabelMode.WordTransforms: # For the v2 notebook
            dest.extend(paragraph)

    if labelMode == LabelMode.LetterTransforms:
        assert len(source) == len(dest)
    elif labelMode == LabelMode.WordTransforms:
        assert len(dest) > len(source) and len(source) > 0
    return source, dest # y, x

def load_data(dirPath: str, labelMode: LabelMode = LabelMode.LetterTransforms):
    path = pathlib.Path(dirPath)
    source, dest = [], []

    for path in path.iterdir():
        if not path.is_file() or not path.as_posix().endswith('.txt'):
            continue
        src, dst = load_file_data(path, labelMode)
        source.extend(src)
        dest.extend(dst)
    
    return np.array(source), np.array(dest)
