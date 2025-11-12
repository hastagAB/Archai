import subprocess
import json
from pathlib import Path


class MCPClient:
    """Client to communicate with MCP servers"""

    def __init__(self, server_script):
        self.server_path = Path(__file__).parent.parent / "mcp_servers" / server_script
        self.process = None
        self.request_id = 0

    def start(self):
        """Start the MCP server process"""
        self.process = subprocess.Popen(
            ["python3", str(self.server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

    def stop(self):
        """Stop the MCP server"""
        if self.process:
            self.process.terminate()
            self.process.wait()

    def list_tools(self):
        """List available tools from server"""
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/list",
            "params": {}
        }
        self.request_id += 1

        return self._send_request(request)

    def call_tool(self, tool_name, arguments):
        """Call a tool on the MCP server"""
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
        """Send request to server and get response"""
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

