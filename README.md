# Diffusers Web

This project is a web based image generation tool, a front-end wrapper for [HuggingFace's diffusers](https://github.com/huggingface/diffusers).

## Usage

Run the web server:

```.bash
python ./main.py
```

If this works, navigate to *http://localhost:8157* in your browser.

## Features

### Text to image

![text2image](./doc/text2image.gif)

### Image transform

Navigate to *http://localhost:8157/converter*.

![transform](./doc/transform.gif)

### Inpainting and outpainting

Before run web server, config the diffuser model to an inpainting model. E.g. add an environment variable in `.env.local`:

```
DIFFUSER_MODEL_PATH=runwayml/stable-diffusion-inpainting
```

Then navigate to *http://localhost:8157/painter*.

![mask](./doc/mask.gif)

![outpaint](./doc/outpaint.gif)

Tips: image copy in a web page other than *localhost* requires *https* protocol, config `SSL_CONTEXT="'adhoc'"` in `.env.local` to achieve this.

## Requirements

### Hardware

A GPU with CUDA capability is required for good performence. The more video memory the better, 24GB is recommended.

### Python Libraries

Install dependency libraries with pip, reference to [requirements.txt](./requirements.txt).

### Authorization

You may need a [HuggingFace access token](https://huggingface.co/settings/tokens) to download pretrained models for the first running.

## Local Environment Variables

Edit local environment variables in file *.env.local*.

Variable Name						| Default Value						| Description
:--									| :--								| :--
**HF_TOKEN**						|									| Your HuggingFace access token. If a local config path provided, this can be ignored.
**DIFFUSER_MODEL_PATH**				| stabilityai/stable-diffusion-2	| This can be a local model config path.
**TEXTGEN_MODEL_PATH**				| k-l-lambda/clip-text-generator	| The random painting description generator model path. This can be a local model config path.
**HTTP_HOST**						| 127.0.0.1							| Use `0.0.0.0` for network access.
**HTTP_PORT**						| 8157								|
**SSL_CONTEXT**						| None								| Use `'adhoc'` for https server.
**DEVICE**							|									| `cuda` or *None*
**TEXT_DEVICE_INDEX**				| 0									| This can be greater than 0 if **CUDA_VISIBLE_DEVICES** has more than 1 gpu specified.
