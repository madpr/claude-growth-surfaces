#!/usr/bin/env bash
# Claude Code status line: billing attribution + continuity headroom.
#
# Answers two questions the current UI does not:
#   1. Which credential is paying for this session, and did it displace another?
#   2. Will this run be allowed to finish, in whichever currency applies?
#
# Receives session JSON on stdin. Field reference:
#   https://code.claude.com/docs/en/statusline
set -uo pipefail

input=$(cat)

# ---------------------------------------------------------------- attribution
#
# `claude auth status --json` reports what Claude Code resolved for THIS
# environment. Probing again with the credential env vars stripped reveals what
# it would have resolved without them. The difference between the two is the
# displacement -- an entitlement that exists but is not being spent.
#
# Verified on v2.1.252: with ANTHROPIC_API_KEY set, `authMethod` still reports
# "claude.ai" and `apiProvider` still reports "firstParty". The only signal that
# a subscription has been displaced is `subscriptionType` going null. That is
# why this comparison is necessary rather than just reading authMethod.

cache_dir="${TMPDIR:-/tmp}/cc-billing-$(id -u)"
mkdir -p "$cache_dir" 2>/dev/null

# Key the cache on the credential env vars so flipping one invalidates instantly.
env_print=$(printf '%s|%s' "${ANTHROPIC_API_KEY:-}" "${ANTHROPIC_AUTH_TOKEN:-}")
cache_key=$(printf '%s' "$env_print" | cksum | tr -d ' ')
cache_file="$cache_dir/$cache_key"

cache_age() {
  [ -f "$1" ] || { echo 99999; return; }
  local now mtime
  now=$(date +%s)
  mtime=$(stat -f %m "$1" 2>/dev/null || stat -c %Y "$1" 2>/dev/null || echo 0)
  echo $(( now - mtime ))
}

# The auth probe costs ~210ms; the status line redraws far more often than that.
if [ "$(cache_age "$cache_file")" -gt 30 ]; then
  {
    resolved=$(claude auth status --json 2>/dev/null)
    latent=$(env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN \
             claude auth status --json 2>/dev/null)
    jq -nc --argjson r "${resolved:-null}" --argjson l "${latent:-null}" \
      '{resolved: $r, latent: $l}'
  } > "$cache_file.tmp" 2>/dev/null && mv "$cache_file.tmp" "$cache_file" 2>/dev/null
fi

auth=$(cat "$cache_file" 2>/dev/null)
[ -z "$auth" ] && auth='{"resolved":null,"latent":null}'

resolved_sub=$(jq -r '.resolved.subscriptionType // empty' <<<"$auth")
latent_sub=$(jq -r   '.latent.subscriptionType   // empty' <<<"$auth")
auth_method=$(jq -r  '.resolved.authMethod       // "?"'   <<<"$auth")

# Which env var is in play, and a safe tail of it for identification.
cred_var=""
cred_tail=""
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  cred_var="ANTHROPIC_API_KEY"
  cred_tail="${ANTHROPIC_API_KEY: -4}"
elif [ -n "${ANTHROPIC_AUTH_TOKEN:-}" ]; then
  cred_var="ANTHROPIC_AUTH_TOKEN"
  cred_tail="${ANTHROPIC_AUTH_TOKEN: -4}"
fi

# Three states, only one of which is a problem.
#   SUB      -- subscription is paying. Nothing displaced.
#   CONFLICT -- an env credential displaced a subscription that is sitting idle.
#   API      -- an API credential is paying and no subscription exists. Correct.
if [ -n "$resolved_sub" ]; then
  bill_state="SUB"
elif [ -n "$latent_sub" ] && [ -n "$cred_var" ]; then
  bill_state="CONFLICT"
elif [ -n "$cred_var" ]; then
  bill_state="API"
else
  bill_state="UNKNOWN"
fi

# --------------------------------------------------------------- session data
model=$(jq -r '.model.display_name // "?"' <<<"$input")
dir=$(jq -r  '.workspace.current_dir // .cwd // ""' <<<"$input")
cost=$(jq -r '.cost.total_cost_usd // 0' <<<"$input")
elapsed_ms=$(jq -r '.cost.total_duration_ms // 0' <<<"$input")
pct=$(jq -r  '.context_window.used_percentage // 0' <<<"$input" | cut -d. -f1)

five_used=$(jq -r '.rate_limits.five_hour.used_percentage // empty' <<<"$input")
five_reset=$(jq -r '.rate_limits.five_hour.resets_at // empty'      <<<"$input")

# ----------------------------------------------------------------- continuity
#
# The continuity contract: project current burn to the horizon that actually
# stops this session. For a subscription that horizon is the rate-limit window
# reset; for an API credential it is money. Same question, different currency.

headroom=""
project_window() {
  # Burn per minute against the 5h window, extrapolated to the reset.
  local used="$1" reset="$2" mins now remaining rate projected
  mins=$(awk -v ms="$elapsed_ms" 'BEGIN{printf "%.2f", ms/60000}')
  now=$(date +%s)
  remaining=$(awk -v r="$reset" -v n="$now" 'BEGIN{printf "%.1f", (r-n)/60}')

  # Not enough session history to extrapolate honestly.
  awk -v m="$mins" 'BEGIN{exit !(m < 2)}' && { echo ""; return; }

  rate=$(awk -v u="$used" -v m="$mins" 'BEGIN{printf "%.3f", u/m}')
  projected=$(awk -v u="$used" -v r="$rate" -v rem="$remaining" \
              'BEGIN{printf "%.0f", u + r*rem}')

  if   [ "$projected" -lt 85 ]; then printf '\033[32mfinishes\033[0m'
  elif [ "$projected" -lt 100 ]; then printf '\033[33mtight (%s%%)\033[0m' "$projected"
  else
    local until_cap
    until_cap=$(awk -v u="$used" -v r="$rate" 'BEGIN{printf "%.0f", (100-u)/r}')
    printf '\033[31mcaps in ~%smin\033[0m' "$until_cap"
  fi
}

if [ "$bill_state" = "SUB" ] && [ -n "$five_used" ] && [ -n "$five_reset" ]; then
  verdict=$(project_window "$five_used" "$five_reset")
  five_int=$(printf '%.0f' "$five_used" 2>/dev/null || echo 0)
  headroom="5h ${five_int}%"
  [ -n "$verdict" ] && headroom="$headroom · $verdict"
elif [ "$bill_state" = "CONFLICT" ] || [ "$bill_state" = "API" ]; then
  headroom=$(awk -v c="$cost" 'BEGIN{printf "$%.2f", c}')
fi

# -------------------------------------------------------------------- palette
grn=$'\033[32m'; amb=$'\033[33m'; red=$'\033[31m'; blu=$'\033[36m'
dim=$'\033[2m';  bold=$'\033[1m'; rst=$'\033[0m'

case "$bill_state" in
  SUB)
    badge="${grn}◆ ${bold}$(echo "$resolved_sub" | tr '[:lower:]' '[:upper:]') SUB${rst}"
    note=""
    ;;
  CONFLICT)
    badge="${amb}▲ ${bold}API KEY ····${cred_tail}${rst}"
    note="${amb}${cred_var} displaced your ${latent_sub} subscription${rst}"
    ;;
  API)
    badge="${blu}◇ API KEY ····${cred_tail}${rst}"
    note=""
    ;;
  *)
    badge="${dim}? auth unknown${rst}"
    note=""
    ;;
esac

# ------------------------------------------------------------------ git + dir
branch=""
if [ -n "$dir" ] && git -C "$dir" rev-parse --git-dir >/dev/null 2>&1; then
  name=$(git -C "$dir" branch --show-current 2>/dev/null)
  [ -z "$name" ] && name=$(git -C "$dir" rev-parse --short HEAD 2>/dev/null)
  dirty=""
  git -C "$dir" diff --quiet 2>/dev/null && git -C "$dir" diff --cached --quiet 2>/dev/null || dirty="*"
  branch=" ${dim}·${rst} ${name}${dirty}"
fi

# Ten-cell context bar, coloured by remaining headroom.
filled=$(( pct / 10 )); (( filled > 10 )) && filled=10; (( filled < 0 )) && filled=0
bar=""
for ((i = 0; i < 10; i++)); do
  if (( i < filled )); then bar+="█"; else bar+="░"; fi
done
if   (( pct >= 85 )); then ctx_col="$red"
elif (( pct >= 60 )); then ctx_col="$amb"
else                       ctx_col="$grn"
fi

# --------------------------------------------------------------------- render
printf '%s %s·%s %s%s\n' "$badge" "$dim" "$rst" "$model" "$branch"
printf '%s%s%s %s%%%s' "$ctx_col" "$bar" "$rst" "$pct" "$dim"
[ -n "$headroom" ] && printf ' · %s' "$headroom"
printf '%s' "$rst"
if [ -n "$note" ]; then
  printf '\n%s' "$note"
  printf '\n%s  ↳ press ⌥B to bill the subscription instead%s' "$dim" "$rst"
fi
printf '\n'
