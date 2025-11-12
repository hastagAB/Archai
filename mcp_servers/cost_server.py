#!/usr/bin/env python3
import os
import json
import sys
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class CostMCPServer:
    """
    MCP server for cost analysis.
    
    Provides cost estimation and optimization tools via MCP protocol.
    Runs as isolated subprocess for security and reliability.
    """

    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.tools = [
            {
                "name": "estimate_cost",
                "description": "Estimate infrastructure costs",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "architecture": {"type": "string"}
                    },
                    "required": ["architecture"]
                }
            },
            {
                "name": "optimize_cost",
                "description": "Suggest cost optimizations",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "architecture": {"type": "string"}
                    },
                    "required": ["architecture"]
                }
            }
        ]

    def handle_request(self, request):
        """Process incoming JSON-RPC requests from MCP client."""
        method = request.get("method")

        if method == "tools/list":
            return {"tools": self.tools}

        elif method == "tools/call":
            tool_name = request["params"]["name"]
            arguments = request["params"]["arguments"]

            if tool_name == "estimate_cost":
                result = self._estimate_cost(arguments["architecture"])
                return {"content": [{"type": "text", "text": result}]}

            elif tool_name == "optimize_cost":
                result = self._optimize_cost(arguments["architecture"])
                return {"content": [{"type": "text", "text": result}]}

        return {"error": "Unknown method"}

    def _estimate_cost(self, architecture):
        """Estimate infrastructure costs for architecture."""
        prompt = f"""Estimate monthly infrastructure costs for:

{architecture}

Provide breakdown by component and total estimate."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    def _optimize_cost(self, architecture):
        """Generate cost optimization recommendations."""
        prompt = f"""Suggest cost optimizations for:

{architecture}

Focus on: right-sizing, reserved instances, storage tiers, idle resources."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    def run(self):
        """Main server event loop processing JSON-RPC requests."""
        sys.stderr.write("Cost MCP Server started\n")
        sys.stderr.flush()

        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break

                request = json.loads(line)
                response = self.handle_request(request)

                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

            except Exception as e:
                error_response = {"error": str(e)}
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()


if __name__ == "__main__":
    server = CostMCPServer()
    server.run()

