# Description

<!-- What this changes and why. Link the issue it closes, if any. -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation
- [ ] Maintenance (CI, dependencies, refactor)

## Checklist

- [ ] `uv run pytest` passes
- [ ] `uv run black --check --diff .` is clean — CI verifies formatting, it does not fix it
- [ ] Everything I wrote is in English: code, comments, docstrings, docs
- [ ] `CHANGELOG.md` updated under `[Unreleased]`, with breaking changes marked

## If you touched dependencies

- [ ] `uv lock` run, and `requirements.txt` regenerated with the command in its first line
- [ ] New dependency is core only if the package imports it — otherwise it belongs in an extra

## If you touched docstrings or added a module

- [ ] `./scripts/build_api_reference.sh` run with Python 3.13, artifact committed
- [ ] Sphinx build still reports zero warnings
- [ ] New modules added to the relevant file in `sphinx/`

## If you touched the documentation

- [ ] Pages are `.mdx` with a `title` in the frontmatter
- [ ] Every new page is listed in `docs/docs.json`
- [ ] Links are absolute from the docs root, without the extension
- [ ] `rm -rf docs/.mint && cd docs && npx mint dev` previewed, `npx mint broken-links` clean
- [ ] Signatures and parameters link to the API reference instead of being restated
