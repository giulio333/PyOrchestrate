Plugins
=======

PyOrchestrate.core.plugins.plugin_manager
-----------------------------------------

.. automodule:: PyOrchestrate.core.plugins.plugin_manager

PyOrchestrate.core.plugins.plugin_protocols
-------------------------------------------

.. automodule:: PyOrchestrate.core.plugins.plugin_protocols

PyOrchestrate.core.plugins.com
------------------------------

.. The concrete plugins implement only initialize(); send, recv, finalize and
   the socket property live on ZeroMQSocketPlugin. Without inherited-members
   autodoc lists each plugin with just its constructor and initialize, which is
   how the reference would silently lose the methods users actually call.

.. automodule:: PyOrchestrate.core.plugins.com
   :inherited-members:

PyOrchestrate.core.plugins.heartbeat
------------------------------------

.. automodule:: PyOrchestrate.core.plugins.heartbeat
