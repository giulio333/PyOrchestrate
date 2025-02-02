import time
import multiprocessing
import zmq

from PyOrchestrate.core.orchestrator import Orchestrator, AgentEntry
from PyOrchestrate.core.plugins.communication_plugins import ZeroMQPubSub
from PyOrchestrate.core.base.periodic_agent import PeriodicProcessAgent

############################################################
# FILE SEND AGENT
############################################################


class FileSendConfig(PeriodicProcessAgent.Config):
    # Path of the file to send
    file_path: str = "file_to_send.dat"
    # Chunk size in bytes
    chunk_size: int = 1024
    # Execution interval in seconds
    execution_interval = 0.2
    # If 'limit' is 0, runs indefinitely (used here to send the file in chunks)
    limit = 0


class FileSendAgent(PeriodicProcessAgent[FileSendConfig]):
    Config = FileSendConfig

    def setup(self) -> None:
        super().setup()
        # Configure the ZeroMQ plugin in PUB mode and bind it to tcp://0.0.0.0:5555
        zmq_plugin = ZeroMQPubSub("tcp://0.0.0.0:5555", zmq.PUB)
        self.plugin_manager.register(zmq_plugin)
        self.logger.info(
            f"Initializing FileSendAgent. File to send: {self.config.file_path}"
        )
        try:
            self.file = open(self.config.file_path, "rb")
        except Exception as e:
            self.logger.error(f"Error opening file: {e}")
            self.file = None
        self.finished = False

    def runner(self) -> None:
        super().runner()
        # If the file is not opened or we have finished reading it, do nothing
        if self.file is None or self.finished:
            return

        # Read a chunk from the file
        chunk = self.file.read(self.config.chunk_size)
        if chunk:
            self.logger.info(f"Sending chunk of {len(chunk)} bytes...")
            self.com.send(chunk)
        else:
            self.logger.info("Sending complete: file finished.")
            # Send a special message to signal the end of transfer
            self.com.send_string("FILE_COMPLETE")
            self.finished = True

    def on_close(self):
        self.logger.warning("FileSendAgent terminated.")
        if self.file and not self.file.closed:
            self.file.close()
        # Optionally send a STOP message
        self.com.send_string("STOP")
        self.plugin_manager.unregister()


############################################################
# FILE RECEIVE AGENT
############################################################


class FileReceiveConfig(PeriodicProcessAgent.Config):
    # Path where to save the received file
    output_file: str = "file_received.dat"
    execution_interval = 0.2
    limit = 0  # run indefinitely


class FileReceiveAgent(PeriodicProcessAgent[FileReceiveConfig]):
    Config = FileReceiveConfig

    def setup(self) -> None:
        super().setup()
        # Configure the ZeroMQ plugin in SUB mode and connect to the publisher
        zmq_plugin = ZeroMQPubSub("tcp://localhost:5555", zmq.SUB)
        self.plugin_manager.register(zmq_plugin)
        # Subscribe to all messages
        self.com.setsockopt(zmq.SUBSCRIBE, b"")
        self.logger.info("FileReceiveAgent initialized, waiting for incoming file...")
        try:
            self.file = open(self.config.output_file, "wb")
        except Exception as e:
            self.logger.error(f"Error opening destination file: {e}")
            self.file = None

    def runner(self) -> None:
        super().runner()
        if self.file is None:
            return

        try:
            message = self.com.recv()
        except zmq.Again:
            message = None

        if message is not None:
            # If the file complete signal is received, close the file and log
            if isinstance(message, bytes) and message == b"FILE_COMPLETE":
                self.logger.info("Received file complete signal.")
                self.file.close()
            # If STOP is received, close the file (optional)
            elif isinstance(message, bytes) and message == b"STOP":
                self.logger.info("Received STOP signal.")
                if not self.file.closed:
                    self.file.close()
            else:
                # Received a data chunk
                if isinstance(message, str):
                    message = message.encode("utf-8")
                self.file.write(message)
                self.file.flush()
                self.logger.info(f"Received and saved a chunk of {len(message)} bytes.")

    def on_close(self):
        self.logger.warning("FileReceiveAgent terminated.")
        if self.file and not self.file.closed:
            self.file.close()
        self.plugin_manager.unregister()


############################################################
# MAIN: REGISTERING AGENTS AND STARTUP
############################################################

if __name__ == "__main__":
    # Required for multiprocessing support
    multiprocessing.set_start_method("spawn")

    # Orchestrator initialization
    orchestrator = Orchestrator()

    # Registering agents
    send_agent: AgentEntry = orchestrator.register_agent(FileSendAgent, "FileSendAgent")
    receive_agent: AgentEntry = orchestrator.register_agent(
        FileReceiveAgent, "FileReceiveAgent"
    )

    # Starting agents
    orchestrator.start()

    # Waiting for agents to terminate
    orchestrator.join()
