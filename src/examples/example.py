import time
import os, sys
from time import sleep

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.master_example import Launcher, LauncherConfig
from models.periodic_slave_example import Worker, WorkerConfig
from models.threadpool_slave_example import Engine, PrinterConfig

if __name__ == "__main__":

    master = Launcher(config=LauncherConfig())

    master.init_multiple_slave(slave_class=Engine, configs=[PrinterConfig])

    master.run()
