"""
Command Handler for PyOrchestrate CLI Interface

This module contains the CommandHandler class which processes external CLI commands
and provides structured responses. This separates command handling logic from the
core Orchestrator functionality.
"""

import json
import time
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyOrchestrate.core.orchestrator.orchestrator import Orchestrator


class CommandHandler:
    """
    Handles external CLI commands for the orchestrator.

    This class processes commands received from the CLI interface and returns
    structured responses. It keeps the command logic separate from the core
    orchestrator functionality.
    """

    def __init__(self, orchestrator: "Orchestrator"):
        """
        Initialize the command handler with an orchestrator reference.

        Args:
            orchestrator: The orchestrator instance to operate on
        """
        self.orchestrator = orchestrator
        self.logger = orchestrator.logger

    def execute_command(self, command: str, args: list) -> dict:
        """Execute external commands and return structured responses."""
        if command in ["ps", "list"]:
            return self._cmd_list_agents()
        elif command == "start" and args:
            return self._cmd_start_agent(args[0])
        elif command == "stop" and args:
            return self._cmd_stop_agent(args[0])
        elif command == "status" and args:
            return self._cmd_agent_status(args[0])
        elif command == "status":
            return self._cmd_orchestrator_status()
        elif command == "report":
            return self._cmd_full_report()
        elif command == "dependencies":
            return self._cmd_show_dependencies()
        elif command == "stats":
            return self._cmd_stats()
        elif command == "history":
            return self._cmd_history(args)
        elif command == "history-stats":
            return self._cmd_history_stats(args)
        elif command == "shutdown":
            return self._cmd_shutdown()
        else:
            return {"status": "error", "message": f"Unknown command: {command}"}

    def _cmd_list_agents(self) -> dict:
        """List all registered agents with their status."""
        try:
            agents_info = []
            for agent in self.orchestrator.memory.agents:
                agents_info.append(
                    {
                        "name": agent.name,
                        "alive": (
                            agent.instance.is_alive()
                            if hasattr(agent, "instance") and agent.instance
                            else False
                        ),
                        "started": agent.name in self.orchestrator._started_agents,
                        "in_queue": agent.name
                        in self.orchestrator._waiting_agents_queue,
                    }
                )
            return {
                "status": "success",
                "data": {
                    "agents": agents_info,
                    "running_count": self.orchestrator._running_agents,
                    "max_workers": self.orchestrator.config.max_workers,
                    "waiting_count": len(self.orchestrator._waiting_agents_queue),
                },
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to list agents: {str(e)}",
            }

    def _cmd_start_agent(self, agent_name: str) -> dict:
        """Start a specific agent."""
        try:
            if agent_name in self.orchestrator._started_agents:
                return {
                    "status": "error",
                    "message": f"Agent {agent_name} is already started",
                }

            if agent_name not in [
                agent.name for agent in self.orchestrator.memory.agents
            ]:
                return {
                    "status": "error",
                    "message": f"Agent {agent_name} is not registered",
                }

            # Start the agent using existing logic
            self.orchestrator._start_agent_callback(agent_name)
            return {
                "status": "success",
                "message": f"Agent {agent_name} start initiated",
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to start agent {agent_name}: {str(e)}",
            }

    def _cmd_stop_agent(self, agent_name: str) -> dict:
        """Stop a specific agent."""
        try:
            agent = self.orchestrator.memory.get_agent(agent_name)
            if not agent:
                return {"status": "error", "message": f"Agent {agent_name} not found"}

            agent.stop()
            if agent_name in self.orchestrator._started_agents:
                self.orchestrator._started_agents.remove(agent_name)
                self.orchestrator._running_agents -= 1

            return {"status": "success", "message": f"Agent {agent_name} stopped"}

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to stop agent {agent_name}: {str(e)}",
            }

    def _cmd_agent_status(self, agent_name: str) -> dict:
        """Get detailed status of a specific agent."""
        try:
            agent = self.orchestrator.memory.get_agent(agent_name)
            if not agent:
                return {"status": "error", "message": f"Agent {agent_name} not found"}

            return {
                "status": "success",
                "data": {
                    "name": agent.name,
                    "alive": (
                        agent.instance.is_alive()
                        if hasattr(agent, "instance") and agent.instance
                        else False
                    ),
                    "started": agent.name in self.orchestrator._started_agents,
                    "in_queue": agent.name in self.orchestrator._waiting_agents_queue,
                    "dependencies": self.orchestrator.dependencies.get(agent.name, []),
                },
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get status for {agent_name}: {str(e)}",
            }

    def _cmd_orchestrator_status(self) -> dict:
        """Get overall orchestrator status."""
        try:
            return {
                "status": "success",
                "data": {
                    "total_agents": len(self.orchestrator.memory.agents),
                    "running_agents": self.orchestrator._running_agents,
                    "max_workers": self.orchestrator.config.max_workers,
                    "waiting_agents": len(self.orchestrator._waiting_agents_queue),
                    "command_interface_enabled": self.orchestrator.config.enable_command_interface,
                    "command_socket_path": (
                        self.orchestrator.config.command_socket_path
                        if self.orchestrator.config.enable_command_interface
                        else None
                    ),
                },
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get orchestrator status: {str(e)}",
            }

    def _cmd_full_report(self) -> dict:
        """Get full orchestrator report."""
        try:
            agents_info = []
            for agent in self.orchestrator.memory.agents:
                agents_info.append(
                    {
                        "name": agent.name,
                        "alive": (
                            agent.instance.is_alive()
                            if hasattr(agent, "instance") and agent.instance
                            else False
                        ),
                        "started": agent.name in self.orchestrator._started_agents,
                        "in_queue": agent.name
                        in self.orchestrator._waiting_agents_queue,
                        "dependencies": self.orchestrator.dependencies.get(
                            agent.name, []
                        ),
                    }
                )

            return {
                "status": "success",
                "data": {
                    "orchestrator": {
                        "running_agents": self.orchestrator._running_agents,
                        "max_workers": self.orchestrator.config.max_workers,
                        "waiting_agents": len(self.orchestrator._waiting_agents_queue),
                        "check_interval": self.orchestrator.config.check_interval,
                    },
                    "agents": agents_info,
                    "dependencies": dict(self.orchestrator.dependencies),
                },
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate full report: {str(e)}",
            }

    def _cmd_show_dependencies(self) -> dict:
        """Show agent dependencies."""
        try:
            return {
                "status": "success",
                "data": {"dependencies": dict(self.orchestrator.dependencies)},
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to show dependencies: {str(e)}",
            }

    def _cmd_stats(self) -> dict:
        """Get real-time statistics of all agents."""
        try:
            agents_stats = []
            for agent in self.orchestrator.memory.agents:
                # Get basic agent info
                agent_stat = {
                    "name": agent.name,
                    "alive": (
                        agent.instance.is_alive()
                        if hasattr(agent, "instance") and agent.instance
                        else False
                    ),
                    "started": agent.name in self.orchestrator._started_agents,
                    "in_queue": agent.name in self.orchestrator._waiting_agents_queue,
                    "pid": (
                        agent.instance.pid
                        if hasattr(agent, "instance")
                        and agent.instance
                        and hasattr(agent.instance, "pid")
                        else None
                    ),
                    "uptime": self._get_agent_uptime(agent),
                }

                # Add process-specific stats if available
                if (
                    hasattr(agent, "instance")
                    and agent.instance
                    and hasattr(agent.instance, "pid")
                ):
                    try:
                        import psutil

                        process = psutil.Process(agent.instance.pid)
                        agent_stat.update(
                            {
                                "cpu_percent": process.cpu_percent(),
                                "memory_mb": round(
                                    process.memory_info().rss / 1024 / 1024, 2
                                ),
                                "memory_percent": process.memory_percent(),
                                "threads": process.num_threads(),
                            }
                        )
                    except (ImportError, psutil.NoSuchProcess, psutil.AccessDenied):
                        # If psutil is not available or process not accessible
                        agent_stat.update(
                            {
                                "cpu_percent": "N/A",
                                "memory_mb": "N/A",
                                "memory_percent": "N/A",
                                "threads": "N/A",
                            }
                        )
                else:
                    agent_stat.update(
                        {
                            "cpu_percent": "N/A",
                            "memory_mb": "N/A",
                            "memory_percent": "N/A",
                            "threads": "N/A",
                        }
                    )

                agents_stats.append(agent_stat)

            return {
                "status": "success",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "orchestrator": {
                        "running_agents": self.orchestrator._running_agents,
                        "max_workers": self.orchestrator.config.max_workers,
                        "waiting_agents": len(self.orchestrator._waiting_agents_queue),
                    },
                    "agents": agents_stats,
                },
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get statistics: {str(e)}",
            }

    def _get_agent_uptime(self, agent) -> str:
        """Calculate agent uptime if possible."""
        try:
            if (
                hasattr(agent, "instance")
                and agent.instance
                and hasattr(agent.instance, "pid")
            ):
                import psutil

                process = psutil.Process(agent.instance.pid)
                create_time = process.create_time()
                uptime_seconds = time.time() - create_time

                hours = int(uptime_seconds // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                seconds = int(uptime_seconds % 60)

                if hours > 0:
                    return f"{hours}h {minutes}m {seconds}s"
                elif minutes > 0:
                    return f"{minutes}m {seconds}s"
                else:
                    return f"{seconds}s"
            else:
                return "N/A"
        except (ImportError, Exception):
            return "N/A"

    def _cmd_shutdown(self) -> dict:
        """Shutdown the orchestrator gracefully."""
        try:
            self.logger.info("Shutdown command received via CLI")

            # Signal the orchestrator to shutdown
            self.orchestrator._shutdown_requested = True

            return {"status": "success", "message": "Orchestrator shutdown initiated"}
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to shutdown orchestrator: {str(e)}",
            }

    def _cmd_history(self, args: list) -> dict:
        """Get event history with optional filtering."""
        try:
            # Parse arguments (expecting a dict-like structure or individual params)
            if args and isinstance(args[0], str):
                try:
                    # Try to parse as JSON
                    params = json.loads(args[0])
                except (json.JSONDecodeError, ValueError):
                    # Fall back to simple parameter parsing
                    params = {}
            elif args and isinstance(args[0], dict):
                params = args[0]
            else:
                params = {}

            # Extract parameters with defaults
            last = int(params.get("last", 100))
            agent = params.get("agent")
            event_type = params.get("type")
            after_seq = (
                int(params.get("after_seq", 0)) if params.get("after_seq") else None
            )

            # Get events from the event store
            events = self.orchestrator.event_store.last(
                n=last,
                agent=agent,
                type=event_type,
                after_seq=after_seq,
            )

            # Convert EventRecord namedtuples to dictionaries for JSON serialization
            events_data = []
            for event in events:
                event_dict = event._asdict()
                # Convert timestamp to ISO format for better readability
                event_dict["timestamp"] = datetime.fromtimestamp(
                    event.t_wall
                ).isoformat()
                events_data.append(event_dict)

            return {
                "status": "success",
                "data": {
                    "events": events_data,
                    "count": len(events_data),
                    "filters": {
                        "last": last,
                        "agent": agent,
                        "type": event_type,
                        "after_seq": after_seq,
                    },
                    "capacity_info": self.orchestrator.event_store.get_capacity_info(),
                },
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get event history: {str(e)}",
            }

    def _cmd_history_stats(self, args: list) -> dict:
        """Get aggregated event statistics."""
        try:
            # Parse arguments
            if args and isinstance(args[0], str):
                try:
                    params = json.loads(args[0])
                except (json.JSONDecodeError, ValueError):
                    params = {}
            elif args and isinstance(args[0], dict):
                params = args[0]
            else:
                params = {}

            agent = params.get("agent")

            # Get statistics from the event store
            stats = self.orchestrator.event_store.stats(agent=agent)
            capacity_info = self.orchestrator.event_store.get_capacity_info()

            return {
                "status": "success",
                "data": {
                    "statistics": stats,
                    "capacity_info": capacity_info,
                    "agent_filter": agent,
                    "timestamp": datetime.now().isoformat(),
                },
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get event statistics: {str(e)}",
            }
