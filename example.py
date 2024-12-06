import time
from models.launcher import Launcher, LauncherConfig
from models.video import Worker, WorkerConfig1, WorkerConfig2


if __name__ == "__main__":

    master = Launcher(config=LauncherConfig(), monitor_health=True)

    master.init_multiple_children(
        child_class=Worker, configs=[WorkerConfig1(), WorkerConfig2()]
    )

    master.run()
