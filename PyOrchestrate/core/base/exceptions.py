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


class RecoverableException(Exception):
    """Exception raised to signal a recoverable error in an Agent.

    This custom exception can be used to signal that an error occurred during the execution
    of an Agent, but that the Agent can be recovered and resumed.
    """

    def __init__(self, message: str) -> None:
        """Initialize the RecoverableException exception.

        Args:
            message (str): The message to be displayed when the exception is raised.
        """
        super().__init__(message)


class NonRecoverableException(Exception):
    """Exception raised to signal a non-recoverable error in an Agent.

    This custom exception can be used to signal that an error occurred during the execution
    of an Agent, and that the Agent cannot be recovered and should be stopped.
    """

    def __init__(self, message: str) -> None:
        """Initialize the NonRecoverableException exception.

        Args:
            message (str): The message to be displayed when the exception is raised.
        """
        super().__init__(message)
