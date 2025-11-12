import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class BaseAgent:
    """
    Base class for specialized analysis agents.
    
    Provides common functionality for security, cost, and performance
    analysis using Claude API with role-specific prompts.
    """

    def __init__(self, role_prompt):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.role = role_prompt

    def analyze(self, architecture):
        """
        Perform specialized analysis on architecture.
        
        Args:
            architecture: Architecture description to analyze
            
        Returns:
            Analysis results as text
        """
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0.1,
            system=self.role,
            messages=[{"role": "user", "content": f"Analyze:\n{architecture}"}]
        )
        return response.content[0].text


class SecurityAgent(BaseAgent):
    """
    Security analysis specialist agent.
    
    Focuses on authentication, authorization, encryption, network security,
    OWASP compliance, and secrets management.
    """
    def __init__(self):
        super().__init__(
            "You are a Security Specialist. Analyze for: authentication, "
            "authorization, encryption, network security, OWASP compliance, "
            "secrets management. Provide specific risks and fixes."
        )


class CostAgent(BaseAgent):
    """
    Cost optimization specialist agent.
    
    Analyzes resource sizing, pricing models, storage optimization,
    data transfer costs, and idle resources.
    """
    def __init__(self):
        super().__init__(
            "You are a Cost Optimizer. Analyze for: resource sizing, "
            "reserved vs on-demand instances, storage optimization, "
            "data transfer costs, idle resources. Provide cost estimates."
        )


class PerformanceAgent(BaseAgent):
    """
    Performance analysis specialist agent.
    
    Evaluates caching strategies, database optimization, load balancing,
    async processing, and identifies performance bottlenecks.
    """
    def __init__(self):
        super().__init__(
            "You are a Performance Specialist. Analyze for: caching strategies, "
            "database optimization, load balancing, async processing, "
            "bottlenecks. Provide performance improvements."
        )
