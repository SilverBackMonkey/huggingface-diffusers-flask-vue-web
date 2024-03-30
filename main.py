
import sys
import os
import re
import flask
import json
import io
import PIL
import PIL.PngImagePlugin
import piexif
import base64
import math
import torch
import numpy as np
#import logging

import env
from pipeline_stable_diffusion import StableDiffusionPipeline
from sentenceGen import SentenceGenerator
from textGen import SentenceGenerator as SentenceGeneratorV2



app = flask.Flask(__name__, static_url_path = '', static_folder = './static')


DIST_DIR = './dist'

HTTP_HOST = os.getenv('HTTP_HOST')
HTTP_PORT = int(os.getenv('HTTP_PORT'))
SSL_CONTEXT = eval(os.getenv('SSL_CONTEXT'))
HF_TOKEN = os.getenv('HF_TOKEN')
DIFFUSER_MODEL_PATH = os.getenv('DIFFUSER_MODEL_PATH')
TEXTGEN_MODEL_PATH = os.getenv('TEXTGEN_MODEL_PATH')
DEVICE = os.getenv('DEVICE')
TEXT_DEVICE_INDEX = os.getenv('TEXT_DEVICE_INDEX')

MODEL_NAME = os.path.basename(DIFFUSER_MODEL_PATH)

TEMPERATURE = 4.


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


def encodeImageToDataURL (image, info=None, ext='.png'):
	option = None
	exif = None
	if info and ext == '.png':
		option = PIL.PngImagePlugin.PngInfo()
		for key, value in info.items():
			if value is not None:
				option.add_itxt(key, value)
	else:
		exif = piexif.dump({'0th': {305: json.dumps(info).encode('ascii')}})[6:]

	fp = io.BytesIO()
	image.save(fp, PIL.Image.registered_extensions()[ext], pnginfo=option, exif=exif)

	return 'data:image/%s;base64,%s' % (ext[1:], base64.b64encode(fp.getvalue()).decode('ascii'))


@app.route('/paint-by-text', methods=['GET'])
def paintByText ():
	prompt = flask.request.args.get('prompt')
	neg_prompt = flask.request.args.get('neg_prompt', None)
	multi = int(flask.request.args.get('multi', 1))
	n_steps = int(flask.request.args.get('n_steps', 50))
	width = int(flask.request.args.get('w', 512))
	height = int(flask.request.args.get('h', 512))
	img_only = flask.request.args.get('img_only')
	temperature = float(flask.request.args.get('temperature', 1))
	seed = flask.request.args.get('seed') and int(flask.request.args.get('seed'))
	ext = flask.request.args.get('ext', 'png')
	#print('paint by text:', prompt, multi)

	global senGen, senGen2
	if prompt == '***':
		prompt = senGen2.generate(temperature=temperature)
	elif prompt == '**':
		prompt = senGen.generate(temperature=temperature)

	global pipe
	global rand_generator

	if seed is not None:
		rand_generator.manual_seed(seed)
	else:
		seed = rand_generator.seed()

	result = pipe.generate([prompt] * multi, negative_prompt=[neg_prompt] * multi if neg_prompt is not None else None, num_inference_steps=n_steps, width=width, height=height, generator=rand_generator)

	if img_only is not None:
		fp = io.BytesIO()
		result['images'][0].save(fp, PIL.Image.registered_extensions()[f'.{ext}'], quality=100)

		res = flask.Response(fp.getvalue(), mimetype = f'image/${ext}')

		filename = re.sub(r'[^\w\s]', '', prompt)[:240].encode("ascii", "ignore").decode()
		res.headers['Content-Disposition'] = f'inline; filename="{filename}.{ext}"'

		return res

	result = {
		'prompt': prompt,
		'images': [encodeImageToDataURL(img, {
			'prompt': prompt,
			'seed': str(seed),
			'negative_prompt': neg_prompt,
			'model': MODEL_NAME,
			'resolution': f'{width}x{height}',
		}, ext=f'.{ext}') for img in result['images']],
		'latents': result['latents'],
		'seed': seed,
		'model': MODEL_NAME,
	}

	return flask.Response(json.dumps(result, ensure_ascii=True), mimetype='application/json')


@app.route('/img2img', methods=['POST'])
def img2img ():
	prompt = flask.request.args.get('prompt')
	n_steps = int(flask.request.args.get('n_steps', 50))
	strength = float(flask.request.args.get('strength', 0.5))
	seed = flask.request.args.get('seed') and int(flask.request.args.get('seed'))

	imageFile = flask.request.files.get('image')
	if not imageFile:
		flask.abort(400, 'image field is requested.')

	image = PIL.Image.open(imageFile.stream)

	PIXELS_SIZE = 640 * 640
	w, h = image.size
	scaling = 1 if w * h <= PIXELS_SIZE else math.sqrt(PIXELS_SIZE / (w * h))
	w, h = round(w * scaling / 64.) * 64, round(h * scaling / 64.) * 64
	if w != image.size[0] or h != image.size[1]:
		image = image.resize((w, h), resample=PIL.Image.BICUBIC)
	#print('image:', image.size, scaling)

	global pipe
	global rand_generator

	if seed is not None:
		rand_generator.manual_seed(seed)
	else:
		seed = rand_generator.seed()

	result = pipe.convert(prompt, init_image=image, num_inference_steps=n_steps, strength=strength, generator=rand_generator)

	result = {
		'prompt': prompt,
		'source': encodeImageToDataURL(image),
		'image': encodeImageToDataURL(result['images'][0], {'prompt': prompt, 'seed': str(seed), 'model': MODEL_NAME}),
		'latent': result['latents'][0],
		'seed': seed,
	}

	return flask.Response(json.dumps(result, ensure_ascii=True), mimetype='application/json')


@app.route('/inpaint', methods=['POST'])
def inpaint():
	prompt = flask.request.args.get('prompt')
	n_steps = int(flask.request.args.get('n_steps', 50))
	strength = float(flask.request.args.get('strength', 0.5))

	imageFile = flask.request.files.get('image')
	if not imageFile:
		flask.abort(400, 'image field is requested.')

	image = PIL.Image.open(imageFile.stream)

	data = np.array(image)
	#source_arr = data[:, :, :3].astype(np.float32) / 255.
	#mask_arr = data[:, :, 3:].astype(np.float32) / 255.

	# fill blank
	#source_arr = source_arr * mask_arr + np.random.randn(*source_arr.shape) * (1 - mask_arr)
	#source_arr = source_arr * mask_arr + np.ones(source_arr.shape) * (1 - mask_arr)

	#source = PIL.Image.fromarray((source_arr * 255).astype(np.uint8))
	source = PIL.Image.fromarray(data[:, :, :3])
	mask = PIL.Image.fromarray(255 - data[:, :, 3])

	global pipe
	result = pipe.inpaint(prompt, image=source, mask_image=mask, num_inference_steps=n_steps)

	#result_arr = np.array(result['images'][0]).astype(np.float32) / 255.
	#result_arr = result_arr * (1 - mask_arr) + source_arr * mask_arr
	#result_arr = (result_arr * 255).astype(np.uint8)

	fp = io.BytesIO()
	#PIL.Image.fromarray(result_arr).save(fp, PIL.Image.registered_extensions()['.png'])
	result['images'][0].save(fp, PIL.Image.registered_extensions()['.png'])

	return flask.Response(fp.getvalue(), mimetype = 'image/png')


@app.route('/random-sentence', methods=['GET'])
def randomSentence ():
	global senGen

	if senGen is None:
		device = torch.device(f'{DEVICE}:{TEXT_DEVICE_INDEX}') if DEVICE else None
		senGen = SentenceGenerator(templates_path='corpus/templates.txt', reserved_path='corpus/reserved.txt', device=device)

	return flask.Response(senGen.generate(temperature=TEMPERATURE), mimetype = 'text/plain')


@app.route('/random-sentence-v2', methods=['GET'])
def randomSentenceV2 ():
	global senGen2

	temperature = float(flask.request.args.get('temperature', 1))
	begin = flask.request.args.get('begin', '')

	return flask.Response(senGen2.generate(leading_text=begin, temperature=temperature), mimetype='text/plain')


def main (argv):
	global pipe, senGen2, senGen, rand_generator
	pipe = StableDiffusionPipeline.from_pretrained(DIFFUSER_MODEL_PATH, use_auth_token=HF_TOKEN, torch_dtype=torch.float32)

	device = torch.device(f'{DEVICE}:{TEXT_DEVICE_INDEX}') if DEVICE else None
	senGen = SentenceGenerator(templates_path='corpus/templates.txt', reserved_path='corpus/reserved.txt', device=device)
	senGen2 = SentenceGeneratorV2(TEXTGEN_MODEL_PATH, pipe.tokenizer, device=device)

	rand_generator = torch.Generator(device)

	if DEVICE:
		pipe.to(DEVICE)

	try:
		app.run(port=HTTP_PORT, host=HTTP_HOST, threaded=False, ssl_context=SSL_CONTEXT)
	except:
		print('server interrupted:', sys.exc_info())



if __name__ == "__main__":
	main(sys.argv)
