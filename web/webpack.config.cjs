const CopyPlugin = require('copy-webpack-plugin');
const path = require('path');

const distDir = path.resolve(__dirname, 'dist');
const distDirCopyPattern = path.join(distDir, '[name][ext]');

module.exports = {
	entry: './index.ts',
	mode: 'development',
	module: {
		rules: [ { test: /\.ts$/, use: 'ts-loader', exclude: /node_modules/ } ],
	},
	resolve: {
		extensions: [ '.tsx', '.ts', '.js', '.json' ],
	},
	output: {
		filename: 'bundle.js',
		path: distDir,
	},
	plugins: [
		new CopyPlugin({
			patterns: [
				{ from: 'node_modules/onnxruntime-web/dist/*.wasm', to: distDirCopyPattern },
				{ from: 'node_modules/onnxruntime-web/dist/*.mjs', to: distDirCopyPattern },
				{ from: '*.onnx', to: distDirCopyPattern },
				{ from: '*.html', to: distDirCopyPattern },
			],
		}),
	],
};