# ZeroMQReqRep Plugin

## Introduction to Request-Reply Pattern

The **Request-Reply (ReqRep)** pattern is a messaging paradigm where a client (requester) sends a request to a server (replier) and waits for a reply. This pattern is useful for synchronous communication where the client needs a response from the server to proceed.

## Installation Instructions

To use the ZeroMQReqRep plugin, you need to install the `pyzmq` library. You can install it using pip:

```bash
pip install pyzmq
```

## Usage

You can create a **Requester** or **Replier** using the `ZeroMQReqRep` and use them to send and receive messages.

### Requester Example

```python
from PyOrchestrate.core.agent import BaseProcessAgent
from PyOrchestrate.core.plugins import ZeroMQReqRep
import zmq

class RequesterAgent(BaseProcessAgent):

    class Plugin(BaseProcessAgent.Plugin):
        zmq = ZeroMQReqRep("tcp://localhost:5555", zmq.REQ)

    plugin: Plugin

    def execute(self):
        super().execute()
        self.plugin.zmq.send("Hello, Server!".encode())
        reply = self.plugin.zmq.recv()
        self.logger.info(f"Received reply: {reply.decode()}")
```

### Replier Example

```python
from PyOrchestrate.core.agent import PeriodicProcessAgent
from PyOrchestrate.core.plugins import ZeroMQReqRep
import zmq

class ReplierAgent(PeriodicProcessAgent):

    class Plugin(PeriodicProcessAgent.Plugin):
        zmq = ZeroMQReqRep("tcp://localhost:5555", zmq.REP)

    plugin: Plugin

    def runner(self):
        message = self.plugin.zmq.recv()
        self.logger.info(f"Received message: {message.decode()}")
        self.plugin.zmq.send("Hello, Client!".encode())
```

## Error Handling

### Request Timeout

In a request-reply pattern, the requester may not receive a reply if the server is down or unresponsive. To handle this, you can set a timeout for the request and retry if necessary.

### Message Loss Considerations

ZeroMQ does not guarantee message delivery. If a message is lost, the requester may need to retry the request. Implementing a retry mechanism can help ensure reliable communication.

### Ensuring Proper Request-Reply Matching

To verify that requests and replies are correctly matched, you can include unique identifiers in the messages and log the received messages and their identifiers.

## Advantages of ZeroMQ in PyOrchestrate

ZeroMQ is a high-performance asynchronous messaging library that is well-suited for distributed systems. It provides several advantages in PyOrchestrate:

- **Scalability**: ZeroMQ can handle a large number of connections and messages efficiently.
- **Flexibility**: It supports various messaging patterns, including ReqRep, publish-subscribe, and push-pull.
- **Ease of Use**: ZeroMQ's API is simple and easy to integrate with PyOrchestrate agents.

## Resource Links

For further exploration, refer to the following resources:

- [ZeroMQ Official Documentation](https://zeromq.org/documentation/)
- [PyZMQ Documentation](https://pyzmq.readthedocs.io/en/latest/)
- [ZeroMQ Guide](http://zguide.zeromq.org/page:all)
