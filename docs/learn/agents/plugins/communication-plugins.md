# Communication Plugins

Communication plugins in PyOrchestrate allow agents to interact with other agents, external systems, and more.

## How to Use Communication Plugins

You can easily use pre-built communication plugins in your agents simply by importing them from the `PyOrchestrate.core.plugins` module.

::: tip
Every communication plugin has a `initialize` method that initializes the plugin and a `finalize` method that cleans up resources when the agent is closed.
:::

## Available Communication Plugins

### ZeroMQPubSub Plugin

The `ZeroMQPubSub` Plugin provides communication using ZeroMQ Pub/Sub sockets.

**Example**

```python
from PyOrchestrate.core.plugins import ZeroMQPubSub

class MyAgent(PeriodicProcessAgent):
    def setup(self):
        self.zmq = ZeroMQPubSub("tcp://localhost:5555", zmq.SUB)
        self.zmq.initialize()

    def runner(self):
        message = self.zmq.send("Hello, World!".encode())

    def on_close(self):
        self.zmq.finalize()
```

## Autonomous Initialization and Release of Resources

The `agent.plugin` object is useful for retrieving user-initialized plugins. The agent will autonomously initialize and release their resources at startup and shutdown. This ensures that the plugins are properly managed throughout the agent's lifecycle.

```python
class MyAgent(PeriodicProcessAgent):

    def setup(self):
        super().setup()
        self.my_plugin = self.plugin.get('my_plugin')
        self.logger.info("Plugin initialized")

    def runner(self):
        self.my_plugin.do_something()
        self.logger.info("Plugin action executed")

    def on_close(self):
        self.logger.info("Agent is closing, plugin resources will be released")
```

## Future Enhancements

### HTTP Plugin

The HTTP Plugin allows agents to communicate with external HTTP services.

**Purpose**: To send and receive HTTP requests.

**Example**:

```python
class MyAgent(PeriodicProcessAgent):
    def runner(self):
        response = self.http.get("https://api.example.com/data")
        self.logger.info(f"Received data: {response.json()}")
```

### File System Plugin

The File System Plugin allows agents to read from and write to the file system.

**Purpose**: To perform file operations such as reading, writing, and deleting files.

**Example**:

```python
class MyAgent(PeriodicProcessAgent):
    def runner(self):
        with self.file_system.open("file.txt", "r") as file:
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
        self.database.connect("database_connection_string")

    def runner(self):
        result = self.database.query("SELECT * FROM table")
        self.logger.info(f"Query result: {result}")
```

### MQTT Plugin

The MQTT Plugin facilitates communication with MQTT brokers for IoT applications.

**Purpose**: To publish and subscribe to MQTT topics.

**Example**:

```python
class MyAgent(PeriodicProcessAgent):
    def setup(self):
        self.mqtt.connect("mqtt://broker.example.com")

    def runner(self):
        self.mqtt.publish("topic/test", "Hello, MQTT!")
```


For more detailed information about each communication plugin, refer to the respective sections above.
