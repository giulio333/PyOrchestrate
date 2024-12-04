from framework.master import MasterProcess
from framework.child import ChildProcess
import time
from dataclasses import dataclass
from datetime import datetime
from logging import DEBUG

from framework.base import BaseConfig
from framework.utilities import LoggerConfig


@dataclass
class LauncherConfig(BaseConfig):
    version: str = "1.0"
    start_time: datetime = datetime.now()
    logger = LoggerConfig(level=DEBUG)


class Launcher(MasterProcess[LauncherConfig]):
    def __init__(self, name: str, config: LauncherConfig, monitor_health=False) -> None:
        super().__init__(name, config, monitor_health)
