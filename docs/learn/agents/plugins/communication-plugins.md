# Communication Plugins

Communication plugins in PyOrchestrate allow agents to interact with other agents, external systems, and more.

## How to Use Communication Plugins

You can easily use **pre-built** communication plugins in your agents simply by importing them from the `PyOrchestrate.core.plugins` module.

For example, to use the `ZeroMQPubSub` plugin, you can import it as follows:

```python
from PyOrchestrate.core.plugins import ZeroMQPubSub
```

The `agent.plugin` object is useful for retrieving user-initialized plugins. The agent will autonomously initialize and release their resources at startup and shutdown. This ensures that the plugins are properly managed throughout the agent's lifecycle.

```python
class MyAgent(PeriodicProcessAgent):

    class Plugin(PeriodicProcessAgent.Plugin):
        zmq = ZeroMQPubSub("tcp://localhost:5555", zmq.SUB)

    plugin: Plugin

    def runner(self):
        message = self.plugin.zmq.send("Hello, World!".encode())
```

::: tip
You can always put plugin outside the Plugin class and use it directly in the agent class but keep in mind that the plugin will not be initialized and finalized automatically.

You need to manually call the `plugin.initialize()` and `plugin.finalize()` methods to initialize and finalize the plugin.
:::

## Available Communication Plugins

### ZeroMQPubSub Plugin

The `ZeroMQPubSub` Plugin provides communication using ZeroMQ Pub/Sub sockets.

**Example**

```python
from PyOrchestrate.core.plugins import ZeroMQPubSub

# Initialize the ZeroMQPubSub plugin
zmq = ZeroMQPubSub("tcp://localhost:5555", zmq.SUB)

# Send a message
zmq.send("Hello, World!".encode())
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
