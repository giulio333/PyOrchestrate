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
pyorchestrate <command> [arguments] [options]
```

Where:
- `<command>` is the runtime command to execute
- `[arguments]` are command-specific parameters
- `[options]` are common options like `--socket` and `--format`

### Common Options

All runtime commands support these options:

- `--socket SOCKET_PATH`: Path to the orchestrator's UNIX socket (default: `/tmp/pyorchestrate.sock`)
- `--format FORMAT`: Output format - `table` (human-readable, default) or `json` (machine-readable)

### Output Formats

The CLI supports two main output formats:

1. **Table format (`table`)**: Human-readable output with formatted tables and colors
2. **JSON format (`json`)**: Structured output for automation and scripting

To specify the format:
```bash
pyorchestrate ps --format table    # Human-readable output (default)
pyorchestrate ps --format json     # JSON output
```

## CLI Version

To check the CLI version:

```bash
pyorchestrate --version
pyorchestrate -v
```

Output:
```
PyOrchestrate version 0.2.0
```

## Available Commands

### `ps`

```bash
pyorchestrate ps [--socket SOCKET_PATH] [--format FORMAT]
```

**Options:**
- `--socket`: Orchestrator socket path (default: `/tmp/pyorchestrate.sock`)
- `--format`: Output format - `table` (default) or `json`

**Table format output:**
```
Orchestrator Status: 3/5 agents running
Waiting in queue: 2

Name                 Status     Started  In Queue
--------------------------------------------------
WeatherAgent         ALIVE      YES      NO
DataProcessor        DEAD       NO       YES
AlertManager         ALIVE      YES      NO
```

**Output formato JSON:**
```json
{
  "status": "success",
  "data": {
    "agents": [
      {
        "agent_name": "WeatherAgent",
        "alive": true,
        "started": true,
        "in_queue": false
      },
      {
        "agent_name": "DataProcessor",
        "alive": false,
        "started": false,
        "in_queue": true
      }
    ],
    "running_count": 3,
    "max_workers": 5,
    "waiting_count": 2
  }
}
```

### `start`

Start a specific agent by name.

```bash
pyorchestrate start [AGENT_NAME] [--socket SOCKET_PATH] [--format FORMAT]
```

**Parameters:**
- `AGENT_NAME`: Name of the agent to start (optional if specified in command)

**Options:**
- `--socket`: Orchestrator socket path (default: `/tmp/pyorchestrate.sock`)
- `--format`: Output format - `table` (default) or `json`

**Table format output:**
```
Agent 'WeatherAgent' started successfully
```

**JSON format output:**
```json
{
  "status": "success", 
  "message": "Agent 'WeatherAgent' started successfully"
}
```

### `stop`

Stop a specific agent by name.

```bash
pyorchestrate stop [AGENT_NAME] [--socket SOCKET_PATH] [--format FORMAT]
```

**Parameters:**
- `AGENT_NAME`: Name of the agent to stop (optional if specified in command)

**Options:**
- `--socket`: Orchestrator socket path (default: `/tmp/pyorchestrate.sock`)
- `--format`: Output format - `table` (default) or `json`

**Table format output:**
```
Agent 'WeatherAgent' stopped successfully
```

**JSON format output:**
```json
{
  "status": "success",
  "message": "Agent 'WeatherAgent' stopped successfully"
}
```

### `status`

Get detailed status information for the orchestrator or a specific agent.

```bash
pyorchestrate status [AGENT_NAME] [--socket SOCKET_PATH] [--format FORMAT]
```

**Parameters:**
- `AGENT_NAME`: Name of the agent to get status for (optional, if omitted shows orchestrator status)

**Options:**
- `--socket`: Orchestrator socket path (default: `/tmp/pyorchestrate.sock`)
- `--format`: Output format - `table` (default) or `json`

**Table format output (agent status):**
```
Agent: WeatherAgent
Alive: True
Started: True
In Queue: False
Dependencies: DataProcessor, ConfigManager
```

**Table format output (orchestrator status):**
```
Total Agents: 5
Running Agents: 3
Max Workers: 8
Waiting Agents: 2
Command Interface: Enabled
Socket Path: /tmp/pyorchestrate.sock
```

**JSON format output (agent status):**
```json
{
  "status": "success",
  "data": {
    "name": "WeatherAgent",
    "alive": true,
    "started": true,
    "in_queue": false,
    "dependencies": ["DataProcessor", "ConfigManager"]
  }
}
```

**JSON format output (orchestrator status):**
```json
{
  "status": "success",
  "data": {
    "total_agents": 5,
    "running_agents": 3,
    "max_workers": 8,
    "waiting_agents": 2,
    "command_interface_enabled": true,
    "command_socket_path": "/tmp/pyorchestrate.sock"
  }
}
```

### `dependencies`

Show agent dependencies for the orchestrator.

```bash
pyorchestrate dependencies [--socket SOCKET_PATH] [--format FORMAT]
```

**Options:**
- `--socket`: Orchestrator socket path (default: `/tmp/pyorchestrate.sock`)
- `--format`: Output format - `table` (default) or `json`

**Table format output:**
```
Agent Dependencies:
  WeatherAgent -> DataProcessor, ConfigManager
  DataProcessor -> DatabaseAgent
  AlertManager -> WeatherAgent, DataProcessor
```

**JSON format output:**
```json
{
  "status": "success",
  "data": {
    "dependencies": {
      "WeatherAgent": ["DataProcessor", "ConfigManager"],
      "DataProcessor": ["DatabaseAgent"],
      "AlertManager": ["WeatherAgent", "DataProcessor"]
    }
  }
}
```

### `history`

Get event history with optional filtering parameters.

```bash
pyorchestrate history [--socket SOCKET_PATH] [--format FORMAT] [--last N] [--agent AGENT_NAME] [--type EVENT_TYPE] [--after-seq SEQ_NUMBER]
```

**Options:**
- `--socket`: Orchestrator socket path (default: `/tmp/pyorchestrate.sock`)
- `--format`: Output format - `table` (default) or `json`
- `--last N`: Number of last N events to show
- `--agent AGENT_NAME`: Filter by agent name
- `--type EVENT_TYPE`: Filter by event type
- `--after-seq SEQ_NUMBER`: Filter by sequence number

**Table format output:**
```
=== Event History (15 events) ===
Filters: agent=WeatherAgent, last=10
Buffer: 15/1000 events

SEQ    TIME               CATEGORY     TYPE                 AGENT           SEV  
--------------------------------------------------------------------------------
1001   2025-08-16T10:30:15 AGENT       AGENT_STARTED        WeatherAgent    INFO
1002   2025-08-16T10:30:20 EXECUTION   EXECUTION_COMPLETED  WeatherAgent    INFO
1003   2025-08-16T10:30:45 AGENT       AGENT_STOPPED        WeatherAgent    INFO
```

**JSON format output:**
```json
{
  "status": "success",
  "data": {
    "events": [
      {
        "seq": 1001,
        "timestamp": "2025-08-16T10:30:15",
        "category": "AGENT",
        "type": "AGENT_STARTED",
        "agent": "WeatherAgent",
        "severity": "INFO"
      }
    ],
    "count": 15,
    "filters": {
      "agent": "WeatherAgent",
      "last": 10
    },
    "capacity_info": {
      "current_size": 15,
      "capacity": 1000
    }
  }
}
```

### `history-stats`

Get aggregated event statistics with optional filtering.

```bash
pyorchestrate history-stats [--socket SOCKET_PATH] [--format FORMAT] [--agent AGENT_NAME]
```

**Options:**
- `--socket`: Orchestrator socket path (default: `/tmp/pyorchestrate.sock`)
- `--format`: Output format - `table` (default) or `json`
- `--agent AGENT_NAME`: Filter statistics by agent name

**Table format output:**
```
=== Event Statistics ===
Timestamp: 2025-08-16T10:45:00
Agent Filter: WeatherAgent
Buffer: 125/1000 events
Total Events: 1250

Event Type Breakdown:
  EXECUTION_COMPLETED       45
  AGENT_STARTED            12
  AGENT_STOPPED            8
  ERROR_OCCURRED           3
```

**JSON format output:**
```json
{
  "status": "success",
  "data": {
    "statistics": {
      "by_type": {
        "EXECUTION_COMPLETED": 45,
        "AGENT_STARTED": 12,
        "AGENT_STOPPED": 8,
        "ERROR_OCCURRED": 3
      }
    },
    "capacity_info": {
      "current_size": 125,
      "capacity": 1000,
      "total_events": 1250
    },
    "agent_filter": "WeatherAgent",
    "timestamp": "2025-08-16T10:45:00"
  }
}
```

### `stats`

Display real-time stats of all agents (like docker stats) with continuous monitoring.

```bash
pyorchestrate stats [--socket SOCKET_PATH] [--interval SECONDS]
```

**Options:**
- `--socket`: Orchestrator socket path (default: `/tmp/pyorchestrate.sock`)
- `--interval`: Refresh interval in seconds (default: `2.0`)

**Table format output (continuous updates):**
```
AGENT STATS - Press Ctrl+C to stop
================================================================================
Timestamp: 2025-08-16T10:45:30
Running: 3/5 agents
Waiting: 2 agents

NAME                 STATUS   PID      CPU %    MEM MB   MEM %    THREADS  UPTIME      
--------------------------------------------------------------------------------------
WeatherAgent         ALIVE    12345    2.5      45.2     1.2      8        01:15:30
DataProcessor        ALIVE    12346    1.8      32.1     0.9      6        01:15:28
AlertManager         DEAD     N/A      N/A      N/A      N/A      N/A      N/A
ConfigManager        ALIVE    12348    0.5      18.7     0.5      4        01:15:25
DatabaseAgent        DEAD     N/A      N/A      N/A      N/A      N/A      N/A
```

::: tip Continuous Monitoring
The `stats` command continues to run until Ctrl+C is pressed, updating information every `--interval` seconds (default 2 seconds).
:::

### `shutdown`

Gracefully shutdown the orchestrator and all agents.

```bash
pyorchestrate shutdown [--socket SOCKET_PATH] [--format FORMAT]
```

**Options:**
- `--socket`: Orchestrator socket path (default: `/tmp/pyorchestrate.sock`)
- `--format`: Output format - `table` (default) or `json`

**Table format output:**
```
Orchestrator shutdown initiated successfully
```

**JSON format output:**
```json
{
  "status": "success",
  "message": "Orchestrator shutdown initiated successfully"
}
```

::: warning Complete Shutdown
The `shutdown` command will stop all agents and the orchestrator. This operation cannot be undone once started.
:::

## Comando di Creazione Progetto

### `create`

Create a new PyOrchestrate project structure.

```bash
pyorchestrate create APP_NAME
```

**Parameters:**
- `APP_NAME`: Name of the application/project to create

**Output:**
```
Project structure for 'my-weather-app' created successfully.
📁 Created directories: my-weather-app/models, my-weather-app/configurations
📄 Created file: my-weather-app/starter.py

🚀 To get started:
   cd my-weather-app
   python starter.py

📋 Then use CLI commands to control it:
   pyorchestrate ps
   pyorchestrate shutdown
```

This command creates:
- Directory `APP_NAME/models/` for agent models
- Directory `APP_NAME/configurations/` for configurations
- File `APP_NAME/starter.py` with base template for the orchestrator

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
if pyorchestrate status --socket "$SOCKET" --format json > /dev/null 2>&1; then
    echo "Orchestrator is running"
    
    # Get running agent count
    STATS=$(pyorchestrate status --socket "$SOCKET" --format json)
    RUNNING=$(echo "$STATS" | jq '.data.running_agents // 0')
    TOTAL=$(echo "$STATS" | jq '.data.total_agents // 0')
    
    echo "Running agents: $RUNNING/$TOTAL"
    
    # Check if any agents are stopped
    if [ "$RUNNING" -lt "$TOTAL" ]; then
        echo "Warning: Some agents are not running"
        
        # List all agents to see which ones are stopped
        pyorchestrate ps --socket "$SOCKET" --format table
    fi
else
    echo "Orchestrator is not responsive"
    exit 1
fi

# Example: Auto-restart stopped agents
restart_stopped_agents() {
    local socket_path="$1"
    
    # Get list of agents in JSON format
    local agents_json=$(pyorchestrate ps --socket "$socket_path" --format json)
    
    # Check if command was successful
    if echo "$agents_json" | jq -e '.status == "success"' > /dev/null; then
        # Get agents that are not alive
        local stopped_agents=$(echo "$agents_json" | jq -r '.data.agents[] | select(.alive == false) | .agent_name')
        
        for agent in $stopped_agents; do
            echo "Restarting stopped agent: $agent"
            pyorchestrate start "$agent" --socket "$socket_path"
        done
    else
        echo "Failed to get agent list"
        return 1
    fi
}

# Call the function
restart_stopped_agents "$SOCKET"
```

### Python Integration

```python
import json
import subprocess


def get_orchestrator_status(socket_path="/tmp/pyorchestrate.sock"):
    """Get orchestrator status via CLI."""
    try:
        result = subprocess.run(
            ["python", "-m", "PyOrchestrate.cli", "status", "--socket", socket_path, "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return None


def list_agents(socket_path="/tmp/pyorchestrate.sock"):
    """List all agents via CLI."""
    try:
        result = subprocess.run(
            ["python", "-m", "PyOrchestrate.cli", "ps", "--socket", socket_path, "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return None


def start_agent(agent_name, socket_path="/tmp/pyorchestrate.sock"):
    """Start an agent via CLI."""
    try:
        result = subprocess.run(
            ["python", "-m", "PyOrchestrate.cli", "start", agent_name, "--socket", socket_path, "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return None


# Usage examples
if __name__ == "__main__":
    socket_path = "/tmp/pyorchestrate.sock"
    
    # Get orchestrator status
    status = get_orchestrator_status(socket_path)
    if status and status.get("status") == "success":
        data = status["data"]
        print(f"Orchestrator Status:")
        print(f"  Total agents: {data.get('total_agents', 'unknown')}")
        print(f"  Running agents: {data.get('running_agents', 'unknown')}")
        print(f"  Waiting agents: {data.get('waiting_agents', 'unknown')}")
        print(f"  Max workers: {data.get('max_workers', 'unknown')}")
        print(f"  Socket path: {data.get('command_socket_path', 'unknown')}")
    
    # List all agents
    agents_response = list_agents(socket_path)
    if agents_response and agents_response.get("status") == "success":
        agents = agents_response["data"]["agents"]
        print(f"\nAgents ({len(agents)}):")
        for agent in agents:
            status = "ALIVE" if agent.get("alive") else "DEAD"
            started = "YES" if agent.get("started") else "NO"
            print(f"  {agent['agent_name']}: {status} (Started: {started})")
    
    # Start a specific agent
    start_result = start_agent("WeatherAgent", socket_path)
    if start_result and start_result.get("status") == "success":
        print(f"\n{start_result.get('message', 'Agent started successfully')}")
```

## Troubleshooting

### Socket Connection Issues

```bash
# Check if socket exists
ls -la /tmp/pyorchestrate.sock

# Check socket permissions
stat /tmp/pyorchestrate.sock

# Test basic connectivity
pyorchestrate status --socket /tmp/pyorchestrate.sock
```

### Permission Errors

Ensure your user has read/write permissions to the socket file:

```bash
# Set socket permissions (run as orchestrator user)
chmod 660 /tmp/pyorchestrate.sock
chgrp mygroup /tmp/pyorchestrate.sock
```

### Debugging Commands

```bash
# Test with verbose output (if available)
pyorchestrate ps --socket /tmp/pyorchestrate.sock --format json

# Check orchestrator logs
# (location depends on your logging configuration)
tail -f /var/log/pyorchestrate.log

# Check if process is running
ps aux | grep -i orchestrat
```