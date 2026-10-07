"""
The Python snippets in the documentation, checked against the code.

A reader copies these into a project that type-checks them (the annotations
are shipped, `py.typed`), and a framework `Config` accepts any keyword without
complaint: an unknown one is stored as a user-defined attribute that nothing
reads. Snippets drifted in exactly those two ways, so CI checks:

- every `PyOrchestrate` import resolves, fragments included;
- every complete snippet passes mypy;
- every keyword passed to a framework `Config(...)` is one of its settings.

A *complete* snippet parses and imports from `PyOrchestrate`. A fragment that
continues an earlier block on its page may use names that block defined, so an
undefined name is reported only when it is a module the snippet forgot to
import.
"""

import ast
import difflib
import importlib
import importlib.util
import inspect
import pathlib
import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass

import pytest

# Only to skip cleanly where mypy is not installed: it runs in a subprocess,
# because in-process it leaves a heap so large that the per-test gc.collect()
# in conftest.py slowed the whole suite by half.
pytest.importorskip("mypy")

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = sorted((ROOT / "docs").rglob("*.mdx")) + [ROOT / "README.md"]
FENCE = re.compile(r"```[ \t]*python[^\n]*\n(.*?)```", re.S)
IMPORT_LINE = re.compile(
    r"^[ \t]*(from\s+PyOrchestrate[\w.]*\s+import\s+(?:\([^)]*\)|[^\n]*)"
    r"|import\s+PyOrchestrate[^\n]*)",
    re.M,
)


@dataclass
class Snippet:
    page: pathlib.Path
    index: int
    code: str

    @property
    def where(self) -> str:
        return f"{self.page.relative_to(ROOT)} (python block {self.index + 1})"

    @property
    def tree(self) -> ast.Module | None:
        try:
            return ast.parse(self.code)
        except SyntaxError:
            return None

    @property
    def is_complete(self) -> bool:
        return self.tree is not None and "PyOrchestrate" in self.code


def _snippets() -> list[Snippet]:
    found = []
    for page in PAGES:
        for index, code in enumerate(FENCE.findall(page.read_text())):
            found.append(Snippet(page, index, textwrap.dedent(code)))
    return found


SNIPPETS = _snippets()


def _imports(snippet: Snippet) -> list[ast.Import | ast.ImportFrom]:
    tree = snippet.tree
    if tree is None:
        # A fragment: its import lines may still parse on their own.
        tree = ast.Module(body=[], type_ignores=[])
        for line in IMPORT_LINE.findall(snippet.code):
            try:
                tree.body += ast.parse(line.strip()).body
            except SyntaxError:
                pass
    return [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]


def test_the_documentation_has_python_snippets():
    """Guards the extraction itself: a broken pattern would check nothing."""
    assert len(SNIPPETS) > 100
    assert sum(s.is_complete for s in SNIPPETS) > 40


def test_every_pyorchestrate_import_in_the_docs_resolves():
    failures = []
    for snippet in SNIPPETS:
        for node in _imports(snippet):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if not module.startswith("PyOrchestrate"):
                    continue
                for alias in node.names:
                    try:
                        loaded = importlib.import_module(module)
                        if not hasattr(loaded, alias.name):
                            importlib.import_module(f"{module}.{alias.name}")
                    except Exception as error:
                        failures.append(
                            f"{snippet.where}: from {module} import {alias.name}"
                            f" ({type(error).__name__})"
                        )
            else:
                for alias in node.names:
                    if not alias.name.startswith("PyOrchestrate"):
                        continue
                    try:
                        importlib.import_module(alias.name)
                    except Exception as error:
                        failures.append(
                            f"{snippet.where}: import {alias.name}"
                            f" ({type(error).__name__})"
                        )

    assert not failures, "\n".join(failures)


def _is_module(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def test_every_complete_snippet_type_checks(tmp_path):
    complete = [s for s in SNIPPETS if s.is_complete]
    files = {}
    for number, snippet in enumerate(complete):
        path = tmp_path / f"snippet_{number:03d}.py"
        path.write_text(snippet.code)
        files[path.name] = snippet

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--no-incremental",
            "--check-untyped-defs",
            "--ignore-missing-imports",
            "--python-version",
            "3.11",
            "--no-error-summary",
            "--show-error-codes",
            # An inferred empty container in an example is a style choice, not
            # a mistake a reader would copy.
            "--disable-error-code",
            "var-annotated",
            *[str(tmp_path / name) for name in files],
        ],
        capture_output=True,
        text=True,
        # From the repository root, so PyOrchestrate resolves to its sources.
        # Through the editable install mypy reports spurious `has-type` errors
        # on attributes a subclass reassigns, which a wheel install does not.
        cwd=ROOT,
    )
    stdout, stderr, status = result.stdout, result.stderr, result.returncode

    # 1 means "found errors"; 2 means mypy itself could not run.
    assert status in (0, 1), stdout + stderr

    failures = []
    for line in stdout.splitlines():
        match = re.match(r".*?(snippet_\d+\.py):(\d+): error: (.*)", line)
        if not match:
            continue
        name, lineno, message = match.groups()
        if "[name-defined]" in message:
            undefined = re.search(r'Name "(\w+)" is not defined', message)
            # Defined by an earlier block on the same page, unless it is a
            # module the snippet should have imported.
            if undefined and not _is_module(undefined.group(1)):
                continue
        failures.append(f"{files[name].where}, line {lineno}: {message}")

    assert not failures, "\n".join(failures)


# --- Config keywords --------------------------------------------------------


def _settings(cls: type) -> set[str]:
    names: set[str] = set()
    for klass in cls.__mro__:
        names |= {n for n in vars(klass) if not n.startswith("_")}
        names |= set(getattr(klass, "__annotations__", {}))
        try:
            parameters = inspect.signature(klass.__init__).parameters
        except (TypeError, ValueError):
            continue
        names |= {p for p in parameters if p not in ("self", "args", "kwargs")}
    return names


def _framework_configs() -> dict[str, type]:
    """Names a snippet can use for a framework config, mapped to the class."""
    from PyOrchestrate.core import agent
    from PyOrchestrate.core.base.base import BaseClass, BaseClassConfig
    from PyOrchestrate.core.base.utilities import LoggerConfig
    from PyOrchestrate.core.orchestrator.orchestrator import (
        Orchestrator,
        OrchestratorConfig,
    )
    from PyOrchestrate.core.utilities.validation import ValidationPolicy

    configs: dict[str, type] = {
        "BaseClassConfig": BaseClassConfig,
        "LoggerConfig": LoggerConfig,
        "OrchestratorConfig": OrchestratorConfig,
        "ValidationPolicy": ValidationPolicy,
        "Orchestrator.Config": Orchestrator.Config,
        "BaseClass.Config": BaseClass.Config,
    }
    for name in agent.__all__:
        owner = getattr(agent, name)
        if hasattr(owner, "Config"):
            configs[f"{name}.Config"] = owner.Config
    return configs


def _dotted(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return f"{base}.{node.attr}" if base else None
    return None


def _assigned_names(body: list[ast.stmt]) -> set[str]:
    names = set()
    for statement in body:
        targets = (
            statement.targets
            if isinstance(statement, ast.Assign)
            else [statement.target] if isinstance(statement, ast.AnnAssign) else []
        )
        names |= {t.id for t in targets if isinstance(t, ast.Name)}
    return names


def _snippet_configs(tree: ast.Module, framework: dict[str, type]) -> dict:
    """
    Configs a snippet defines, as `name -> settings`.

    `class MyConfig(PeriodicProcessAgent.Config)` defines `MyConfig`; an inner
    `class Config(...)` of `class MyAgent(...)` defines `MyAgent.Config`. Their
    settings are the base's plus whatever the class body assigns.
    """
    known: dict[str, set[str]] = {k: _settings(v) for k, v in framework.items()}

    def base_settings(bases: list[ast.expr]) -> set[str] | None:
        for base in bases:
            name = _dotted(base)
            if name in known:
                return known[name]
        return None

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        settings = base_settings(node.bases)
        if settings is not None:
            known[node.name] = settings | _assigned_names(node.body)
        for inner in node.body:
            if isinstance(inner, ast.ClassDef) and inner.name == "Config":
                settings = base_settings(inner.bases)
                if settings is not None:
                    known[f"{node.name}.Config"] = settings | _assigned_names(
                        inner.body
                    )
    return known


def test_every_config_keyword_in_the_docs_is_a_setting():
    framework = _framework_configs()
    failures = []
    for snippet in SNIPPETS:
        tree = snippet.tree
        if tree is None:
            continue
        configs = _snippet_configs(tree, framework)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            settings = configs.get(_dotted(node.func) or "")
            if settings is None:
                continue
            for keyword in node.keywords:
                if keyword.arg and keyword.arg not in settings:
                    hint = difflib.get_close_matches(keyword.arg, settings, n=1)
                    failures.append(
                        f"{snippet.where}: {_dotted(node.func)}({keyword.arg}=...)"
                        + (f", did you mean {hint[0]}?" if hint else "")
                    )

    assert not failures, "\n".join(failures)
