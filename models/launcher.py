from framework.master import MasterProcess
from framework.child import ChildProcess
import time
from dataclasses import dataclass
from datetime import datetime
from logging import DEBUG

from framework.master import MasterConfig
from framework.utilities import LoggerConfig


@dataclass
class LauncherConfig(MasterConfig):
    version: str = "1.0"
    start_time: datetime = datetime.now()
    logger = LoggerConfig(level=DEBUG)

    wait_mode = "none"


class Launcher(MasterProcess[LauncherConfig]):
    def __init__(self, config: LauncherConfig, monitor_health=False) -> None:
        super().__init__(config, monitor_health)
