from datetime import datetime
from typing import Dict, List, Optional
import json
from pathlib import Path


class Memory:
    """
    Conversation memory and context management.
    
    Tracks review history, architecture context, and reasoning steps.
    Provides file persistence for session data and review results.
    """

    def __init__(self):
        self.history = []
        self.architecture = None
        self.key_findings = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path("outputs")
        self.output_dir.mkdir(exist_ok=True)

    def set_architecture(self, arch):
        self.architecture = arch

    def has_architecture(self):
        return self.architecture is not None

    def get_architecture(self):
        return self.architecture

    def add_entry(self, role, content):
        """Add entry to conversation history."""
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def add_thought(self, thought):
        """Add reasoning thought to history."""
        self.history.append({
            "role": "thought",
            "content": thought,
            "timestamp": datetime.now().isoformat()
        })

    def add_action(self, tool, params):
        """Add tool execution action to history."""
        self.history.append({
            "role": "action",
            "content": f"{tool}: {params}",
            "tool": tool,
            "params": params,
            "timestamp": datetime.now().isoformat()
        })

    def add_observation(self, observation, tool):
        """Add tool observation result to history."""
        self.history.append({
            "role": "observation",
            "content": observation[:500],
            "tool": tool,
            "full_content": observation,
            "timestamp": datetime.now().isoformat()
        })

    def get_context(self, last_n=10):
        recent = self.history[-last_n:]
        context = "CONVERSATION CONTEXT:\n\n"

        if self.architecture:
            context += f"Architecture:\n{self.architecture[:300]}...\n\n"

        context += "Recent exchanges:\n"
        for entry in recent:
            role = entry["role"]
            content = entry["content"][:150]
            context += f"[{role}] {content}...\n"

        return context

    def get_summary(self):
        """Get summary statistics of memory contents."""
        thoughts = len([e for e in self.history if e.get("role") == "thought"])
        actions = len([e for e in self.history if e.get("role") == "action"])
        observations = len([e for e in self.history if e.get("role") == "observation"])

        return {
            "total_entries": len(self.history),
            "has_architecture": self.has_architecture(),
            "thoughts": thoughts,
            "actions": actions,
            "observations": observations,
            "session_id": self.session_id
        }

    def save_to_file(self, review_result=None):
        """
        Save session data to files.
        
        Creates timestamped files for memory, review results, and traces
        in the outputs directory.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save memory history
        memory_file = self.output_dir / f"memory_{timestamp}.json"
        memory_data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "architecture": self.architecture,
            "history": self.history,
            "summary": self.get_summary()
        }

        with open(memory_file, 'w') as f:
            json.dump(memory_data, f, indent=2)

        print(f"\nMemory saved to: {memory_file}")

        review_file = None
        trace_file = None

        # Save review result if provided
        if review_result:
            review_file = self.output_dir / f"review_{timestamp}.txt"

            with open(review_file, 'w') as f:
                f.write("="*70 + "\n")
                f.write("ARCHITECTURE REVIEW\n")
                f.write("="*70 + "\n\n")
                f.write(f"Session ID: {self.session_id}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Status: {review_result['status']}\n\n")

                f.write("="*70 + "\n")
                f.write("ARCHITECTURE\n")
                f.write("="*70 + "\n\n")
                f.write(self.architecture + "\n\n")

                f.write("="*70 + "\n")
                f.write("REASONING TRACE\n")
                f.write("="*70 + "\n\n")

                f.write(f"Total Thoughts: {len(review_result['trace']['thoughts'])}\n")
                f.write(f"Total Actions: {len(review_result['trace']['actions'])}\n")
                f.write(f"Total Observations: {len(review_result['trace']['observations'])}\n\n")

                f.write("Thoughts:\n")
                for i, thought in enumerate(review_result['trace']['thoughts'], 1):
                    f.write(f"{i}. {thought}\n\n")

                f.write("\nActions Executed:\n")
                for i, action in enumerate(review_result['trace']['actions'], 1):
                    f.write(f"{i}. {action}\n\n")

                f.write("="*70 + "\n")
                f.write("FINAL REVIEW\n")
                f.write("="*70 + "\n\n")
                f.write(review_result['final_answer'] + "\n")

            print(f"Review saved to: {review_file}")

            # Save detailed trace
            trace_file = self.output_dir / f"trace_{timestamp}.json"
            with open(trace_file, 'w') as f:
                json.dump(review_result, f, indent=2)

            print(f"Trace saved to: {trace_file}")

        return {
            "memory_file": str(memory_file),
            "review_file": str(review_file) if review_file else None,
            "trace_file": str(trace_file) if trace_file else None
        }

    def clear(self):
        self.history = []
        self.architecture = None
        self.key_findings = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
