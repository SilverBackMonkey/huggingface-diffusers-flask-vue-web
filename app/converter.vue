<template>
	<div class="converter"
		@paste="onPaste"
		@drop.prevent="onDropFiles"
		@dragover.prevent="drageHover = true"
		@drageleave="drageHover = false"
		@mouseup="drageHover = false"
	>
		<header>
			<img class="source" :src="sourceURL" :class="{'drop-hover': drageHover}" />
			<input class="description" v-model="description" type="text" placeholder="prompt text" />
			<StoreInput sessionKey="description" type="text" v-model="description" v-show="false" />
			<StoreInput sessionKey="n_steps" type="number" v-model="n_steps"  v-show="false" />
			<StoreInput sessionKey="strength" type="number" v-model="strength" v-show="false" />
			<StoreInput sessionKey="seed" type="number" v-model="seed" v-show="false" />
			<input type="number" v-model.number="n_steps" min="1" max="250" :size="1" />
			<input type="text" v-model.number="seed" placeholder="seed" :size="1" />
			<input type="range" v-model.number="strength" min="0" max="1" step="any" />
			<em title="strength">{{strength.toFixed(2)}}</em>
			<button class="submit" @click="paint">&#x1f4ad;</button>
		</header>
		<main>
			<section v-for="(result, i) of results" :key="i">
				<div><em v-text="result.prompt"></em><span v-if="result.loading">...</span></div>
				<div class="images" v-if="result.source">
					<img v-if="result.source" :src="result.source" />
					<span>&#x21e8;</span>
					<div class="picture">
						<img v-if="result.target" :src="result.target" />
						<a class="download" :href="result.target" :download="`[conversion]${result.prompt && result.prompt.replace(/[^\w\s]/g, '').substr(0, 240)}.png`">&#x2913;</a>
					</div>
				</div>
				<p v-if="result.error" class="error" v-html="result.error"></p>
				<hr />
			</section>
		</main>
	</div>
</template>

<script>
	import StoreInput from "./storeinput.vue";

	import {toBlobURL} from "./utils";



	export default {
		name: "index",


		components: {
			StoreInput,
		},


		data () {
			return {
				description: null,
				results: [],
				n_steps: 50,
				sourceURL: null,
				drageHover: false,
				strength: 0.5,
				seed: null,
			};
		},


		created () {
			window.$main = this;
		},


		methods: {
			onPaste(event) {
				const image = [...event.clipboardData.items].filter(item => item.type.match(/image/))[0];
				if (image) {
					const file = image.getAsFile();
					this.sourceURL = URL.createObjectURL(file);
				}
			},


			async onDropFiles(event) {
				this.drageHover = false;

				const file = event.dataTransfer.files[0];
				if (file)
					if (/^image/.test(file.type))
						this.sourceURL = URL.createObjectURL(file);
			},


			async paint () {
				const item = {
					prompt: this.description,
					source: null,
					target: null,
					loading: true,
				};
				this.results.push(item);

				const image = await (await fetch(this.sourceURL)).blob();

				const form = new FormData();
				form.append("image", image);

				let url = `/img2img?prompt=${encodeURIComponent(this.description)}&n_steps=${this.n_steps}&strength=${this.strength}`;
				if (Number.isInteger(this.seed))
					url += `&seed=${this.seed}`;

				const response = await fetch(url, {
					method: "POST",
					body: form,
				});
				if (response.ok) {
					const result = await response.json();
					//console.log("result:", result);

					item.source = await toBlobURL(result.source);
					item.target = await toBlobURL(result.image);
				}
				else
					item.error = await response.text();

				item.loading = false;
			},
		},
	};
</script>

<style src="./common.css"></style>
<style>
	.converter
	{
		display: flex;
		flex-direction: column;
		height: 100%;
	}

	header button
	{
		flex: 0 0 4em;
	}

	header .source
	{
		min-width: 64px;
		width: 64px;
		max-height: 128px;
		vertical-align: top;
	}

	.source.drop-hover
	{
		outline: 4px lightgreen dashed;
	}

	main section .images > *
	{
		vertical-align: middle;
		font-size: 64px;
	}

	main section .images > span
	{
		display: inline-block;
		margin: .6em;
	}
</style>
