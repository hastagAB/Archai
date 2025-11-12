# data/check_vectors.py
import os
from pinecone import Pinecone
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

class VectorChecker:
    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = self.pc.Index("architecture-kb")
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def get_embedding(self, text: str):
        """Generate embedding for query"""
        response = self.openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    def check_stats(self):
        """Display index statistics"""
        stats = self.index.describe_index_stats()
        print("="*60)
        print("INDEX STATISTICS")
        print("="*60)
        print(f"Total vectors: {stats.total_vector_count}")
        print(f"Dimension: {stats.dimension}")
        print(f"Index fullness: {stats.index_fullness}")
        print()
    
    def test_retrieval(self, query: str, top_k: int = 5):
        """Test semantic retrieval with a query"""
        print("="*60)
        print(f"QUERY: {query}")
        print("="*60)
        
        query_embedding = self.get_embedding(query)
        
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        if not results.matches:
            print("No results found!")
            return
        
        for i, match in enumerate(results.matches, 1):
            print(f"\n[Result {i}]")
            print(f"Score: {match.score:.4f}")
            print(f"Source: {match.metadata.get('source', 'N/A')}")
            print(f"Doc Type: {match.metadata.get('doc_type', 'N/A')}")
            print(f"Tags: {match.metadata.get('tags', 'N/A')}")
            print(f"Chunk: {match.metadata.get('chunk_index', 0)}/{match.metadata.get('total_chunks', 0)}")
            print(f"\nText Preview:")
            text = match.metadata.get('text', '')
            print(text[:300] + "..." if len(text) > 300 else text)
            print("-"*60)
    
    def test_filtered_retrieval(self, query: str, doc_type: str, top_k: int = 3):
        """Test retrieval with filters"""
        print("="*60)
        print(f"FILTERED QUERY: {query}")
        print(f"Filter: doc_type = {doc_type}")
        print("="*60)
        
        query_embedding = self.get_embedding(query)
        
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter={"doc_type": {"$eq": doc_type}}
        )
        
        if not results.matches:
            print(f"No results found for doc_type: {doc_type}")
            return
        
        for i, match in enumerate(results.matches, 1):
            print(f"\n[Result {i}]")
            print(f"Score: {match.score:.4f}")
            print(f"Source: {match.metadata.get('source', 'N/A')}")
            print(f"\nText Preview:")
            text = match.metadata.get('text', '')
            print(text[:200] + "..." if len(text) > 200 else text)
            print("-"*60)
    
    def run_test_suite(self):
        """Run comprehensive test suite"""
        self.check_stats()
        
        test_queries = [
            "How to implement authentication in microservices?",
            "Best practices for API Gateway design",
            "Caching strategies for high performance",
            "Security baseline for cloud architecture",
            "Cost optimization techniques for AWS"
        ]
        
        print("\n" + "="*60)
        print("RUNNING TEST RETRIEVALS")
        print("="*60 + "\n")
        
        for query in test_queries:
            self.test_retrieval(query, top_k=3)
            print("\n")
        
        print("\n" + "="*60)
        print("TESTING FILTERED RETRIEVALS")
        print("="*60 + "\n")
        
        self.test_filtered_retrieval(
            "security best practices",
            doc_type="security",
            top_k=3
        )
        
        print("\n")
        
        self.test_filtered_retrieval(
            "AWS architecture patterns",
            doc_type="cloud-pattern",
            top_k=3
        )


def main():
    checker = VectorChecker()
    
    print("\n" + "="*60)
    print("PINECONE VECTOR STORE TEST")
    print("="*60 + "\n")
    
    checker.run_test_suite()
    
    print("\n" + "="*60)
    print("CUSTOM QUERY TEST")
    print("="*60 + "\n")
    
    custom_query = input("Enter your custom query (or press Enter to skip): ")
    if custom_query.strip():
        checker.test_retrieval(custom_query, top_k=5)


if __name__ == "__main__":
    main()