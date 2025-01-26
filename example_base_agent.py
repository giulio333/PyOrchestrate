from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.orchestrator import AgentEntry
from PyOrchestrate.core.agent import BaseProcessAgent
from PyOrchestrate.core.plugins.communication_plugins import ZeroMQPlugin
import zmq
import time
import multiprocessing


class MyConfig(BaseProcessAgent.Config):
    log_file: str = "application.log"
    keyword: str = "ERROR"


class LogMonitorAgent(BaseProcessAgent[MyConfig]):

    Config = MyConfig

    def setup(self) -> None:
        """
        Ensure the log file exists.
        """
        super().setup()

        zmqPlugin = ZeroMQPlugin("tcp://localhost:5555", zmq.PUB)
        self.register_plugin(zmqPlugin)

        self.logger.info(
            f"Initializing LogMonitorAgent for file: {self.config.log_file}."
        )

        self.logger.info("Waiting for receiver to connect...")
        time.sleep(1)

        try:
            with open(self.config.log_file, "r") as f:
                self.logger.info("Log file found.")
        except FileNotFoundError:
            self.logger.error(f"Log file {self.config.log_file} does not exist.")

    def execute(self) -> None:
        """
        Monitor the log file for the specified keyword.
        """
        super().execute()

        self.logger.info(f"Monitoring for keyword: '{self.config.keyword}'")
        try:
            with open(self.config.log_file, "r") as f:
                for line in f:
                    if self.config.keyword in line:
                        self.logger.warning(f"Keyword found: {line.strip()}")
                        cm = self.get_plugin("ZeroMQPlugin")
                        cm.send(f"Keyword found: {line.strip()}")  # type: ignore

        except Exception as e:
            self.logger.exception(f"Error reading the log file: {e}")
        finally:
            cm = self.get_plugin("ZeroMQPlugin")
            cm.send("STOP")  # type: ignore
            cm.finalize()

    def on_stop(self):
        """
        Log the agent's shutdown.
        """
        self.logger.info("LogMonitorAgent stopped.")


class LogReceiverAgent(BaseProcessAgent[MyConfig]):
    Config = MyConfig

    def setup(self) -> None:
        """
        Ensure the log file exists.
        """
        super().setup()

        zmqPlugin = ZeroMQPlugin("tcp://localhost:5555", zmq.SUB)
        self.register_plugin(zmqPlugin)

        self.config.logger_config.level = "INFO"

        self.logger.info(
            f"Initializing LogReceiverAgent for file: {self.config.log_file}"
        )

    def execute(self) -> None:
        """
        Monitor the log file for the specified keyword.
        """
        super().execute()

        self.logger.info(f"Monitoring for keyword: '{self.config.keyword}'")
        try:
            cm = self.get_plugin("ZeroMQPlugin")
            while True:
                message = cm.receive()  # type: ignore
                self.logger.success(f"Received message: {message}")

                if message == "STOP":
                    break

        except Exception as e:
            self.logger.exception(f"Error reading the log file: {e}")
        finally:
            cm = self.get_plugin("ZeroMQPlugin")
            cm.finalize()

    def on_stop(self):
        """
        Log the agent's shutdown.
        """
        self.logger.info("LogReceiverAgent stopped.")


if __name__ == "__main__":
    orchestrator = Orchestrator()

    # register agents
    lr_agent: AgentEntry = orchestrator.register_agent(
        LogReceiverAgent, "LogReceiverAgent"
    )
    fw_agent: AgentEntry = orchestrator.register_agent(
        LogMonitorAgent, "LogMonitorAgent"
    )

    # start all agents
    orchestrator.start()

    # wait for all agents to complete
    orchestrator.join()
