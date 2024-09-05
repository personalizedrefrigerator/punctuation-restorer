const CopyPlugin = require('copy-webpack-plugin');
const path = require('path');

const distDir = path.resolve(__dirname, 'dist');

module.exports = {
	entry: './index.ts',
	module: {
		rules: [ { test: /\.ts$/, use: 'ts-loader', exclude: /node_modules/ } ],
		resolve: {
			extensions: [ '.tsx', '.ts', '.js' ],
		},
	},
	output: {
		filename: 'bundle.js',
		path: distDir,
	},
	plugins: [
		new CopyPlugin({
			patterns: [
				{ from: 'node_modules/onnxruntime-web/dist/*.wasm', to: path.join(distDir, '[name][ext]') },
				{ from: '*.onnx', to: path.join(distDir, '[name][ext]') },
			],
		}),
	],
};