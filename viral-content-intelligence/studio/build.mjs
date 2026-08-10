/**
 * Inlines the app into one self-contained HTML file.
 *
 * The modular sources are the thing you edit; this is only for handing someone
 * a single file (or publishing it) with no server and no external requests.
 *
 *   node build.mjs   ->  dist/studio.html
 */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const read = (p) => readFileSync(join(here, p), 'utf8');

/** Strip ESM syntax so the modules can be concatenated into one script. */
const flatten = (src) =>
  src
    .replace(/^\s*import\s+[\s\S]*?from\s+['"][^'"]+['"];?\s*$/gm, '')
    .replace(/^export\s+(const|function|let|class)\s/gm, '$1 ')
    .replace(/^export\s*\{[^}]*\};?\s*$/gm, '');

const css = read('styles.css');
const js = ['js/data.js', 'js/scoring.js', 'js/app.js'].map((f) => flatten(read(f))).join('\n\n');

// Body markup, lifted from index.html between <body> and </body>.
const body = read('index.html')
  .replace(/[\s\S]*?<body>/, '')
  .replace(/<\/body>[\s\S]*/, '')
  .replace(/\s*<script[\s\S]*?<\/script>\s*/g, '\n');

// The <head> from index.html is dropped, so the viewport meta has to be
// re-emitted here or phones render this as a zoomed-out desktop page.
const out = `<title>Viral Content Studio</title>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<style>
${css}
</style>
${body}
<script type="module">
${js}
</script>
`;

mkdirSync(join(here, 'dist'), { recursive: true });
writeFileSync(join(here, 'dist/studio.html'), out);
console.log(`dist/studio.html — ${(out.length / 1024).toFixed(0)} KB`);
