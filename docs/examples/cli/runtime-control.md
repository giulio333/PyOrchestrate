---
title: CLI Runtime Control Example
editLink: true
---

# CLI Runtime Control Example

This example demonstrates how to use the PyOrchestrate CLI for real-time control and monitoring of a running orchestrator.

## Project Setup

Let's create a simple multi-agent system and show how to control it using CLI commands.

### 1. Create the Agents

First, we'll create a few example agents:

```python
# agents.py
from PyOrchestrate.core.agents import PeriodicProcessAgent
import time
import random

class WeatherAgent(PeriodicProcessAgent):
    """Agent that simulates weather data collection."""
    
    class Config(PeriodicProcessAgent.Config):
        execution_interval: int = 10  # Run every 10 seconds
        city: str = "New York"
    
    config: Config
    
    def setup(self):
        super().setup()
        self.logger.info(f"WeatherAgent initialized for {self.config.city}")
    
    def runner(self):
        # Simulate weather data collection
        temperature = random.uniform(-10, 35)
        humidity = random.uniform(30, 90)
        
        self.logger.info(f"Weather in {self.config.city}: {temperature:.1f}°C, {humidity:.1f}% humidity")
        
        # Simulate some processing time
        time.sleep(2)

class DataProcessorAgent(PeriodicProcessAgent):
    """Agent that processes collected data."""
    
    class Config(PeriodicProcessAgent.Config):
        execution_interval: int = 15
        batch_size: int = 10
    
    config: Config
    
    def setup(self):
        super().setup()
        self.logger.info("DataProcessorAgent initialized")
    
    def runner(self):
        # Simulate data processing
        self.logger.info(f"Processing batch of {self.config.batch_size} records")
        time.sleep(3)
        self.logger.info("Data processing completed")

class AlertManagerAgent(PeriodicProcessAgent):
    """Agent that manages alerts and notifications."""
    
    class Config(PeriodicProcessAgent.Config):
        execution_interval: int = 30
        alert_threshold: float = 30.0
    
    config: Config
    
    def setup(self):
        super().setup()
        self.logger.info("AlertManagerAgent initialized")
    
    def runner(self):
        # Simulate alert checking
        self.logger.info("Checking for alerts...")
        
        # Randomly generate an alert
        if random.random() < 0.3:  # 30% chance of alert
            self.logger.warning("ALERT: High temperature detected!")
        else:
            self.logger.info("No alerts - all systems normal")
```

### 2. Create the Orchestrator

Now create an orchestrator with CLI support enabled:

```python
# orchestrator.py
from PyOrchestrate.core.orchestrator import BaseOrchestrator
from agents import WeatherAgent, DataProcessorAgent, AlertManagerAgent

class WeatherOrchestrator(BaseOrchestrator):
    """Main orchestrator for the weather monitoring system."""
    
    class Config(BaseOrchestrator.Config):
        # Enable CLI command interface
        enable_command_interface: bool = True
        command_socket_path: str = "/tmp/weather_orchestrator.sock"
        
        # Logging configuration
        log_cli_commands: bool = True
        cli_log_level: str = "INFO"
    
    config: Config
    
    def setup(self):
        super().setup()
        
        # Register agents
        self.add_agent(
            WeatherAgent, 
            "WeatherNYC", 
            WeatherAgent.Config(city="New York")
        )
        
        self.add_agent(
            WeatherAgent, 
            "WeatherLondon", 
            WeatherAgent.Config(city="London", execution_interval=12)
        )
        
        self.add_agent(
            DataProcessorAgent, 
            "DataProcessor", 
            DataProcessorAgent.Config(batch_size=15)
        )
        
        self.add_agent(
            AlertManagerAgent, 
            "AlertManager", 
            AlertManagerAgent.Config(alert_threshold=25.0)
        )
        
        self.logger.info("Weather monitoring system configured")

if __name__ == "__main__":
    orchestrator = WeatherOrchestrator(WeatherOrchestrator.Config())
    orchestrator.start()
```

### 3. Main Application

Create the main application file:

```python
# main.py
import sys
import signal
from orchestrator import WeatherOrchestrator

def signal_handler(sig, frame):
    print("\nShutdown signal received")
    sys.exit(0)

def main():
    print("Starting Weather Monitoring System...")
    print("CLI socket will be available at: /tmp/weather_orchestrator.sock")
    print("Use Ctrl+C to stop or use CLI: pyorchestrate shutdown /tmp/weather_orchestrator.sock")
    
    # Set up signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start orchestrator
    config = WeatherOrchestrator.Config()
    orchestrator = WeatherOrchestrator(config)
    
    try:
        orchestrator.start()
    except KeyboardInterrupt:
        print("\nGraceful shutdown...")
        orchestrator.stop()

if __name__ == "__main__":
    main()
```

## CLI Usage Examples

Now let's explore various CLI commands to control and monitor this system.

### Starting the Application

```bash
# Start the weather monitoring system
python main.py &

# Wait a moment for the orchestrator to initialize
sleep 3
```

### Basic Monitoring

```bash
# Check if the orchestrator is running
pyorchestrate stats

# List all agents and their status
pyorchestrate ps

# Get detailed status of a specific agent
pyorchestrate status WeatherNYC
```

Expected output for `ps` command:
```json
{
  "status": "success",
  "data": {
    "agents": [
      {
        "name": "WeatherNYC",
        "status": "running",
        "pid": 12345,
        "uptime": "00:02:15"
      },
      {
        "name": "WeatherLondon", 
        "status": "running",
        "pid": 12346,
        "uptime": "00:02:13"
      },
      {
        "name": "DataProcessor",
        "status": "running", 
        "pid": 12347,
        "uptime": "00:02:10"
      },
      {
        "name": "AlertManager",
        "status": "running",
        "pid": 12348, 
        "uptime": "00:02:08"
      }
    ]
  },
  "timestamp": "2025-07-27T10:30:00Z"
}
```

### Dynamic Agent Control

```bash
# Stop a specific agent
pyorchestrate stop WeatherLondon

# Verify it's stopped
pyorchestrate ps

# Start it again
pyorchestrate start WeatherLondon

# Check detailed status
pyorchestrate status WeatherLondon
```

### System Monitoring

```bash
# Get comprehensive system statistics
pyorchestrate stats

# Generate a full system report
pyorchestrate report
```

Sample stats output:
```json
{
  "status": "success",
  "data": {
    "orchestrator": {
      "uptime": "00:05:42",
      "total_agents": 4,
      "running_agents": 4,
      "waiting_agents": 0, 
      "failed_agents": 0
    },
    "system": {
      "memory_usage": "128.5 MB",
      "cpu_usage": "5.2%",
      "open_files": 28
    },
    "dependencies": {
      "total_dependencies": 6,
      "satisfied": 6,
      "unsatisfied": 0
    }
  },
  "timestamp": "2025-07-27T10:35:42Z"
}
```

## Monitoring Scripts

### Real-time Dashboard

Create a simple monitoring dashboard:

```bash
#!/bin/bash
# monitor.sh - Real-time monitoring dashboard

SOCKET="/tmp/weather_orchestrator.sock"

echo "Weather Monitoring System Dashboard"
echo "==================================="

while true; do
    clear
    echo "Weather Monitoring System - $(date)"
    echo "Socket: $SOCKET"
    echo "=================================="
    
    # Check if orchestrator is running
    if pyorchestrate stats "$SOCKET" 2>/dev/null | jq -e '.status == "success"' > /dev/null; then
        echo "STATUS: RUNNING ✓"
        echo ""
        
        # Show summary statistics
        echo "SYSTEM OVERVIEW:"
        pyorchestrate stats "$SOCKET" | jq -r '
            .data.orchestrator | 
            "  Agents: \(.total_agents) total, \(.running_agents) running, \(.failed_agents) failed"
        '
        
        echo ""
        echo "AGENT STATUS:"
        pyorchestrate ps "$SOCKET" | jq -r '
            .data.agents[] | 
            "  \(.name | ljust(15)): \(.status | ljust(10)) (PID: \(.pid))"
        '
        
        echo ""
        echo "SYSTEM RESOURCES:"
        pyorchestrate stats "$SOCKET" | jq -r '
            .data.system | 
            "  Memory: \(.memory_usage)    CPU: \(.cpu_usage)"
        '
        
    else
        echo "STATUS: NOT RUNNING ✗"
    fi
    
    echo ""
    echo "Press Ctrl+C to exit"
    sleep 5
done
```

### Health Check Script

```bash
#!/bin/bash
# health-check.sh - Automated health monitoring

SOCKET="/tmp/weather_orchestrator.sock"
LOG_FILE="/tmp/weather_health.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

check_health() {
    # Test orchestrator connectivity
    if ! pyorchestrate stats "$SOCKET" > /dev/null 2>&1; then
        log "ERROR: Cannot connect to orchestrator"
        return 1
    fi
    
    # Check for failed agents
    failed_count=$(pyorchestrate stats "$SOCKET" | jq '.data.orchestrator.failed_agents')
    
    if [ "$failed_count" -gt 0 ]; then
        log "WARNING: $failed_count agents have failed"
        
        # List failed agents
        pyorchestrate ps "$SOCKET" | jq -r '
            .data.agents[] | 
            select(.status == "failed") | 
            "FAILED: \(.name)"
        ' | while read line; do
            log "$line"
        done
        
        return 1
    fi
    
    log "OK: All systems healthy"
    return 0
}

log "Starting health check"
check_health
exit_code=$?
log "Health check completed with status: $exit_code"
exit $exit_code
```

## Advanced Usage

### Automated Recovery

```bash
#!/bin/bash
# auto-recovery.sh - Automatic agent recovery

SOCKET="/tmp/weather_orchestrator.sock"

restart_failed_agents() {
    echo "Checking for failed agents..."
    
    failed_agents=$(pyorchestrate ps "$SOCKET" | jq -r '
        .data.agents[] | 
        select(.status == "failed") | 
        .name
    ')
    
    if [ -n "$failed_agents" ]; then
        echo "Found failed agents: $failed_agents"
        
        for agent in $failed_agents; do
            echo "Restarting $agent..."
            pyorchestrate start "$agent" "$SOCKET"
            
            # Wait and verify
            sleep 3
            status=$(pyorchestrate status "$agent" "$SOCKET" | jq -r '.data.status')
            echo "$agent status after restart: $status"
        done
    else
        echo "No failed agents found"
    fi
}

restart_failed_agents
```

### Load Testing Support

```bash
#!/bin/bash
# load-test.sh - CLI support during load testing

SOCKET="/tmp/weather_orchestrator.sock"

echo "Starting load test monitoring..."

# Capture baseline
pyorchestrate report "$SOCKET" > "baseline_$(date +%s).json"

# Monitor during test
for i in {1..60}; do  # Monitor for 5 minutes
    timestamp=$(date +%s)
    pyorchestrate stats "$SOCKET" > "stats_${timestamp}.json"
    
    # Quick status check
    running=$(pyorchestrate stats "$SOCKET" | jq '.data.orchestrator.running_agents')
    failed=$(pyorchestrate stats "$SOCKET" | jq '.data.orchestrator.failed_agents')
    
    echo "Minute $i: Running=$running, Failed=$failed"
    
    sleep 5
done

echo "Load test monitoring completed"
```

## Graceful Shutdown

```bash
# Stop the entire system gracefully
pyorchestrate shutdown

# Or stop individual agents first
pyorchestrate stop WeatherNYC
pyorchestrate stop WeatherLondon
pyorchestrate stop DataProcessor
pyorchestrate stop AlertManager

# Then shutdown orchestrator
pyorchestrate shutdown
```

## Integration with Other Tools

### JSON Processing with jq

The CLI outputs structured JSON that can be easily processed:

```bash
# Get only agent names
pyorchestrate ps /tmp/weather_orchestrator.sock | jq -r '.data.agents[].name'

# Count running agents
pyorchestrate stats /tmp/weather_orchestrator.sock | jq '.data.orchestrator.running_agents'

# Get agents with specific status
pyorchestrate ps /tmp/weather_orchestrator.sock | jq -r '
    .data.agents[] | 
    select(.status == "running") | 
    .name
'

# Format output as table
pyorchestrate ps /tmp/weather_orchestrator.sock | jq -r '
    ["NAME", "STATUS", "PID", "UPTIME"], 
    (.data.agents[] | [.name, .status, .pid, .uptime]) | 
    @tsv
' | column -t
```

### Integration with systemd

Create a systemd service that supports CLI management:

```ini
# /etc/systemd/system/weather-monitor.service
[Unit]
Description=Weather Monitoring System
After=network.target

[Service]
Type=simple
User=pyorchestrate
WorkingDirectory=/opt/weather-monitor
ExecStart=/usr/bin/python3 main.py
ExecStop=/usr/bin/pyorchestrate shutdown /tmp/weather_orchestrator.sock
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

This example demonstrates the full lifecycle of using PyOrchestrate CLI for real-time orchestrator control, from basic monitoring to advanced automation and integration scenarios.
