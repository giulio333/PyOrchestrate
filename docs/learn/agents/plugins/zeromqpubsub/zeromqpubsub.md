---
title: ZeroMQPubSub Plugin
description: Learn how to use the ZeroMQPubSub plugin to enable communication between agents using the ZeroMQ Publish-Subscribe pattern.
---

# ZeroMQPubSub Plugin

## Introduction to Publish-Subscribe Pattern

The **Publish-Subscribe (PubSub)** pattern is a messaging paradigm where senders (publishers) send messages to topics without knowing who will receive them. Receivers (subscribers) express interest in specific topics and receive messages that match their interests. This decouples the sender and receiver, making it ideal for distributed systems where components need to communicate asynchronously.

## Installation Instructions

To use the ZeroMQPubSub plugin, you need to install the `pyzmq` library. You can install it using pip:

```bash
pip install pyzmq
```

## Usage

You can create a **Publisher** or **Subscriber** using the `ZeroMQPubSub` and use them to send and receive messages.

### Publisher Example

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

### Subscriber Example

```python
from PyOrchestrate.core.agent import PeriodicProcessAgent
from PyOrchestrate.core.plugins import ZeroMQPubSub
import zmq

class SubscriberAgent(PeriodicProcessAgent):

    class Plugin(PeriodicProcessAgent.Plugin):
        zmq = ZeroMQPubSub("tcp://localhost:5555", zmq.SUB)

    plugin: Plugin

    def runner(self):
        message = self.plugin.zmq.recv()
        self.logger.info(f"Received message: {message.decode()}")
```

## Error Handling

### Subscriber Connection Delay

ZeroMQ subscribers take some time to establish a connection with the publisher. If the publisher starts sending messages immediately, early messages may be lost. To mitigate this, you can introduce a delay before the publisher starts sending messages.

### Message Loss Considerations

ZeroMQ does not queue messages for late subscribers by default. A subscriber that connects after messages are published will not receive past messages. To handle this, you can use delayed publishing or queue-based architectures.

### Ensuring Proper Topic Subscriptions

To verify that subscribers correctly filter messages based on topic prefixes, you can log the received messages and their topics.

## Advantages of ZeroMQ in PyOrchestrate

ZeroMQ is a high-performance asynchronous messaging library that is well-suited for distributed systems. It provides several advantages in PyOrchestrate:

- **Scalability**: ZeroMQ can handle a large number of connections and messages efficiently.
- **Flexibility**: It supports various messaging patterns, including PubSub, request-reply, and push-pull.
- **Ease of Use**: ZeroMQ's API is simple and easy to integrate with PyOrchestrate agents.

## Resource Links

For further exploration, refer to the following resources:

- [ZeroMQ Official Documentation](https://zeromq.org/documentation/)
- [PyZMQ Documentation](https://pyzmq.readthedocs.io/en/latest/)
- [ZeroMQ Guide](http://zguide.zeromq.org/page:all)