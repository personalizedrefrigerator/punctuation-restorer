import { InferenceSession, Tensor, TypedTensor } from 'onnxruntime-web';
import wordEncodings from './wordEncodings';

const punctuationExp = /[?.:,\-'!]/g;
const unsupportedCharactersExp = /[^a-z0-9ùúûüÿàâæçéèêëïîôœ .,?!\-\':]/ig;

const wordToId = new Map<string, number>();
const idToWord = new Map<number, string>();
for (const [id, word] of Object.entries(wordEncodings)) {
	wordToId.set(word, Number(id));
	idToWord.set(Number(id), word);
}

const encodeText = (text: string) => {
	text = text
		.replace(unsupportedCharactersExp, ' ')
		.replace(punctuationExp, ' $0 ')
		.replace(/(\s|^)([A-Z])/g, ' [CAP] $2')
		.toLowerCase()
		.trim();

	const wordStrings = `[START] ${text} [END]`.split(/\s+/);
	const unknownToken = wordToId.get('[UNK]');
	if (unknownToken === undefined) {
		throw new Error('Missing [UNK] token!');
	}

	const wordInts = wordStrings.map((word): number => {
		const wordId = wordToId.get(word);
		if (wordId !== undefined) {
			return wordId;
		} else {
			return unknownToken;
		}
	});
	return new Tensor('int64', wordInts);
};

const decodeText = async (tensor: TypedTensor<'int64'>) => {
	const data = await tensor.getData();

	const result: string[] = [];
	for (let i = 0; i < data.length; i++) {
		const value = Number(data.at(i));
		const word = idToWord.get(value);
		if (word === undefined) {
			throw new Error('Invalid ID: ' + value);
		} else if (word === '[END]') {
			break;
		}

		result.push(word);
	}

	return result
		.join(' ')
		// Interpret [cap] tokens
		.replace(/\[cap\]\s(\w)/g, (_, capture) => {
			return capture.toUpperCase();
		})
		// Remove extra whitespace before most punctuation tokens
		.replace(/\s([?.'!])/g, '$1');
};

(async () => {
	const session = await InferenceSession.create('./model.onnx');

	const container = document.createElement('div');
	const testInput = document.createElement('textarea');
	testInput.value = 'this sentence shall be punctuated for the following reasons first punctatuion makes things easier to read second um';
	const testButton = document.createElement('button');
	testButton.textContent = 'Test';

	testButton.onclick = async () => {
		const encodedInput = encodeText(
			testInput.value.replace(punctuationExp, ' ').toLowerCase()
		);
		const results = await session.run({
			'input': encodedInput,
		});
		if ('output_0' in results) {
			const output = results['output_0'] as TypedTensor<'int64'>;
			const decoded = await decodeText(output);
			alert(decoded);
			console.log('out:', decoded)
			output.dispose();
		} else {
			alert('No output found!');
		}
		encodedInput.dispose();
	};

	container.replaceChildren(testInput, testButton);
	document.body.appendChild(container);
})();