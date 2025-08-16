---
title: Web Interface
editLink: true
---

# PyOrchestrate Web Interface

The PyOrchestrate Web Interface provides a browser-based dashboard for monitoring and controlling your orchestrator and agents. It offers the same functionality as the CLI commands but through an intuitive web interface.

## Command Overview

```bash
pyorchestrate-web [--host HOST] [--port PORT] [--socket SOCKET] [--enable-auth] [--auth-token AUTH_TOKEN]
```

## Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--host` | `str` | `127.0.0.1` | Host address to bind the web server to |
| `--port` | `int` | `8080` | Port number for the web server |
| `--socket` | `str` | `/tmp/pyorchestrate.sock` | Path to the orchestrator's UNIX socket |
| `--enable-auth` | `flag` | `False` | Enable token-based authentication |
| `--auth-token` | `str` | `None` | Authentication token (required if auth is enabled) |

## Basic Usage

### Start Web Interface

Start the web interface with default settings:

```bash
pyorchestrate-web
```

This will start the web server on `http://127.0.0.1:8080` and connect to the default socket at `/tmp/pyorchestrate.sock`.

### Custom Host and Port

Start the web interface on a specific host and port:

```bash
pyorchestrate-web --host 0.0.0.0 --port 3000
```

This allows access from any network interface on port 3000.

### Custom Socket Path

Connect to an orchestrator using a custom socket path:

```bash
pyorchestrate-web --socket /var/run/pyorchestrate/prod.sock
```

## Authentication

### Enable Authentication

For production environments, enable token-based authentication:

```bash
pyorchestrate-web --enable-auth --auth-token "your-secret-token"
```

### Environment Variables

You can also set the authentication token via environment variable:

```bash
export PYORCHESTRATE_AUTH_TOKEN="your-secret-token"
pyorchestrate-web --enable-auth
```

## Web Interface Features

### Dashboard Overview

The web interface provides:

- **Real-time Agent Status**: Live view of all registered agents
- **System Statistics**: CPU, memory, and performance metrics
- **Event History**: Browsable log of orchestrator events
- **Agent Control**: Start, stop, and restart agents
- **Dependency Graph**: Visual representation of agent dependencies

### Main Sections

#### 1. Agents Overview
- List of all registered agents
- Status indicators (Running, Stopped, Failed)
- Quick action buttons (Start/Stop/Restart)
- Agent-specific metrics

#### 2. System Status
- Orchestrator health information
- Resource utilization graphs
- Performance metrics over time
- Error rates and alerts

#### 3. Event Log
- Filterable event history
- Real-time event streaming
- Export capabilities
- Search and pagination

#### 4. Dependencies
- Interactive dependency graph
- Agent relationship visualization
- Dependency health status
- Impact analysis

## Production Configuration

### Secure Setup

For production deployments:

```bash
# Generate a secure token
export AUTH_TOKEN=$(openssl rand -hex 32)

# Start with authentication and specific binding
pyorchestrate-web \
  --host 0.0.0.0 \
  --port 8080 \
  --socket /var/run/pyorchestrate/prod.sock \
  --enable-auth \
  --auth-token "$AUTH_TOKEN"
```

### Reverse Proxy Setup

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name pyorchestrate.example.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for real-time updates
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["pyorchestrate-web", "--host", "0.0.0.0", "--port", "8080", "--socket", "/var/run/pyorchestrate/orchestrator.sock"]
```

Docker Compose example:

```yaml
version: '3.8'
services:
  orchestrator:
    build: .
    volumes:
      - socket-volume:/var/run/pyorchestrate
    command: python orchestrator.py
    
  web-interface:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - socket-volume:/var/run/pyorchestrate
    command: pyorchestrate-web --host 0.0.0.0 --port 8080 --socket /var/run/pyorchestrate/orchestrator.sock --enable-auth --auth-token ${AUTH_TOKEN}
    environment:
      - AUTH_TOKEN=${AUTH_TOKEN}
    depends_on:
      - orchestrator

volumes:
  socket-volume:
```

## API Integration

The web interface also exposes REST API endpoints for programmatic access:

### Endpoints

- `GET /api/status` - Get orchestrator status
- `GET /api/agents` - List all agents
- `POST /api/agents/{name}/start` - Start an agent
- `POST /api/agents/{name}/stop` - Stop an agent
- `GET /api/events` - Get event history
- `GET /api/stats` - Get system statistics

### Authentication Headers

When authentication is enabled, include the token in requests:

```bash
curl -H "Authorization: Bearer your-secret-token" http://localhost:8080/api/status
```

## Development and Testing

### Development Mode

For development, start without authentication:

```bash
pyorchestrate-web --host 127.0.0.1 --port 3000
```

### Testing Connection

Test if the web interface can connect to your orchestrator:

```bash
# Start orchestrator with command interface
python your_orchestrator.py &

# Start web interface
pyorchestrate-web --socket /tmp/pyorchestrate.sock

# Open browser to http://localhost:8080
```

## Troubleshooting

### Common Issues

#### Cannot Connect to Socket

```bash
# Check if socket exists
ls -la /tmp/pyorchestrate.sock

# Check orchestrator is running with command interface
python -c "
import socket
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
try:
    sock.connect('/tmp/pyorchestrate.sock')
    print('Socket connection successful')
except Exception as e:
    print(f'Socket connection failed: {e}')
finally:
    sock.close()
"
```

#### Permission Denied

```bash
# Check socket permissions
stat /tmp/pyorchestrate.sock

# Fix permissions if needed
chmod 660 /tmp/pyorchestrate.sock
```

#### Port Already in Use

```bash
# Find process using the port
lsof -i :8080

# Use a different port
pyorchestrate-web --port 8081
```

### Debug Mode

Enable debug logging:

```bash
export PYORCHESTRATE_DEBUG=1
pyorchestrate-web --port 8080
```

## Integration Examples

### Monitoring Dashboard

Create a custom monitoring setup:

```bash
#!/bin/bash
# monitoring-setup.sh

# Start orchestrator
python orchestrator.py &
ORCH_PID=$!

# Wait for orchestrator to initialize
sleep 3

# Start web interface with monitoring-specific settings
pyorchestrate-web \
  --host 0.0.0.0 \
  --port 8080 \
  --socket /tmp/pyorchestrate.sock \
  &
WEB_PID=$!

echo "Orchestrator PID: $ORCH_PID"
echo "Web Interface PID: $WEB_PID"
echo "Dashboard available at: http://localhost:8080"

# Cleanup function
cleanup() {
    echo "Shutting down..."
    kill $WEB_PID 2>/dev/null
    kill $ORCH_PID 2>/dev/null
}

trap cleanup EXIT
wait
```

### Health Check Script

```bash
#!/bin/bash
# health-check-web.sh

WEB_URL="http://localhost:8080"
AUTH_TOKEN="your-token"

# Check web interface health
if curl -f -H "Authorization: Bearer $AUTH_TOKEN" "$WEB_URL/api/status" > /dev/null 2>&1; then
    echo "Web interface is healthy"
    exit 0
else
    echo "Web interface is not responding"
    exit 1
fi
```

The PyOrchestrate Web Interface provides a user-friendly alternative to CLI commands, making it easy to monitor and control your orchestrator through a browser-based dashboard.
