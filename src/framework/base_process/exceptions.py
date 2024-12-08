class TerminateProcess(Exception):
    def __init__(self, reason: str = "") -> None:
        self.reason = reason
        message = f"TerminateProcess request\n request = {reason}"
        super().__init__(message)

    def __str__(self):
        return self.args[0]
