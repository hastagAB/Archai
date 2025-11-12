from datetime import datetime
from typing import Dict, List, Optional


class Memory:
    """Manages conversation history and context"""

    def __init__(self):
        self.history = []
        self.architecture = None
        self.key_findings = []

    def set_architecture(self, arch):
        self.architecture = arch

    def has_architecture(self):
        return self.architecture is not None

    def get_architecture(self):
        return self.architecture

    def add_entry(self, role, content):
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def add_thought(self, thought):
        self.add_entry("thought", thought)

    def add_action(self, tool, params):
        self.add_entry("action", f"{tool}: {params}")

    def add_observation(self, observation, tool):
        self.add_entry("observation", f"{tool}: {observation[:200]}")

    def get_context(self, last_n=10):
        recent = self.history[-last_n:]
        context = "CONVERSATION CONTEXT:\n\n"

        if self.architecture:
            context += f"Architecture:\n{self.architecture[:300]}...\n\n"

        context += "Recent exchanges:\n"
        for entry in recent:
            context += f"[{entry['role']}] {entry['content'][:150]}...\n"

        return context

    def get_summary(self):
        return {
            "total_entries": len(self.history),
            "has_architecture": self.has_architecture(),
            "thoughts": len([e for e in self.history if e["role"] == "thought"]),
            "actions": len([e for e in self.history if e["role"] == "action"])
        }

    def clear(self):
        self.history = []
        self.architecture = None
        self.key_findings = []
