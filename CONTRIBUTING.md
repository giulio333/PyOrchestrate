# Contributing to PyOrchestrate

Thanks for taking the time to contribute. This document covers what you need to
know to get a change merged.

## Language

**The repository is in English** — code, comments, docstrings, documentation
pages, commit messages and issues. Contributions in other languages will be
asked to be translated before review.

## Development environment

The project uses [uv](https://docs.astral.sh/uv/). It creates the virtual
environment from `uv.lock`, so everyone gets the same versions:

```bash
uv sync --extra web    # dependencies + web extra + dev group
uv run pytest
```

- The `web` extra brings in `fastapi`, `uvicorn` and `pydantic`, needed only by
  `PyOrchestrate/web_interface/`.
- The `dev` group (pytest, black, flake8, pylint, coverage, sphinx) is
  installed by default, so `uv run <tool>` works with no extra flags.
- Do not install dependencies with `pip` on your host: `uv run` handles it.

Target Python is the version in `.python-version` (3.13). CI runs the suite on
3.11, 3.12 and 3.13, so avoid syntax newer than 3.11.

## Before you open a pull request

Run what CI runs:

```bash
uv run black --check --diff .   # CI verifies formatting, it does not fix it
uv run flake8 . --count --select=E9,F63,F7,F82,F401,F811,F841 --show-source --statistics
uv run pytest
```

Formatting is not negotiable in CI: `black --check` fails the build. The style
is pinned in `[tool.black]` (line length 88, target py311) so it does not
depend on which black version your machine has.

## Tests

Prefer integration tests over mocks: start a real orchestrator with real
agents and assert on the observable outcome. Tests live in `test/`.

## Dependencies

Core dependencies are only what the package actually imports. Before adding
one, check whether it belongs in an extra instead — the `web` extra exists
precisely because the web interface should not be everyone's problem.

After changing `pyproject.toml`:

```bash
uv lock
uv export --format requirements-txt --all-extras --no-dev --no-emit-project \
  --output-file requirements.txt
```

`requirements.txt` is generated, never edited by hand. Dependabot reads both it
and `uv.lock`, so an updated lock with a stale export leaves alerts open.

## Documentation

The docs are a [Mintlify](https://mintlify.com) site in `docs/`, deployed on
every push to `main`. A few rules that are easy to get wrong:

- **Pages are `.mdx`, never `.md`.** In `.md`, Mintlify does not render
  components: `<Tip>`, `<Warning>` and `<Card>` come out as raw text or vanish.
- **Every page needs a `title` in the frontmatter.**
- **Links and images use absolute paths from the docs root, without the
  extension:** `/learn/agents/index`, not `./index.mdx`.
- **Every page must be listed in `docs/docs.json`**, otherwise it exists but is
  unreachable.

Preview locally, clearing the cache first — the dev server keeps the previous
build and will happily show you stale content:

```bash
rm -rf docs/.mint
cd docs
npx mint dev
npx mint broken-links
```

### API reference

The API Reference tab is generated from docstrings, not written by hand:

```bash
./scripts/build_api_reference.sh
```

- Run it with the Python version in `.python-version` (3.13), the same as CI.
  Autodoc renders signatures inherited from the standard library, and those
  change between versions: a different interpreter makes the artifact flip back
  and forth on every build.
- **The Sphinx build must stay at zero warnings.** If warnings appear after
  your change, your change introduced them. In particular, do not add
  `Methods:` sections to docstrings, and put examples in ```` ```python ````
  fences.
- New modules must be added to a file in `sphinx/` or they will not appear.
- Commit the regenerated `docs/sdk-artifacts/` along with your docstring
  change.

Narrative pages should **link to the API reference for signatures and
parameters** rather than restating them. Hand-copied signatures are how the
documentation ends up describing methods that no longer exist.

## Changelog

User-visible changes go in `CHANGELOG.md`, under `[Unreleased]`. Mark anything
that breaks an existing user's code as **Breaking**.

## Commit messages

Follow the existing convention, in English:

```
type: short description in the imperative

feat, fix, docs, style, refactor, test, ci, chore
```
