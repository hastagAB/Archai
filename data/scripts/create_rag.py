# data/create_rag.py
import os
from pathlib import Path
from typing import List, Dict
import hashlib
import PyPDF2
from openai import OpenAI
import pinecone
from dotenv import load_dotenv

# Load environment variables from parent directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class RAGBuilder:
    def __init__(self, pinecone_api_key: str, openai_api_key: str, index_name: str = "architecture-kb"):
        self.openai = OpenAI(api_key=openai_api_key)
        
        pc = pinecone.Pinecone(api_key=pinecone_api_key)
        
        existing_indexes = [index.name for index in pc.list_indexes()]
        if index_name not in existing_indexes:
            print(f"Creating new index: {index_name}")
            pc.create_index(
                name=index_name,
                dimension=1536,
                metric="cosine",
                spec=pinecone.ServerlessSpec(cloud="aws", region="us-east-1")
            )
        
        self.index = pc.Index(index_name)
        print(f"Connected to index: {index_name}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                print(f"  Extracting {total_pages} pages from PDF")
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
                    
                    if (page_num + 1) % 100 == 0:
                        print(f"  Processed {page_num + 1}/{total_pages} pages")
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
        
        return text.strip()
    
    def extract_text_from_markdown(self, md_path: str) -> str:
        try:
            with open(md_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading Markdown {md_path}: {e}")
            return ""
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        if len(text) < chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end < len(text):
                chunk_end = end
                
                next_double_newline = text.find('\n\n', end - 100, end + 100)
                if next_double_newline != -1:
                    chunk_end = next_double_newline + 2
                else:
                    next_newline = text.find('\n', end - 50, end + 50)
                    if next_newline != -1:
                        chunk_end = next_newline + 1
                    else:
                        next_period = text.find('. ', end - 50, end + 50)
                        if next_period != -1:
                            chunk_end = next_period + 2
                        else:
                            next_space = text.find(' ', end - 20, end + 20)
                            if next_space != -1:
                                chunk_end = next_space + 1
                
                chunk = text[start:chunk_end].strip()
            else:
                chunk = text[start:].strip()
            
            if chunk:
                chunks.append(chunk)
            
            start = max(start + chunk_size - overlap, start + 1)
            
            if start >= len(text):
                break
        
        return chunks
    
    def get_embedding(self, text: str) -> List[float]:
        text = text[:8000]
        response = self.openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    def classify_document(self, filepath: Path, content_sample: str) -> Dict:
        filename = filepath.name.lower()
        content = content_sample.lower()
        
        doc_type = "reference"
        tags = []
        
        if 'adr' in filename or 'decision' in filename:
            doc_type = "adr"
            tags.append("decision-record")
        elif 'security' in filename or 'owasp' in content:
            doc_type = "security"
            tags.append("security")
        elif 'cost' in filename or 'pricing' in content:
            doc_type = "cost"
            tags.append("cost-optimization")
        elif 'performance' in filename:
            doc_type = "performance"
            tags.append("performance")
        elif 'aws' in filename or 'aws' in content[:500]:
            doc_type = "cloud-pattern"
            tags.append("aws")
        elif 'azure' in filename or 'azure' in content[:500]:
            doc_type = "cloud-pattern"
            tags.append("azure")
        elif 'gcp' in filename or 'google cloud' in content[:500]:
            doc_type = "cloud-pattern"
            tags.append("gcp")
        
        content_keywords = {
            'microservices': ['microservice', 'api gateway'],
            'database': ['database', 'sql', 'nosql'],
            'caching': ['cache', 'redis', 'cdn'],
            'authentication': ['auth', 'oauth', 'jwt'],
            'messaging': ['queue', 'kafka', 'event'],
            'serverless': ['lambda', 'serverless'],
            'container': ['docker', 'kubernetes'],
            'monitoring': ['monitoring', 'logging'],
        }
        
        for tag, keywords in content_keywords.items():
            if any(keyword in content for keyword in keywords):
                tags.append(tag)
        
        return {
            'doc_type': doc_type,
            'tags': ','.join(list(set(tags)))
        }
    
    def process_file(self, filepath: Path) -> List[Dict]:
        print(f"\nProcessing: {filepath.name}")
        
        if filepath.suffix.lower() == '.pdf':
            text = self.extract_text_from_pdf(str(filepath))
        elif filepath.suffix.lower() in ['.md', '.markdown']:
            text = self.extract_text_from_markdown(str(filepath))
        else:
            print(f"Skipping unsupported file type: {filepath.suffix}")
            return []
        
        if not text or len(text) < 100:
            print(f"Skipping empty or too short file")
            return []
        
        classification = self.classify_document(filepath, text[:2000])
        
        chunks = self.chunk_text(text)
        print(f"Created {len(chunks)} chunks")
        
        vectors = []
        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.md5(f"{filepath.stem}-{i}".encode()).hexdigest()
            
            embedding = self.get_embedding(chunk)
            
            # Limit metadata text to 5KB per vector (much smaller to be safe)
            truncated_text = chunk[:5000] if len(chunk) > 5000 else chunk
            
            vector = {
                "id": chunk_id,
                "values": embedding,
                "metadata": {
                    "text": truncated_text,
                    "source": str(filepath.name)[:200],
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "doc_type": classification['doc_type'],
                    "tags": classification['tags'][:200],
                }
            }
            vectors.append(vector)
            
            if (i + 1) % 50 == 0:
                print(f"  Embedded {i + 1}/{len(chunks)} chunks")
        
        return vectors
    
    def upsert_vectors_safe(self, vectors: List[Dict]):
        """Safely upsert vectors with automatic batch size reduction"""
        batch_size = 20
        
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i+batch_size]
            
            try:
                self.index.upsert(vectors=batch)
            except Exception as e:
                if "message length too large" in str(e):
                    print(f"  Batch too large, splitting into smaller pieces...")
                    
                    for j in range(0, len(batch), 5):
                        small_batch = batch[j:j+5]
                        try:
                            self.index.upsert(vectors=small_batch)
                        except Exception as e2:
                            print(f"  Error with micro-batch: {e2}")
                            
                            for single_vector in small_batch:
                                try:
                                    self.index.upsert(vectors=[single_vector])
                                except Exception as e3:
                                    print(f"  Skipping problematic vector: {e3}")
                else:
                    print(f"  Error upserting batch: {e}")
    
    def build_rag(self, md_dir: str, pdf_dir: str):
        print("Starting RAG build process")
        print(f"MD directory: {md_dir}")
        print(f"PDF directory: {pdf_dir}")
        
        all_files = []
        
        md_path = Path(md_dir)
        if md_path.exists():
            md_files = list(md_path.rglob("*.md")) + list(md_path.rglob("*.markdown"))
            all_files.extend(md_files)
            print(f"Found {len(md_files)} markdown files")
        
        pdf_path = Path(pdf_dir)
        if pdf_path.exists():
            pdf_files = list(pdf_path.rglob("*.pdf"))
            all_files.extend(pdf_files)
            print(f"Found {len(pdf_files)} PDF files")
        
        print(f"\nTotal files to process: {len(all_files)}\n")
        
        for file_num, filepath in enumerate(all_files, 1):
            print(f"\n[{file_num}/{len(all_files)}]")
            
            vectors = self.process_file(filepath)
            
            if vectors:
                print(f"Upserting {len(vectors)} vectors to Pinecone")
                self.upsert_vectors_safe(vectors)
        
        print("\n" + "="*50)
        print("RAG build complete")
        
        stats = self.index.describe_index_stats()
        print(f"Total vectors in index: {stats.total_vector_count}")
        print("="*50)


def main():
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    if not PINECONE_API_KEY or not OPENAI_API_KEY:
        print("Error: Set PINECONE_API_KEY and OPENAI_API_KEY in .env file")
        return
    
    MD_DIR = "./md"
    PDF_DIR = "./pdf"
    
    builder = RAGBuilder(
        pinecone_api_key=PINECONE_API_KEY,
        openai_api_key=OPENAI_API_KEY,
        index_name="architecture-kb"
    )
    
    builder.build_rag(md_dir=MD_DIR, pdf_dir=PDF_DIR)


if __name__ == "__main__":
    main()