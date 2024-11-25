import uuid
from datetime import datetime
from typing import Any, Literal


class PacketHeader:
    def __init__(
        self,
        environment: Literal["DEVELOPMENT", "PRODUCTION", "TEST"] = "DEVELOPMENT",
        source: str | None = None,
        topic: str = "",
    ):
        """
        Inizializza un nuovo PacketHeader.

        Args:
            source (str, optional): Nome del mittente/destinatario del messaggio.
            topic (str, optional): Argomento del messaggio. Default è una stringa vuota.
        """

        # self.packet_id = str(uuid.uuid4())
        self.environment: Literal["DEVELOPMENT", "PRODUCTION", "TEST"] = environment
        self.topic: str = topic
        self.source: str | None = source
        self.route: list[dict] = []

        assert (
            self.topic is not None
        ), "Topic must be defined, use empty string to send/receive to all"

    def __str__(self) -> str:
        """
        Rappresentazione stringa del PacketHeader.

        Returns:
            str: Rappresentazione stringa del PacketHeader.
        """
        return (
            f"PacketHeader(\n"
            f"environment={self.environment},\n"
            f"topic={self.topic},\n"
            f"source={self.source},\n"
            f"route= (through {len(self.route)} nodes) {self.route}\n"
            f")"
        )

    def __repr__(self) -> str:
        return self.__str__()


class PacketBody:
    def __init__(self, data: Any):
        """
        Inizializza un nuovo PacketBody.

        Args:
            data (Any): Dati del messaggio.
        """

        self.data = data

    def __str__(self) -> str:
        """
        Rappresentazione stringa del PacketBody.

        Returns:
            str: Rappresentazione stringa del PacketBody.
        """
        return f"PacketBody(\n" f"data={self.data}\n" f")"

    def __repr__(self) -> str:
        return self.__str__()


class SocketPacket:
    def __init__(
        self,
        body: Any,
        environment: Literal["DEVELOPMENT", "PRODUCTION", "TEST"] = "PRODUCTION",
        topic: str = "",
        source: str = "Start",
        fps: float = 0.0,
    ):
        """
        Inizializza un nuovo SocketPacket.

        Args:
            body (Any): Corpo del messaggio.
            environment (Literal["DEVELOPMENT", "PRODUCTION", "TEST"]): Modalità operativa del messaggio. Default è "PRODUCTION".
            topic (str, optional): Argomento del messaggio. Default è una stringa vuota.
            source (str, optional): Nome del mittente del messaggio. Default è "Start".
            fps (float, optional): Framerate desiderato. Default è 0.0.
        """

        self.header = PacketHeader(topic=topic, environment=environment)
        self.body: Any = body
        self.environment = environment
        self.fps = fps  # TODO: Levare da qui

    def add_to_route(self, source: str):
        """
        Registra la rotta specificata nell'header del `SocketPacket` includendo il timestamp.

        Le rotte sono utilizzate per tracciare il percorso di un messaggio attraverso i processi.

        Note:
            Questo metodo non deve essere chiamato in modalità `PRODUCTION`.

        Args:
            source (str): Nome del mittente/destinatario del messaggio.
        """

        self.header.route.append(
            {
                "source": source,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            }
        )

    def get_packet_lifetime(self) -> float:
        """
        Restituisce il tempo trascorso dalla creazione del messaggio.

        Returns:
            float: Tempo trascorso dal primo invio del messaggio in secondi.
        """

        start_time = datetime.strptime(
            self.header.route[0]["timestamp"], "%Y-%m-%d %H:%M:%S.%f"
        )
        end_time = datetime.strptime(
            self.header.route[-1]["timestamp"], "%Y-%m-%d %H:%M:%S.%f"
        )
        return (end_time - start_time).total_seconds()

    def __str__(self) -> str:
        return (
            f"<SocketPacket:\n" f"header={self.header},\n" f"body={self.body},\n" f">"
        )

    def __repr__(self) -> str:
        return self.__str__()
