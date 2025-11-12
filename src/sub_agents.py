import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class BaseAgent:
    """Base class for specialist agents"""

    def __init__(self, role_prompt):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.role = role_prompt

    def analyze(self, architecture):
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0.1,
            system=self.role,
            messages=[{"role": "user", "content": f"Analyze:\n{architecture}"}]
        )
        return response.content[0].text


class SecurityAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "You are a Security Specialist. Analyze for: authentication, "
            "authorization, encryption, network security, OWASP compliance, "
            "secrets management. Provide specific risks and fixes."
        )


class CostAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "You are a Cost Optimizer. Analyze for: resource sizing, "
            "reserved vs on-demand instances, storage optimization, "
            "data transfer costs, idle resources. Provide cost estimates."
        )


class PerformanceAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "You are a Performance Specialist. Analyze for: caching strategies, "
            "database optimization, load balancing, async processing, "
            "bottlenecks. Provide performance improvements."
        )
