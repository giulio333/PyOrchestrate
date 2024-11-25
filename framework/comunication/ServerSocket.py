import zmq
import pickle
from typing import Any
from time import sleep
from logging import Logger

from .SocketPacket import SocketPacket


class ServerSocket:
    """
    Classe per la gestione di un socket server TCP utilizzando il pattern publisher-subscriber.

    Attributes:
        ip_addr (str): Indirizzo IP del server.
        port (int): Porta del server.
        snd_hwm (int): Watermark di alto livello per i messaggi in uscita (dimensione della coda).
        logger (Logger): Oggetto Logger per la gestione dei messaggi di log.
        debug (bool): Se True, i messaggi di debug saranno registrati.
        context (zmq.Context): Contesto ZeroMQ.
        socket (zmq.Socket): Socket ZeroMQ.
        environment (str): Modalità operativa del socket, es. "PRODUCTION".

    Methods:
        send_packet(obj: SocketPacket): Invia un oggetto `SocketPacket` serializzato ai sottoscrittori.
        close(): Chiude il socket.
        get_libzmq_version(): Metodo di classe che restituisce la versione di libzmq.
        get_pyzmq_version(): Metodo di classe che restituisce la versione di pyzmq.
    """

    @classmethod
    def get_libzmq_version(cls) -> str:
        """Restituisce la versione di libzmq."""
        return zmq.zmq_version()

    @classmethod
    def get_pyzmq_version(cls) -> str:
        """Restituisce la versione di pyzmq."""
        return zmq.__version__

    def __init__(
        self,
        ip_addr: str,
        port: int,
        logger: Logger,
        environment: str,
        context: zmq.Context,
        snd_hwm: int = 100,
        debug: bool = True,
    ) -> None:
        """
        Inizializza un socket server TCP utilizzando il pattern publisher-subscriber.

        Args:
            ip_addr (str): Indirizzo IP del server.
            port (int): Porta del server.
            logger (Logger): Oggetto Logger per la gestione dei messaggi di log.
            environment (str): Modalità operativa del socket, es. "PRODUCTION".
            context (zmq.Context): Contesto ZeroMQ.
            snd_hwm (int, opzionale): Watermark di alto livello per i messaggi in uscita. Valore predefinito: 100.
            debug (bool, opzionale): Se True, i messaggi di debug saranno registrati. Valore predefinito: True.
        """
        self.ip_addr: str = ip_addr
        self.port: int = port
        self.snd_hwm: int = snd_hwm
        self.logger: Logger = logger
        self.debug: bool = debug
        self.environment: str = environment
        self.context: zmq.Context = context
        self.socket: zmq.Socket = self.context.socket(zmq.PUB)

        self._init_server_socket()

    def _init_server_socket(self) -> None:
        """Inizializza il socket server, imposta HWM e si associa all'indirizzo."""
        self.socket.setsockopt(zmq.SNDHWM, self.snd_hwm)
        self.socket.setsockopt(zmq.LINGER, 0)
        endpoint = f"tcp://{self.ip_addr}:{self.port}"
        self.socket.bind(endpoint)
        self.log(
            f"Publisher bound to {endpoint}, HWM={self.socket.getsockopt(zmq.SNDHWM)}"
        )

    def send_packet(self, obj: SocketPacket) -> None:
        """
        Invia un oggetto `SocketPacket` serializzato ai sottoscrittori.

        Args:
            obj (SocketPacket): Oggetto pacchetto da inviare.

        Raises:
            zmq.ZMQError: Se si verifica un errore ZeroMQ durante l'invio.
            pickle.PicklingError: Se si verifica un errore durante la serializzazione.
        """
        try:

            topic: str = obj.header.topic

            if self.environment != "PRODUCTION":
                obj.add_to_route(source="sender")

            to_send = pickle.dumps(obj)
            msg = f"{topic} ".encode("utf-8") + to_send

            self.socket.send(msg, flags=zmq.NOBLOCK)

        except (pickle.PicklingError, zmq.ZMQError) as e:
            self.logger.exception(f"Error sending packet: {e}")
            raise e

    def close(self) -> None:
        """Chiude il socket."""
        self.socket.close()
        self.log("Server socket closed.")

    def log(self, msg: str) -> None:
        """Registra un messaggio se il debug è abilitato."""
        if self.debug:
            self.logger.debug("Sender: " + msg)
