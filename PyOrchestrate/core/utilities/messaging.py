import queue
import multiprocessing
from datetime import datetime
from dataclasses import dataclass
from typing import Union, Optional, Literal


@dataclass
class ServiceMessage:
    sender: str
    type: Literal["COMMAND", "STATUS"]
    payload: dict
    timestamp: datetime


class MessageChannel:
    """
    A class that provides a message channel for communication between agents and orchestrators.

    A MessageChannel is a communication channel that can be used to send and receive messages
    between different components of the system. It can be used for both threading and multiprocessing
    scenarios. The channel can be configured to use either a thread-safe queue or a process-safe queue
    depending on the type of communication required.
    """

    def __init__(self, a_type: str):
        if a_type == "thread":
            self._queue = queue.Queue()
        elif a_type == "process":
            self._queue = multiprocessing.Queue()
        else:
            raise ValueError("Invalid a_type. Must be 'thread' or 'process'.")

    def send(self, target: str, msg: ServiceMessage) -> None:
        self._queue.put((target, msg))

    def receive(self, timeout: Optional[float] = None) -> Optional[ServiceMessage]:
        try:
            target, msg = self._queue.get(timeout=timeout)
            return msg
        except queue.Empty:
            return None
