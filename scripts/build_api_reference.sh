#!/usr/bin/env bash
# Genera l'artifact JSON che alimenta il tab "API Reference" di Mintlify.
# Va rieseguito quando cambiano le docstring o si aggiungono moduli.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/docs/sdk-artifacts/sphinx-output"

rm -rf "$OUT"
python -m sphinx -b json -E -q -d "$(mktemp -d)/doctrees" "$ROOT/sphinx" "$OUT"

# Cache interna di Sphinx: 2.5 MB inutili per Mintlify, che legge i .fjson.
rm -f "$OUT/environment.pickle" "$OUT/last_build"
rm -rf "$OUT/_static"

echo "Artifact generato in docs/sdk-artifacts/sphinx-output ($(du -sh "$OUT" | cut -f1))"
