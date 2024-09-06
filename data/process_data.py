from collections.abc import Callable
from pathlib import Path
import os, re

spaces_exp = re.compile(r'\s+')
def word_count(text: str):
	return len(spaces_exp.split(text))

def split_long_paragraphs(text: str):
	paragraphs = text.split('\n')
	result = []

	for paragraph in paragraphs:
		max_paragraph_length = 64
		if word_count(paragraph) > max_paragraph_length:
			sentences = paragraph.split('. ')
			prev_sentence = None
			for sentence in sentences:
				if len(sentence.strip()) == 0:
					continue
				if not sentence.endswith(('.', '?', ':')):
					sentence += '. '

				if prev_sentence and word_count(sentence) + word_count(prev_sentence) < max_paragraph_length:
					result.pop()
					new_sentence = prev_sentence + sentence
					result.append(new_sentence)
					prev_sentence = new_sentence
				else:
					words = sentence.split(' ')
					for i in range(0, len(words), max_paragraph_length):
						current = ' '.join(words[i:i+max_paragraph_length])
						result.append(current)
						prev_sentence = current
		else:
			result.append(paragraph)
	return result

chapter_exp = re.compile(r'^.{0,3}(chapter|vol\.|part) [0-9IX]', re.IGNORECASE)
def filter_chapter_headings(text: list[str]):
	def is_body_paragraph(paragraph: str):
		paragraph = paragraph.strip().lower()
		return not chapter_exp.match(paragraph)
	return list(filter(is_body_paragraph, text))

def process_data(normalize: Callable[[str, str], str])->None:
	"""
		Processes the data present in /data/processed and outputs to /data/raw.
		[normalize] should be a function that accepts two arguments:
		- text (str): The text to normalize
		- paragraph_break (str): What to use as a paragraph break.
	"""
	data_dir_path = Path(__file__).parent
	raw_data_path = data_dir_path / 'raw'
	processed_data_path = data_dir_path / 'processed'

	print('[....] Clearing processed data...', end='', flush=True)
	for root, _, files in os.walk(processed_data_path):
		root = Path(root)
		assert root.is_absolute()

		for name in files:
			file_path = root / name
			assert file_path.name.endswith('.txt'), 'Should only delete .txt files'
			file_path.unlink()
	
	print('\r[DONE]')

	print('[....] Processing data...', end='', flush=True)

	for root, dirs, files in os.walk(raw_data_path):
		root = Path(root)
		assert root.is_absolute()
		
		for name in files:
			file_path = root / name

			rel_path = file_path.relative_to(raw_data_path)
			target_path = processed_data_path / rel_path
			assert not target_path.exists()

			processed = '\n'.join(
				filter_chapter_headings(
					split_long_paragraphs(normalize(file_path.read_text('utf-8'), '\n'))
				)
			)
			target_path.write_text(processed, 'utf-8')

		for name in dirs:
			dir_path = root / name
			rel_path = dir_path.relative_to(raw_data_path)
			target_path = processed_data_path / rel_path

			if not target_path.exists():
				target_path.mkdir()

	print('\r[DONE]')

