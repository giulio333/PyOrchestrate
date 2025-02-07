---
title: ZeroMQPubSub Plugin
description: Learn how to use the ZeroMQPubSub plugin to communicate between agents.
---

# ZeroMQPubSub Plugin
ZeroMQPubSub plugin allows agents to communicate with each other using the **ZeroMQ Publish-Subscribe** pattern. This plugin is useful when you want to broadcast messages to multiple agents.

## Usage

You can create a Publisher or Subscriber using the `ZeroMQPubSub` plugin and register it with the `plugin_manager` inside your agent.

```python
import zmq
from PyOrchestrate.core.agents import PeriodicProcessAgent
from PyOrchestrate.core.plugins.communication_plugins import ZeroMQPubSub

class MyAgent(PeriodicProcessAgent):
    def setup(self):
        sub = ZeroMQPubSub("tcp://localhost:5555", zmq.SUB)
        self.plugin_manager.register(sub)
    
    def runner(self):
        message = self.com.recv()
        print("Received message:", message)
```

## Publisher

The **Publisher** sends messages to all the **Subscribers** connected. You can send messages using the `send` method:

```python
pub.send(b"Hello, World!")
```

::: tip
The message should be a byte string (`bytes`).
:::

## Subscriber

The **Subscriber** receives messages from the **Publisher**. You can receive messages using the `recv` method:

```python
message = sub.recv()
```

## Working with Topics

Topics allow you to filter messages so that only subscribers with matching topic filters receive them. When a subscriber is created, you can provide a topic filter (e.g., b"my_topic") so that it only processes messages with a topic that matches or contains the filter. Similarly, a publisher can send a message with an associated topic. For successful communication, both the publisher and the subscriber must agree on the topic filter.

For example:

```python
pub = ZeroMQPubSub("tcp://localhost:5555", zmq.PUB)
sub = ZeroMQPubSub("tcp://localhost:5555", zmq.SUB, b"my_topic")
```

As shown in the example above, only **Subscribers** take the topic as an argument. Then you can send messages specifying the topic:

```python
pub.send(b"Hello, World!", b"my_topic")
```

::: tip 
If you don't specify a topic in the `send` method, the message will be broadcasted to all **Subscribers**.
:::

::: tip
If sending a message with a topic, the **Subscriber** should also subscribe to the same topic to receive the messages correctly. Note that it could also receive messages by subscribing to a substring of the topic as shown in the example above.

```python
pub = ZeroMQPubSub("tcp://localhost:5555", zmq.PUB)
sub = ZeroMQPubSub("tcp://localhost:5555", zmq.SUB, b"my_topic")
pub.send(b"Hello, World!", b"my")
```