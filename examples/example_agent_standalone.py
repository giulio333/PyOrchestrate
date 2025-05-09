from PyOrchestrate.core.agent import PeriodicProcessAgent


class SimpleCounterAgent(PeriodicProcessAgent):

    class Config(PeriodicProcessAgent.Config):
        # Maximum number to count to
        limit: int = 10
        # Interval between numbers in seconds
        execution_interval: float = 0.5

    config: Config

    def setup(self) -> None:
        """
        Agent initialization: logs the setup information.
        """
        super().setup()

        self.count = 0

    def runner(self) -> None:
        """
        Counts up to the configured maximum number with regular intervals.
        """
        super().runner()

        self.count += 1
        self.logger.info(f"Count: {self.count} of {self.config.limit}")


if __name__ == "__main__":

    agent = SimpleCounterAgent()
    agent.start()

    agent.state_events.start_event.wait()
    print("Agent started.")

    agent.state_events.ready_event.wait()
    print("Agent ready.")

    agent.state_events.close_event.wait()
    print("Agent closed.")
