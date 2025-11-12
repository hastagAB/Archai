import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools import RAGTool, GraphTool
from agent import ArchitectureAgent


class TestSystem(unittest.TestCase):

    def test_rag(self):
        rag = RAGTool()
        docs = rag.retrieve("microservices", top_k=2)
        self.assertGreater(len(docs), 0)

    def test_graph(self):
        graph = GraphTool()
        analysis = graph.analyze("Web app with database and cache")
        self.assertIn("components", analysis)

    def test_agent(self):
        agent = ArchitectureAgent(verbose=False)
        result = agent.review("Simple web app", max_iterations=2)
        self.assertIn("status", result)


if __name__ == "__main__":
    unittest.main()
