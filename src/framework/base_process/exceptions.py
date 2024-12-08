class TerminateProcess(Exception):
    """Exception raised to signal the termination of a process with an optional reason.

    This custom exception can be used to gracefully terminate processes or threads,
    providing a clear message indicating the reason for termination.
    """

    def __init__(self, reason: str = "") -> None:
        """Initialize the TerminateProcess exception.

        Args:
            reason (str, optional): The reason for terminating the process.
                Defaults to an empty string, indicating no specific reason.
        """

        self.reason = reason

        if reason:
            message = f"TerminateProcess request: Reason = '{reason}'."
        else:
            message = "TerminateProcess request: No reason provided."

        super().__init__(message)

    def __str__(self) -> str:
        """Return the string representation of the exception.

        Returns:
            str: The exception message.
        """
        return self.args[0]
