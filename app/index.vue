<template>
	<div class="home"
		@dragover.prevent="drageHover = true"
		@dragleave="drageHover = false"
		@drop.prevent="onDrop"
	>
		<header>
			<input class="description" v-model="description" type="text" placeholder="prompt text" />
			<input class="neg-decription" v-model="negativeDescription" type="text" placeholder="negative prompt text" />
			<button @click="rollDescription" title="Give me an idea.">&#x1f3b2;</button>
			<StoreInput localKey="description" type="text" v-model="description" v-show="false" />
			<StoreInput localKey="negativeDescription" type="text" v-model="negativeDescription" v-show="false" />
			<StoreInput localKey="n_steps" type="number" v-model="n_steps" v-show="false" />
			<StoreInput localKey="seed" type="number" v-model="seed" v-show="false" />
			<StoreInput localKey="multi" type="number" v-model="multi" v-show="false" />
			<StoreInput localKey="size_w" type="number" v-model="width" v-show="false" />
			<StoreInput localKey="size_h" type="number" v-model="height" v-show="false" />
			<StoreInput localKey="ext" type="text" v-model="ext" v-show="false" />
			<input type="number" v-model.number="n_steps" min="1" max="250" :style="{width: '2.4em'}" />
			<input type="text" v-model.number="seed" placeholder="seed" :size="2" @click="$event.target.select()" />
			<!--select v-model.number="multi">
				<option v-for="i of 4" :key="i" :value="i">{{i}}</option>
			</select-->
			<span>
				<select v-model.number="width">
					<option v-for="i of 30" :key="i" :value="64 * (i + 2)">{{64 * (i + 2)}}</option>
				</select>
				&times;
				<select v-model.number="height">
					<option v-for="i of 30" :key="i" :value="64 * (i + 2)">{{64 * (i + 2)}}</option>
				</select>
			</span>
			<button class="submit" :class="{active: requesting}" @click="paintByText">&#x1f4ad;</button>
		</header>
		<main ref="main">
			<section class="item" v-for="(result, i) of results" :key="i">
				<header>
					<button class="activate" @click="activateItem(result)">^</button>
					<em v-text="result.prompt"></em>
					<i v-if="result.negative" :title="result.negative">&#x2d31;</i>
					<span v-if="Number.isFinite(result.seed)">[{{result.seed}}]</span>
					<span v-if="result.loading">...</span>
				</header>
				<div v-if="result.images">
					<div class="picture-container" v-for="(img, ii) of result.images" :key="ii">
						<div class="picture">
							<img :src="img" @load="onImageLoad" />
							<a class="download" :href="img" :download="`${result.prompt && result.prompt.replace(/[^\w\s]/g, '').substr(0, 240)}.png`">&#x2913;</a>
						</div>
						<i class="favorite" :class="{done: result.favorited}" v-if="uploader" @click="favoriteImage(result, img)">&#x26e4;</i>
					</div>
				</div>
				<p v-if="result.error" class="error" v-html="result.error"></p>
				<hr />
			</section>
		</main>
		<button class="purge" @click="purgeList">&#x2421;</button>
		<button class="pick-img" @click="pickImage">..</button>
	</div>
</template>

<script>
	import ExifReader from "exifreader";
	import md5 from "md5";

	import StoreInput from "./storeinput.vue";



	const toBlobURL = async url => {
		const blob = await (await fetch(url)).blob();
		return URL.createObjectURL(blob);
	};



	export default {
		name: "index",


		components: {
			StoreInput,
		},


		data () {
			return {
				description: null,
				negativeDescription: null,
				results: [],
				multi: 1,
				n_steps: 50,
				width: 512,
				height: 512,
				seed: null,
				requesting: false,
				ext: "webp",
				drageHover: false,
				uploader: window.uploader,
			};
		},


		created () {
			window.$main = this;
		},


		methods: {
			async paintByText () {
				const item = {
					prompt: this.description,
					negative: this.negativeDescription,
					seed: this.seed,
					loading: true,
					favorited: false,
					resolution: `${this.width}x${this.height}`,
				};
				this.results.push(item);
				this.requesting = true;

				let url = `/paint-by-text?prompt=${encodeURIComponent(this.description || "")}&multi=${this.multi}&n_steps=${this.n_steps}&w=${this.width}&h=${this.height}&ext=${this.ext}`;
				if (Number.isInteger(this.seed))
					url += `&seed=${this.seed}`;
				if (this.negativeDescription)
					url += `&neg_prompt=${encodeURIComponent(this.negativeDescription)}`;

				const response = await fetch(url);
				if (response.ok) {
					const result = await response.json();
					if (result.images)
						result.images = await Promise.all(result.images.map(toBlobURL));

					Object.assign(item, result);
				}
				else
					item.error = await response.text();

				item.loading = false;
				this.requesting = false;
			},


			async rollDescription (event) {
				const begin = event.shiftKey ? this.description : "";
				const response = await fetch(`/random-sentence-v2?begin=${begin}`);
				this.description = await response.text();
			},


			onImageLoad () {
				this.$refs.main.scrollTo(0, this.$refs.main.scrollHeight);
			},


			async loadImage (file) {
				const tags = await ExifReader.load(file);
				//console.log('tags:', tags);
				if (tags && tags.Software) {
					const info = JSON.parse(tags.Software.description);
					console.log("info:", info);
					this.description = info.prompt;
					this.negativeDescription = info.negative_prompt
					this.seed = Number(info.seed);
					if (info.resolution)
						[this.width, this.height] = info.resolution.split("x").map(Number);
				}
			},


			onDrop (event) {
				const file = event.dataTransfer.files[0];
				if (file)
					this.loadImage(file)
			},


			activateItem (item) {
				this.description = item.prompt;
				this.negativeDescription = item.negative;
				this.seed = item.seed;
			},


			purgeList () {
				if (confirm("clear results?"))
					this.results = [];
			},


			async pickImage () {
				const url = window.prompt("Image URL");
				if (url) {
					const response = await fetch(url);
					if (response.ok)
						this.loadImage(await response.blob());
				}
			},


			async favoriteImage (item, url) {
				if (!this.uploader)
					return;
				const res = await fetch(url);
				const file = await res.blob();

				const data = {
					model: item.model,
					prompt: item.prompt,
					negative: item.negative,
					seed: item.seed,
					resolution: item.resolution,
				};
				const hash = md5(JSON.stringify(data));

				const body = new FormData();
				body.append("file", file, `${this.uploader.dir}/${item.model}/${hash}.${this.ext}`);

				const res2 = await fetch(this.uploader.host, {
					method: "POST",
					body,
				});
				if (res2.ok) {
					const result = await res2.json();
					if (result.result === "ok")
						item.favorited = true;
					else
						console.warn("upload failed:", result);
				}
				else {
					const result = await res2.text();
					console.warn("upload failed:", result);
				}
			},
		},
	};
</script>

<style src="./common.css"></style>
<style>
	.home
	{
		display: flex;
		flex-direction: column;
		height: 100%;
		position: relative;
	}

	.submit.active
	{
		background-color: #cfc;
	}

	.home > button
	{
		display: inline-block;
		position: absolute;
		background: none;
		border: 0;
		font-size: 200%;
		color: #aaa;
		right: 8px;
	}

	button.purge
	{
		bottom: 8px;
	}

	button.pick-img
	{
		bottom: 108px;
	}

	i
	{
		font-style: normal;
		cursor: default;
	}

	.item header i
	{
		font-weight: bold;
		color: #600;
	}

	.picture-container i
	{
		display: inline-block;
		margin: 2em;
		cursor: pointer;
	}

	i.favorite.done
	{
		font-weight: bold;
		color: orange;
		text-shadow: 1px 1px 2px orange;
	}

	.activate
	{
		margin-right: 1em;
		border: 0;
	}
</style>
