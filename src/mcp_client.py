import subprocess
import json
from pathlib import Path


class MCPClient:
    """
    Model Context Protocol client.
    
    Manages communication with MCP servers via subprocess and JSON-RPC
    over stdin/stdout. Handles server lifecycle and tool invocation.
    """

    def __init__(self, server_script):
        """Initialize MCP client for specified server script."""
        self.server_path = Path(__file__).parent.parent / "mcp_servers" / server_script
        self.process = None
        self.request_id = 0

    def start(self):
        """Start the MCP server subprocess."""
        self.process = subprocess.Popen(
            ["python3", str(self.server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

    def stop(self):
        """Terminate the MCP server subprocess."""
        if self.process:
            self.process.terminate()
            self.process.wait()

    def list_tools(self):
        """Query server for available tools."""
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/list",
            "params": {}
        }
        self.request_id += 1

        return self._send_request(request)

    def call_tool(self, tool_name, arguments):
        """Invoke a tool on the MCP server with given arguments."""
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        self.request_id += 1

        return self._send_request(request)

    def _send_request(self, request):
        """Send JSON-RPC request and parse response."""
        if not self.process:
            raise Exception("MCP server not started")

        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()

        response_line = self.process.stdout.readline()
        return json.loads(response_line)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

