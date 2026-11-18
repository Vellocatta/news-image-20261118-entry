// news-image-20261118 entry (Node 22, standard library only).
// The image is the entry.png bundled beside this file: a front-page poster
// summing up the world news of Wednesday 18 November 2026 — 35 stories, 6
// continents, one front page and a map — drawn with PIL by gen_frontpage.py
// so every headline is spelled correctly and legible. The program copies it
// to /output/entry.png, deterministically — the same bytes on every run.
//
// Run locally with:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
// Verified: two runs write byte-identical output (sha256 compared).

import { copyFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
mkdirSync(outDir, { recursive: true });
const source = fileURLToPath(new URL('./entry.png', import.meta.url));
copyFileSync(source, join(outDir, 'entry.png'));
