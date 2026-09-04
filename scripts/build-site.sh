#!/usr/bin/env sh
# Build the deployable site into a directory. One command, so the wrap rule lives
# here rather than in someone's memory.
#
#   sh scripts/build-site.sh out/          # pages only
#   sh scripts/build-site.sh out/ --app    # also rebuild the migrations app (needs npm)
#
# Page sources under */page/ are artifact-style fragments with no doctype or charset.
# A static host needs both, or the page renders in quirks mode with mojibake. This
# prepends the three lines and changes nothing else.

set -eu

OUT="${1:?usage: build-site.sh <outdir> [--app]}"
BUILD_APP="${2:-}"
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

# The M prototype is a Vite build. Its asset paths are relative, which is why it
# survives living under a path.
if [ "$BUILD_APP" = "--app" ]; then
  ( cd "$ROOT/02-openai-migration/app" && npm ci --silent && npm run build --silent )
fi
if [ -d "$ROOT/02-openai-migration/app/dist" ]; then
  rm -rf "$OUT/migrations"
  cp -R "$ROOT/02-openai-migration/app/dist" "$OUT/migrations"
  echo "  migrations/              <- 02-openai-migration/app/dist"
else
  echo "  migrations/              SKIPPED (no dist; pass --app to build it)"
fi

echo
echo "built into $OUT"
