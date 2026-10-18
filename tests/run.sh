#!/usr/bin/env bash
# dv-generate test runner.
#
#   tests/run.sh                 offline tests only (no Dataverse needed)
#   tests/run.sh <env-url>       offline tests + live import/export round trip against a DEV environment
#
# Live mode imports unmanaged test solutions (DvgenTest, DvgenFull; prefix 'dvgen') into <env-url>,
# re-exports them, and compares the export with what was generated. It leaves the test solutions
# installed; see tests/README.md for cleanup. Never point it at a shared or production environment.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_URL="${1:-}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
FAILED=0
step() { printf '\n== %s\n' "$1"; }
run()  { if ! "$@"; then FAILED=$((FAILED + 1)); echo "   ^ FAILED: $*"; fi; }

step "1. generated fixture matches generator (DvgenFull)"
python3 -I "$ROOT/tests/gen_full.py" "$WORK/gen" >/dev/null
run diff -r "$WORK/gen" "$ROOT/fixtures/DvgenFull/DvgenFull" && echo "   fixture is up to date"

step "2. XML well-formedness (all fixtures)"
for f in $(find "$ROOT/fixtures" -name '*.xml'); do run xmllint --noout "$f"; done

step "3. lint (gotchas from SKILL.md)"
for s in "$ROOT"/fixtures/*/*/; do run python3 -I "$ROOT/tests/lint.py" "$s"; done

step "4. lint mutation tests (every gotcha must be detectable)"
run python3 -I "$ROOT/tests/test_lint_mutations.py" "$ROOT/fixtures/DvgenFull/DvgenFull"

step "4b. drift/pull tool (offline, all 16 regeneration scenarios)"
run python3 -I "$ROOT/tests/test_drift.py"

step "5. pack.sh builds a zip with the expected layout"
for d in "$ROOT"/fixtures/*/; do
  n="$(basename "$d")"
  run bash "$d/pack.sh" >/dev/null
  if [ -f "$d/$n.zip" ]; then
    listing="$(unzip -Z1 "$d/$n.zip")"   # capture first: grep -q under pipefail can SIGPIPE unzip
    if grep -qx '\[Content_Types\].xml' <<<"$listing" && grep -qx 'solution.xml' <<<"$listing" \
       && grep -qx 'customizations.xml' <<<"$listing"; then
      echo "   $n.zip layout OK"
    else
      FAILED=$((FAILED + 1)); echo "   $n.zip has wrong layout"
    fi
    rm -f "$d/$n.zip"
  fi
done

step "6. SolutionPackager can unpack the packed fixtures (requires pac)"
if command -v pac >/dev/null; then
  for d in "$ROOT"/fixtures/*/; do
    n="$(basename "$d")"
    bash "$d/pack.sh" >/dev/null
    if pac solution unpack --zipfile "$d/$n.zip" --folder "$WORK/unpack-$n" --packagetype Unmanaged 2>&1 | grep -q 'Extract complete'; then
      echo "   $n unpacks"
    else
      FAILED=$((FAILED + 1)); echo "   $n FAILED to unpack"
    fi
    rm -f "$d/$n.zip"
  done
else
  echo "   skipped: pac not installed"
fi

if [ -n "$ENV_URL" ]; then
  command -v pac >/dev/null || { echo "pac is required for live mode"; exit 2; }
  for d in "$ROOT"/fixtures/*/; do
    n="$(basename "$d")"
    step "7. live round trip: $n -> $ENV_URL"
    bash "$d/pack.sh" >/dev/null
    for pass in 1 2; do
      if pac solution import --path "$d/$n.zip" --environment "$ENV_URL" --publish-changes 2>&1 | grep -q 'Solution Imported successfully'; then
        echo "   import $pass OK"
      else
        FAILED=$((FAILED + 1)); echo "   import $pass FAILED"
      fi
    done
    rm -rf "$WORK/x-$n"; mkdir -p "$WORK/x-$n"
    if pac solution export --name "$n" --path "$WORK/x-$n.zip" --overwrite --environment "$ENV_URL" 2>&1 | grep -q 'export succeeded'; then
      (cd "$WORK/x-$n" && unzip -q "../x-$n.zip")
      run python3 -I "$ROOT/tests/verify_export.py" "$d/$n" "$WORK/x-$n"
    else
      FAILED=$((FAILED + 1)); echo "   export FAILED"
    fi
    if pac solution export --name "$n" --path "$WORK/m-$n.zip" --managed --overwrite --environment "$ENV_URL" 2>&1 | grep -q 'export succeeded' \
       && unzip -p "$WORK/m-$n.zip" solution.xml | grep -q '<Managed>1</Managed>'; then
      echo "   managed export from dev OK"
    else
      FAILED=$((FAILED + 1)); echo "   managed export FAILED"
    fi
    rm -f "$d/$n.zip"
  done
else
  printf '\n(live import/export round trip skipped: pass a dev environment URL as the first argument)\n'
fi

printf '\n'
if [ "$FAILED" -eq 0 ]; then echo "ALL TESTS PASSED"; else echo "$FAILED CHECK(S) FAILED"; fi
exit "$FAILED"
