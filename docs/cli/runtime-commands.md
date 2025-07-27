---
title: Runtime Commands
editLink: true
---

# Runtime Commands

Runtime commands allow you to interact with a running PyOrchestrate orchestrator in real-time via UNIX sockets. This enables dynamic control, monitoring, and debugging without stopping your application.

## Prerequisites

To use runtime commands, your orchestrator must be configured with the command interface enabled:

```python
from PyOrchestrate.core.orchestrator import BaseOrchestrator

class MyOrchestrator(BaseOrchestrator):
    class Config(BaseOrchestrator.Config):
        enable_command_interface: bool = True  # Enable command interface
        command_socket_path: str = "/tmp/pyorchestrate.sock"  # Socket path
```

## Command Syntax

All runtime commands follow this pattern:

```bash
pyorchestrate <command> [arguments] <socket_path>
```

Where:
- `<command>` is the runtime command to execute
- `[arguments]` are command-specific parameters
- `<socket_path>` is the path to the orchestrator's UNIX socket

## Available Commands

### `ps`

List all agents with their current status.

```bash
pyorchestrate ps <socket_path>
```

**Terminal output:**
```
NAME             STATUS    PID     UPTIME
WeatherAgent     running   12345   00:15:32
DataProcessor    waiting   12346   00:15:30
AlertManager     running   12347   00:15:28
```

**JSON output:**
```json
{
  "status": "success",
  "data": {
    "agents": [
      {
        "name": "WeatherAgent",
        "status": "running",
        "pid": 12345,
        "uptime": "00:15:32"
      },
      {
        "name": "DataProcessor", 
        "status": "waiting",
        "pid": 12346,
        "uptime": "00:15:30"
      }
    ]
  },
  "timestamp": "2025-07-27T10:30:00Z"
}
```

### `start`

Start a specific agent by name.

```bash
pyorchestrate start <agent_name> <socket_path>
```

**Example:**
```bash
pyorchestrate start WeatherAgent
```

**Terminal output:**
```
✓ Agent 'WeatherAgent' started successfully (PID: 12347)
```

**JSON output:**
```json
{
  "status": "success", 
  "data": {
    "agent": "WeatherAgent",
    "action": "started",
    "pid": 12347
  },
  "timestamp": "2025-07-27T10:35:00Z"
}
```

### `stop`

Stop a specific agent by name.

```bash
pyorchestrate stop <agent_name> <socket_path>
```

**Example:**
```bash
pyorchestrate stop WeatherAgent
```

**Terminal output:**
```
✓ Agent 'WeatherAgent' stopped gracefully
```

**JSON output:**
```json
{
  "status": "success",
  "data": {
    "agent": "WeatherAgent", 
    "action": "stopped",
    "graceful_shutdown": true
  },
  "timestamp": "2025-07-27T10:40:00Z"
}
```

### `status`

Get detailed status information for a specific agent.

```bash
pyorchestrate status <agent_name> <socket_path>
```

**Example:**
```bash
pyorchestrate status WeatherAgent
```

**Terminal output:**
```
Agent: WeatherAgent
Status: running
PID: 12345
Uptime: 00:20:15
Memory: 45.2 MB
CPU: 2.3%
Last Activity: 2025-07-27T10:39:45Z

Configuration:
  execution_interval: 300
  timeout: 30
```

**JSON output:**
```json
{
  "status": "success",
  "data": {
    "name": "WeatherAgent",
    "status": "running",
    "pid": 12345,
    "uptime": "00:20:15",
    "memory_usage": "45.2 MB",
    "cpu_usage": "2.3%",
    "last_activity": "2025-07-27T10:39:45Z",
    "configuration": {
      "execution_interval": 300,
      "timeout": 30
    }
  },
  "timestamp": "2025-07-27T10:45:00Z"
}
```

### `stats`

Get comprehensive statistics about the orchestrator and all agents.

```bash
pyorchestrate stats <socket_path>
```

**Terminal output:**
```
Orchestrator Statistics
=======================
Uptime: 02:15:32
Total Agents: 5
Running: 3  |  Waiting: 2  |  Failed: 0

System Resources:
  Memory: 256.8 MB
  CPU: 15.2%
  Open Files: 42

Dependencies:
  Total: 8  |  Satisfied: 8  |  Unsatisfied: 0
```

**JSON output:**
```json
{
  "status": "success",
  "data": {
    "orchestrator": {
      "uptime": "02:15:32",
      "total_agents": 5,
      "running_agents": 3,
      "waiting_agents": 2,
      "failed_agents": 0
    },
    "system": {
      "memory_usage": "256.8 MB",
      "cpu_usage": "15.2%",
      "open_files": 42
    },
    "dependencies": {
      "total_dependencies": 8,
      "satisfied": 8,
      "unsatisfied": 0
    }
  },
  "timestamp": "2025-07-27T10:50:00Z"
}
```

### `report`

Generate a comprehensive report of the entire orchestrator state.

```bash
pyorchestrate report <socket_path>
```

**Terminal output:**
```
PyOrchestrate System Report
===========================
Generated: 2025-07-27T11:00:00Z

Orchestrator Configuration:
  Name: WeatherOrchestrator
  Socket: /tmp/weather_orchestrator.sock
  Uptime: 02:15:32

Agent Details:
  WeatherAgent (PID: 12345)    - running   - Memory: 45.2 MB
  DataProcessor (PID: 12346)   - waiting   - Memory: 32.1 MB
  AlertManager (PID: 12347)    - running   - Memory: 28.9 MB

System Resources:
  Total Memory: 256.8 MB
  CPU Usage: 15.2%
  Load Average: 0.85, 0.72, 0.68

Dependencies Graph:
  ✓ WeatherAgent → DataProcessor
  ✓ DataProcessor → AlertManager
  ✓ All dependencies satisfied

Performance Metrics:
  Messages processed: 1,247
  Average response time: 125ms
  Error rate: 0.2%
```

This command provides detailed information including:
- Orchestrator configuration
- Agent details and dependencies
- System resource usage
- Performance metrics
- Event history summary

### `shutdown`

Gracefully shutdown the orchestrator and all agents.

```bash
pyorchestrate shutdown <socket_path>
```

**Terminal output:**
```
Initiating graceful shutdown...
Stopping 5 agents in dependency order...
✓ AlertManager stopped
✓ DataProcessor stopped  
✓ WeatherAgent stopped
✓ All agents stopped successfully
✓ Orchestrator shutdown complete

Estimated time: 30 seconds
```

**JSON output:**
```json
{
  "status": "success",
  "data": {
    "action": "shutdown_initiated",
    "agents_to_stop": 5,
    "estimated_time": "30 seconds"
  },
  "timestamp": "2025-07-27T11:00:00Z"
}
```

::: warning Graceful Shutdown
The shutdown command will stop all agents in dependency order and then terminate the orchestrator. This operation cannot be undone.
:::

## Error Handling

All commands return structured JSON responses with error information when something goes wrong:

```json
{
  "status": "error",
  "error": {
    "code": "AGENT_NOT_FOUND",
    "message": "Agent 'InvalidAgent' not found in orchestrator",
    "details": {
      "available_agents": ["WeatherAgent", "DataProcessor"]
    }
  },
  "timestamp": "2025-07-27T11:05:00Z"
}
```

Common error codes:
- `AGENT_NOT_FOUND`: Specified agent doesn't exist
- `AGENT_ALREADY_RUNNING`: Agent is already in requested state
- `PERMISSION_DENIED`: Insufficient permissions for operation
- `SOCKET_CONNECTION_ERROR`: Cannot connect to orchestrator socket
- `ORCHESTRATOR_BUSY`: Orchestrator is processing another command

## Integration Examples

### Shell Scripts

```bash
#!/bin/bash
# Monitor script example

SOCKET="/tmp/pyorchestrate.sock"

# Check if orchestrator is responsive
if pyorchestrate stats "$SOCKET" > /dev/null 2>&1; then
    echo "Orchestrator is running"
    
    # Get running agent count
    RUNNING=$(pyorchestrate stats "$SOCKET" | jq '.data.orchestrator.running_agents')
    echo "Running agents: $RUNNING"
else
    echo "Orchestrator is not responsive"
    exit 1
fi
```

### Python Integration

```python
import json
import subprocess


def get_orchestrator_status(socket_path):
    """Get orchestrator status via CLI."""
    try:
        result = subprocess.run(
            ["pyorchestrate", "status", "--socket", socket_path, "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return None

# Usage
status = get_orchestrator_status("/tmp/pyorchestrate.sock")
if status:
    if status.get("status") == "success":
        data = status["data"]
        print(f"Orchestrator Status:")
        print(f"  Total agents: {data.get('total_agents', 'unknown')}")
        print(f"  Running agents: {data.get('running_agents', 'unknown')}")
        print(f"  Waiting agents: {data.get('waiting_agents', 'unknown')}")
        print(f"  Max workers: {data.get('max_workers', 'unknown')}")
        print(f"  Socket path: {data.get('command_socket_path', 'unknown')}")
    else:
        print(f"Error: {status.get('message', 'Unknown error')}")
else:
    print("Failed to get orchestrator status")
```

## Troubleshooting

### Socket Connection Issues

```bash
# Check if socket exists
ls -la /tmp/pyorchestrate.sock

# Check socket permissions
stat /tmp/pyorchestrate.sock

# Test basic connectivity
pyorchestrate stats /tmp/pyorchestrate.sock
```

### Permission Errors

Ensure your user has read/write permissions to the socket file:

```bash
# Set socket permissions (run as orchestrator user)
chmod 660 /tmp/pyorchestrate.sock
chgrp mygroup /tmp/pyorchestrate.sock
```