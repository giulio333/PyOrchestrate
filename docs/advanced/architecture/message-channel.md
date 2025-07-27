# MessageChannel

The `MessageChannel` class serves as the core communication infrastructure in PyOrchestrate, providing a unified interface for message passing between different system components.

## Architecture Overview

### Core Design Principles

The `MessageChannel` implements a **strategy pattern** that abstracts three different communication mechanisms under a single interface:

1. **Thread Queues** (`thread`) - For thread-based agents using `queue.Queue`
2. **Process Queues** (`process`) - For process-based agents using `multiprocessing.Queue`
3. **UNIX Domain Sockets** (`unix_socket`) - For external CLI communication

### Class Structure

```python
class MessageChannel:
    def __init__(self, a_type: Literal["thread", "process", "unix_socket"], socket_path: str = DEFAULT_SOCKET_PATH)
    def send(self, target: str, msg: ServiceMessage) -> None
    def receive(self, timeout: Optional[float] = None) -> Optional[ServiceMessage]
    def close(self) -> None
```

### Message Format

All communication uses the standardized `ServiceMessage` dataclass:

```python
@dataclass
class ServiceMessage:
    sender: str
    type: Literal["COMMAND", "STATUS"] 
    payload: str
    timestamp: datetime
```

## Usage Patterns in Orchestrator

The Orchestrator employs **dual MessageChannel architecture** for handling different communication flows:

### 1. Agent Communication Channel (`self.msg_channel`)

**Purpose**: Internal communication between agents and orchestrator  
**Type**: `"process"` (uses `multiprocessing.Queue`)  
**Direction**: Bidirectional (agents → orchestrator, orchestrator → agents)

```python
# Orchestrator initialization
self.msg_channel = MessageChannel("process")

# Agent registration - shares the same channel
agent_entry: AgentEntry = self.memory.add_agent(
    # ...
    msg_channel=msg_channel or self.msg_channel,
    # ...
)
```

**Message Flow**:
- **Agents → Orchestrator**: Status updates, lifecycle events, error reports
- **Orchestrator → Agents**: Control commands, configuration updates

### 2. External Command Channel (`self.command_channel`)

**Purpose**: External CLI and tooling integration  
**Type**: `"unix_socket"` (uses UNIX domain sockets)  
**Direction**: Bidirectional (CLI tools ↔ orchestrator)

```python
# Conditional initialization based on configuration
if self.config.enable_command_interface:
    self.command_channel = MessageChannel(
        "unix_socket", 
        self.config.command_socket_path
    )
```

**Message Flow**:
- **External CLI → Orchestrator**: Commands (`start`, `stop`, `status`, `report`)
- **Orchestrator → CLI**: Responses, status updates, acknowledgments

## Technical Implementation Details

### Timeout Handling

The `MessageChannel` implements **unified timeout behavior** across all communication types:

- **Thread/Process Queues**: Uses native `queue.get(timeout=timeout)`
- **UNIX Sockets**: Uses `socket.settimeout(timeout)` on client connections
- **Default Behavior**: `timeout=None` blocks indefinitely for queues, uses `CLIENT_RECEIVE_TIMEOUT` for sockets

### Agent Integration

Agents inherit the communication channel from their registration:

```python
class BaseAgent:
    def __init__(self, msg_channel: Optional[MessageChannel] = None, **kwargs):
        self.msg_channel = msg_channel or MessageChannel(self.a_type)
    
    def send_message(self, msg: ServiceMessage) -> None:
        """Send message to orchestrator via shared channel"""
        self.msg_channel.send("orchestrator", msg)
```

### Event-Driven Communication

The system uses **centralized event management** where:

1. **Agents** send status messages via `MessageChannel`
2. **Orchestrator** receives messages and converts them to events
3. **EventManager** handles event dispatch and callback execution

```python
def handle_agent_message(self, msg: ServiceMessage) -> None:
    if msg.type == "STATUS":
        if msg.payload == AgentEvent.AGENT_CLOSE.value:
            self.event_manager.emit(OrchestratorEvent.AGENT_TERMINATED, agent_name=msg.sender)
        elif msg.payload == AgentEvent.AGENT_START.value:
            self.event_manager.emit(OrchestratorEvent.AGENT_STARTED, agent_name=msg.sender)
```

## Message Threading Architecture

The Orchestrator implements **non-blocking message processing** using a dedicated thread:

### Thread Lifecycle

```python
def _start_message_thread(self):
    self._message_thread_running = True
    self._message_thread = threading.Thread(
        target=self._message_thread_function,
        daemon=True,
        name="OrchestratorMessageThread"
    )
    self._message_thread.start()
```

### Concurrent Message Processing

- **Dual Channel Monitoring**: Both agent and command channels checked in single loop
- **Timeout Management**: 0.5s timeouts prevent blocking while maintaining responsiveness
- **Error Isolation**: Exception handling prevents thread termination
- **CPU Optimization**: 0.01s sleep prevents excessive CPU usage

## UNIX Socket Implementation

### Server Setup

```python
def _setup_unix_socket(self):
    self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    
    # Cleanup existing socket file
    if os.path.exists(self.socket_path):
        os.unlink(self.socket_path)
    
    # Bind and configure
    self._socket.bind(self.socket_path)
    self._socket.listen(SOCKET_LISTEN_BACKLOG)
    self._socket.settimeout(SOCKET_TIMEOUT)
    
    self._clients: list[socket.socket] = []
```

### Client Management

- **Dynamic Connection Handling**: New clients accepted during `receive()` calls
- **Automatic Cleanup**: Disconnected clients removed from active list
- **Broadcast Communication**: Messages sent to all connected clients
- **Error Resilience**: Connection errors don't terminate the socket server

## Security Considerations

### UNIX Socket Security

- **Filesystem Permissions**: Socket file inherits directory permissions
- **Local Access Only**: UNIX sockets provide local-only access by design
- **Process Ownership**: Only processes with appropriate permissions can connect

### Message Validation

- **Type Safety**: Literal types enforce valid message types
- **JSON Schema**: Structured payload format prevents injection
- **Error Boundaries**: Invalid messages logged but don't crash system

## Performance Characteristics

### Throughput

- **Thread/Process Queues**: High throughput, low latency for internal communication
- **UNIX Sockets**: Moderate throughput, suitable for CLI interaction
- **Message Threading**: Non-blocking design maintains system responsiveness

### Resource Usage

- **Memory**: Minimal overhead, messages garbage collected after processing
- **File Descriptors**: UNIX socket uses one descriptor per connected client
- **CPU**: Minimal CPU usage with sleep-optimized message loop

## Best Practices for Developers

### MessageChannel Usage

1. **Always specify timeout**: Prevents indefinite blocking in production
2. **Handle None returns**: `receive()` returns `None` when no message available
3. **Proper cleanup**: Call `close()` for UNIX socket channels
4. **Error handling**: Wrap message operations in try-catch blocks

### Agent Communication

1. **Use shared channels**: Register agents with orchestrator's message channel
2. **Standard message format**: Use `ServiceMessage` for all communication
3. **Event-driven design**: Send status updates, let orchestrator handle events
4. **Timeout considerations**: Account for message processing delays

### External Integration

1. **Enable command interface**: Set `enable_command_interface=True` in config
2. **Custom socket paths**: Use application-specific socket paths
3. **Client libraries**: Implement client libraries for common languages
4. **Monitoring integration**: Use external commands for health checks

## Future Considerations

### Scalability Enhancements

- **Message Routing**: Implement target-based message routing
- **Load Balancing**: Distribute agents across multiple orchestrator instances
- **Network Protocols**: Add TCP/WebSocket support for distributed deployments

### Security Improvements

- **Authentication**: Add client authentication for external commands
- **Encryption**: Implement message encryption for sensitive data
- **Audit Logging**: Enhanced logging for security monitoring

### Performance Optimizations

- **Message Batching**: Batch multiple messages for improved throughput
- **Compression**: Compress large payloads for network efficiency
- **Async/Await**: Consider async implementation for better concurrency

---

This architecture provides a robust, scalable foundation for PyOrchestrate's communication infrastructure while maintaining simplicity and reliability.
