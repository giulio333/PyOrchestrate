from PyOrchestrate.core.utilities.messaging import (
    MessageChannel,
    ServiceMessage,
    make_request_payload,
)
import datetime
import json

client = MessageChannel("unix_socket_client")
request_payload = make_request_payload("ps")
msg = ServiceMessage(
    sender="test",
    type="COMMAND",
    payload=request_payload,
    timestamp=datetime.datetime.now(),
)

response: ServiceMessage | None = client.send_and_receive(msg, timeout=5)
if response:
    print(response.to_json(indent=2))
