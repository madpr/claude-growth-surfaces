#!/usr/bin/env sh
# Build the deployable site into a directory. One command, so the wrap rule lives
# here rather than in someone's memory.
#
#   sh scripts/build-site.sh out/
#
# Page sources under */page/ are artifact-style fragments with no doctype or charset.
# A static host needs both, or the page renders in quirks mode with mojibake. This
# prepends the three lines and changes nothing else.

set -eu

OUT="${1:?usage: build-site.sh <outdir>}"
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

mkdir -p "$OUT"
touch "$OUT/.nojekyll"

wrap() {
  printf '<!doctype html>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n' > "$OUT/$2"
  cat "$ROOT/$1" >> "$OUT/$2"
  printf '  %-24s <- %s\n' "$2" "$1"
}

wrap 01-dev-to-production/page/home.html              index.html
wrap 01-dev-to-production/page/promote-cli.html       promote-cli.html
wrap 01-dev-to-production/page/promote-to-agent.html  promote-to-agent.html
wrap 03-platform-entry/page/platform-entry.html       platform-entry.html
wrap bonus-billing-attribution/page/who-is-paying.html who-is-paying.html
wrap 02-openai-migration/page/migrate-cli.html       migrate.html

# The migration demo used to live at /migrations/. Keep that path as a redirect so
# old links land on the terminal.
mkdir -p "$OUT/migrations"
printf '<!doctype html>\n<meta charset="utf-8">\n<meta http-equiv="refresh" content="0; url=../migrate.html">\n<title>Migrate from OpenAI</title>\n<a href="../migrate.html">The migration demo moved to /migrate.html</a>\n' > "$OUT/migrations/index.html"
printf '  %-24s -> %s\n' migrations/index.html migrate.html

echo
echo "built into $OUT"
