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
from PyOrchestrate.core.agent import BaseProcessAgent
from PyOrchestrate.core.plugins import ZeroMQPubSub
import zmq

class MyAgent(BaseProcessAgent):

    class Plugin(BaseProcessAgent.Plugin):
        zmq = ZeroMQPubSub("tcp://localhost:5555", zmq.PUB)

    plugin: Plugin

    def execute(self):
        super().execute()
        self.plugin.zmq.send("Hello, World!".encode())
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

# Receive a message
message = zmq.recv()
print("Received message:", message.decode())
```

## Future Enhancements

### HTTP Plugin

The HTTP Plugin allows agents to communicate with external HTTP services.

**Purpose**: To send and receive HTTP requests.

**Example**

```python
from PyOrchestrate.core.plugins import HTTPPlugin

# Initialize the HTTP Plugin
http = HTTPPlugin("https://api.example.com")

# Send a GET request and retrieve JSON data
response = http.get("/data")
print("Received data:", response.json())
```

### Database Plugin

The Database Plugin provides methods to interact with various databases.

**Purpose**: To perform database operations such as queries and updates.

**Example**

```python
from PyOrchestrate.core.plugins import DatabasePlugin

# Initialize the Database Plugin
db = DatabasePlugin("database_connection_string")

# Execute a query and log the results
result = db.query("SELECT * FROM table")
print("Query result:", result)
```

### MQTT Plugin

The MQTT Plugin facilitates communication with MQTT brokers for IoT applications.

**Purpose**: To publish and subscribe to MQTT topics.

**Example**

```python
from PyOrchestrate.core.plugins import MQTTPlugin

# Initialize the MQTT Plugin
mqtt = MQTTPlugin("mqtt://broker.example.com")

# Publish a message
mqtt.publish("topic/test", "Hello, MQTT!")
```

For more detailed information about each communication plugin, refer to the respective sections above.
