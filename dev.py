
import sys
import os
import io
import re
import flask
import json
import PIL.Image
import random
import numpy as np
import time

import env



app = flask.Flask(__name__, static_url_path = '', static_folder = './static')


DIST_DIR = './dist'

HTTP_HOST = os.getenv('HTTP_HOST')
HTTP_PORT = int(os.getenv('HTTP_PORT'))


@app.route('/bundles/<path:filename>')
def bundle(filename):
	if re.match(r'.*\.bundle\.js$', filename):
		return flask.send_from_directory(DIST_DIR, filename)

	flask.abort(404, 'Invalid request path.')


pageRouters = {
	'/':				'index.html',
	'/converter':		'converter.html',
	'/painter':			'painter.html',
}
for path in pageRouters:
	def getHandler(filename):
		return lambda: flask.send_from_directory(DIST_DIR, filename)

	app.route(path, endpoint = 'handler' + path)(getHandler(pageRouters[path]))


@app.route('/paint-by-text', methods=['GET'])
def paintByText():
	prompt = flask.request.args.get('prompt')
	img_only = flask.request.args.get('img_only')
	width = int(flask.request.args.get('w', 512))
	height = int(flask.request.args.get('h', 512))

	result = {
		'prompt': prompt,
		'images': ['/favicon.ico'],
		'model': 'dev-test',
		'resolution': f'{width}x{height}',
	}

	if img_only is not None:
		file = open('./static/favicon.ico', 'rb')

		return flask.Response(file, mimetype = 'image/png')

	return flask.Response(json.dumps(result), mimetype='application/json')


@app.route('/img2img', methods=['POST'])
def img2img():
	prompt = flask.request.args.get('prompt')
	n_steps = int(flask.request.args.get('n_steps', 50))

	imageFile = flask.request.files.get('image')
	if not imageFile:
		flask.abort(400, 'image field is requested.')

	image = PIL.Image.open(imageFile.stream)
	print('image:', image.size)

	result = {
		'prompt': prompt,
		'source': '/favicon.ico',
		'image': '/favicon.ico',
	}

	return flask.Response(json.dumps(result), mimetype='application/json')


@app.route('/inpaint', methods=['POST'])
def inpaint():
	prompt = flask.request.args.get('prompt')
	n_steps = int(flask.request.args.get('n_steps', 50))

	imageFile = flask.request.files.get('image')
	if not imageFile:
		flask.abort(400, 'image field is requested.')

	image = PIL.Image.open(imageFile.stream)
	#print('image:', image.size)

	data = np.array(image)
	#print('data:', data.shape)

	source = data[:, :, :3] / 255.
	mask = data[:, :, 3:] / 255.

	result = source * mask + np.random.randn(*source.shape) * (1 - mask)
	result = (result * 255).astype(np.uint8)
	result = PIL.Image.fromarray(result)

	fp = io.BytesIO()
	result.save(fp, PIL.Image.registered_extensions()['.png'])

	time.sleep(2)

	return flask.Response(fp.getvalue(), mimetype = 'image/png')


@app.route('/random-sentence', methods=['GET'])
def randomSentence ():
	return flask.Response(''.join([chr(random.randrange(48, 126)) for i in range(16)]), mimetype='text/plain')


def main(argv):
	try:
		app.run(port=HTTP_PORT, host=HTTP_HOST, threaded=False)
	except:
		print('server interrupted:', sys.exc_info())



if __name__ == "__main__":
	main(sys.argv)
