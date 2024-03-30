<template>
	<div class="resize-box" :class="{resizing}"
		:style="{
			left: `${left}px`,
			width: `${right - left}px`,
			top: `${top}px`,
			height: `${bottom - top}px`,
		}"
	>
		<span class="label" v-if="resizing">{{right - left}} &times; {{bottom - top}}</span>
		<div class="inner"
			@mousemove="onMove"
			@mouseup="onUp"
		>
			<div class="lt" @mousedown="onDown($event, 'l', 't')"   ></div>
			<div class="mt" @mousedown="onDown($event, null, 't')"  ></div>
			<div class="rt" @mousedown="onDown($event, 'r', 't')"   ></div>
			<div class="lm" @mousedown="onDown($event, 'l', null)"  ></div>
			<div class="mm" @mousedown="onDown($event, null, null)" ></div>
			<div class="rm" @mousedown="onDown($event, 'r', null)"  ></div>
			<div class="lb" @mousedown="onDown($event, 'l', 'b')"   ></div>
			<div class="mb" @mousedown="onDown($event, null, 'b')"  ></div>
			<div class="rb" @mousedown="onDown($event, 'r', 'b')"   ></div>
		</div>
	</div>
</template>

<script>
	export default {
		name: "resize-box",


		props: {
			left: Number,
			right: Number,
			top: Number,
			bottom: Number,
		},


		data () {
			return {
				tx: null,
				ty: null,
				resizing: false,
			};
		},


		computed: {
			ll: {
				get () {
					return this.left;
				},

				set (value) {
					this.$emit("update:left", value);
				},
			},

			rr: {
				get () {
					return this.right;
				},

				set (value) {
					this.$emit("update:right", value);
				},
			},

			tt: {
				get () {
					return this.top;
				},

				set (value) {
					this.$emit("update:top", value);
				},
			},

			bb: {
				get () {
					return this.bottom;
				},

				set (value) {
					this.$emit("update:bottom", value);
				},
			},
		},


		methods: {
			onDown (event, tx, ty) {
				if (event.buttons === 1) {
					this.tx = tx;
					this.ty = ty;

					this.resizing = true;
				}
			},


			onUp () {
				this.$emit("released", this.tx, this.ty);

				this.resizing = false;
				this.tx = null;
				this.ty = null;
			},


			onMove (event) {
				if (this.resizing && !event.ctrlKey) {
					const {movementX, movementY} = event;

					if (!this.tx && !this.ty) {
						this.ll += movementX;
						this.rr += movementX;
						this.tt += movementY;
						this.bb += movementY;

						return;
					}

					switch (this.tx) {
					case "l":
						this.ll += movementX;
						break;
					case "r":
						this.rr += movementX;
						break;
					}

					switch (this.ty) {
					case "t":
						this.tt += movementY;
						break;
					case "b":
						this.bb += movementY;
						break;
					}
				}
			},
		},
	};
</script>

<style>
	.resize-box
	{
		position: absolute;
	}

	.resize-box .inner
	{
		position: absolute;
		left: -5px;
		right: -5px;
		top: -5px;
		bottom: -5px;
		display: grid;
		grid-template-columns: 7px 1fr 7px;
		grid-template-rows: 7px 1fr 7px;
	}

	.resize-box .label
	{
		background-color: #fffa;
	}

	.resize-box.resizing .inner
	{
		transform: scale(2);
	}

	.resize-box .inner .mm
	{
		cursor: move;
	}

	.resize-box .inner .lt, .resize-box .inner .rb
	{
		cursor: nwse-resize;
	}

	.resize-box .inner .rt, .resize-box .inner .lb
	{
		cursor: nesw-resize;
	}

	.resize-box .inner .mt, .resize-box .inner .mb
	{
		cursor: ns-resize;
	}

	.resize-box .inner .lm, .resize-box .inner .rm
	{
		cursor: ew-resize;
	}
</style>
