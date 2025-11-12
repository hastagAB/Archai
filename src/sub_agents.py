import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class SubAgent:
    def __init__(self, system_prompt: str):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.system_prompt = system_prompt
    
    def analyze(self, architecture_info: str, context: str = "") -> str:
        prompt = f"""Architecture to analyze:
{architecture_info}

Additional context:
{context}

Provide your analysis."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0.1,
            system=self.system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text


class SecurityAgent(SubAgent):
    def __init__(self):
        super().__init__(
            system_prompt="""You are a Security Specialist. Analyze architectures for:
- Authentication and authorization
- Encryption (at rest and in transit)
- Network security
- OWASP Top 10 compliance
- Secrets management

Provide specific security concerns and fixes."""
        )


class CostAgent(SubAgent):
    def __init__(self):
        super().__init__(
            system_prompt="""You are a Cost Optimization Specialist. Analyze for:
- Resource right-sizing
- Reserved vs on-demand instances
- Storage optimization
- Data transfer costs
- Idle resources

Provide cost estimates and optimization recommendations."""
        )


class PerformanceAgent(SubAgent):
    def __init__(self):
        super().__init__(
            system_prompt="""You are a Performance Specialist. Analyze for:
- Caching strategies (CDN, app cache, DB cache)
- Database optimization
- Load balancing
- Async processing
- Bottlenecks

Provide performance improvement recommendations."""
        )