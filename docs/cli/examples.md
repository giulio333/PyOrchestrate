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
pyorchestrate create my-weather-app
cd my-weather-app

# Start your orchestrator with CLI enabled
python starter.py &
ORCHESTRATOR_PID=$!

# Wait for orchestrator to start
sleep 2

# Check if orchestrator is running
pyorchestrate status

# Monitor agents during development
pyorchestrate ps

# Test agent lifecycle
pyorchestrate start WeatherAgent
pyorchestrate status WeatherAgent
pyorchestrate stop WeatherAgent

# Check event history
pyorchestrate history --last 10

# Monitor real-time stats
pyorchestrate stats --interval 3

# Clean shutdown for development
python -m PyOrchestrate.cli shutdown

# Alternative: Start web interface for visual monitoring
pyorchestrate-web --port 3000 --socket /tmp/pyorchestrate.sock
```

### Web Interface Development Setup

```bash
#!/bin/bash
# web-dev-setup.sh - Development setup with web interface

PROJECT_NAME="my-weather-app"
SOCKET_PATH="/tmp/${PROJECT_NAME}.sock"
WEB_PORT=3000

# Create and setup project
python -m PyOrchestrate.cli create "$PROJECT_NAME"
cd "$PROJECT_NAME"

# Start orchestrator in background
python starter.py &
ORCH_PID=$!

# Wait for orchestrator to start
sleep 3

# Start web interface
pyorchestrate-web --port "$WEB_PORT" --socket "$SOCKET_PATH" &
WEB_PID=$!

echo "Development environment ready:"
echo "  Project: $PROJECT_NAME"
echo "  Orchestrator PID: $ORCH_PID"
echo "  Web Interface: http://localhost:$WEB_PORT"
echo "  Socket: $SOCKET_PATH"

# Cleanup function
cleanup() {
    echo "Cleaning up development environment..."
    kill $WEB_PID 2>/dev/null
    python -m PyOrchestrate.cli shutdown --socket "$SOCKET_PATH" 2>/dev/null
    kill $ORCH_PID 2>/dev/null
}

trap cleanup EXIT
echo "Press Ctrl+C to stop all services"
wait
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
    
    if pyorchestrate status --socket "$SOCKET" --format json > /dev/null 2>&1; then
        echo "Orchestrator Status: RUNNING ✓"
        
        # Show agent summary
        echo -e "\nAgent Summary:"
        pyorchestrate status --socket "$SOCKET" --format json | jq -r '
            .data | 
            "  Total: \(.total_agents)  Running: \(.running_agents)  Waiting: \(.waiting_agents)"
        '
        
        # Show individual agents
        echo -e "\nAgent Details:"
        pyorchestrate ps --socket "$SOCKET" --format json | jq -r '
            .data.agents[] | 
            "  \(.agent_name): \(if .alive then "ALIVE" else "DEAD" end) (Started: \(if .started then "YES" else "NO" end))"
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
    stats_output=$(pyorchestrate status --socket "$SOCKET" --format json 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        log "ERROR: Cannot connect to orchestrator"
        return 1
    fi
    
    local running_agents total_agents
    running_agents=$(echo "$stats_output" | jq -r '.data.running_agents // 0')
    total_agents=$(echo "$stats_output" | jq -r '.data.total_agents // 0')
    local failed_agents=$((total_agents - running_agents))
    
    if [ "$failed_agents" -gt "$ALERT_THRESHOLD" ]; then
        log "ALERT: $failed_agents agents have failed (threshold: $ALERT_THRESHOLD)"
        
        # Get details of failed agents
        pyorchestrate ps --socket "$SOCKET" --format json | jq -r '
            .data.agents[] | 
            select(.alive == false) | 
            "FAILED AGENT: \(.agent_name) - Alive: \(.alive) - Started: \(.started)"
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
    failed_agents=$(pyorchestrate ps --socket "$SOCKET" --format json | jq -r '
        .data.agents[] | 
        select(.alive == false) | 
        .agent_name
    ')
    
    for agent in $failed_agents; do
        log "Attempting to restart failed agent: $agent"
        
        # Try to restart the agent
        if pyorchestrate start "$agent" --socket "$SOCKET" --format json > /dev/null 2>&1; then
            log "SUCCESS: Restart command sent for $agent"
            
            # Wait and verify it's running
            sleep 5
            alive=$(pyorchestrate status "$agent" --socket "$SOCKET" --format json 2>/dev/null | jq -r '.data.alive // false')
            
            if [ "$alive" = "true" ]; then
                log "VERIFIED: $agent is now alive"
            else
                log "WARNING: $agent restart failed - alive: $alive"
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
    
    if pyorchestrate status --socket "$SOCKET" --format json > /dev/null 2>&1; then
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
    alive=$(pyorchestrate status "$agent" --socket "$SOCKET" --format json 2>/dev/null | jq -r '.data.alive // false')
    
    if [ "$alive" = "true" ]; then
        echo "✓ $agent is running"
    else
        echo "✗ $agent is not running (alive: $alive)"
        all_agents_ready=false
    fi
doneif [ "$all_agents_ready" = true ]; then
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
          pyorchestrate status --socket /var/run/pyorchestrate/orchestrator.sock --format table || echo 'Orchestrator not ready'
          sleep 30
        done
      "
    depends_on:
      - orchestrator
      
  web-interface:
    image: pyorchestrate/cli
    ports:
      - "8080:8080"
    volumes:
      - socket-volume:/var/run/pyorchestrate
    environment:
      - PYORCHESTRATE_AUTH_TOKEN=${AUTH_TOKEN:-changeme}
    command: |
      pyorchestrate-web 
        --host 0.0.0.0 
        --port 8080 
        --socket /var/run/pyorchestrate/orchestrator.sock
        --enable-auth 
        --auth-token ${PYORCHESTRATE_AUTH_TOKEN}
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
            pyorchestrate status --socket /var/run/pyorchestrate/orchestrator.sock --format json | \
              jq -r '.data | 
                "# HELP pyorchestrate_running_agents Number of running agents\n# TYPE pyorchestrate_running_agents gauge\npyorchestrate_running_agents \(.running_agents // 0)\n# HELP pyorchestrate_total_agents Total number of agents\n# TYPE pyorchestrate_total_agents gauge\npyorchestrate_total_agents \(.total_agents // 0)"
              ' > /tmp/metrics.txt 2>/dev/null || echo "# Metrics unavailable" > /tmp/metrics.txt
            sleep 30
          done
        - name: web-interface
          image: my-pyorchestrate-cli:latest
          ports:
          - containerPort: 8080
          volumeMounts:
          - name: socket-volume
            mountPath: /var/run/pyorchestrate
          env:
          - name: AUTH_TOKEN
            valueFrom:
              secretKeyRef:
                name: pyorchestrate-secret
                key: auth-token
          command:
          - pyorchestrate-web
          - --host=0.0.0.0
          - --port=8080
          - --socket=/var/run/pyorchestrate/orchestrator.sock
          - --enable-auth
          - --auth-token=$(AUTH_TOKEN)
        
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
stats=$(pyorchestrate status --socket "$SOCKET" --format json 2>/dev/null)

if [ $? -eq 0 ]; then
    # Export metrics in Prometheus format
    cat > "$METRICS_FILE" << EOF
# HELP pyorchestrate_total_agents Total number of agents
# TYPE pyorchestrate_total_agents gauge
pyorchestrate_total_agents $(echo "$stats" | jq '.data.total_agents // 0')

# HELP pyorchestrate_running_agents Number of running agents  
# TYPE pyorchestrate_running_agents gauge
pyorchestrate_running_agents $(echo "$stats" | jq '.data.running_agents // 0')

# HELP pyorchestrate_waiting_agents Number of waiting agents
# TYPE pyorchestrate_waiting_agents gauge
pyorchestrate_waiting_agents $(echo "$stats" | jq '.data.waiting_agents // 0')

# HELP pyorchestrate_max_workers Maximum worker threads
# TYPE pyorchestrate_max_workers gauge
pyorchestrate_max_workers $(echo "$stats" | jq '.data.max_workers // 0')
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
stats=$(pyorchestrate status --socket "$SOCKET" --format json 2>/dev/null)

if [ $? -ne 0 ]; then
    send_alert "critical" "PyOrchestrate Orchestrator Down" "Cannot connect to orchestrator socket"
    exit 1
fi

running_agents=$(echo "$stats" | jq '.data.running_agents // 0')
total_agents=$(echo "$stats" | jq '.data.total_agents // 0')
failed_agents=$((total_agents - running_agents))

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
    pyorchestrate ps --socket "$SOCKET" --format json > "$BACKUP_DIR/pre_maintenance_agents.json"
    pyorchestrate status --socket "$SOCKET" --format json > "$BACKUP_DIR/pre_maintenance_status.json"
    
    # Gracefully stop non-critical agents
    non_critical_agents=("DataProcessor" "LogCollector")
    
    for agent in "${non_critical_agents[@]}"; do
        echo "Stopping $agent..."
        pyorchestrate stop "$agent" --socket "$SOCKET"
    done
    
    echo "Maintenance mode active"
}

exit_maintenance() {
    echo "Exiting maintenance mode..."
    
    # Restart stopped agents
    backup_agents=$(ls -t "$BACKUP_DIR"/pre_maintenance_agents.json | head -1)
    
    if [ -f "$backup_agents" ]; then
        # Extract agents that were alive before maintenance
        running_agents=$(jq -r '.data.agents[] | select(.alive == true) | .agent_name' "$backup_agents")
        
        for agent in $running_agents; do
            echo "Starting $agent..."
            pyorchestrate start "$agent" --socket "$SOCKET"
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
pyorchestrate ps --socket "$SOCKET" --format json > "$RESULTS_DIR/pre_test_agents.json"
pyorchestrate status --socket "$SOCKET" --format json > "$RESULTS_DIR/pre_test_status.json"

# Start load test monitoring
monitor_during_test() {
    echo "Starting load test monitoring..."
    
    while [ -f "/tmp/load_test_running" ]; do
        timestamp=$(date +%s)
        pyorchestrate status --socket "$SOCKET" --format json > "$RESULTS_DIR/stats_$timestamp.json" 2>/dev/null
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
        try:
            data = json.load(f)
            timestamp = os.path.basename(stats_file).replace('stats_', '').replace('.json', '')
            if 'data' in data and data['data']:
                stats = data['data']
                running = stats.get('running_agents', 0)
                total = stats.get('total_agents', 0)
                waiting = stats.get('waiting_agents', 0)
                print(f"Time {timestamp}: Running={running}/{total}, Waiting={waiting}")
            else:
                print(f"Time {timestamp}: No data available")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Time {timestamp}: Error reading data - {e}")

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
if ! pyorchestrate status --socket "$SOCKET" --format json > /dev/null 2>&1; then
    log "ERROR: Cannot connect to orchestrator"
    exit 1
fi

# 3. Verify all agents started
log "Step 3: Verifying agent startup..."
expected_count=5
orchestrator_stats=$(pyorchestrate status --socket "$SOCKET" --format json)
running_count=$(echo "$orchestrator_stats" | jq '.data.running_agents // 0')

if [ "$running_count" -ne "$expected_count" ]; then
    log "WARNING: Expected $expected_count agents, found $running_count running"
fi

# 4. Performance baseline
log "Step 4: Capturing performance baseline..."
pyorchestrate status --socket "$SOCKET" --format json > "/var/log/pyorchestrate/baseline_$(date +%Y%m%d_%H%M%S).json"

log "Deployment verification completed successfully"
```

### Web Interface Production Setup

```bash
#!/bin/bash
# web-production-setup.sh - Production web interface deployment

SOCKET="/var/run/pyorchestrate/prod.sock"
WEB_PORT=8080
AUTH_TOKEN=$(openssl rand -hex 32)
LOG_FILE="/var/log/pyorchestrate/web.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

# Start web interface with authentication
start_web_interface() {
    log "Starting PyOrchestrate Web Interface..."
    
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Start web interface
    pyorchestrate-web \
        --host 0.0.0.0 \
        --port "$WEB_PORT" \
        --socket "$SOCKET" \
        --enable-auth \
        --auth-token "$AUTH_TOKEN" \
        >> "$LOG_FILE" 2>&1 &
    
    WEB_PID=$!
    
    # Wait for web interface to start
    sleep 3
    
    # Test web interface
    if curl -f -H "Authorization: Bearer $AUTH_TOKEN" \
            "http://localhost:$WEB_PORT/api/status" > /dev/null 2>&1; then
        log "Web interface started successfully (PID: $WEB_PID)"
        log "Dashboard available at: http://localhost:$WEB_PORT"
        log "Authentication token: $AUTH_TOKEN"
        
        # Save token to secure file
        echo "$AUTH_TOKEN" > /etc/pyorchestrate/web-token
        chmod 600 /etc/pyorchestrate/web-token
        
        return 0
    else
        log "ERROR: Web interface failed to start"
        return 1
    fi
}

# Health check for web interface
check_web_health() {
    local token_file="/etc/pyorchestrate/web-token"
    
    if [ -f "$token_file" ]; then
        local token=$(cat "$token_file")
        
        if curl -f -H "Authorization: Bearer $token" \
                "http://localhost:$WEB_PORT/api/status" > /dev/null 2>&1; then
            log "Web interface health check: OK"
            return 0
        else
            log "Web interface health check: FAILED"
            return 1
        fi
    else
        log "Web interface token file not found"
        return 1
    fi
}

# Main execution
if start_web_interface; then
    # Setup periodic health checks
    while true; do
        sleep 60
        check_web_health || break
    done
else
    log "Failed to start web interface"
    exit 1
fi
```

These examples demonstrate real-world usage patterns for the PyOrchestrate CLI, from simple development workflows to complex production monitoring and automation scenarios.
