#!/usr/bin/env sh
# Reproduces the surface-collision table from the two installed binaries.
# Reads no account, makes no API calls, requires no login.
#
#   sh research/probe.sh
#   sh research/probe.sh --identity    # the one check that needs you signed in
#
# Every line the note quotes is printed here from the binaries themselves,
# so the note and the build cannot disagree.
#
# --identity compares the organization each CLI is signed in to. It reads both
# credentials but prints only whether they agree -- never an organization id, a
# workspace id, an email or a name. That is deliberate: the finding is that the
# two differ, and reproducing it should not require publishing your own account.

set -u

if [ "${1:-}" = "--identity" ]; then
  echo 'identity check -- needs both CLIs signed in; prints no identifiers'
  echo

  cc=$(claude auth status 2>/dev/null \
        | grep -oE '"orgId"[[:space:]]*:[[:space:]]*"[0-9a-fA-F-]{36}"' \
        | grep -oE '[0-9a-fA-F-]{36}' | head -1)
  pl=$(ant auth status 2>/dev/null \
        | grep -oE 'organization:.*\([0-9a-fA-F-]{36}\)' \
        | grep -oE '[0-9a-fA-F-]{36}' | head -1)

  [ -n "$cc" ] && echo '  claude  signed in' || echo '  claude  NOT signed in (run: claude auth login)'
  [ -n "$pl" ] && echo '  ant     signed in' || echo '  ant     NOT signed in (run: ant auth login)'
  echo

  if [ -z "$cc" ] || [ -z "$pl" ]; then
    echo '  inconclusive -- sign both in and re-run'
    exit 2
  fi
  if [ "$cc" = "$pl" ]; then
    echo '  SAME organization.'
    echo '  On this account the two surfaces share an identity, so the'
    echo '  n=1 observation in surface-collision.md does not generalise.'
    exit 0
  fi
  echo '  DIFFERENT organizations.'
  echo '  Promotion from Claude Code to a hosted agent would cross an'
  echo '  identity boundary on this account, not just a tooling gap.'
  exit 1
fi

echo "claude:  $(claude --version 2>/dev/null || echo 'NOT INSTALLED')"
printf 'ant:     '
if command -v ant >/dev/null 2>&1; then ant --version 2>&1; else echo 'NOT INSTALLED'; fi
echo

echo '=== 1. "agents" means background sessions, not hosted agents ==='
claude --help 2>&1 | grep -E '^  agents '
echo '  ant, for the same word:'
ant beta:agents --help 2>&1 | sed -n '/COMMANDS/,/OPTIONS/p' | grep -E '^   (create|list)' | sed 's/^/  /'
echo

echo '=== 2. "environment" is a ccpool_, not a Managed Agents env_ ==='
claude --help 2>&1 | grep -A2 -- '--environment <environment_id>'
echo

echo '=== 3. a second, differently-scoped dollar budget ==='
claude --help 2>&1 | grep -A1 -- '--max-budget-usd'
echo

echo '=== 4. import points inward only; there is no outbound verb ==='
claude --help 2>&1 | grep -E '^  import '
claude --help 2>&1 | grep -cE '^  (export|promote|deploy|publish) ' \
  | sed 's/^/  outbound commands in claude: /'
echo '  and the reverse direction, in ant:'
for c in "beta:agents create" "beta:environments create" "beta:deployments create"; do
  printf '    %-26s ' "$c"
  ant $c --help 2>&1 \
    | grep -ciE "claude[ -]code|CLAUDE\.md|\.claude/|settings\.json|mcp\.json" \
    | sed 's/$/ references to Claude Code/'
done
echo

echo '=== 5. an auth surface identical in name across two binaries ==='
printf '  claude auth: '; claude auth --help 2>&1 | sed -n '/Commands:/,$p' \
  | grep -oE '^  (login|logout|status)' | tr -d ' ' | tr '\n' ' '; echo
printf '  ant auth:    '; ant auth --help 2>&1 | sed -n '/COMMANDS/,$p' \
  | grep -oE '^   (login|logout|status)' | tr -d ' ' | tr '\n' ' '; echo
echo '  (documented: Claude Code warns of a credential conflict after `ant auth login`)'
echo

echo '=== 6. every field ant needs, Claude Code already holds ==='
echo '  ant beta:agents create requires:'
ant beta:agents create --help 2>&1 | sed -n '/OPTIONS/,$p' \
  | grep -oE '^   --(model|name|description|system|tool|skill|mcp-server)' \
  | tr -d ' ' | sed 's/^/    /'
