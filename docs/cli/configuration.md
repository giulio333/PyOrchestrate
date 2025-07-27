---
title: CLI Configuration
editLink: true
---

# CLI Configuration

The PyOrchestrate CLI command interface requires specific configuration in your orchestrator to enable real-time control and monitoring capabilities.

## Orchestrator Configuration

To enable CLI runtime commands, you need to configure your orchestrator with the command interface settings.

### Basic Configuration

```python
from PyOrchestrate.core.orchestrator import BaseOrchestrator

class MyOrchestrator(BaseOrchestrator):
    class Config(BaseOrchestrator.Config):
        # Enable the command interface
        enable_command_interface: bool = True
        
        # UNIX socket path for communication
        command_socket_path: str = "/tmp/pyorchestrate.sock"
```

### Advanced Configuration

For production environments, you may want additional configuration options:

```python
class MyOrchestrator(BaseOrchestrator):
    class Config(BaseOrchestrator.Config):
        # Command interface settings
        enable_command_interface: bool = True
        command_socket_path: str = "/var/run/pyorchestrate/orchestrator.sock"
        
        # Security settings
        command_socket_permissions: int = 0o660  # rw-rw----
        command_timeout: int = 30  # seconds
        
        # Logging for CLI operations
        log_cli_commands: bool = True
        cli_audit_log_path: str = "/var/log/pyorchestrate/cli.log"
```

## Configuration Options

### Core Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enable_command_interface` | `bool` | `False` | Enable/disable the CLI command interface |
| `command_socket_path` | `str` | `"/tmp/pyorchestrate.sock"` | Path to the UNIX socket file |

### Security Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `command_socket_permissions` | `int` | `0o600` | UNIX socket file permissions |
| `command_timeout` | `int` | `30` | Command execution timeout in seconds |
| `allowed_commands` | `List[str]` | `None` | Whitelist of allowed commands (None = all) |
| `blocked_commands` | `List[str]` | `[]` | Blacklist of blocked commands |

### Logging Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `log_cli_commands` | `bool` | `True` | Log all CLI command executions |
| `cli_audit_log_path` | `str` | `None` | Separate audit log file for CLI operations |
| `cli_log_level` | `str` | `"INFO"` | Log level for CLI operations |

## Socket Configuration

### Socket Path Selection

Choose socket paths based on your deployment environment:

**Development:**
```python
command_socket_path: str = "/tmp/pyorchestrate.sock"
```

**Production (single user):**
```python
command_socket_path: str = "/var/run/pyorchestrate/orchestrator.sock"
```

**Production (multi-user):**
```python
command_socket_path: str = "/var/run/pyorchestrate/orchestrator-{user}.sock"
```

### Socket Permissions

Configure appropriate permissions for your security requirements:

```python
# Owner read/write only (most secure)
command_socket_permissions: int = 0o600  # rw-------

# Owner and group read/write
command_socket_permissions: int = 0o660  # rw-rw----

# Owner, group, and others read/write (least secure)
command_socket_permissions: int = 0o666  # rw-rw-rw-
```

## Security Configuration

### Command Filtering

Restrict which commands can be executed:

```python
class MyOrchestrator(BaseOrchestrator):
    class Config(BaseOrchestrator.Config):
        enable_command_interface: bool = True
        command_socket_path: str = "/tmp/pyorchestrate.sock"
        
        # Only allow monitoring commands, no control commands
        allowed_commands: List[str] = ["ps", "status", "stats", "report"]
        
        # Block dangerous commands
        blocked_commands: List[str] = ["shutdown"]
```

### Audit Logging

Enable comprehensive logging for security compliance:

```python
class MyOrchestrator(BaseOrchestrator):
    class Config(BaseOrchestrator.Config):
        enable_command_interface: bool = True
        command_socket_path: str = "/var/run/pyorchestrate/orchestrator.sock"
        
        # Audit configuration
        log_cli_commands: bool = True
        cli_audit_log_path: str = "/var/log/pyorchestrate/cli-audit.log"
        cli_log_level: str = "DEBUG"
```

Audit log format:
```
2025-07-27T10:30:00Z [CLI] user=admin command=start agent=WeatherAgent result=success
2025-07-27T10:31:15Z [CLI] user=admin command=stats result=success
2025-07-27T10:32:30Z [CLI] user=monitor command=shutdown result=blocked
```

## Environment-Specific Configurations

### Development Environment

```python
class DevelopmentOrchestrator(BaseOrchestrator):
    class Config(BaseOrchestrator.Config):
        # Development settings - more permissive
        enable_command_interface: bool = True
        command_socket_path: str = "/tmp/dev-pyorchestrate.sock"
        command_socket_permissions: int = 0o666
        command_timeout: int = 60
        log_cli_commands: bool = True
        cli_log_level: str = "DEBUG"
```

### Production Environment

```python
class ProductionOrchestrator(BaseOrchestrator):
    class Config(BaseOrchestrator.Config):
        # Production settings - security focused
        enable_command_interface: bool = True
        command_socket_path: str = "/var/run/pyorchestrate/prod.sock"
        command_socket_permissions: int = 0o660
        command_timeout: int = 15
        
        # Security restrictions
        allowed_commands: List[str] = ["ps", "status", "stats", "report"]
        blocked_commands: List[str] = ["shutdown"]
        
        # Comprehensive logging
        log_cli_commands: bool = True
        cli_audit_log_path: str = "/var/log/pyorchestrate/cli-audit.log"
        cli_log_level: str = "INFO"
```

### Monitoring-Only Environment

```python
class MonitoringOrchestrator(BaseOrchestrator):
    class Config(BaseOrchestrator.Config):
        # Read-only monitoring configuration
        enable_command_interface: bool = True
        command_socket_path: str = "/var/run/pyorchestrate/monitor.sock"
        command_socket_permissions: int = 0o644
        
        # Only monitoring commands allowed
        allowed_commands: List[str] = ["ps", "status", "stats", "report"]
        
        # No control commands
        blocked_commands: List[str] = ["start", "stop", "shutdown"]
```

## Deployment Considerations

### Docker Environments

When running in containers, consider volume mounts for socket access:

```yaml
# docker-compose.yml
services:
  pyorchestrate:
    image: my-pyorchestrate-app
    volumes:
      - /var/run/pyorchestrate:/var/run/pyorchestrate
    environment:
      - PYORCHESTRATE_SOCKET_PATH=/var/run/pyorchestrate/orchestrator.sock
```

```python
import os

class DockerOrchestrator(BaseOrchestrator):
    class Config(BaseOrchestrator.Config):
        enable_command_interface: bool = True
        command_socket_path: str = os.getenv(
            "PYORCHESTRATE_SOCKET_PATH", 
            "/var/run/pyorchestrate/orchestrator.sock"
        )
```

### Kubernetes Environments

Use shared volumes for CLI access:

```yaml
# kubernetes deployment
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: orchestrator
    image: my-pyorchestrate-app
    volumeMounts:
    - name: socket-volume
      mountPath: /var/run/pyorchestrate
  - name: cli-sidecar
    image: my-pyorchestrate-cli
    volumeMounts:
    - name: socket-volume
      mountPath: /var/run/pyorchestrate
  volumes:
  - name: socket-volume
    emptyDir: {}
```

### Systemd Integration

Configure socket activation with systemd:

```ini
# /etc/systemd/system/pyorchestrate.socket
[Unit]
Description=PyOrchestrate Command Socket

[Socket]
ListenStream=/var/run/pyorchestrate/orchestrator.sock
SocketUser=pyorchestrate
SocketGroup=pyorchestrate
SocketMode=0660

[Install]
WantedBy=sockets.target
```

## Validation and Testing

### Configuration Validation

Test your configuration before deployment:

```python
# Test script
from your_app import MyOrchestrator

config = MyOrchestrator.Config()
validation_results = config.validate()

for result in validation_results:
    print(f"{result.severity}: {result.field} - {result.message}")
```

### CLI Connectivity Test

```bash
# Test script
#!/bin/bash
SOCKET="/var/run/pyorchestrate/orchestrator.sock"

echo "Testing CLI connectivity..."

if [ -S "$SOCKET" ]; then
    echo "Socket exists: $SOCKET"
    
    if pyorchestrate stats "$SOCKET" > /dev/null 2>&1; then
        echo "CLI connection successful"
    else
        echo "CLI connection failed"
        exit 1
    fi
else
    echo "Socket not found: $SOCKET"
    exit 1
fi
```

## Troubleshooting

### Common Configuration Issues

1. **Socket Permission Denied**
   ```bash
   # Check current permissions
   ls -la /var/run/pyorchestrate/orchestrator.sock
   
   # Fix permissions
   chmod 660 /var/run/pyorchestrate/orchestrator.sock
   ```

2. **Socket Path Not Found**
   ```python
   # Ensure directory exists
   import os
   socket_dir = os.path.dirname(config.command_socket_path)
   os.makedirs(socket_dir, exist_ok=True)
   ```

3. **Command Blocked**
   ```python
   # Check allowed/blocked commands configuration
   print(f"Allowed: {config.allowed_commands}")
   print(f"Blocked: {config.blocked_commands}")
   ```

### Debug Configuration

Enable debug logging to troubleshoot configuration issues:

```python
class DebugOrchestrator(BaseOrchestrator):
    class Config(BaseOrchestrator.Config):
        enable_command_interface: bool = True
        command_socket_path: str = "/tmp/debug-pyorchestrate.sock"
        cli_log_level: str = "DEBUG"
        log_cli_commands: bool = True
```
