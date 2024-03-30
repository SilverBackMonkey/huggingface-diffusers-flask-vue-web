<template>
	<div class="loading-dots">
		<div class="ellipsis">
			<div></div>
			<div></div>
			<div></div>
			<div></div>
		</div>
	</div>
</template>

<script>
	export default {
		name: "loading-dots",
	};
</script>

<style scoped>
	.loading-dots
	{
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background-color: #fff4;
	}

	.ellipsis {
		display: inline-block;
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 80px;
		height: 80px;
	}

	.ellipsis div {
		position: absolute;
		top: 33px;
		width: 13px;
		height: 13px;
		border-radius: 50%;
		background: #666c;
		animation-timing-function: cubic-bezier(0, 1, 1, 0);
	}

	.ellipsis div:nth-child(1) {
		left: 8px;
		animation: ellipsis1 0.6s infinite;
	}

	.ellipsis div:nth-child(2) {
		left: 8px;
		animation: ellipsis2 0.6s infinite;
	}

	.ellipsis div:nth-child(3) {
		left: 32px;
		animation: ellipsis2 0.6s infinite;
	}

	.ellipsis div:nth-child(4) {
		left: 56px;
		animation: ellipsis3 0.6s infinite;
	}

	@keyframes ellipsis1 {
		0% {
			transform: scale(0);
		}
		100% {
			transform: scale(1);
		}
	}

	@keyframes ellipsis3 {
		0% {
			transform: scale(1);
		}
		100% {
			transform: scale(0);
		}
	}

	@keyframes ellipsis2 {
		0% {
			transform: translate(0, 0);
		}
		100% {
			transform: translate(24px, 0);
		}
	}
</style>
