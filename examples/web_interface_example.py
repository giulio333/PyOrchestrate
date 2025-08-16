# Example usage of the PyOrchestrate Web Interface

"""
This example shows how to start the web interface server
that provides HTTP access to orchestrator data.
"""

import os
import sys

# Add the parent directory to the path to import PyOrchestrate
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from PyOrchestrate.web_interface.server import WebServerConfig, PyOrchestrateWebServer


def main():
    """Example of running the web interface."""

    # Configuration
    config = WebServerConfig(
        host="127.0.0.1",
        port=8000,
        socket_path="/tmp/pyorchestrate.sock",
        enable_auth=False,  # Set to True in production
        cors_origins=["http://localhost:3000"],
    )

    # Create and run server
    server = PyOrchestrateWebServer(config)

    print("🚀 Starting PyOrchestrate Web Interface...")
    print(f"🌐 Web Interface: http://{config.host}:{config.port}")
    print(f"📚 API Documentation: http://{config.host}:{config.port}/docs")
    print(f"🔌 Socket: {config.socket_path}")
    print("\n📋 Available endpoints:")
    print("  🏠 GET /                               → Root (redirects to status)")
    print("  ❤️  GET /api/health                    → Health check")
    print("  📊 GET /api/orchestrator/status        → Orchestrator status")
    print("  🤖 GET /api/agents                     → List all agents")
    print("  🎯 GET /api/agents/{agent_name}        → Specific agent status")
    print("  🔗 GET /api/orchestrator/dependencies  → Agent dependencies")
    print("  📋 GET /api/orchestrator/report        → Full report")
    print("  📈 GET /api/orchestrator/stats         → Real-time statistics")
    print("  📜 GET /api/history                    → Event history")
    print("  📊 GET /api/history/stats              → History statistics")
    print("\n💡 Tips:")
    print("  • Add ?format=json to any endpoint for raw JSON")
    print("  • Browser access shows formatted HTML interface")
    print("  • Stats page auto-refreshes every 30 seconds")
    print("  • Use API docs for testing: /docs")

    try:
        server.run()
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
