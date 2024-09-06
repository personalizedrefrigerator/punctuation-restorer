import re

# Matches the Project Gutenberg (TM) book start/end headers.
gutenbergHeaderExp = re.compile(r'[\n]+\*\*\* (?:START|END) OF THE [^*]+\*\*\*[\n]+')
spacesExp = re.compile(r'\s+')
paragraphBreakExp = re.compile(r'[\n]{2,}')
repeatedDashExp = re.compile(r'[-]{2,}')
unsupportedCharactersExp = re.compile(r'[^a-z0-9ùúûüÿàâæçéèêëïîôœ \t\n.,?!\-\':;]', re.IGNORECASE)
punctuationExp = re.compile(r'[.,?!\-\':;]')

def normalize_text(text: str, par_separator: str = ' [PAR] ')->str:
    """
    Replaces unsupported and unusual characters and collapses paragraphs in [text].
    The [par_separator] parameter is used as a replacement for paragraphs.
    """
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
    text = repeatedDashExp.sub('--', text)
    
	# Handle newlines and paragraphs
    par_temp_replacement = '[PARAGRAPH BREAK]'
    
    text = paragraphBreakExp.sub(par_temp_replacement, text)
    text = text.replace('\n', ' ')
    text = spacesExp.sub(' ', text)
    
    text = text.replace(par_temp_replacement, par_separator)
    return text.strip()

def remove_punctuation_and_lowercase(text: str)->str:
    text = punctuationExp.sub('', text)
    text = text.lower()

    # Remove repeated spaces caused by the removal of punctuation
    return spacesExp.sub(' ', text)


##
## Tests
##

assert normalize_text('test') == 'test', 'should preprocess a single word'
assert normalize_text('test thing') == 'test thing', 'should preserve spaces'
assert normalize_text('test thing') == 'test thing', 'should preserve spaces'
assert normalize_text('Test thing?') == 'Test thing?', 'should preserve punctuation'
assert normalize_text('Test thing?\nTest...\nTest.') == 'Test thing? Test... Test.', 'should replace newlines'
assert normalize_text('Test thing?\n\nTest...\n\n\n\nTEST.') == 'Test thing? [PAR] Test... [PAR] TEST.', 'should replace double newlines'
assert normalize_text('Test\n*** START OF THE TEST BOOK ***\n\nTest\n\n*** END OF THE TEST BOOK ***\n\n End') == 'Test'
assert remove_punctuation_and_lowercase('Test thing? Test -- ha.') == 'test thing test ha', 'should remove punctuation'
