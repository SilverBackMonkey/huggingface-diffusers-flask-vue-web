
import fs from "fs";
import path from "path";
import fetch from "node-fetch";



const fetchOne = (fetcher, dir) => {
	const promise = fetcher();
	promise.then(async response => {
			await new Promise(resolve => setTimeout(resolve, 0));

			const [_, filename] = response.headers.get('content-disposition').match(/filename="(.+)"/);
			//console.log("filename:", filename);
	
			// find a unique name
			let fullname = path.resolve(dir, filename);
			let i = 0;
	
			const [stem, ext] = filename.split(".");
			while (fs.existsSync(fullname))
				fullname = path.resolve(dir, `${stem} [${i++}].${ext}`);
	
			const buffer = await response.buffer();
	
			fs.writeFileSync(fullname, buffer);
	}).catch(err => console.warn('res err:', err));

	return promise;
};


const TOTAL = 200;


const main = async argv => {
	const fetcher = () => fetch(`${argv[2]}/paint-by-text?prompt=**&img_only&w=512&h=768&ext=webp`);
	const dir = argv[3] || "./";

	for (let i = 0; i < TOTAL; ++i) {
		try {
			await fetchOne(fetcher, dir);
		}
		catch(err) {
			console.warn(i, err);
		}

		if (i % 10 === 0)
			console.log(`${i}/${TOTAL}`);
	}

	console.log("Done.");
};


main(process.argv).catch(err => console.log('fatal:', err));
