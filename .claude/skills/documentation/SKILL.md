---
name: documentation
description: Build, preview and maintain the PyOrchestrate documentation — the Mintlify site in docs/ and the Sphinx-generated API reference. Use when editing pages under docs/, adding a page, changing docstrings, regenerating the API reference artifact, or when the local preview shows stale, missing or 404 content.
---

# PyOrchestrate documentation

Two things, in one repo with the code:

- **The Mintlify site** in `docs/` — hand-written `.mdx` pages, deployed
  automatically via GitHub App on every push to `main`. The dashboard has the
  repo in monorepo mode with path `/docs`, so `docs.json` lives at
  `docs/docs.json` and every path in the navigation is relative to `docs/`
  (`learn/agents/index`, not `docs/learn/agents/index`).
- **The API Reference tab** — not written by hand. Sphinx reads the docstrings
  and emits a JSON artifact into `docs/sdk-artifacts/`, which Mintlify consumes
  through its *SDK reference* feature (`"sdk": {"format": "sphinx"}` in
  `docs.json`). The artifact is committed because Mintlify reads it from the
  repo; `docs/.mintignore` keeps it from being published as static content.

## Local preview

```bash
rm -rf docs/.mint          # see the cache note below — always
cd docs
npx mint dev               # http://localhost:3000
npx mint broken-links      # internal link check
```

Run it before pushing any documentation change.

> **Always clear `docs/.mint` before starting `mint dev`.** The dev server
> caches the previous build there and does not re-read everything from scratch
> — the Sphinx artifact in particular. Skip this and you keep seeing the old
> version and conclude your change had no effect: it has already happened both
> with the API reference pages and with the `/api/...` slugs after moving the
> `.rst` files. If a change "doesn't show up", suspect the cache before you
> suspect the configuration.

> **If the API Reference tab is empty locally, it is the CLI version, not the
> configuration.** `mint` >= 4.2.742 is required: with 4.2.507 the dev server
> did not render the SDK reference feature — the tab appeared in the bar but
> was empty and every `/api/...` returned 404. Note that `npx mint` prefers the
> globally installed binary and will **not** fetch the newer version by itself:
>
> ```bash
> npm install -g mint@latest    # then check: mint --version
> ```
>
> Do not touch `docs.json` chasing this symptom. The config is valid against
> the Mintlify schema (`mint validate` passes) and the artifact is read even
> though `sdk-artifacts/` is in `.mintignore`. Both verified.

> **`mint broken-links` reports every `/api/...` link as broken: false
> positives.** The checker only looks at pages backed by an `.mdx` file and
> knows nothing about the ones generated from the SDK artifact, so it keeps
> reporting them even with an up-to-date CLI and a dev server serving them at
> 200. Before "fixing" one of those links, try it at
> `http://localhost:3000/api/...`. The correct slugs are `/api/<rst-name>`, per
> `directory: "api"` in `docs.json`.

## Writing pages

- **Pages are `.mdx`, never `.md`.** In `.md` Mintlify does not render
  components: `<Tip>`, `<Warning>` and `<Card>` come out as raw text or vanish
  entirely, and the problem only surfaces once deployed.
- **Every page has a `title` in the frontmatter.**
- **Links and images use absolute paths from the docs root, without the
  extension:** `/learn/agents/index`, not `./index.mdx` nor
  `../agents/index.md`.
- **Every page must be listed in `docs/docs.json`**, otherwise it exists but is
  unreachable from the navigation.
- Diagrams come in light/dark pairs, swapped with `className="block dark:hidden"`
  and `"hidden dark:block"`.
- When a page moves, add a `redirects` entry in `docs.json` instead of leaving
  the old URL dead.
- Everything is written in English, like the rest of the repo.

## API reference

```bash
./scripts/build_api_reference.sh   # needs sphinx, run under Python 3.13
```

> **Always regenerate with the Python version in `.python-version` (3.13), the
> same one the workflow uses.** Autodoc also renders signatures inherited from
> the standard library, and those change between versions: generating with a
> different Python makes the artifact flip back and forth on every build —
> `enum.Enum`'s signature changed in 3.12 — and CI produces regeneration
> commits matching no docstring change at all. If the artifact diff shows
> signature changes you did not cause, you are on the wrong interpreter.

- `sphinx/conf.py` — configuration (autodoc + napoleon, Google-style
  docstrings).
- `sphinx/*.rst` — one file per section (`agent`, `orchestrator`, `plugins`,
  `utilities`, `base`, `cli`, `web`). **New modules go here** and into the
  toctree in `sphinx/index.rst`, or they never appear in the reference.
- The `.rst` files sit at the root of `sphinx/`, not in a subdirectory:
  Mintlify appends the internal path to `directory` from `docs.json` and you
  would get URLs like `/api/api/agent`.
- **The Sphinx build must stay at zero warnings.** If warnings appear after
  your change, your change introduced them. In particular do not add
  `Methods:` sections to docstrings, and put examples in ```` ```python ````
  fences.
- Narrative pages **link to the reference for signatures and parameters**
  (`/api/plugins`, `/api/agent`, …) instead of copying them. A hand-written
  signature in an `.mdx` is a second place it can drift from the code, and it
  is the mechanism that produced the phantom `OMemory` methods.

The artifact regenerates itself on `main` when the Python sources change, via
`.github/workflows/docs-api-reference.yml`. Locally it is a manual step after
editing docstrings — commit `docs/sdk-artifacts/` together with the docstring
change so the branch is self-consistent.

After every regeneration, restart `mint dev` with the cache cleared, per the
preview note above, or you keep looking at the previous reference.

## When the code changes

Documentation moves in the same change as the code — this is the rule stated in
`CLAUDE.md`, and this is the checklist for it:

1. Grep `docs/` for the class, method or CLI command you touched, and update
   every narrative page that covers it. Do not assume there is none.
2. If you renamed or removed something, grep `docs/` for the **old** name too:
   stale mentions and warnings that are no longer true, on pages otherwise
   unrelated to your change, are the usual leftovers.
3. Docstrings updated → `./scripts/build_api_reference.sh` → commit
   `docs/sdk-artifacts/`.
4. New module → add it to a `.rst` in `sphinx/` and to `sphinx/index.rst`.
5. New page → add it to `docs/docs.json`.
6. Add the user-visible change to `CHANGELOG.md` under `[Unreleased]`, marked
   **Breaking** when it breaks code a user already wrote.
7. Preview locally with the cache cleared before pushing.
