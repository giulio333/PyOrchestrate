from .ServerSocket import ServerSocket
import threading
from queue import Queue, Empty
from logging import Logger

from SocketPacket import SocketPacket


class Sender(threading.Thread):
    """
    Classe wrapper per la gestione di un socket server tcp di tipo publisher-subscriber

    Attributes:
        ip_addr (str): indirizzo ip del server
        port (int): porta del server
        queue (Queue): coda dove prelevare i messaggi da trasmettere
        snd_hwm (int): high level watermark per i messaggi in uscita (dimensione coda tx)

    Methods:
        run: eseguito al lancio della thread, contiene il loop di attesa e invio msg
        close: termina l'esecuzione della thread

    Examples:
    ``` py
    if __name__ == "__main__":
        socket_wrapper = Sender("127.0.0.1", 5556, q, 200)
    ```
    """

    def __init__(
        self,
        ip_addr: str,
        port: int,
        queue: Queue,
        logger: Logger,
        environment: str,
        context,
        snd_hwm=100,
    ):
        """
        Costruttore. Crea un istanza di Sender

        Args:
            ip_addr (str): indirizzo ip del server
            port (int): porta del server
            queue (Queue): coda dove prelevare i messaggi da trasmettere
            snd_hwm (int): optional - high level watermark per i messaggi in uscita (dimensione coda tx)
        """
        super().__init__(name="Sender")

        self.logger = logger

        self.sender = ServerSocket(
            ip_addr=ip_addr,
            port=port,
            logger=self.logger,
            environment=environment,
            snd_hwm=snd_hwm,
            context=context,
        )
        self.q = queue

        self.stop_thread = threading.Event()
        self.start()

    def run(self):
        """
        Metodo interno eseguito all'avvio della thread
        Si blocca sulla coda in attesa di un messaggio e,
        al suo arrivo, lo invia al socket per la trasmissione
        """

        try:

            while not self.stop_thread.is_set():

                try:

                    msg: SocketPacket = self.q.get(timeout=1)

                    self.sender.send_packet(msg)

                except Empty:
                    pass

        except Exception as e:
            self.logger.exception(f"Sender: Error in Main Run: {e}.")
            raise e

        finally:
            self.sender.close()
            self.logger.critical("Sender: Finish.")

    def stop(self):
        """
        Metodo pubblico per chiudere il socket e terminare la thread associata
        """
        self.stop_thread.set()


#########################################
# for testing purpose only. #############
#########################################

if __name__ == "__main__":
    from time import sleep
    from time import time

    lg = Logger("")

    class Message:
        def __init__(self):
            self.topic = 0
            self.id_camera = 1
            self.msg_time = 0.0
            self.msg_counter: int = 0
            self.msg: str = "0123456789" * 10

    msg_counters = [0] * 10

    print(f"\nlibzmq version: {ServerSocket.get_libzmq_version()}")
    print(f"pyzmq version: {ServerSocket.get_pyzmq_version()}\n")

    q = Queue()

    sender = Sender("127.0.0.1", 5556, q, lg, "", 1000)

    while True:
        m = Message()
        m.topic = 1
        m.id_camera = 1
        m.msg_counter = msg_counters[m.id_camera]
        msg_counters[m.id_camera] += 1
        m.msg = "0123456789" * 10
        m.msg_time = time()

        q.put(m)

        sleep(0.0001)

    sender.close()
