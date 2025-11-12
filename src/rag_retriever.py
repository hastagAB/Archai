import os
from typing import List, Dict
from openai import OpenAI
import pinecone
from dotenv import load_dotenv

load_dotenv()

class RAGRetriever:
    def __init__(self):
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        pc = pinecone.Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = pc.Index("architecture-kb")
    
    def retrieve(self, query: str, top_k: int = 5, doc_type: str = None) -> List[Dict]:
        query_embedding = self.openai.embeddings.create(
            model="text-embedding-3-small",
            input=query
        ).data[0].embedding
        
        filter_dict = {"doc_type": {"$eq": doc_type}} if doc_type else None
        
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict
        )
        
        docs = []
        for match in results.matches:
            docs.append({
                "text": match.metadata.get("text", ""),
                "score": match.score,
                "source": match.metadata.get("source", ""),
                "doc_type": match.metadata.get("doc_type", "")
            })
        
        return docs