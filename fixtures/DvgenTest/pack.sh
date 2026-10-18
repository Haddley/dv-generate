#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOLUTION_DIR="$SCRIPT_DIR/DvgenTest"
OUTPUT="$SCRIPT_DIR/DvgenTest.zip"
echo "Packing from: $SOLUTION_DIR"
cd "$SOLUTION_DIR"
rm -f "$OUTPUT"
FILES=("[Content_Types].xml" solution.xml customizations.xml)
[ -d environmentvariabledefinitions ] && FILES+=(environmentvariabledefinitions)
zip -r "$OUTPUT" "${FILES[@]}"
echo "Created: $OUTPUT"
echo ""
echo "Import:  pac solution import --path $OUTPUT"
