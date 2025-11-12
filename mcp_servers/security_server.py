#!/usr/bin/env python3
import os
import json
import sys
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class SecurityMCPServer:
    """
    MCP Server for security analysis.
    Runs as a separate process and communicates via stdin/stdout.
    """

    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.tools = [
            {
                "name": "analyze_security",
                "description": "Analyze architecture for security vulnerabilities",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "architecture": {
                            "type": "string",
                            "description": "Architecture description to analyze"
                        }
                    },
                    "required": ["architecture"]
                }
            },
            {
                "name": "check_owasp",
                "description": "Check against OWASP Top 10",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "architecture": {
                            "type": "string",
                            "description": "Architecture description"
                        }
                    },
                    "required": ["architecture"]
                }
            }
        ]

    def handle_request(self, request):
        """Handle incoming MCP requests"""
        method = request.get("method")

        if method == "tools/list":
            return {"tools": self.tools}

        elif method == "tools/call":
            tool_name = request["params"]["name"]
            arguments = request["params"]["arguments"]

            if tool_name == "analyze_security":
                result = self._analyze_security(arguments["architecture"])
                return {"content": [{"type": "text", "text": result}]}

            elif tool_name == "check_owasp":
                result = self._check_owasp(arguments["architecture"])
                return {"content": [{"type": "text", "text": result}]}

        return {"error": "Unknown method"}

    def _analyze_security(self, architecture):
        """Perform security analysis using Claude"""
        prompt = f"""Analyze this architecture for security vulnerabilities:

{architecture}

Focus on:
- Authentication and authorization
- Data encryption (at rest and in transit)
- Network security
- Secrets management
- API security

Provide specific vulnerabilities and remediation steps."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    def _check_owasp(self, architecture):
        """Check against OWASP Top 10"""
        prompt = f"""Check this architecture against OWASP Top 10:

{architecture}

List which OWASP Top 10 risks apply and how."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    def run(self):
        """Main server loop - reads from stdin, writes to stdout"""
        sys.stderr.write("Security MCP Server started\n")
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
    server = SecurityMCPServer()
    server.run()

