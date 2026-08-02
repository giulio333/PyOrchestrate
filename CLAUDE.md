# PyOrchestrate

Python framework for orchestrating multi-process and multi-thread applications
built out of agents. The package is `PyOrchestrate/`, the test suite `test/`,
the documentation site `docs/`, the Sphinx sources behind the API reference
`sphinx/`.

Version 0.2.0, alpha. Requires Python >= 3.11; development happens on the
version in `.python-version` (3.13) and CI runs the suite on 3.11, 3.12 and
3.13 — so no syntax newer than 3.11.

## Language

**Everything in this repository is in English**: code, comments, docstrings,
documentation pages, commit messages, changelog entries, issue and pull request
text. This applies to what you write too, whatever language the conversation is
being held in. `CONTRIBUTING.md` states the policy for humans — contributions
in other languages are sent back for translation — and it applies to you
without exception.

## Code and documentation ship together

**A behaviour change is not finished until its documentation is updated in the
same change.** Whatever the trigger — an issue, a pull request, a drive-by fix
— anything that touches `PyOrchestrate/` carries with it:

1. the narrative pages under `docs/` that describe that behaviour. Grep the
   docs for the class, method or CLI command you touched rather than assuming
   nothing covers it;
2. an entry in `CHANGELOG.md` under `[Unreleased]`, marked **Breaking** when it
   breaks code a user already wrote;
3. the updated docstrings and the regenerated `docs/sdk-artifacts/` (see
   [Documentation](#documentation));
4. tests in `test/`.

Deferring the documentation "to a follow-up PR" is how the site came to
describe `OMemory` methods that did not exist. The recent history is the
standard to match: a fix commit touches the source, the test, the page and the
changelog in one go.

When a change removes or renames something, search `docs/` for the old name.
Stale mentions and warnings that are no longer true on otherwise unrelated
pages are the usual leftovers — several commits exist for no other reason than
cleaning those up afterwards.

## Architecture

An `Orchestrator` owns the lifecycle of isolated execution units (`Agent`s),
each running in its own process or thread. Its internals live in
`PyOrchestrate/core/orchestrator/` and are wired together in `Orchestrator`:

| Component | Role |
| --- | --- |
| `DependencyGraph` | declared inter-agent dependencies and their start order |
| `AgentLifecycleManager` | start, stop and restart of the individual agent |
| `WorkerPoolScheduler` | the worker slots the agents actually run in |
| `OrchestratorEventBus` + `EventStore` | emission and history of the events |
| `MessageRouter` | inbound agent messages routed onto the bus |
| `CommandInterface` | the ZeroMQ endpoint the CLI and the web interface talk to |
| `PluginManager` | orchestrator-level plugins |
| `OMemory` | registry of the agent entries, their groups and lifecycle state |

Agents live in `PyOrchestrate/core/agent/`, each in a `Process` and a `Thread`
flavour: `BaseAgent` (`setup` / `execute` / `on_stop`), `LoopingAgent`
(`execute`, continuous), `PeriodicAgent` (`runner`, on a schedule), `PoolAgent`
(`runner`, work distributed over a pool). `PoolProcessAgent` and
`PoolThreadAgent` are resolved lazily via PEP 562 in
`core/agent/__init__.py`: `pool_agent` imports `Orchestrator`, which imports
`base_agent`, so an eager import would hit a partially initialised module.

Communication plugins (`ZeroMQPubSub`, `ZeroMQReqRep`, `ZeroMQPushPull`,
`ZeroMQRouterDealer`, `ZeroMQPair`, `ZeroMQPoller`) and the heartbeat plugins
live in `PyOrchestrate/core/plugins/`.

Conventions that silently break things when ignored:

- **Call `super()` first in every lifecycle hook.** `setup`, `execute` and
  `runner` do bookkeeping in the base class (counters, limits, plugin
  wiring); skipping the call, or making it last, breaks it.
- **Configuration goes in the inner `Config` class, plugins in the inner
  `Plugin` class**, both re-declared with their type annotation
  (`config: Config`, `plugin: Plugin`). This is the framework's public shape,
  not a stylistic preference.
- **The version number has one source**, `pyproject.toml`, exposed as
  `PyOrchestrate.__version__`. Never write the literal anywhere else.

The CLI (`pyorchestrate`, `PyOrchestrate/cli.py`) exposes `create`, `ps`,
`status`, `dependencies`, `start`, `stop`, `commands`, `shutdown`, `history`,
`history-stats` and `stats`, all speaking to `CommandInterface` over ZeroMQ.
`pyorchestrate-web` serves the FastAPI interface in
`PyOrchestrate/web_interface/`.

## Working on the code

```bash
uv sync --extra web      # dependencies, web extra and dev group into .venv
uv run pytest
```

Before pushing, run what CI runs — the three of them, in this order:

```bash
uv run black --check --diff .    # CI verifies formatting, it does not fix it
uv run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
uv run pytest
```

`black --check` fails the build; the style is pinned in `[tool.black]` (line
length 88, target py311) so it does not depend on the version installed on the
machine. `flake8` reads `.flake8`, which excludes `.venv` — `uv` creates it
inside the project, and without the exclude a local `flake8 .` reports some
sixty findings from third-party sources while CI, which has no `.venv`, reports
none.

**This repo has no devcontainer, and the global "run the tests in the
devcontainer" rule does not apply here.** `.devcontainer/devcontainer.json` was
removed: it declared only `tasks`, with no `image` or `build`, so it defined no
environment and could not be started — following it literally left you stuck.
The isolation comes from `uv`, which rebuilds `.venv` from `uv.lock` without
touching the system interpreter. Do not install dependencies with `pip` on the
host: `uv run` does it by itself in the project venv.

Prefer integration tests over mocks: start a real orchestrator with real agents
and assert on the observable outcome.

## Documentation

The docs are a [Mintlify](https://mintlify.com) site in `docs/`, deployed
automatically on every push to `main`, plus an API Reference tab generated from
the docstrings by Sphinx. **Load the `documentation` skill before editing
anything under `docs/`, `sphinx/` or the docstrings** — it carries the build
and preview commands and the failure modes that cost hours when rediscovered
from scratch (stale `.mint` cache, `mint` CLI version, `broken-links` false
positives).

The four rules that are worth having in mind at all times:

- **Pages are `.mdx`, never `.md`.** In `.md`, Mintlify does not render
  components: `<Tip>`, `<Warning>` and `<Card>` come out as raw text or vanish,
  and it is only visible once deployed.
- **Every page has a `title` in the frontmatter and an entry in
  `docs/docs.json`**, otherwise it exists but is unreachable.
- **Links and images use absolute paths from the docs root, without the
  extension:** `/learn/agents/index`, not `./index.mdx`.
- **Narrative pages link to the API reference for signatures and parameters**
  (`/api/agent`, `/api/plugins`, …) instead of restating them. A signature
  copied by hand into an `.mdx` is a second place it can drift from the code.

After changing docstrings, regenerate the artifact with
`./scripts/build_api_reference.sh` using Python 3.13 and commit
`docs/sdk-artifacts/` alongside the change. New modules must be added to a
`.rst` in `sphinx/` or they will not show up at all. The Sphinx build must stay
at zero warnings.

## Dependencies

- **Core** (`[project.dependencies]`): only what the package actually imports —
  `loguru`, `psutil`, `pyzmq`. Before adding one, check whether it belongs in
  an extra instead.
- **Extra `web`**: `fastapi`, `uvicorn`, `pydantic`, used solely by
  `PyOrchestrate/web_interface/`. Without the extra the web interface is not
  importable: if you add a test or a module touching it, remember CI installs
  `pip install -e ".[web]"`.
- **Group `dev`** (`[dependency-groups]`, PEP 735): pytest, black, flake8,
  pylint, coverage, sphinx. `uv` installs it by default, so `uv run pytest`
  needs no flags. It replaced `requirements-dev.txt`.
- `requirements.txt` is **generated**, never hand-edited. Regenerate it after
  every `uv lock` with the command annotated on its first line. It is one of
  the two files Dependabot reads (the other is `uv.lock`), so an updated lock
  with a stale export leaves alerts open.

## One place for the conventions

This file and the skills under `.claude/skills/` are the only guidance for
assistants in this repo. A parallel set of Copilot files under `.github/`
(`copilot-instructions.md`, `instructions/`, `context/`, `chatmodes/`, 3,672
lines) was removed for a reason worth remembering: nothing kept it in sync, and
by the end it taught four imports that raise `ImportError` — including a
`HeartbeatPlugin` that never existed — in snippets written to be copied. Do not
recreate a second copy of these conventions. If a tool needs its own file, make
it point here rather than restate.
