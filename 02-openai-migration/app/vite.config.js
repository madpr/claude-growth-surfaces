import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Relative base so the build works from any static host path (GitHub Pages
// project sites, Vercel, or a file opened straight from disk).
//
// Default (ESM) output is kept because overriding the Rollup output format
// suppresses CSS emission. The single-file preview build strips the module
// type at inline time instead -- see page/build-single-file.py.
export default defineConfig({
  plugins: [react()],
  base: './',
  build: { modulePreload: { polyfill: false } },
})
