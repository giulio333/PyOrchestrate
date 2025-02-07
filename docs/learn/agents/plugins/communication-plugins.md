# Communication Plugins

Communication plugins in PyOrchestrate allow agents to interact with other agents, external systems, and more.

## Accessing Communication Plugins

Agents can interact with communication plugins through the dedicated `com` property, which provides a unified interface for integrating various messaging systems and protocols.

To integrate a plugin, follow these steps:
1. Import the plugin.
2. Register it with the plugin manager.
3. When it is no longer required, invoke the `finalize()` method to properly release its resources.

::: warning
Please note that each agent currently supports only one communication plugin type. 
:::

## Available Communication Plugins

### ZeroMQPubSub Plugin

The `ZeroMQPubSub` Plugin provides communication using ZeroMQ Pub/Sub sockets.

**Example**

```python
from PyOrchestrate.core.plugins.communication_plugins import ZeroMQPubSub

class MyAgent(PeriodicProcessAgent):
    def setup(self):
        zmq_plugin = ZeroMQPubSub("tcp://localhost:5555", zmq.SUB)
        self.plugin_manager.register(zmq_plugin)

    def runner(self):
        message = self.com.send("Hello, World!")

    def on_close(self):
        self.com.finalize()
```

## Future Enhancements

### HTTP Plugin

The HTTP Plugin allows agents to communicate with external HTTP services.

**Purpose**: To send and receive HTTP requests.

**Example**:

```python
class MyAgent(PeriodicProcessAgent):
    def runner(self):
        response = self.com.http.get("https://api.example.com/data")
        self.logger.info(f"Received data: {response.json()}")
```

### File System Plugin

The File System Plugin allows agents to read from and write to the file system.

**Purpose**: To perform file operations such as reading, writing, and deleting files.

**Example**:

```python
class MyAgent(PeriodicProcessAgent):
    def runner(self):
        with self.com.file_system.open("file.txt", "r") as file:
            content = file.read()
            self.logger.info(f"File content: {content}")
```

### Database Plugin

The Database Plugin provides methods to interact with various databases.

**Purpose**: To perform database operations such as queries and updates.

**Example**:

```python
class MyAgent(PeriodicProcessAgent):
    def setup(self):
        self.com.database.connect("database_connection_string")

    def runner(self):
        result = self.com.database.query("SELECT * FROM table")
        self.logger.info(f"Query result: {result}")
```

### MQTT Plugin

The MQTT Plugin facilitates communication with MQTT brokers for IoT applications.

**Purpose**: To publish and subscribe to MQTT topics.

**Example**:

```python
class MyAgent(PeriodicProcessAgent):
    def setup(self):
        self.com.mqtt.connect("mqtt://broker.example.com")

    def runner(self):
        self.com.mqtt.publish("topic/test", "Hello, MQTT!")
```


For more detailed information about each communication plugin, refer to the respective sections above.
