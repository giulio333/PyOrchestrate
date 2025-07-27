---
title: CLI Examples
editLink: true
---

# CLI Examples

This page provides practical examples of using the PyOrchestrate CLI for various scenarios, from development workflows to production monitoring and DevOps integration.

## Development Workflow

### Project Setup and Testing

```bash
# Initialize a new PyOrchestrate project
pyorchestrate init my-weather-app
cd my-weather-app

# Start your orchestrator with CLI enabled
python main.py &
ORCHESTRATOR_PID=$!

# Wait for orchestrator to start
sleep 2

# Check if orchestrator is running
pyorchestrate stats

# Monitor agents during development
pyorchestrate ps

# Test agent lifecycle
pyorchestrate start WeatherAgent
pyorchestrate status WeatherAgent
pyorchestrate stop WeatherAgent

# Clean shutdown for development
pyorchestrate shutdown
```

### Development Monitoring Script

```bash
#!/bin/bash
# dev-monitor.sh - Development monitoring script

SOCKET="/tmp/pyorchestrate.sock"
INTERVAL=5

echo "Starting development monitoring..."

while true; do
    clear
    echo "=== PyOrchestrate Development Monitor ==="
    echo "Time: $(date)"
    echo "----------------------------------------"
    
    if pyorchestrate stats "$SOCKET" 2>/dev/null | jq -e '.status == "success"' > /dev/null; then
        echo "Orchestrator Status: RUNNING ✓"
        
        # Show agent summary
        echo -e "\nAgent Summary:"
        pyorchestrate stats "$SOCKET" | jq -r '
            .data.orchestrator | 
            "  Total: \(.total_agents)  Running: \(.running_agents)  Waiting: \(.waiting_agents)"
        '
        
        # Show individual agents
        echo -e "\nAgent Details:"
        pyorchestrate ps "$SOCKET" | jq -r '
            .data.agents[] | 
            "  \(.name): \(.status) (PID: \(.pid))"
        '
        
    else
        echo "Orchestrator Status: NOT RUNNING ✗"
    fi
    
    echo -e "\n----------------------------------------"
    echo "Press Ctrl+C to stop monitoring"
    
    sleep $INTERVAL
done
```

## Production Monitoring

### Health Check Script

```bash
#!/bin/bash
# health-check.sh - Production health monitoring

SOCKET="/var/run/pyorchestrate/prod.sock"
LOG_FILE="/var/log/pyorchestrate/health.log"
ALERT_THRESHOLD=1  # Maximum allowed failed agents

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

check_orchestrator_health() {
    local stats_output
    stats_output=$(pyorchestrate stats "$SOCKET" 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        log "ERROR: Cannot connect to orchestrator"
        return 1
    fi
    
    local failed_agents
    failed_agents=$(echo "$stats_output" | jq -r '.data.orchestrator.failed_agents')
    
    if [ "$failed_agents" -gt "$ALERT_THRESHOLD" ]; then
        log "ALERT: $failed_agents agents have failed (threshold: $ALERT_THRESHOLD)"
        
        # Get details of failed agents
        pyorchestrate ps "$SOCKET" | jq -r '
            .data.agents[] | 
            select(.status == "failed") | 
            "FAILED AGENT: \(.name) - Last seen: \(.last_activity)"
        ' | while read line; do
            log "$line"
        done
        
        return 1
    fi
    
    log "OK: System healthy - $failed_agents failed agents"
    return 0
}

# Main health check
log "Starting health check"
if check_orchestrator_health; then
    exit 0
else
    exit 1
fi
```

### Automated Recovery Script

```bash
#!/bin/bash
# auto-recovery.sh - Automatic agent recovery

SOCKET="/var/run/pyorchestrate/prod.sock"
LOG_FILE="/var/log/pyorchestrate/recovery.log"
MAX_RESTART_ATTEMPTS=3

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

restart_failed_agents() {
    local failed_agents
    failed_agents=$(pyorchestrate ps "$SOCKET" | jq -r '
        .data.agents[] | 
        select(.status == "failed") | 
        .name
    ')
    
    for agent in $failed_agents; do
        log "Attempting to restart failed agent: $agent"
        
        # Try to restart the agent
        if pyorchestrate start "$agent" "$SOCKET" > /dev/null 2>&1; then
            log "SUCCESS: Restarted $agent"
            
            # Wait and verify it's running
            sleep 5
            status=$(pyorchestrate status "$agent" "$SOCKET" | jq -r '.data.status')
            
            if [ "$status" = "running" ]; then
                log "VERIFIED: $agent is now running"
            else
                log "WARNING: $agent restart failed - status: $status"
            fi
        else
            log "ERROR: Failed to restart $agent"
        fi
    done
}

log "Starting automatic recovery process"
restart_failed_agents
log "Recovery process completed"
```

## DevOps Integration

### CI/CD Pipeline Integration

```bash
#!/bin/bash
# ci-deployment-check.sh - Post-deployment verification

SOCKET="/var/run/pyorchestrate/prod.sock"
DEPLOYMENT_TIMEOUT=300  # 5 minutes
CHECK_INTERVAL=10

echo "Starting post-deployment verification..."

# Wait for orchestrator to be ready
start_time=$(date +%s)
while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))
    
    if [ $elapsed -gt $DEPLOYMENT_TIMEOUT ]; then
        echo "ERROR: Deployment verification timeout after ${DEPLOYMENT_TIMEOUT}s"
        exit 1
    fi
    
    if pyorchestrate stats "$SOCKET" > /dev/null 2>&1; then
        echo "✓ Orchestrator is responding"
        break
    fi
    
    echo "Waiting for orchestrator to start... (${elapsed}s)"
    sleep $CHECK_INTERVAL
done

# Verify all expected agents are running
expected_agents=("WeatherAgent" "DataProcessor" "AlertManager" "LogCollector")
all_agents_ready=true

for agent in "${expected_agents[@]}"; do
    status=$(pyorchestrate status "$agent" "$SOCKET" 2>/dev/null | jq -r '.data.status')
    
    if [ "$status" = "running" ]; then
        echo "✓ $agent is running"
    else
        echo "✗ $agent is not running (status: $status)"
        all_agents_ready=false
    fi
done

if [ "$all_agents_ready" = true ]; then
    echo "✓ Deployment verification successful"
    exit 0
else
    echo "✗ Deployment verification failed"
    exit 1
fi
```

### Docker Compose Integration

```yaml
# docker-compose.yml
version: '3.8'

services:
  orchestrator:
    build: .
    volumes:
      - socket-volume:/var/run/pyorchestrate
      - ./logs:/var/log/pyorchestrate
    environment:
      - PYORCHESTRATE_SOCKET_PATH=/var/run/pyorchestrate/orchestrator.sock
    
  monitor:
    image: pyorchestrate/cli
    volumes:
      - socket-volume:/var/run/pyorchestrate
    command: |
      sh -c "
        while true; do
          echo '=== System Status ===' 
          pyorchestrate stats /var/run/pyorchestrate/orchestrator.sock || echo 'Orchestrator not ready'
          sleep 30
        done
      "
    depends_on:
      - orchestrator

volumes:
  socket-volume:
```

### Kubernetes Monitoring Sidecar

```yaml
# kubernetes-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pyorchestrate-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: pyorchestrate
  template:
    metadata:
      labels:
        app: pyorchestrate
    spec:
      containers:
      - name: orchestrator
        image: my-pyorchestrate:latest
        volumeMounts:
        - name: socket-volume
          mountPath: /var/run/pyorchestrate
        
      - name: monitor
        image: my-pyorchestrate-cli:latest
        volumeMounts:
        - name: socket-volume
          mountPath: /var/run/pyorchestrate
        command:
        - sh
        - -c
        - |
          while true; do
            # Export metrics for Prometheus
            pyorchestrate stats /var/run/pyorchestrate/orchestrator.sock | \
              jq -r '.data.orchestrator | 
                "# HELP pyorchestrate_running_agents Number of running agents\n# TYPE pyorchestrate_running_agents gauge\npyorchestrate_running_agents \(.running_agents)\n# HELP pyorchestrate_failed_agents Number of failed agents\n# TYPE pyorchestrate_failed_agents gauge\npyorchestrate_failed_agents \(.failed_agents)"
              ' > /tmp/metrics.txt
            sleep 30
          done
        
      volumes:
      - name: socket-volume
        emptyDir: {}
```

## Monitoring Dashboard Integration

### Grafana Data Source Script

```bash
#!/bin/bash
# grafana-metrics.sh - Export metrics for Grafana

SOCKET="/var/run/pyorchestrate/prod.sock"
METRICS_FILE="/var/lib/prometheus/pyorchestrate.prom"

# Get orchestrator stats
stats=$(pyorchestrate stats "$SOCKET" 2>/dev/null)

if [ $? -eq 0 ]; then
    # Export metrics in Prometheus format
    cat > "$METRICS_FILE" << EOF
# HELP pyorchestrate_total_agents Total number of agents
# TYPE pyorchestrate_total_agents gauge
pyorchestrate_total_agents $(echo "$stats" | jq '.data.orchestrator.total_agents')

# HELP pyorchestrate_running_agents Number of running agents  
# TYPE pyorchestrate_running_agents gauge
pyorchestrate_running_agents $(echo "$stats" | jq '.data.orchestrator.running_agents')

# HELP pyorchestrate_failed_agents Number of failed agents
# TYPE pyorchestrate_failed_agents gauge
pyorchestrate_failed_agents $(echo "$stats" | jq '.data.orchestrator.failed_agents')

# HELP pyorchestrate_memory_usage_bytes Memory usage in bytes
# TYPE pyorchestrate_memory_usage_bytes gauge
pyorchestrate_memory_usage_bytes $(echo "$stats" | jq '.data.system.memory_usage_bytes')

# HELP pyorchestrate_cpu_usage_percent CPU usage percentage
# TYPE pyorchestrate_cpu_usage_percent gauge  
pyorchestrate_cpu_usage_percent $(echo "$stats" | jq '.data.system.cpu_usage_percent')
EOF

    echo "Metrics exported to $METRICS_FILE"
else
    echo "Failed to get orchestrator stats"
    exit 1
fi
```

### Alert Manager Integration

```bash
#!/bin/bash
# alertmanager-check.sh - Send alerts based on orchestrator status

SOCKET="/var/run/pyorchestrate/prod.sock"
WEBHOOK_URL="http://alertmanager:9093/api/v1/alerts"

send_alert() {
    local severity=$1
    local summary=$2
    local description=$3
    
    curl -XPOST "$WEBHOOK_URL" -H 'Content-Type: application/json' -d "[
        {
            \"labels\": {
                \"alertname\": \"PyOrchestrateAlert\",
                \"service\": \"pyorchestrate\",
                \"severity\": \"$severity\"
            },
            \"annotations\": {
                \"summary\": \"$summary\",
                \"description\": \"$description\"
            }
        }
    ]"
}

# Check orchestrator health
stats=$(pyorchestrate stats "$SOCKET" 2>/dev/null)

if [ $? -ne 0 ]; then
    send_alert "critical" "PyOrchestrate Orchestrator Down" "Cannot connect to orchestrator socket"
    exit 1
fi

failed_agents=$(echo "$stats" | jq '.data.orchestrator.failed_agents')

if [ "$failed_agents" -gt 0 ]; then
    send_alert "warning" "PyOrchestrate Agents Failed" "$failed_agents agents have failed"
fi

echo "Health check completed - $failed_agents failed agents"
```

## Automation Scripts

### Maintenance Mode Script

```bash
#!/bin/bash
# maintenance-mode.sh - Gracefully handle maintenance

SOCKET="/var/run/pyorchestrate/prod.sock"
BACKUP_DIR="/var/backups/pyorchestrate"

enter_maintenance() {
    echo "Entering maintenance mode..."
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR/$(date +%Y%m%d_%H%M%S)"
    
    # Get current state for restoration
    pyorchestrate report "$SOCKET" > "$BACKUP_DIR/pre_maintenance_report.json"
    
    # Gracefully stop non-critical agents
    non_critical_agents=("DataProcessor" "LogCollector")
    
    for agent in "${non_critical_agents[@]}"; do
        echo "Stopping $agent..."
        pyorchestrate stop "$agent" "$SOCKET"
    done
    
    echo "Maintenance mode active"
}

exit_maintenance() {
    echo "Exiting maintenance mode..."
    
    # Restart stopped agents
    backup_report=$(ls -t "$BACKUP_DIR"/pre_maintenance_report.json | head -1)
    
    if [ -f "$backup_report" ]; then
        # Extract agents that were running before maintenance
        running_agents=$(jq -r '.data.agents[] | select(.status == "running") | .name' "$backup_report")
        
        for agent in $running_agents; do
            echo "Starting $agent..."
            pyorchestrate start "$agent" "$SOCKET"
        done
    fi
    
    echo "Maintenance mode completed"
}

case "$1" in
    enter)
        enter_maintenance
        ;;
    exit)
        exit_maintenance
        ;;
    *)
        echo "Usage: $0 {enter|exit}"
        exit 1
        ;;
esac
```

### Load Testing Support

```bash
#!/bin/bash
# load-test-support.sh - CLI support for load testing

SOCKET="/var/run/pyorchestrate/test.sock"
RESULTS_DIR="/tmp/load_test_results"

mkdir -p "$RESULTS_DIR"

# Pre-test state capture
echo "Capturing pre-test state..."
pyorchestrate report "$SOCKET" > "$RESULTS_DIR/pre_test_state.json"

# Start load test monitoring
monitor_during_test() {
    echo "Starting load test monitoring..."
    
    while [ -f "/tmp/load_test_running" ]; do
        timestamp=$(date +%s)
        pyorchestrate stats "$SOCKET" > "$RESULTS_DIR/stats_$timestamp.json"
        sleep 5
    done
    
    echo "Load test monitoring completed"
}

# Start monitoring in background
touch /tmp/load_test_running
monitor_during_test &
MONITOR_PID=$!

echo "Load test monitoring started (PID: $MONITOR_PID)"
echo "Run your load test now..."
echo "When finished, run: rm /tmp/load_test_running"

# Wait for test completion signal
while [ -f "/tmp/load_test_running" ]; do
    sleep 1
done

# Cleanup
wait $MONITOR_PID

# Post-test analysis
echo "Generating load test report..."
python3 << EOF
import json
import glob
import os

results_dir = "$RESULTS_DIR"
stats_files = sorted(glob.glob(f"{results_dir}/stats_*.json"))

print("Load Test Results Summary:")
print("=" * 40)

for stats_file in stats_files:
    with open(stats_file) as f:
        data = json.load(f)
        timestamp = os.path.basename(stats_file).replace('stats_', '').replace('.json', '')
        stats = data['data']['orchestrator']
        print(f"Time {timestamp}: Running={stats['running_agents']}, Failed={stats['failed_agents']}")

print("=" * 40)
print(f"Detailed results saved in: {results_dir}")
EOF
```

## Best Practices Examples

### Production Deployment Checklist

```bash
#!/bin/bash
# deployment-checklist.sh - Production deployment verification

SOCKET="/var/run/pyorchestrate/prod.sock"
CONFIG_FILE="/etc/pyorchestrate/production.yaml"
LOG_FILE="/var/log/pyorchestrate/deployment.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

# 1. Verify configuration
log "Step 1: Verifying configuration..."
if [ ! -f "$CONFIG_FILE" ]; then
    log "ERROR: Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# 2. Check socket connectivity
log "Step 2: Testing CLI connectivity..."
if ! pyorchestrate stats "$SOCKET" > /dev/null 2>&1; then
    log "ERROR: Cannot connect to orchestrator"
    exit 1
fi

# 3. Verify all agents started
log "Step 3: Verifying agent startup..."
expected_count=5
running_count=$(pyorchestrate stats "$SOCKET" | jq '.data.orchestrator.running_agents')

if [ "$running_count" -ne "$expected_count" ]; then
    log "WARNING: Expected $expected_count agents, found $running_count running"
fi

# 4. Performance baseline
log "Step 4: Capturing performance baseline..."
pyorchestrate stats "$SOCKET" > "/var/log/pyorchestrate/baseline_$(date +%Y%m%d_%H%M%S).json"

log "Deployment verification completed successfully"
```

These examples demonstrate real-world usage patterns for the PyOrchestrate CLI, from simple development workflows to complex production monitoring and automation scenarios.
