---
title: CommandInterface
editLink: true
---

# CommandInterface

The **CommandInterface** provides external control of the orchestrator through a command-based API exposed over a ZeroMQ socket. It enables CLI tools and other external clients to query and control the orchestrator at runtime.

## Purpose and Design

The CommandInterface allows you to interact with a running orchestrator without modifying your application code. This is particularly useful for:

- **Production monitoring**: Query agent status without stopping the system
- **Runtime control**: Pause, resume, or shutdown agents dynamically
- **Debugging**: Inspect agent states and event history
- **CI/CD Integration**: Automated health checks and deployment verification

## Core Responsibilities

| Responsibility | Description |
|---------------|-------------|
| **Command Reception** | Listen for commands via ZMQ REQ/REP socket |
| **Command Validation** | Validate commands against allowed whitelist |
| **Command Execution** | Execute approved commands and return results |
| **Event Recording** | Log command executions to event history |
| **Security** | Enforce command restrictions via whitelist |

## Architecture

```
CLI Tool / External Client
    ↓ (ZMQ REQ socket)
CommandInterface (ZMQ REP socket)
    ↓ validates command
    ↓ executes command
    ↓ records to EventStore
    ↓ (ZMQ REP socket)
CLI Tool receives JSON response
```

## Configuration

### Enabling CommandInterface

The CommandInterface is **disabled by default** for security. Enable it in the orchestrator configuration:

```python
config = OrchestratorConfig(
    enable_command_interface=True,
    command_zmq_address="tcp://127.0.0.1:5570",
    allowed_commands="basic"  # Security level
)

orchestrator = Orchestrator(config=config)
```

### Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `enable_command_interface` | `bool` | Enable/disable command interface (default: `False`) |
| `command_zmq_address` | `str` | ZMQ socket address (default: `"tcp://127.0.0.1:5570"`) |
| `allowed_commands` | `str` or `set` | Command whitelist preset or custom set |

### Command Whitelist Presets

The `allowed_commands` setting controls which commands are permitted:

```python
# Basic commands only (safe for production)
config = OrchestratorConfig(
    allowed_commands="basic"
)
# Allows: ps, status

# Monitoring commands (read-only operations)
config = OrchestratorConfig(
    allowed_commands="monitoring"
)
# Allows: ps, status, stats, history

# All commands (use with caution!)
config = OrchestratorConfig(
    allowed_commands="all"
)
# Allows: ps, status, stats, history, shutdown, and more

# Custom whitelist
config = OrchestratorConfig(
    allowed_commands={"ps", "status"}
)
# Allows only specified commands
```

## Available Commands

### `ps` - List Agents

Lists all registered agents with their current status.

**CLI Usage**:
```bash
pyorchestrate ps
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "agents": [
      {
        "name": "worker1",
        "state": "running",
        "pid": 12345
      },
      {
        "name": "worker2",
        "state": "completed",
        "pid": null
      }
    ]
  }
}
```

### `status` - Agent Status

Get detailed status of a specific agent or all agents.

**CLI Usage**:
```bash
pyorchestrate status
pyorchestrate status worker1
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "agent_name": "worker1",
    "state": "running",
    "uptime_seconds": 127.5,
    "last_heartbeat": "2025-10-26T14:30:00Z"
  }
}
```

### `stats` - System Statistics

Get orchestrator and agent statistics.

**CLI Usage**:
```bash
pyorchestrate stats
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "total_agents": 10,
    "running": 8,
    "completed": 2,
    "max_workers": 10,
    "uptime_seconds": 3600
  }
}
```

### `history` - Event History

Query event history with optional filters.

**CLI Usage**:
```bash
pyorchestrate history --limit 50
pyorchestrate history --category agent --limit 20
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "events": [
      {
        "event_name": "AGENT_STARTED",
        "agent_name": "worker1",
        "timestamp": "2025-10-26T14:25:00Z"
      },
      {
        "event_name": "AGENT_READY",
        "agent_name": "worker1",
        "timestamp": "2025-10-26T14:25:02Z"
      }
    ]
  }
}
```

### `shutdown` - Graceful Shutdown

Initiate graceful shutdown of the orchestrator.

**CLI Usage**:
```bash
pyorchestrate shutdown
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "message": "Shutdown initiated"
  }
}
```

⚠️ **Security Warning**: Only enable this command in controlled environments!

## Security Considerations

### Command Whitelist Strategy

Choose your security level based on environment:

**Development**:
```python
# All commands allowed for testing
config = OrchestratorConfig(
    allowed_commands="all"
)
```

**Staging/QA**:
```python
# Monitoring commands only
config = OrchestratorConfig(
    allowed_commands="monitoring"
)
```

**Production**:
```python
# Basic commands only
config = OrchestratorConfig(
    allowed_commands="basic"
)

# Or even more restrictive
config = OrchestratorConfig(
    allowed_commands={"ps"}  # Only list agents
)
```

### Network Security

**Bind to localhost only** (default):
```python
config = OrchestratorConfig(
    command_zmq_address="tcp://127.0.0.1:5570"  # Local only
)
```

**Allow network access** (use with authentication):
```python
config = OrchestratorConfig(
    command_zmq_address="tcp://0.0.0.0:5570"  # All interfaces
)
# ⚠️ Requires additional security measures!
```

### Rejected Command Response

When a command is not in the whitelist:

```json
{
  "status": "error",
  "code": 403,
  "error": "Command 'shutdown' not allowed"
}
```

## Integration with CLI

The PyOrchestrate CLI uses the CommandInterface to communicate with running orchestrators:

```bash
# CLI connects to default address
pyorchestrate ps

# CLI connects to custom address
pyorchestrate --address tcp://192.168.1.100:5570 ps

# CLI waits for orchestrator to be ready
pyorchestrate status --wait
```

## Event Recording

All command executions are recorded to the EventStore:

```python
# Command execution is automatically logged
orchestrator.event_bus.event_store.query(
    category="command",
    limit=10
)

# Returns:
# [
#   {"event_name": "COMMAND_EXECUTED", "command": "ps", "timestamp": "..."},
#   {"event_name": "COMMAND_EXECUTED", "command": "status", "timestamp": "..."},
# ]
```

This provides an audit trail of all external interactions.

## Lifecycle Management

### Automatic Startup

The CommandInterface starts automatically when enabled:

```python
# In Orchestrator.__init__()
if config.enable_command_interface:
    self.command_interface = CommandInterface(...)
    self.command_interface.start()  # Starts ZMQ listener
```

### Graceful Shutdown

The interface is stopped during orchestrator cleanup:

```python
# In Orchestrator.join()
if self.command_interface:
    self.command_interface.stop(timeout=2.0)
    # Waits for pending commands to complete
```

## Error Handling

### Connection Errors

```json
{
  "status": "error",
  "code": 500,
  "error": "Internal server error: connection failed"
}
```

### Malformed Requests

```json
{
  "status": "error",
  "code": 400,
  "error": "Invalid command format"
}
```

### Command Execution Failures

```json
{
  "status": "error",
  "code": 500,
  "error": "Failed to execute command: agent not found"
}
```

## Common Patterns

### Health Check in CI/CD

```bash
#!/bin/bash
# Wait for orchestrator to be ready
pyorchestrate status --wait --timeout 60

# Check all agents are running
agents=$(pyorchestrate ps --json | jq '.data.agents | length')

if [ $agents -eq 10 ]; then
  echo "All agents running"
  exit 0
else
  echo "Only $agents agents running"
  exit 1
fi
```

### Production Monitoring

```python
import zmq

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://orchestrator-host:5570")

# Send command
socket.send_json({
    "command": "stats",
    "args": []
})

# Receive response
response = socket.recv_json()
print(f"Running agents: {response['data']['running']}")
```

### Graceful Deployment

```bash
# 1. Check current status
pyorchestrate status

# 2. Initiate graceful shutdown
pyorchestrate shutdown

# 3. Wait for completion
while pyorchestrate status 2>/dev/null; do
  echo "Waiting for shutdown..."
  sleep 2
done

# 4. Deploy new version
./deploy_new_version.sh
```

## Testing

### Testing with Mock Socket

```python
import unittest
from unittest.mock import Mock, patch

class TestCommandInterface(unittest.TestCase):
    @patch('zmq.Context')
    def test_command_execution(self, mock_zmq):
        # Setup mock socket
        mock_socket = Mock()
        mock_zmq.return_value.socket.return_value = mock_socket
        
        # Test command interface
        interface = CommandInterface(...)
        interface.handle_command({
            "command": "ps",
            "args": []
        })
        
        # Verify response
        mock_socket.send_json.assert_called_once()
```

## Best Practices

### 1. Use Appropriate Security Level

```python
# Good: Restrictive in production
config = OrchestratorConfig(
    allowed_commands="basic"  # Read-only
)

# Avoid: Too permissive in production
config = OrchestratorConfig(
    allowed_commands="all"  # Dangerous!
)
```

### 2. Bind to Localhost by Default

```python
# Good: Local access only
command_zmq_address="tcp://127.0.0.1:5570"

# Avoid: Network access without security
command_zmq_address="tcp://0.0.0.0:5570"
```

### 3. Monitor Command Usage

```python
# Track command execution frequency
commands = orchestrator.event_bus.event_store.query(
    category="command",
    limit=100
)

command_counts = {}
for event in commands:
    cmd = event.data.get("command")
    command_counts[cmd] = command_counts.get(cmd, 0) + 1

print(f"Command usage: {command_counts}")
```

### 4. Implement Timeouts

```python
# CLI should timeout if orchestrator is unresponsive
import zmq

socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
try:
    response = socket.recv_json()
except zmq.Again:
    print("Orchestrator not responding")
```

## Debugging

### Test Connection

```python
import zmq

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://127.0.0.1:5570")

socket.send_json({"command": "ps", "args": []})
print(socket.recv_json())
```

### Enable Debug Logging

```python
import logging
logging.getLogger("PyOrchestrate.CommandInterface").setLevel(logging.DEBUG)
```

## See Also

- [CLI Reference](../../cli/runtime-commands.md) - Complete CLI command documentation
- [OrchestratorEventBus](./event-bus.md) - Event recording
- [MessageChannel](../utilities/message-channel.md) - Low-level communication
- [Orchestrator Internals](./index.md) - Architecture overview
