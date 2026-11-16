#!/usr/bin/env bash
# Checks every case under cases/ against its expected result, then renders each
# passing case and validates it with nft -c (needs root, or NFT="sudo nft") and sh -n.
set -euo pipefail
cd "$(dirname "$0")"
NFT=${NFT:-nft}
out=$(mktemp -d); trap 'rm -rf "$out"' EXIT
failed=0
for case in cases/pass/*.yml cases/fail/*.yml; do
  want=${case#cases/}; want=${want%%/*}
  if ansible-playbook -i localhost, checks.yml -e "@$case" >"$out/log" 2>&1; then got=pass; else got=fail; fi
  if [ "$got" = "$want" ]; then echo "ok   $case"; else echo "FAIL $case (expected $want, got $got)"; tail -20 "$out/log"; failed=1; fi
done
for case in cases/pass/*.yml; do
  d="$out/$(basename "$case" .yml)"; mkdir -p "$d"
  ansible-playbook -i localhost, render.yml -e "@$case" -e "out_dir=$d" >"$out/log" 2>&1 || { echo "FAIL render $case"; tail -20 "$out/log"; failed=1; continue; }
  if $NFT -c -f "$d/agents-guard.nft" && sh -n "$d/agents-network-guard.sh"; then echo "ok   render $case"; else echo "FAIL render $case"; failed=1; fi
done
exit $failed
