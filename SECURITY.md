# Security Policy

## Supported versions

PyOrchestrate is at an early stage (`Development Status :: 3 - Alpha`). Only
the latest release receives security fixes.

| Version | Supported |
| ------- | --------- |
| 0.2.x   | Yes       |
| < 0.2   | No        |

## Reporting a vulnerability

**Do not open a public issue for a security problem.**

Report it privately through GitHub's
[Report a vulnerability](https://github.com/giulio333/PyOrchestrate/security/advisories/new)
form, which creates a draft advisory visible only to the maintainers.

Please include:

- what the problem is and what an attacker gains from it;
- the affected version and platform;
- steps to reproduce, ideally a minimal script;
- any workaround you already found.

You can expect an acknowledgement within a few days. Since this is a
volunteer-maintained project, there is no guaranteed remediation deadline —
the report will be triaged and you will be told what the plan is.

## Scope

Worth reporting:

- the CLI's command socket or the ZeroMQ endpoint accepting commands from a
  peer that should not be able to send them;
- the web interface (`pyorchestrate-web`) exposing data beyond its read-only
  contract, or its authentication being bypassable when enabled;
- code execution triggered by data that a user would reasonably treat as
  untrusted.

Out of scope, because they are documented behaviour rather than flaws:

- binding the orchestrator or the web interface to a public interface. Both
  default to `127.0.0.1`; exposing them to a network is the operator's
  decision, and they carry no transport encryption.
- agents running arbitrary Python. That is what the framework is for: an agent
  is your code, and PyOrchestrate is not a sandbox.
- vulnerabilities in dependencies with no exploitable path through this
  package. Report those upstream; Dependabot already tracks them here.

## Dependencies

Dependency versions are pinned in `uv.lock` and mirrored in
`requirements.txt`, both of which Dependabot scans. Advisories are addressed by
upgrading the lock rather than by patching vendored code.
