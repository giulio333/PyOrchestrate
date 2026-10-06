import gc

import pytest


@pytest.fixture(autouse=True)
def _collect_reference_cycles():
    """Collect each test's reference cycles before the next test starts.

    An `Orchestrator` and its components reference each other, so they are
    freed only by the cyclic garbage collector, together with the
    multiprocessing semaphores they hold. Left to run whenever it likes, the
    collector can fire while the multiprocessing resource tracker holds its
    lock: the semaphores' finalizers then call back into it and every one of
    them warns "ResourceTracker called reentrantly" (CPython gh-109629).
    Nothing leaks, but a single unlucky collection floods the report.
    """
    yield
    gc.collect()
