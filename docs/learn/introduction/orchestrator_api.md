---
title: Orchestrator API
editLink: false
---

# Orchestrator API

The **Orchestrator API** provides a communication channel for external tools to interact with the Orchestrator.  
It is exposed through a local `UNIX socket`, similar to how Docker communicates with its daemon.

## Interfaces

Two main clients use this channel:

- **Command-Line Interface (CLI):** a lightweight tool for interactive use or scripting.  
  Typical commands: `start`, `stop`, `status`, and runtime queries.  

- **Web UI:** a minimal HTTP layer built on top of the same channel.  
  It can return data as **JSON** for machines or render **HTML** dashboards for humans.  

## What You Can Do

Through these interfaces, you can:

- Start or stop agents dynamically.  
- Inspect running agents and their configurations.  
- Collect performance metrics and orchestrator statistics.  
- Query event history for auditing and debugging.  

## Security Notes

The channel is local by default (filesystem socket).  
To keep it secure, you should:  

- Restrict file permissions.  
- Limit available commands with `allowed_commands` or presets.  
- Protect any HTTP-facing UI with authentication, TLS, or network restrictions.  

## Learn More

For full command references, security guidelines, and usage examples, see the [CLI Documentation](/cli/).  
