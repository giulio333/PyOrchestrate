"""Configurazione Sphinx per l'API reference di PyOrchestrate.

L'output utile non è HTML ma l'artifact JSON che Mintlify consuma:

    python -m sphinx -b json sphinx docs/sdk-artifacts/sphinx-output

Vive fuori da docs/ perché quella cartella è la docs root di Mintlify e
tutto ciò che contiene verrebbe pubblicato come pagina.
"""

import os
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.fspath(ROOT))

project = "PyOrchestrate"
author = "giulio333"
release = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",  # docstring in stile Google, già usate nel progetto
    "sphinx.ext.intersphinx",
]

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "member-order": "bysource",
}
autodoc_typehints = "description"
napoleon_google_docstring = True
napoleon_numpy_docstring = False
# Rende le sezioni "Attributes:" campi :ivar: invece di descrizioni separate:
# senza questo, ogni attributo documentato nella docstring della classe e
# presente anche come membro reale viene emesso due volte.
napoleon_use_ivar = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.11", None),
    "pyzmq": ("https://pyzmq.readthedocs.io/en/latest/", None),
}

exclude_patterns = ["_build"]


def _markdown_fences_to_rst(app, what, name, obj, options, lines):
    """Converte i code fence Markdown delle docstring in direttive RST.

    Le docstring del progetto usano ```python ... ```, che RST non riconosce:
    senza questa conversione il blocco finisce nella pagina come testo
    letterale e trascina con sé il resto della sezione. Farlo qui evita di
    riscrivere le docstring in RST, che nell'IDE risulterebbero meno leggibili.
    """
    converted = []
    fence_indent = None

    for line in lines:
        stripped = line.lstrip()

        if not stripped.startswith("```"):
            if fence_indent is not None:
                # dentro un blocco: rientra di 3 spazi sotto la direttiva,
                # preservando l'indentazione relativa del codice
                converted.append(
                    " " * (fence_indent + 3) + line[fence_indent:]
                    if line.strip()
                    else ""
                )
            else:
                converted.append(line)
            continue

        if fence_indent is None:
            fence_indent = len(line) - len(stripped)
            language = stripped[3:].strip() or "text"
            converted.append(" " * fence_indent + f".. code-block:: {language}")
            converted.append("")
        else:
            converted.append("")
            fence_indent = None

    lines[:] = converted


def setup(app):
    app.connect("autodoc-process-docstring", _markdown_fences_to_rst)
