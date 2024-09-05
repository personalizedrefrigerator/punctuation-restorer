
from data.process_data import process_data
from utils.text_normalization import normalize_text


if __name__ == '__main__':
	process_data(normalize=normalize_text)