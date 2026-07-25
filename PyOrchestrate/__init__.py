"""PyOrchestrate: orchestrate multi-process and multi-thread Python applications.

The package exposes a single source of truth for the version number,
``PyOrchestrate.__version__``, read at runtime from the metadata of the
installed distribution. The value therefore lives only in ``pyproject.toml``:
the CLI and the web interface import it from here instead of repeating it.
"""

from importlib.metadata import PackageNotFoundError, version as _version

try:
    __version__ = _version("PyOrchestrate")
except PackageNotFoundError:  # pragma: no cover - source checkout only
    # The package is not installed. There is nothing to read the version from:
    # once installed, pyproject.toml is not shipped next to the code, and
    # parsing it here would reintroduce the second source of truth this module
    # exists to remove.
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
