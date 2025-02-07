"""
plugin_protocols module.
This module defines the interfaces (protocols) that plugins must implement to be integrated
with the PyOrchestrate framework. The interfaces provide a standardized structure for:
- Plugin initialization (setup).
- Execution of the main plugin logic.
- Finalization (cleanup) after use.

The protocols defined in this module ensure that every plugin adheres to a common contract,
thus promoting consistency and interoperability within the system.
"""

from typing import Protocol


class Plugin(Protocol):
    """
    Base protocol for all plugins.

    This protocol defines the essential methods required for managing a plugin's lifecycle:
    - initialize: Prepares the plugin by allocating resources or setting up the initial state.
    - execute: Executes the main logic of the plugin.
    - finalize: Handles cleanup and resource release.

    Developers must implement these methods to ensure proper integration with the system.
    """

    def initialize(self):
        """
        Initializes the plugin.

        Called only once at the time of plugin registration.
        Use this method to set up the necessary resources for subsequent execution.
        """
        pass

    def execute(self):
        """
        Executes the main logic of the plugin.

        This method is called during the plugin's operational cycle and should contain
        the core functionality required from the plugin.
        """
        pass

    def finalize(self):
        """
        Finalizes the plugin.

        Called at the end of the plugin lifecycle to release resources, close connections,
        or perform any other cleanup operations.
        """
        pass


class CommunicationPlugin(Plugin):
    """
    Extended protocol for communication plugins.

    This protocol, which extends Plugin, adds specific methods for sending and receiving
    messages (e.g., via sockets or PyZMQ). It is designed to standardize communication
    operations among system components.

    Additional methods:
        - send_string: Sends messages as UTF-8 strings.
        - recv_string: Receives and decodes messages as strings.
        - recv: Receives messages with customizable options (e.g., non-blocking mode).
        - send: Sends messages in bytes or serialized format.
        - setsockopt: Configures socket options.
    """

    def send_string(self, message):
        """
        Sends a message as a string.

        Converts the message to a UTF-8 encoded string and sends it through the communication channel.

        Args:
            message (str): The message to be sent.
        """
        pass

    def recv_string(self):
        """
        Receives a message and decodes it as a string.

        Waits for a message, decodes it using UTF-8, and returns the resulting string.

        Returns:
            str: The received message.
        """
        pass

    def recv(self, flags: int = 0):
        """
        Receives a message from the communication channel.

        Uses the reception mechanism (e.g., provided by PyZMQ) to obtain the message,
        applying any flags to modify the behavior (for example, non-blocking mode).

        Args:
            flags (int, optional): Flags to customize the reception behavior (default: 0).

        Returns:
            Typically returns the received message in bytes.
        """
        pass

    def send(self, message):
        """
        Sends a message through the communication channel.

        The message can be in bytes or already serialized into bytes.

        Args:
            message: The message to send (usually bytes or a serialized object).
        """
        pass

    def setsockopt(self, option, value):
        """
        Configures a socket option.

        Sets a specific option for the socket, useful for customized configurations.
        Refer to the PyZMQ documentation for more details on available options.

        Args:
            option: The option to configure (e.g., zmq.SUBSCRIBE).
            value: The value to assign to the option.
        """
        pass
