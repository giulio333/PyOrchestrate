import time
from models import Launcher, LauncherConfig, Worker1, Worker2, WorkerConfig


if __name__ == "__main__":

    master = Launcher("Master", LauncherConfig(), monitor_health=False)

    master.run()

    master.init_children(Worker1, WorkerConfig())
    master.init_children(Worker2, WorkerConfig())

    master.start_children()

    # time.sleep(2)

    # master.restart_all_children()

    master.wait_for_children()
