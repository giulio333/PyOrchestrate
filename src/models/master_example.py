from dataclasses import dataclass
from datetime import datetime
from logging import DEBUG

from framework.master import (
    MasterProcess,
    MasterConfig,
    LoggerConfig,
    HealthCheckConfig,
)


@dataclass
class LauncherConfig(MasterConfig):
    version: str = "1.0"
    start_time: datetime = datetime.now()

    logger = LoggerConfig(level="DEBUG")
    wait_mode = "none"
    health_check = HealthCheckConfig(enabled=True, check_interval=50)


class Launcher(MasterProcess[LauncherConfig]):
    def __init__(self, config: LauncherConfig) -> None:
        super().__init__(config)
