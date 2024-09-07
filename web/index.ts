import { InferenceSession, Tensor, TypedTensor } from 'onnxruntime-web';
import wordEncodings from './wordEncodings';

const punctuationExp = /[?.:,\-'!;]/g;
const unsupportedCharactersExp = /[^a-z0-9ùúûüÿàâæçéèêëïîôœ .,?!\-\':;]/ig;

const wordToId = new Map<string, number>();
const idToWord = new Map<number, string>();
for (const [id, word] of Object.entries(wordEncodings)) {
	wordToId.set(word, Number(id));
	idToWord.set(Number(id), word);
}

interface EncodingResult {
	tensor: TypedTensor<'int64'>;
	unknownWords: string[];
}

// Converts [text] to a Tensor. 
const encodeText = (text: string): EncodingResult => {
	text = text
		// Compare to standardize_tf_text in v2-seq2seq.ipynb
		.replace(unsupportedCharactersExp, ' ')
		.replace(punctuationExp, ' $0 ')
		.replace(/(\s|^)([A-Z])/g, ' [CAP] $2')
		.replace(/([a-z]{3,})(ing|ed|er|ily|ly|ish|s)(\s|$)/g, '$1 [$2]$3') // move certain suffixes to separate tokens
		.toLowerCase()
		.trim();

	const wordStrings = `[START] ${text} [END]`.split(/\s+/);
	const unknownToken = wordToId.get('[UNK]');
	if (unknownToken === undefined) {
		throw new Error('Missing [UNK] token!');
	}

	const unknowns: string[] = [];

	const wordInts = wordStrings.map((word): number => {
		const wordId = wordToId.get(word);
		if (wordId !== undefined) {
			return wordId;
		} else {
			unknowns.push(word);
			return unknownToken;
		}
	});
	return {
		tensor: new Tensor('int64', wordInts),
		unknownWords: unknowns,
	};
};

// unknowns: Maps from the index of an [UNK] token to its guessed value.
const decodeText = async (tensor: TypedTensor<'int64'>, unknowns: string[]) => {
	const data = await tensor.getData();

	const result: string[] = [];
	let unknownIndex = 0;
	for (let i = 0; i < data.length; i++) {
		const value = Number(data.at(i));
		const word = idToWord.get(value);
		if (word === undefined) {
			throw new Error('Invalid ID: ' + value);
		} else if (word === '[UNK]' && unknownIndex < unknowns.length) {
			result.push(unknowns[unknownIndex]);
			unknownIndex ++;
		} else {
			result.push(word);
		}

		if (word === '[END]') {
			break;
		}
	}

	return result
		.join(' ')
		// Rejoin suffixes
		.replace(/([a-z])\s\[(ing|s|ed|er|ily|ly|ish)\](\s|$)/g, '$1$2$3')
		// Interpret [cap] tokens
		.replace(/\[cap\]\s(\w)/g, (_, capture) => {
			return capture.toUpperCase();
		})
		// Remove extra whitespace before most punctuation tokens
		.replace(/\s([?.!,;:])/g, '$1')
		.replace(/\s'\s/g, '\'');
};

class Punctuator {
	public constructor(
		private session: InferenceSession
	) {}

	public async punctuate(text: string) {
		// Remove any existing punctation
		text = text.replace(punctuationExp, ' ').toLowerCase();

		const { tensor: encodedInput, unknownWords } = encodeText(text);
		console.debug('Unknown tokens:', unknownWords);
		const rawResults = await this.session.run({ 'input': encodedInput });

		let result;
		if ('output_0' in rawResults) {
			const outputTokens = rawResults['output_0'] as TypedTensor<'int64'>;
			const decoded = await decodeText(outputTokens, unknownWords);

			result = decoded;

			outputTokens.dispose();
		} else {
			throw new Error('No output found!');
		}
		encodedInput.dispose();

		return result;
	}
}

(async () => {
	const session = await InferenceSession.create('./model.onnx');
	const punctuator = new Punctuator(session);

	const container = document.createElement('div');
	const testInput = document.createElement('textarea');
	testInput.value = 'this sentence shall be punctuated for the following reasons first punctatuion makes things easier to read second um';
	const testButton = document.createElement('button');
	testButton.textContent = 'Test';

	testButton.onclick = async () => {
		alert(await punctuator.punctuate(testInput.value));
	};

	container.replaceChildren(testInput, testButton);
	document.body.appendChild(container);
})();