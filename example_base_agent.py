from PyOrchestrate.core.orchestrator import Orchestrator
from PyOrchestrate.core.orchestrator import AgentEntry
from PyOrchestrate.core.agent import BaseProcessAgent


class LogMonitorAgent(BaseProcessAgent["LogMonitorAgent.Config"]):
    class Config(BaseProcessAgent.Config):
        log_file: str = "application.log"
        keyword: str = "ERROR"

    def setup(self):
        """
        Ensure the log file exists.
        """
        super().setup()

        self.logger.info(f"Initializing LogMonitorAgent for file: {self.config.log_file}")
        try:
            with open(self.config.log_file, "r") as f:
                self.logger.info("Log file found.")
        except FileNotFoundError:
            self.logger.error(f"Log file {self.config.log_file} does not exist.")
            raise

    def execute(self):
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
        except Exception as e:
            self.logger.error(f"Error reading the log file: {e}")

    def on_stop(self):
        """
        Log the agent's shutdown.
        """
        self.logger.info("LogMonitorAgent stopped.")


if __name__ == "__main__":
    orchestrator = Orchestrator("CoolOrchestrator")

    # register agents
    fw_agent: AgentEntry = orchestrator.register_agent(LogMonitorAgent, "LogMonitorAgent")

    # start all agents
    orchestrator.start()

    # wait for all agents to complete
    orchestrator.join()
