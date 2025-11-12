import os
from anthropic import Anthropic
from dotenv import load_dotenv
from tools import RAGTool, GraphTool
from sub_agents import SecurityAgent, CostAgent, PerformanceAgent
from memory import Memory
from utils import Logger

load_dotenv()


class ArchitectureAgent:
    """
    Main ReAct agent that orchestrates architecture reviews using:
    - RAG for knowledge retrieval
    - Sub-agents for specialized analysis
    - Graph reasoning for dependency analysis
    """

    def __init__(self, verbose=True):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.verbose = verbose
        self.logger = Logger("ArchitectureAgent")

        # Initialize tools
        self.rag = RAGTool()
        self.graph = GraphTool()

        # Initialize sub-agents (MCP concept)
        self.security_agent = SecurityAgent()
        self.cost_agent = CostAgent()
        self.performance_agent = PerformanceAgent()

        # Initialize memory
        self.memory = Memory()

        self.system_prompt = self._load_system_prompt()

    def review(self, architecture, max_iterations=10):
        """
        Main review loop using ReAct reasoning:
        Thought -> Action -> Observation -> Reflection -> Answer
        """
        self.logger.info("Starting architecture review")
        self.memory.set_architecture(architecture)

        messages = [{"role": "user", "content": f"Review this architecture:\n\n{architecture}"}]
        trace = {"thoughts": [], "actions": [], "observations": []}

        for iteration in range(max_iterations):
            self._log_iteration(iteration, max_iterations)

            # Get agent response
            response = self._call_llm(messages)
            content = response.content[0].text

            self.memory.add_entry("assistant", content)

            # Show reasoning if verbose
            if self.verbose:
                self._display_reasoning(content)

            # Extract and store thought
            thought = self._extract_thought(content)
            if thought:
                trace["thoughts"].append(thought)
                self.memory.add_thought(thought)

            # Check if review is complete
            if "FINAL_ANSWER:" in content:
                self.logger.info("Review complete")
                return self._build_result(content, trace, "complete")

            # Execute action and get observation
            observation = self._execute_action(content, architecture)

            if observation:
                trace["observations"].append(observation)
                action_name = self._extract_action_name(content)
                trace["actions"].append(action_name)

                self.memory.add_observation(observation, action_name)

                if self.verbose:
                    self._display_observation(observation)

                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": f"OBSERVATION: {observation}\n\nContinue."})
            else:
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": "Continue or provide FINAL_ANSWER."})

        return self._build_result("Max iterations reached", trace, "incomplete")

    def chat(self, message):
        """Chat about current architecture using conversation memory"""
        if not self.memory.has_architecture():
            return "No architecture loaded. Please review an architecture first."

        self.memory.add_entry("user", message)

        context = self.memory.get_context()
        full_prompt = f"{context}\n\nUser Question: {message}"

        response = self._call_llm([{"role": "user", "content": full_prompt}], system="You are an architecture consultant. Use context to answer.")

        answer = response.content[0].text
        self.memory.add_entry("assistant", answer)

        return answer

    def compare(self, arch1, arch2):
        """Compare two architectures"""
        self.logger.info("Comparing architectures")

        prompt = f"""Compare these architectures:

ARCHITECTURE 1:

{arch1}

ARCHITECTURE 2:

{arch2}

Provide comparison on: security, performance, cost, scalability, complexity."""

        response = self._call_llm([{"role": "user", "content": prompt}])
        return response.content[0].text

    def _execute_action(self, message, architecture):
        """Execute tool based on agent's action"""

        # RAG retrieval
        if "RETRIEVE[" in message:
            query = self._extract_between(message, "RETRIEVE[", "]")
            self._log_tool("RAG Retrieval", query)

            docs = self.rag.retrieve(query)
            result = self._format_rag_results(docs)
            self.memory.add_action("rag", {"query": query})
            return result

        # Security analysis
        elif "SECURITY_CHECK" in message:
            self._log_tool("Security Agent", None)
            result = self.security_agent.analyze(architecture)
            self.memory.add_action("security", {})
            return f"SECURITY ANALYSIS:\n\n{result}"

        # Cost analysis
        elif "COST_ANALYSIS" in message:
            self._log_tool("Cost Agent", None)
            result = self.cost_agent.analyze(architecture)
            self.memory.add_action("cost", {})
            return f"COST ANALYSIS:\n\n{result}"

        # Performance analysis
        elif "PERFORMANCE_CHECK" in message:
            self._log_tool("Performance Agent", None)
            result = self.performance_agent.analyze(architecture)
            self.memory.add_action("performance", {})
            return f"PERFORMANCE ANALYSIS:\n\n{result}"

        # Graph analysis
        elif "GRAPH_ANALYSIS" in message:
            self._log_tool("Graph Analyzer", None)
            analysis = self.graph.analyze(architecture)
            result = self._format_graph_results(analysis)
            self.memory.add_action("graph", {})
            return result

        return ""

    def _call_llm(self, messages, system=None):
        """Call Claude API"""
        return self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            temperature=0.2,
            system=system or self.system_prompt,
            messages=messages
        )

    def _load_system_prompt(self):
        return """You are an Architecture Reviewer Agent.

ReAct Process:
1. THOUGHT: Analyze what's needed
2. ACTION: Execute tool or sub-agent
3. OBSERVATION: Review results
4. REFLECTION: Check completeness
5. FINAL_ANSWER: Provide recommendations

Available Actions:
- RETRIEVE[query]: Search knowledge base
- SECURITY_CHECK: Security analysis
- COST_ANALYSIS: Cost analysis
- PERFORMANCE_CHECK: Performance analysis
- GRAPH_ANALYSIS: Dependency analysis

Format your response with clear sections."""

    def _build_result(self, content, trace, status):
        final_answer = content.split("FINAL_ANSWER:")[1].strip() if "FINAL_ANSWER:" in content else content

        return {
            "status": status,
            "final_answer": final_answer,
            "trace": trace,
            "memory_summary": self.memory.get_summary()
        }

    def _format_rag_results(self, docs):
        result = "Retrieved Documents:\n\n"
        for i, doc in enumerate(docs, 1):
            result += f"{i}. {doc['source']} (score: {doc['score']:.3f})\n"
            result += f"   Type: {doc['doc_type']}\n"
            result += f"   {doc['text'][:300]}...\n\n"
        return result

    def _format_graph_results(self, analysis):
        result = "DEPENDENCY ANALYSIS:\n\n"
        result += f"Components: {', '.join(analysis['components'])}\n\n"
        result += "Dependencies:\n"
        for comp, deps in analysis['dependencies'].items():
            result += f"  {comp} -> {', '.join(deps) if deps else 'none'}\n"
        result += f"\nSingle Points of Failure: {', '.join(analysis['spof']) if analysis['spof'] else 'None'}\n"
        result += f"Critical Paths: {', '.join(analysis['paths'])}\n"
        result += f"Bottlenecks: {', '.join(analysis['bottlenecks']) if analysis['bottlenecks'] else 'None'}\n"
        return result

    def _extract_thought(self, content):
        return self._extract_section(content, "THOUGHT:")

    def _extract_action_name(self, content):
        return self._extract_section(content, "ACTION:")

    def _extract_section(self, content, marker):
        if marker in content:
            start = content.find(marker) + len(marker)
            end = content.find("\n\n", start)
            return content[start:end if end != -1 else len(content)].strip()
        return None

    def _extract_between(self, text, start_marker, end_marker):
        start = text.find(start_marker) + len(start_marker)
        end = text.find(end_marker, start)
        return text[start:end]

    def _log_iteration(self, iteration, max_iterations):
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"ITERATION {iteration + 1}/{max_iterations}")
            print(f"{'='*70}")
        self.logger.info(f"Iteration {iteration + 1}/{max_iterations}")

    def _log_tool(self, tool_name, params):
        if self.verbose:
            print(f"\nEXECUTING: {tool_name}")
            if params:
                print(f"Parameters: {params}")
        self.logger.info(f"Executing {tool_name}")

    def _display_reasoning(self, content):
        for line in content.split('\n'):
            if line.startswith('THOUGHT:'):
                print(f"\n{line}")
            elif line.startswith('ACTION:'):
                print(f"\n{line}")
            elif line.startswith('REFLECTION:'):
                print(f"\n{line}")
            elif line.strip():
                print(f"  {line}")

    def _display_observation(self, observation):
        print(f"\n{'='*70}")
        print("OBSERVATION")
        print(f"{'='*70}")
        print(observation[:500] + "..." if len(observation) > 500 else observation)
