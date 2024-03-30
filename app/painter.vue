<template>
	<div class="painter"
		@copy="onCopy"
		@paste="onPaste"
	>
		<main ref="main">
			<canvas class="canvas" ref="canvas"
				:width="canvasSize.width" :height="canvasSize.height"
			/>
			<div class="bench"
				:style="{
					width: `${canvasSize.width}px`,
					height: `${canvasSize.height}px`,
				}"
				@mousemove="onBenchMouseMove"
			>
				<ResizeBox class="diffuser-box"
					:left.sync="diffuserBox.left"
					:right.sync="diffuserBox.right"
					:top.sync="diffuserBox.top"
					:bottom.sync="diffuserBox.bottom"
					@released="onBoxResized"
				/>
			</div>
		</main>
		<Loading v-if="painting" />
		<header>
			<StoreInput sessionKey="description" type="text" v-model="description" v-show="false" />
			<StoreInput sessionKey="n_steps" type="number" v-model="n_steps" v-show="false" />
			<section>
				<button @click="clear">&#x239A;</button>
				<button @click="copy">&#x2398;</button>
				<button @click="download">&#x2913;</button>
			</section>
			<section>
				<input class="description" v-model="description" type="text" placeholder="prompt text" />
				<input type="number" v-model.number="n_steps" min="1" max="250" title="steps" style="width: 2em" />
				<button @click="inpaint" :disabled="painting">&#x1f58c;</button>
			</section>
		</header>
	</div>
</template>

<script>
	import StoreInput from "./storeinput.vue";
	import ResizeBox from "./resizeBox.vue";
	import Loading from "./loading-dots.vue";

	import {downloadURL} from "./utils";



	const ROUND_UNIT = 32;
	const PIXEL_MAX = 640 * 640;



	export default {
		name: "painter",


		components: {
			StoreInput,
			ResizeBox,
			Loading,
		},


		data () {
			return {
				canvasSize: {
					width: 4096,
					height: 4096,
				},
				pointerPosition: {
					x: 0,
					y: 0,
				},
				diffuserBox: {
					left: 200,
					right: 712,
					top: 200,
					bottom: 712,
				},
				description: "",
				n_steps: 50,
				//strength: 0.5,
				painting: false,
			};
		},


		created () {
			window.$main = this;
			this.contentRect = null;

			document.addEventListener("keydown", event => {
				if (["INPUT", "TEXTAREA"].includes(document.activeElement.nodeName))
					return;

				switch (event.code) {
				/*case "KeyC":
					if (event.ctrlKey)
						this.copy();

					break;*/
				case "F9":
					this.inpaint();

					break;
				}
			});
		},


		mounted () {
			//this.canvasSize.width = this.$refs.main.clientWidth;
			//this.canvasSize.height = this.$refs.main.clientHeight;
			this.$refs.main.scrollLeft = (this.canvasSize.width - this.$refs.main.clientWidth) / 2;
			this.$refs.main.scrollTop = (this.canvasSize.height - this.$refs.main.clientHeight) / 2;

			const [w, h] = [this.diffuserBox.right - this.diffuserBox.left, this.diffuserBox.bottom - this.diffuserBox.top];
			this.diffuserBox.left = (this.canvasSize.width - w) / 2;
			this.diffuserBox.top = (this.canvasSize.height - h) / 2;
			this.diffuserBox.right = this.diffuserBox.left + w;
			this.diffuserBox.bottom = this.diffuserBox.top + h;

			this.ctx = this.$refs.canvas.getContext("2d");
		},


		methods: {
			onPaste (event) {
				const image = [...event.clipboardData.items].filter(item => item.type.match(/image/))[0];
				if (image) {
					const file = image.getAsFile();
					this.pasteImage(URL.createObjectURL(file), this.pointerPosition.x, this.pointerPosition.y);
				}
			},


			onCopy () {
				if (!["INPUT", "TEXTAREA"].includes(document.activeElement.nodeName))
					this.copy();
			},


			onDropFiles (event) {
				this.drageHover = false;

				const file = event.dataTransfer.files[0];
				if (file)
					if (/^image/.test(file.type))
						this.pasteImage(URL.createObjectURL(file), this.pointerPosition.x, this.pointerPosition.y);
			},


			onBenchMouseMove (event) {
				if (event.buttons == 1) {
					if (event.ctrlKey) {
						this.$refs.main.scrollLeft -= event.movementX;
						this.$refs.main.scrollTop -= event.movementY;
					}
				}
				else {
					this.pointerPosition.x = event.offsetX;
					this.pointerPosition.y = event.offsetY
				}
			},


			extendContentRect (x, y, width, height) {
				if (!this.contentRect)
					this.contentRect = {left: x, right: x + width, top: y, bottom: y + height};
				else {
					this.contentRect.left = Math.min(this.contentRect.left, x);
					this.contentRect.right = Math.max(this.contentRect.right, x + width);
					this.contentRect.top = Math.min(this.contentRect.top, y);
					this.contentRect.bottom = Math.max(this.contentRect.bottom, y + height);
				}
			},


			async pasteImage (url, x, y) {
				const img = new Image();
				img.src = url;
				await new Promise((resolve, reject) => {
					img.onload = resolve;
					img.onerror = reject;
				});

				//console.log('paste:', img, this.pointerPosition);

				this.ctx.drawImage(img, x, y);

				this.extendContentRect(x, y, img.width, img.height);
			},


			clear () {
				this.ctx.clearRect(0, 0, this.canvasSize.width, this.canvasSize.height);
				this.contentRect = null;
			},


			async copy () {
				if (!this.contentRect) {
					console.warn("no content.");
					return;
				}

				const blob = await this.getImageBlock(this.contentRect);
				const result = await navigator.clipboard.write([new ClipboardItem({ [blob.type]: blob })]);
				console.debug("copy:", result);
			},


			async download () {
				if (!this.contentRect) {
					console.warn("no content.");
					return;
				}

				const blob = await this.getImageBlock(this.contentRect);
				downloadURL(URL.createObjectURL(blob), `[painter]${Date.now().toString()}.png`);
			},


			onBoxResized (tx, ty) {
				const width = this.diffuserBox.right - this.diffuserBox.left;
				const height = this.diffuserBox.bottom - this.diffuserBox.top;
				let rw = Math.round(width / ROUND_UNIT) * ROUND_UNIT;
				let rh = Math.round(height / ROUND_UNIT) * ROUND_UNIT;

				if (rw * rh > PIXEL_MAX) {
					if (ty) {
						rh = PIXEL_MAX / rw;
						rh = Math.round(rh / ROUND_UNIT) * ROUND_UNIT;
					}
					else {
						rw = PIXEL_MAX / rh;
						rw = Math.round(rw / ROUND_UNIT) * ROUND_UNIT;
					}
				}

				if (rw !== width) {
					switch (tx) {
					case "l":
						this.diffuserBox.left = this.diffuserBox.right - rw;
						break;
					case "r":
						this.diffuserBox.right = this.diffuserBox.left + rw;
						break;
					}
				}

				if (rh !== height) {
					switch (ty) {
					case "t":
						this.diffuserBox.top = this.diffuserBox.bottom - rh;
						break;
					case "b":
						this.diffuserBox.bottom = this.diffuserBox.top + rh;
						break;
					}
				}
			},


			async getImageBlock (box) {
				const data = this.ctx.getImageData(box.left, box.top, box.right - box.left, box.bottom - box.top);
				const canvas = document.createElement("canvas");
				canvas.width = data.width;
				canvas.height = data.height;
				const ctx = canvas.getContext("2d");
				ctx.putImageData(data, 0, 0);

				return new Promise(resolve => canvas.toBlob(resolve, "image/png"));
			},


			async inpaint () {
				this.painting = true;

				try {
					const image = await this.getImageBlock(this.diffuserBox);

					const form = new FormData();
					form.append("image", image);

					const response = await fetch(`/inpaint?prompt=${encodeURIComponent(this.description)}&n_steps=${this.n_steps}`, {
						method: "POST",
						body: form,
					});
					const result = await response.blob();
					//console.log("result:", result);

					this.pasteImage(URL.createObjectURL(result), this.diffuserBox.left, this.diffuserBox.top);
				}
				catch (err) {
					console.warn("inpaint error:", err);
				}

				this.painting = false;
			},
		},


		watch: {
		},
	};
</script>

<style src="./common.css"></style>
<style>
	.painter
	{
		height: 100%;
	}

	.painter header
	{
		position: absolute;
		top: 1em;
		left: 50%;
		transform: translate(-50%, 0);
		font-size: 28px;
		padding: .4em 2em;
		background: #fffa;
		border-radius: 1em;
		opacity: 0;
		transition: opacity .4s;
	}

	.painter header:hover, .painter header:focus-within
	{
		opacity: 1;
	}

	.painter header *
	{
		font-size: inherit;
	}

	.painter header > * > *
	{
		height: unset;
	}

	.painter main
	{
		height: 100%;
		overflow: scroll;
		position: relative;
	}

	.canvas
	{
		background-repeat: repeat;
		background-image: url('/transparent-bg.svg');
		display: block;
	}

	main .bench
	{
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
	}

	.diffuser-box
	{
		outline: dashed 2px #111;
	}
</style>
