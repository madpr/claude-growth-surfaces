#!/usr/bin/env python3
"""
Fold the Vite build into one self-contained HTML fragment for preview hosting.

Two things matter here:

  * The script is emitted WITHOUT type="module". Module scripts do not execute
    inside a sandboxed iframe with an opaque origin, which is how the preview is
    embedded -- the page renders completely blank with no console error. The
    bundle is verified import/export-free below, so a classic script is safe.
  * No <html>/<head>/<body> wrapper: the preview host supplies those, including
    the charset the non-ASCII copy depends on.

Usage:  python3 build-single-file.py        (run from app/, after npm run build)
"""

import re
import pathlib
import sys

APP = pathlib.Path(__file__).resolve().parent.parent / 'app'
DIST = APP / 'dist'
OUT = pathlib.Path(__file__).resolve().parent / 'migrations-app.html'

html = (DIST / 'index.html').read_text(encoding='utf-8')
css_files = re.findall(r'<link rel="stylesheet"[^>]*href="\./([^"]+)"', html)
js_files = re.findall(r'<script[^>]*src="\./([^"]+)"', html)

if not js_files:
    sys.exit('error: no script tag found in dist/index.html')
if not css_files:
    sys.exit('error: no stylesheet found -- check that the Rollup output format '
             'has not been overridden, which suppresses CSS emission')

css = '\n'.join((DIST / f).read_text(encoding='utf-8') for f in css_files)
js = '\n'.join((DIST / f).read_text(encoding='utf-8') for f in js_files)

# A classic script cannot carry module syntax. Fail loudly rather than ship a
# blank page.
if re.search(r'(^|[;}])\s*(import|export)[ {(*]', js) or re.search(r'\bimport\s*\(', js):
    sys.exit('error: bundle contains module syntax and cannot run as a classic '
             'script; keep it dependency-free or emit an IIFE build')

OUT.write_text(
    f'<title>Migrations — Claude Console</title>\n\n'
    f'<style>\n{css}\n</style>\n\n'
    f'<div id="root"></div>\n\n'
    f'<script>\n{js}\n</script>\n',
    encoding='utf-8',
)
print(f'wrote {OUT.name}: {len(css)/1024:.0f} KB css + {len(js)/1024:.0f} KB js '
      f'= {OUT.stat().st_size/1024:.0f} KB')
