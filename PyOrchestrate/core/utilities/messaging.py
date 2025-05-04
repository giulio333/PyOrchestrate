import queue
import multiprocessing
from datetime import datetime
from dataclasses import dataclass
from typing import Union, Optional


@dataclass
class ServiceMessage:
    sender: str
    type: str  # e.g., "ERROR", "COMMAND", "STATUS"
    payload: dict
    timestamp: datetime


class MessageChannel:
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
