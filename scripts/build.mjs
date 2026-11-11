import { cp, mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const output = join(root, "dist");
const staticFiles = [
  "index.html",
  "styles.css",
  "app.js",
  "preregister.html",
  "preregister.css",
  "preregister.js",
];

await rm(output, { recursive: true, force: true });
await mkdir(output, { recursive: true });

for (const file of staticFiles) {
  const source = join(root, file);
  let contents = await readFile(source, "utf8");
  if (file === "preregister.js") {
    const expression = "process.env.NEXT_PUBLIC_WEB3FORMS_KEY || 'YOUR_ACCESS_KEY'";
    const configuredKey = JSON.stringify(process.env.NEXT_PUBLIC_WEB3FORMS_KEY || "YOUR_ACCESS_KEY");
    if (!contents.includes(expression)) {
      throw new Error("Could not find the Web3Forms key expression in preregister.js");
    }
    contents = contents.replace(expression, configuredKey);
  }
  await writeFile(join(output, file), contents);
}

const publicDir = join(root, "public");
for (const entry of await readdir(publicDir, { withFileTypes: true })) {
  await cp(join(publicDir, entry.name), join(output, entry.name), { recursive: true });
}

console.log(`Static site built in ${output}`);
