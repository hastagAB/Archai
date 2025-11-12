import os
from openai import OpenAI
import pinecone
from dotenv import load_dotenv

load_dotenv()


class RAGTool:
    """
    Retrieval Augmented Generation tool for architecture knowledge base.
    
    Searches Pinecone vector store to find relevant architecture patterns,
    ADRs, and best practices based on semantic similarity.
    """

    def __init__(self):
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        pc = pinecone.Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = pc.Index("architecture-kb")

    def retrieve(self, query, top_k=5):
        """
        Retrieve relevant documents from knowledge base.
        
        Args:
            query: Search query string
            top_k: Number of results to return (default: 5)
            
        Returns:
            List of document dictionaries with text, score, source, and type
        """
        embedding = self.openai.embeddings.create(
            model="text-embedding-3-small",
            input=query
        ).data[0].embedding

        results = self.index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True
        )

        return [{
            "text": match.metadata.get("text", ""),
            "score": match.score,
            "source": match.metadata.get("source", ""),
            "doc_type": match.metadata.get("doc_type", "")
        } for match in results.matches]


class GraphTool:
    """
    Graph analysis tool for architecture dependency extraction.
    
    Uses LLM to extract components and dependencies from unstructured text,
    then performs deterministic analysis for SPOFs, paths, and bottlenecks.
    """

    def __init__(self):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def analyze(self, architecture):
        """
        Analyze architecture dependencies and identify issues.
        
        Two-step process: LLM extracts structured graph, then deterministic
        algorithms identify SPOFs, critical paths, and bottlenecks.
        """

        # Step 1: Use LLM to extract structured graph
        graph_data = self._extract_graph_with_llm(architecture)

        # Step 2: Deterministic analysis on structured data
        return {
            "components": graph_data["nodes"],
            "dependencies": graph_data["edges"],
            "spof": self._find_spof(graph_data),
            "paths": self._find_paths(graph_data["edges"]),
            "bottlenecks": self._find_bottlenecks(graph_data["edges"])
        }

    def _extract_graph_with_llm(self, architecture):
        """
        Extract component graph using LLM.
        
        Converts unstructured architecture description into structured
        graph with nodes (components) and edges (dependencies).
        """

        prompt = f"""Extract the architecture components and dependencies as a graph.

Architecture:

{architecture}

Return ONLY valid JSON in this exact format:

{{
  "nodes": ["component1", "component2", ...],
  "edges": {{
    "component1": ["component2", "component3"],
    "component2": ["component4"]
  }}
}}

Nodes: List all components (frontend, backend, database, cache, etc.)
Edges: Map each component to its dependencies"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract JSON from response
        response_text = response.content[0].text

        # Clean markdown if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        import json
        try:
            return json.loads(response_text.strip())
        except:
            # Fallback to simple extraction
            return {
                "nodes": self._extract_components_simple(architecture),
                "edges": self._extract_dependencies_simple(architecture, [])
            }

    def _extract_components_simple(self, text):
        """Fallback component extraction using keyword matching."""
        keywords = ["frontend", "backend", "database", "cache", "api gateway",
                   "load balancer", "cdn", "queue", "service", "lambda"]
        text_lower = text.lower()
        return [kw for kw in keywords if kw in text_lower]

    def _extract_dependencies_simple(self, text, components):
        """Fallback dependency extraction using simple inference rules."""
        deps = {}
        if "frontend" in components:
            deps["frontend"] = [c for c in ["api gateway", "cdn"] if c in components]
        return deps

    def _find_spof(self, graph_data):
        """Identify single points of failure in the architecture graph."""
        spof = []

        # Check for single instances
        for node in graph_data["nodes"]:
            if "single" in node.lower() or ("database" in node.lower() and "replica" not in node.lower()):
                spof.append(f"Single instance: {node}")

        # Check for high-dependency components
        incoming = {}
        for source, targets in graph_data["edges"].items():
            for target in targets:
                incoming[target] = incoming.get(target, 0) + 1

        for comp, count in incoming.items():
            if count > 3:
                spof.append(f"High dependency component: {comp}")

        return spof

    def _find_paths(self, edges):
        """Identify critical execution paths through the system."""
        paths = []

        # Find entry points (components with no incoming edges)
        all_targets = set()
        for targets in edges.values():
            all_targets.update(targets)

        entry_points = [node for node in edges.keys() if node not in all_targets]

        # Traverse from each entry point
        for entry in entry_points:
            path = self._traverse_path(entry, edges, set())
            if path:
                paths.append(" -> ".join(path))

        return paths

    def _traverse_path(self, node, edges, visited):
        """Recursively traverse graph to build execution path."""
        if node in visited:
            return []

        visited.add(node)
        path = [node]

        if node in edges and edges[node]:
            next_node = edges[node][0]
            rest = self._traverse_path(next_node, edges, visited)
            path.extend(rest)

        return path

    def _find_bottlenecks(self, edges):
        """Identify components with high dependency counts (bottlenecks)."""
        incoming = {}
        for source, targets in edges.items():
            for target in targets:
                incoming[target] = incoming.get(target, 0) + 1

        return [comp for comp, count in incoming.items() if count > 2]
