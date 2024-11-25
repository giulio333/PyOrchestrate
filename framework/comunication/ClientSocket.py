"""
Questo modulo gestisce la comunicazione tramite socket TCP utilizzando il pattern **publisher-subscriber**.

La classe `ClientSocket` è responsabile di inizializzare e gestire un socket client, sottoscriversi a specifici topics, inviare e ricevere messaggi, e gestire eventuali errori di comunicazione.

Utilizzo
--------

- Creare un contesto `zmq.Context` per ogni processo.
- Creare un'istanza della classe `ClientSocket` con gli endpoint e i topics desiderati, passando il contesto ZeroMQ e un oggetto `Logger`.
- Utilizzare i metodi `send_packet` e `receive_packet` per inviare e ricevere messaggi.
- Usare il metodo `close` per chiude il socket.
- Chiudere il contesto ZeroMQ alla fine del processo `context.term()`.

Eccezioni
---------

- `DuplicateTopic`: Sollevata quando la lista dei topics contiene duplicati.
- `ValueError`: Sollevata quando la lista dei topics è vuota o contiene elementi non stringa.
- `ValueError`: Sollevata quando la lista degli endpoints è vuota.
- `zmq.ZMQError`: Sollevata quando si verifica un errore ZeroMQ durante la ricezione del messaggio.
- `pickle.UnpicklingError`: Sollevata quando si verifica un errore durante la deserializzazione.

Example
-------

```python
from zmq import Context
if __name__ == "__main__":
    context = Context()
    endpoints = [("127.0.0.1", 5555)]
    topics = ["topic1", "topic2"]
    client = ClientSocket(endpoints, topics, logger, "test", context)

        client.send_packet("topic1", "Hello, World!")
    message = client.receive_packet()
    client.close()
```
"""

import zmq
import threading
import pickle
from time import time
from typing import Literal, Any
from logging import Logger
from warnings import warn

from .SocketPacket import SocketPacket


class ClientSocket:
    """
    Classe per la gestione di un socket client TCP utilizzando il pattern publisher-subscriber.

    Attributes:
        endpoints (list[tuple[str, int]]): Lista di tuple con indirizzo IP e porta.
        topics (list[str]): Codici di sottoscrizione. Una stringa vuota sottoscrive a tutti i topics.
        rcv_hwm (int): Watermark di alto livello per i messaggi in arrivo (dimensione della coda).
        conflate (bool): Se True, il socket manterrà solo l'ultimo messaggio ricevuto.
        logger (Logger): Oggetto Logger per la gestione dei messaggi di log.
        debug (bool): Se True, i messaggi di debug saranno registrati.
        context (zmq.Context): Contesto ZeroMQ.
        socket (zmq.Socket): Socket ZeroMQ.
        environment (str): Modalità operativa del socket, es. `production`.

    Methods:
        receive_packet(): Si blocca in attesa di un messaggio e restituisce un oggetto `SocketPacket`.
        close(): Chiude il socket.
        get_libzmq_version(): Metodo di classe che restituisce la versione di `libzmq`.
        get_pyzmq_version(): Metodo di classe che restituisce la versione di `pyzmq`.
    """

    def __init__(
        self,
        endpoints: list[tuple[str, int]],
        topics: list[str],
        logger: Logger,
        context: zmq.Context,
        environment: Literal["PRODUCTION", "DEVELOPMENT", "TEST"] = "PRODUCTION",
        rcv_hwm: int = 100,
        conflate: bool = False,
        debug: bool = True,
    ) -> None:
        """
        Inizializza un socket client TCP usando il pattern publisher-subscriber.

        Args:
            endpoints (list[tuple[str, int]]): Lista di tuple con indirizzo IP e porta.
            topics (list[str]): Codici di sottoscrizione. Una stringa vuota sottoscrive a tutti i topics.
            logger (Logger): Oggetto Logger per la gestione dei messaggi di log.
            context (zmq.Context): Contesto ZeroMQ.
            environment (Literal["PRODUCTION", "DEVELOPMENT", "TEST"], optional): Modalità operativa del socket.
            rcv_hwm (int, optional): Watermark di alto livello per i messaggi in arrivo.
            conflate (bool, optional): Se True, mantiene solo l'ultimo messaggio nella coda.
            debug (bool, optional): Se True, i messaggi di debug saranno registrati.

        Raises:
            ValueError: Se la lista dei topics è vuota o contiene elementi non stringa.
            DuplicateTopic: Se nella lista sono presenti topics duplicati.
            ValueError: Se la lista degli endpoints è vuota.

        Examples:
            ```python
            from zmq import Context

            # create a context for one process
            context = Context()

            client = ClientSocket([("127.0.0.1", 5555)], ["topic1", "topic2"], logger, "TEST", context)

            client.send_packet("topic1", "Hello, World!")
            message = client.receive_packet()
            client.close()
            ```
        """

        assert context is not None, "Context is required."

        if not topics:
            raise ValueError("Topic list is empty.")

        if not all(isinstance(topic, str) for topic in topics):
            raise ValueError("All topics must be strings.")

        if len(set(topics)) != len(topics):
            raise ValueError("Duplicate topics found.")

        if not endpoints:
            raise ValueError("Endpoints list is empty.")

        self.logger: Logger = logger
        self.debug: bool = debug
        self.environment: str = environment
        self.endpoints: list[tuple[str, int]] = endpoints
        self.topics: list[str] = topics
        self.rcv_hwm: int = rcv_hwm
        self.conflate: bool = conflate
        self.context: zmq.Context = context
        self.socket: zmq.Socket = self.context.socket(zmq.SUB)

        self.init_client_socket()

    @classmethod
    def get_libzmq_version(cls) -> str:
        """Returns the version of `libzmq`."""
        return zmq.zmq_version()

    @classmethod
    def get_pyzmq_version(cls) -> str:
        """Returns the version of `pyzmq`."""
        return zmq.__version__

    def init_client_socket(self) -> None:
        """
        Inizializza il socket client, imposta HWM, si connette ai server e si sottoscrive ai topics.
        """

        self.log("Initializing client socket instance.")

        if self.conflate:
            self.socket.setsockopt(zmq.CONFLATE, 1)

        self.socket.setsockopt(zmq.RCVHWM, self.rcv_hwm)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.setsockopt(zmq.RCVTIMEO, 1000)  # timeout di ricezione di 1 secondo

        for ip_addr, port in self.endpoints:
            endpoint = f"tcp://{ip_addr}:{port}"
            self.log(f"Connecting to {endpoint}")
            self.socket.connect(endpoint)

        for topic in self.topics:
            self.log(f"Subscribing to topic: {topic}")
            self.socket.setsockopt_string(zmq.SUBSCRIBE, topic)

        self.log(f"HWM set to {self.socket.getsockopt(zmq.RCVHWM)}")
        self.log("Client socket initialized and ready to receive messages.")

    def receive_packet(self) -> SocketPacket:
        """
        Si blocca finché non viene ricevuto un messaggio e restituisce l'oggetto `SocketPacket` deserializzato.

        Returns:
            SocketPacket: Il pacchetto deserializzato ricevuto dal socket.

        Raises:
            zmq.ZMQError: Se si verifica un errore ZeroMQ durante la ricezione del messaggio.
            pickle.UnpicklingError: Se si verifica un errore durante la deserializzazione.
            zmq.error.Again: Se il socket è in attesa di un messaggio e il timeout scade.
        """

        try:

            msg = self.socket.recv()

            topic, data = msg.split(b" ", 1)

            obj: SocketPacket = pickle.loads(data)

            if self.environment != "PRODUCTION":
                obj.add_to_route(source="receiver")

            return obj

        except zmq.error.Again as e:
            # self.logger.warning(f"Timeout receiving packet: {e}")
            raise e

        except (zmq.ZMQError, pickle.UnpicklingError) as e:
            self.logger.exception(f"Error receiving packet: {e}")
            raise e

    def close(self) -> None:
        """Chiude il socket."""

        self.socket.close()
        self.log("Client socket closed.")

    def log(self, msg: str) -> None:
        """Registra un messaggio se il debug è abilitato."""

        if self.debug:
            self.logger.debug("Receiver: " + msg)
