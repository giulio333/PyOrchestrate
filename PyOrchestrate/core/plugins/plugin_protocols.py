"""
Plugin protocols module.

This module defines the core protocols (interfaces) for the plugin system in PyOrchestrate.
Plugin protocols provide a standardized way to define and implement plugins, ensuring
consistency and interoperability across the entire framework.

The module implements two main protocols:

- Plugin: The base protocol that all plugins must implement, defining the basic
  lifecycle methods (initialize, execute, finalize).
  
- CommunicationPlugin: A specialized protocol for plugins that handle communication,
  extending the base Plugin protocol with additional messaging capabilities.

These protocols serve as contracts that plugin implementations must fulfill, making
the plugin system both extensible and maintainable. By following these protocols,
developers can create new plugins that seamlessly integrate with the PyOrchestrate
framework.

Example:
    To create a new plugin, implement either the Plugin or CommunicationPlugin
    protocol based on your needs:

    class MyPlugin(Plugin):
        def initialize(self):
            # Setup code
            pass
"""

from typing import Protocol


class Plugin(Protocol):
    """
    Protocol for all plugins.

    This protocol provides a common interface for plugin lifecycle management, defining
    the essential methods that a plugin must implement.

    Methods:
        initialize: Initializes the plugin and sets up necessary resources.
        execute: Executes the main logic of the plugin.
        finalize: Finalizes the plugin, cleaning up resources.
    """

    def initialize(self):
        """
        Initializes the plugin.

        Called once when the plugin is registered.
        Perform all necessary setup operations here.
        """
        pass

    def execute(self):
        """
        Executes the main logic of the plugin.

        Called during the plugin's execution cycle.
        This method should contain the primary functionality of the plugin.
        """
        pass

    def finalize(self):
        """
        Finalizes the plugin.

        Called when the plugin is unregistered.
        Perform cleanup operations, such as closing connections and releasing resources.
        """
        pass


class CommunicationPlugin(Plugin):
    """
    Protocol for communication plugins.

    This protocol extends the base Plugin protocol by adding methods for sending and
    receiving messages, similar to those provided by PyZMQ. It is designed to facilitate
    flexible and effective communication between components.

    Methods:
        send_string: Sends a message encoded as a UTF-8 string.
        recv_string: Receives a message and decodes it as a UTF-8 string.
        recv: Receives a message, optionally using flags as defined in PyZMQ.
        send: Sends a message (typically in bytes or serialized format).
        setsockopt: Sets a socket option, as defined by PyZMQ.
    """

    def send_string(self, message):
        """
        Sends a message as a string.

        Converts the message to a UTF-8 encoded string and sends it through the socket.
        Useful for transmitting textual data.

        Parameters:
            message: The message to be sent (str).
        """
        pass

    def recv_string(self):
        """
        Receives a message and decodes it as a string.

        Waits for a message, decodes it using UTF-8 encoding, and returns the resulting string.

        Returns:
            The received message as a string.
        """
        pass

    def recv(self, flags: int = 0):
        """
        Receives a message from the socket.

        Uses PyZMQ's receive method, allowing the use of flags to customize the behavior
        (e.g., non-blocking reception). Refer to the PyZMQ documentation for details on flags.

        Parameters:
            flags (int): Optional flags for the receive operation (default: 0).

        Returns:
            The received message, typically in bytes.
        """
        pass

    def send(self, message):
        """
        Sends a message through the socket.

        The message can be already in bytes or serialized as bytes.
        This method wraps the sending functionality provided by PyZMQ.

        Parameters:
            message: The message to be sent (typically bytes or serialized into bytes).
        """
        pass

    def setsockopt(self, option, value):
        """
        Sets a socket option.

        Allows configuration of the socket by setting specific options as defined by the PyZMQ library.
        For more details on available options, refer to the PyZMQ documentation
        at this link: https://pyzmq.readthedocs.io/en/latest/api/zmq.html#zmq.Socket.setsockopt

        Parameters:
            option: The socket option to set (e.g., zmq.SUBSCRIBE).
            value: The value to assign to the option.
        """
        pass
