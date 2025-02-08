---
title: ZeroMQPubSub Plugin
description: Learn how to use the ZeroMQPubSub plugin to enable communication between agents using the ZeroMQ Publish-Subscribe pattern.
---

# ZeroMQPubSub Plugin
The ZeroMQPubSub plugin enables agents to communicate using the **ZeroMQ Publish-Subscribe** pattern. This is useful when you need to broadcast messages to multiple agents.

## Usage

You can create a **Publisher** or **Subscriber** using the `ZeroMQPubSub` and use them to send and receive messages.

```python
import zmq
from PyOrchestrate.core.agent import PeriodicProcessAgent
from PyOrchestrate.core.plugins import ZeroMQPubSub

class MyAgent(PeriodicProcessAgent):
    def setup(self):
        self.zmq = ZeroMQPubSub("tcp://localhost:5555", zmq.SUB)
        self.zmq.initialize()
    
    def runner(self):
        message = self.zmq.recv().decode()
        print("Received message:", message)

    def on_close(self):
        self.zmq.finalize()
```

::: tip
Make sure to call the `initialize` and `finalize` methods to set up and clean up the plugin resources.
:::

## Publisher

The **Publisher** sends messages to all connected **Subscribers**.

```python
pub.send(b"Hello, World!")
```

## Subscriber

The **Subscriber** receives messages from the **Publisher**.

```python
message: byte = sub.recv()
```

## Working with Topics

Topics allow you to filter messages so that only subscribers with matching filters receive them. 

When creating a **subscriber**, you can supply a topic filter (e.g. `b"my_topic"`) to receive only messages that match. Similarly, a **publisher** can send a message with an associated topic. If no topic is provided with the `send` method, the message is broadcast to all subscribers.

```python
pub = ZeroMQPubSub("tcp://localhost:5555", zmq.PUB)
sub = ZeroMQPubSub("tcp://localhost:5555", zmq.SUB, b"my_topic")
pub.send(b"Hello, World!", b"my_topic")
```

::: tip
If you don't specify a topic when sending a message, all subscribers will receive it. Conversely, to receive topic-specific messages, the subscriber must subscribe using the correct topic filter. 
:::