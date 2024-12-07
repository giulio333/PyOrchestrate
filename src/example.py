import time
from models.launcher import Launcher, LauncherConfig
from models.video import Worker, WorkerConfig1, WorkerConfig2


if __name__ == "__main__":

    master = Launcher(config=LauncherConfig())

    master.init_multiple_slave(
        slave_class=Worker, configs=[WorkerConfig1(), WorkerConfig2()]
    )

    master.run()
