import os
from anthropic import Anthropic
from dotenv import load_dotenv
from tools import RAGTool, GraphTool
from sub_agents import PerformanceAgent
from mcp_client import MCPClient
from memory import Memory
from utils import Logger

load_dotenv()


class ArchitectureAgent:
    """
    Main ReAct agent with structured tool calling.
    Uses Claude's native tool calling instead of string parsing.
    """

    def __init__(self, verbose=True, use_mcp=True):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.verbose = verbose
        self.use_mcp = use_mcp
        self.logger = Logger("ArchitectureAgent")

        # Initialize tools
        self.rag = RAGTool()
        self.graph = GraphTool()

        # MCP servers
        self.security_mcp = None
        self.cost_mcp = None

        # Regular sub-agent
        self.performance_agent = PerformanceAgent()

        # Memory
        self.memory = Memory()

        # Define tools for structured calling
        self.tools = self._define_tools()
        self.system_prompt = self._load_system_prompt()

    def _define_tools(self):
        """Define tools in Claude's structured format"""
        return [
            {
                "name": "rag_retrieve",
                "description": "Search knowledge base for architecture patterns, ADRs, and best practices",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for retrieving relevant documents"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "security_analysis",
                "description": "Analyze architecture for security vulnerabilities and risks",
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
                "name": "cost_analysis",
                "description": "Estimate infrastructure costs and identify optimization opportunities",
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
                "name": "performance_analysis",
                "description": "Evaluate performance characteristics and identify bottlenecks",
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
                "name": "graph_analysis",
                "description": "Analyze component dependencies and identify single points of failure",
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
            }
        ]

    def review(self, architecture, max_iterations=10):
        """
        Main review loop with structured tool calling.
        Uses Claude's native tool calling for reliability.
        """
        self.logger.info("Starting architecture review with structured tools")
        self.memory.set_architecture(architecture)

        messages = [{"role": "user", "content": f"Review this architecture:\n\n{architecture}"}]
        trace = {"thoughts": [], "actions": [], "observations": []}

        for iteration in range(max_iterations):
            self._log_iteration(iteration, max_iterations)

            # Call Claude with tools
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                temperature=0.2,
                system=self.system_prompt,
                tools=self.tools,
                messages=messages
            )

            # Process response
            if response.stop_reason == "end_turn":
                # Agent is done
                final_text = self._extract_text_content(response)
                if "FINAL_ANSWER:" in final_text or iteration == max_iterations - 1:
                    result = self._build_result(final_text, trace, "complete")
                    saved_files = self.memory.save_to_file(result)
                    result["saved_files"] = saved_files
                    return result

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": "Continue analysis or provide FINAL_ANSWER."})

            elif response.stop_reason == "tool_use":
                # Agent wants to use a tool
                assistant_content = response.content
                messages.append({"role": "assistant", "content": assistant_content})

                # Extract thought if present
                text_content = self._extract_text_content(response)
                if text_content:
                    self.memory.add_thought(text_content)
                    trace["thoughts"].append(text_content)
                    if self.verbose:
                        print(f"\nTHOUGHT: {text_content}")

                # Process all tool uses
                tool_results = []
                for content_block in assistant_content:
                    if content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_input = content_block.input
                        tool_use_id = content_block.id

                        self._log_tool(tool_name, tool_input)

                        # Execute tool
                        result = self._execute_structured_tool(tool_name, tool_input, architecture)

                        # Store in trace
                        trace["actions"].append(tool_name)
                        trace["observations"].append(result)
                        self.memory.add_action(tool_name, tool_input)
                        self.memory.add_observation(result, tool_name)

                        if self.verbose:
                            self._display_observation(result)

                        # Add tool result
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": result
                        })

                # Add tool results to conversation
                messages.append({"role": "user", "content": tool_results})

            else:
                # Unexpected stop reason
                break

        result = self._build_result("Max iterations reached", trace, "incomplete")
        saved_files = self.memory.save_to_file(result)
        result["saved_files"] = saved_files
        return result

    def review_with_reflection(self, architecture, max_iterations=10):
        """
        Review with self-reflection step before final answer.
        Agent critiques its own work for improved quality.
        """
        # Do normal review
        result = self.review(architecture, max_iterations)

        if result["status"] != "complete":
            return result

        # Self-reflection step
        if self.verbose:
            print(f"\n{'='*70}")
            print("SELF-REFLECTION PHASE")
            print(f"{'='*70}")

        self.logger.info("Starting self-reflection")

        reflection_prompt = f"""You are a Principal Architect reviewing this analysis:

DRAFT REVIEW:

{result['final_answer']}

ORIGINAL ARCHITECTURE:

{architecture}

Critique this review:

1. Is the reasoning sound and complete?
2. Are recommendations specific and actionable?
3. Have any critical areas been missed?
4. Are there any contradictions or unclear points?

Provide constructive feedback and suggest improvements."""

        reflection = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0.3,
            messages=[{"role": "user", "content": reflection_prompt}]
        )

        critique = reflection.content[0].text

        if self.verbose:
            print(f"\nSELF-CRITIQUE:\n{critique}")

        # Incorporate feedback
        final_prompt = f"""Based on this critique, provide an improved final review:

CRITIQUE:

{critique}

ORIGINAL REVIEW:

{result['final_answer']}

Provide the improved FINAL_ANSWER incorporating the feedback."""

        improved = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            temperature=0.2,
            messages=[{"role": "user", "content": final_prompt}]
        )

        result["final_answer"] = improved.content[0].text
        result["reflection"] = critique

        # Save updated result
        saved_files = self.memory.save_to_file(result)
        result["saved_files"] = saved_files

        return result

    def _execute_structured_tool(self, tool_name, tool_input, architecture):
        """Execute tool with structured input"""

        if tool_name == "rag_retrieve":
            docs = self.rag.retrieve(tool_input["query"])
            return self._format_rag_results(docs)

        elif tool_name == "security_analysis":
            if self.use_mcp and self.security_mcp:
                response = self.security_mcp.call_tool("analyze_security", tool_input)
                return response["content"][0]["text"]
            else:
                from sub_agents import SecurityAgent
                return SecurityAgent().analyze(architecture)

        elif tool_name == "cost_analysis":
            if self.use_mcp and self.cost_mcp:
                response = self.cost_mcp.call_tool("estimate_cost", tool_input)
                return response["content"][0]["text"]
            else:
                from sub_agents import CostAgent
                return CostAgent().analyze(architecture)

        elif tool_name == "performance_analysis":
            return self.performance_agent.analyze(architecture)

        elif tool_name == "graph_analysis":
            analysis = self.graph.analyze(architecture)
            return self._format_graph_results(analysis)

        return "Tool execution failed"

    def _extract_text_content(self, response):
        """Extract text content from response"""
        text_parts = []
        for block in response.content:
            if hasattr(block, 'text'):
                text_parts.append(block.text)
        return "\n".join(text_parts)

    def _load_system_prompt(self):
        return """You are an expert Architecture Reviewer Agent.

Your process:
1. Think about what analysis is needed
2. Use tools to gather information and perform analysis
3. Synthesize findings into recommendations

Available tools will be provided. Use them to:
- Retrieve relevant architecture patterns and ADRs
- Analyze security, cost, and performance
- Analyze component dependencies

When you have completed all necessary analysis, provide your FINAL_ANSWER with comprehensive recommendations."""

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

    def _log_iteration(self, iteration, max_iterations):
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"ITERATION {iteration + 1}/{max_iterations}")
            print(f"{'='*70}")
        self.logger.info(f"Iteration {iteration + 1}/{max_iterations}")

    def _log_tool(self, tool_name, params):
        if self.verbose:
            print(f"\nEXECUTING TOOL: {tool_name}")
            print(f"Parameters: {params}")
        self.logger.info(f"Executing {tool_name}")

    def _display_observation(self, observation):
        print(f"\n{'='*70}")
        print("OBSERVATION")
        print(f"{'='*70}")
        print(observation[:500] + "..." if len(observation) > 500 else observation)

    def chat(self, message):
        """Chat with context"""
        if not self.memory.has_architecture():
            return "No architecture loaded. Please review an architecture first."

        self.memory.add_entry("user", message)
        context = self.memory.get_context()
        full_prompt = f"{context}\n\nUser Question: {message}"

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0.2,
            system="You are an architecture consultant.",
            messages=[{"role": "user", "content": full_prompt}]
        )

        answer = response.content[0].text
        self.memory.add_entry("assistant", answer)
        return answer

    def compare(self, arch1, arch2):
        """Compare architectures"""
        self.logger.info("Comparing architectures")

        prompt = f"""Compare these architectures:

ARCHITECTURE 1:

{arch1}

ARCHITECTURE 2:

{arch2}

Provide comparison on: security, performance, cost, scalability, complexity."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            temperature=0.2,
            system=self.system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    def __enter__(self):
        if self.use_mcp:
            self.logger.info("Starting MCP servers")
            self.security_mcp = MCPClient("security_server.py")
            self.security_mcp.start()
            self.cost_mcp = MCPClient("cost_server.py")
            self.cost_mcp.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.security_mcp:
            self.security_mcp.stop()
        if self.cost_mcp:
            self.cost_mcp.stop()
