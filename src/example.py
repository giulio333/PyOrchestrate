import time
import os, sys
from time import sleep

from models.master_example import Launcher, LauncherConfig
from models.periodic_slave_example import Worker, WorkerConfig1, WorkerConfig2

if __name__ == "__main__":

    master = Launcher(config=LauncherConfig())

    master.init_multiple_slave(slave_class=Worker, configs=[WorkerConfig1])

    master.run()

    sleep(5)
