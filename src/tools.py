import os
from openai import OpenAI
import pinecone
from dotenv import load_dotenv

load_dotenv()


class RAGTool:
    """Retrieves architecture patterns and ADRs from vector store"""

    def __init__(self):
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        pc = pinecone.Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = pc.Index("architecture-kb")

    def retrieve(self, query, top_k=5):
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
    """Analyzes architecture dependencies and identifies issues"""

    def analyze(self, architecture):
        components = self._extract_components(architecture)
        dependencies = self._extract_dependencies(architecture, components)

        return {
            "components": components,
            "dependencies": dependencies,
            "spof": self._find_spof(components, dependencies),
            "paths": self._find_paths(dependencies),
            "bottlenecks": self._find_bottlenecks(dependencies)
        }

    def _extract_components(self, text):
        keywords = ["frontend", "backend", "database", "cache", "api gateway",
                   "load balancer", "cdn", "queue", "service", "lambda"]
        text_lower = text.lower()
        return [kw for kw in keywords if kw in text_lower]

    def _extract_dependencies(self, text, components):
        deps = {}
        if "frontend" in components:
            deps["frontend"] = [c for c in ["api gateway", "cdn"] if c in components]
        if "api gateway" in components:
            deps["api gateway"] = [c for c in ["service", "lambda"] if c in components]
        if "service" in components or "backend" in components:
            deps["services"] = [c for c in ["database", "cache"] if c in components]
        return deps

    def _find_spof(self, components, dependencies):
        spof = []
        if "database" in components and "single" in " ".join(components).lower():
            spof.append("Single database instance")
        return spof

    def _find_paths(self, dependencies):
        paths = []
        if "frontend" in dependencies:
            path = ["frontend"]
            current = "frontend"
            visited = set()
            while current in dependencies and current not in visited:
                visited.add(current)
                if dependencies[current]:
                    next_node = dependencies[current][0]
                    path.append(next_node)
                    current = next_node
                else:
                    break
            paths.append(" -> ".join(path))
        return paths

    def _find_bottlenecks(self, dependencies):
        incoming = {}
        for comp, deps in dependencies.items():
            for dep in deps:
                incoming[dep] = incoming.get(dep, 0) + 1
        return [comp for comp, count in incoming.items() if count > 2]
