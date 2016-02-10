
const toBlobURL = async url => {
	const blob = await (await fetch(url)).blob();
	return URL.createObjectURL(blob);
};



const downloadURL = (url, filename) => {
	const a = document.createElement("a");
	a.setAttribute("download", filename);
	a.href = url;
	a.click();
};



export {
	toBlobURL,
	downloadURL,
};
