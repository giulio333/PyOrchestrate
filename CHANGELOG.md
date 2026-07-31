# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed

- **Breaking:** `PyOrchestrate.settings` has been removed. `LOG_FOLDER` and
  `LOG_LEVEL` were read by nothing, and `LOG_FOLDER` pointed inside the
  installed package (`site-packages/PyOrchestrate/logs`), which is not a
  writable location. Configure logging through `LoggerFactory.set_defaults()`
  or the agent's `logger_config` instead.
- `PyOrchestrate/web_interface/static.js`, referenced by nothing and not
  shipped in the wheel.
- The `if __name__ == "__main__"` demo blocks in
  `PyOrchestrate/core/utilities/scheduler.py` and
  `PyOrchestrate/utilities/logguru.py`. Examples belong in `examples/`.
- `requirements-dev.txt` and `requirements-web.txt`, replaced by the `dev`
  dependency group and the `web` extra in `pyproject.toml`.
- `.devcontainer/`, which declared only `tasks` — no `image`, `build` or
  `dockerComposeFile` — and therefore never defined a usable environment. Use
  `uv sync --extra web && uv run pytest`.

### Changed

- **Breaking:** `fastapi`, `uvicorn` and `pydantic` are no longer core
  dependencies. They are only used by the web interface and now live in the
  `web` extra: install with `pip install "PyOrchestrate[web]"` to keep
  `pyorchestrate-web` working.
- **Breaking:** `requests` is no longer a dependency. The package never
  imported it; only the examples do. Install it yourself to run those.
- **Breaking:** `Scheduler` uses English identifiers. `funzione` is now `func`
  and `calcola_ritardo_iniziale` is now `compute_initial_delay`.
- The version number has a single source of truth. It is declared only in
  `pyproject.toml` and exposed as `PyOrchestrate.__version__`, read from the
  distribution metadata. `CLIConstants.VERSION` and the FastAPI `version` now
  derive from it instead of repeating the literal.
- Dependencies upgraded to close the advisories reported against the
  repository, including `starlette` 1.3.1 (via `fastapi` 0.140.0) and
  `urllib3` 2.7.0.
- Docstrings, comments and error messages translated to English across
  `scheduler.py`, `logguru.py`, `memory.py` and the Sphinx configuration.

### Fixed

- The `shutdown` command left every agent running. It only set
  `_shutdown_requested`, which made `Orchestrator.join()` leave its loop and go
  straight to closing the message router and finalizing plugins: agents
  survived with their service channel already closed, and non-daemon threads
  kept the interpreter alive. `join()` now stops every agent, waits for them
  within `agent_stop_timeout`, force-terminates surviving process agents and
  reports any thread agent that cannot be terminated, all before the channel
  handlers and the plugins are shut down.
- `PoolAgentConfig` declared its class default as `agent_entry` while the rest
  of the class used `agents_entry`. A `PoolAgent` without an explicit
  `agents_entry` raised `AttributeError` inside `setup()` instead of emitting
  the documented validation warning.
- `ZeroMQPair.finalize()` had an empty body and never released its socket or
  context, unlike the other four ZeroMQ plugins. Each agent shutdown leaked a
  file descriptor and an I/O thread.

### Added

- `Orchestrator.Config.agent_stop_timeout` (default `10.0`), the budget shared
  by all agents while shutdown waits for them to terminate.
- `WorkerPoolScheduler.shutdown_all()` and `AgentLifecycleManager.shutdown_all()`,
  the blocking counterparts of `stop_all()` used by the shutdown path. They
  return the names of the agents that are still alive afterwards.
- Documentation for `PoolAgent` (`PoolProcessAgent`, `PoolThreadAgent`) and for
  the four previously undocumented ZeroMQ plugins: `ZeroMQPushPull`,
  `ZeroMQRouterDealer`, `ZeroMQPair` and `ZeroMQPoller`.
- `PyOrchestrate.cli` and `PyOrchestrate.web_interface.server` in the generated
  API reference.
- `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md` and issue/pull request
  templates.

## [0.2.0]

First versions tracked before this changelog existed. See the
[commit history](https://github.com/giulio333/PyOrchestrate/commits/main) for
details.

[Unreleased]: https://github.com/giulio333/PyOrchestrate/compare/main...HEAD
[0.2.0]: https://github.com/giulio333/PyOrchestrate/releases/tag/v0.2.0
