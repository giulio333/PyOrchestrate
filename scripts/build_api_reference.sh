#!/usr/bin/env bash
# Generates the JSON artifact behind Mintlify's "API Reference" tab.
# Re-run it whenever the docstrings change or a module is added.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/docs/sdk-artifacts/sphinx-output"

rm -rf "$OUT"
python -m sphinx -b json -E -q -d "$(mktemp -d)/doctrees" "$ROOT/sphinx" "$OUT"

# Sphinx's internal cache: 2.5 MB of no use to Mintlify, which reads the .fjson.
rm -f "$OUT/environment.pickle" "$OUT/last_build"
rm -rf "$OUT/_static"

echo "Artifact written to docs/sdk-artifacts/sphinx-output ($(du -sh "$OUT" | cut -f1))"
