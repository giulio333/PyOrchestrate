from framework.master import MasterProcess
from framework.child import ChildProcess
import time
from dataclasses import dataclass
from datetime import datetime

from framework.base import BaseConfig


@dataclass
class LauncherConfig(BaseConfig):
    version: str = "1.0"
    start_time: datetime = datetime.now()


class Launcher(MasterProcess[LauncherConfig]):
    def __init__(self, name: str, config: LauncherConfig, monitor_health=False) -> None:
        """
        Inizializza un'istanza di Launcher.

        Args:
        name (str): Nome del processo.
        config (LauncherConfig): Configurazioni del processo.
        """
        super().__init__(name, config, monitor_health)
