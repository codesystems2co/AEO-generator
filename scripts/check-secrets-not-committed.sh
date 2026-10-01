#!/usr/bin/env bash
# Pre-commit guard: block obvious gateway/dev secrets in tracked files.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PATTERNS=(
  'AdminAeo!'
  'aeo-dev-admin'
  'db179383e91442b5eb5244398787493b978cb768'
  '2aea502782cf2ec356721b799c062584'
  'ck_a7e5eccd9ae2d0852761eb06c5fb75bb532381ec'
  'cs_c7d0333f3d6662d476c9fa4dac1435d16ab97b88'
)

FAIL=0
for pat in "${PATTERNS[@]}"; do
  if git grep -n "$pat" -- ':!.secrets/*' ':!*.example' ':!scripts/check-secrets-not-committed.sh' 2>/dev/null; then
    echo "ERROR: matched secret pattern in tracked tree: $pat" >&2
    FAIL=1
  fi
done

if [[ "$FAIL" -ne 0 ]]; then
  echo "Remove secrets from git; use .secrets/mac-gateway-testing.env (gitignored)." >&2
  exit 1
fi

echo "check-secrets-not-committed: OK"
