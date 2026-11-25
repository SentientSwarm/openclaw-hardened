#!/usr/bin/env bash
# Checks every case against its expected result (a fail case must trip the
# assertion its "# Expect:" line names), then renders each passing case and
# validates it with promtool (PROMTOOL=, default promtool) and a YAML parse.
set -euo pipefail
cd "$(dirname "$0")"
PROMTOOL=${PROMTOOL:-promtool}
out=$(mktemp -d); trap 'rm -rf "$out"' EXIT
failed=0
for case in cases/pass/*.yml cases/fail/*.yml; do
  want=${case#cases/}; want=${want%%/*}
  if ansible-playbook -i localhost, checks.yml -e "@$case" >"$out/log" 2>&1; then got=pass; else got=fail; fi
  why=$(sed -n 's/^# Expect: //p' "$case")
  if [ "$got" = fail ] && [ -n "$why" ] && ! grep -qF "$why" "$out/log"; then got="fail for another reason"; fi
  if [ "$got" = "$want" ]; then echo "ok   $case"; else echo "FAIL $case (expected $want, got $got)"; tail -20 "$out/log"; failed=1; fi
done
for case in cases/pass/*.yml; do
  d="$out/$(basename "$case" .yml)"; mkdir -p "$d"
  ansible-playbook -i localhost, render.yml -e "@$case" -e "out_dir=$d" >"$out/log" 2>&1 || { echo "FAIL render $case"; tail -20 "$out/log"; failed=1; continue; }
  if python3 -c 'import sys, yaml; yaml.safe_load(open(sys.argv[1]))' "$d/prometheus.yml" \
     && "$PROMTOOL" check config --syntax-only "$d/prometheus.yml" >"$out/log" 2>&1 \
     && ! { x=$(sed -n 's/^# Render-excludes: //p' "$case"); [ -n "$x" ] && python3 -c 'import sys, yaml; jobs=[j["job_name"] for j in yaml.safe_load(open(sys.argv[1]))["scrape_configs"]]; sys.exit(0 if sys.argv[2].split(": ",1)[1] in jobs else 1)' "$d/prometheus.yml" "$x"; }; then
    echo "ok   render $case"
  else echo "FAIL render $case"; cat "$out/log"; failed=1; fi
done
exit $failed
