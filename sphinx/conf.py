"""Sphinx configuration for the PyOrchestrate API reference.

The useful output is not HTML but the JSON artifact Mintlify consumes:

    python -m sphinx -b json sphinx docs/sdk-artifacts/sphinx-output

This lives outside docs/ because that folder is Mintlify's docs root, and
everything inside it would be published as a page.
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
    "sphinx.ext.napoleon",  # Google-style docstrings, already used in the project
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
# Render "Attributes:" sections as :ivar: fields instead of standalone
# descriptions: without this, every attribute documented in the class docstring
# and also present as a real member is emitted twice.
napoleon_use_ivar = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.11", None),
    "pyzmq": ("https://pyzmq.readthedocs.io/en/latest/", None),
}

exclude_patterns = ["_build"]


def _markdown_fences_to_rst(app, what, name, obj, options, lines):
    """Converts Markdown code fences in docstrings into RST directives.

    The project's docstrings use ```python ... ```, which RST does not
    recognise: without this conversion the block lands on the page as literal
    text and drags the rest of the section along with it. Doing it here avoids
    rewriting the docstrings in RST, which would read worse in the IDE.
    """
    converted = []
    fence_indent = None

    for line in lines:
        stripped = line.lstrip()

        if not stripped.startswith("```"):
            if fence_indent is not None:
                # inside a block: indent 3 spaces under the directive,
                # preserving the code's own relative indentation
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
