import time
from models.launcher import Launcher, LauncherConfig
from models.video import Worker1, Worker2, WorkerConfig


if __name__ == "__main__":

    master = Launcher(name="Master", config=LauncherConfig(), monitor_health=False)

    master.init_children(child_class=Worker1, child_config=WorkerConfig())
    master.init_children(child_class=Worker2, child_config=WorkerConfig())

    master.run()

    master.wait_for_children()
