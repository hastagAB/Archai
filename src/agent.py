import os
from typing import List, Dict
from anthropic import Anthropic
from dotenv import load_dotenv
from rag_retriever import RAGRetriever
from sub_agents import SecurityAgent, CostAgent, PerformanceAgent

load_dotenv()

class ArchitectureReviewerAgent:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.rag = RAGRetriever()
        self.security_agent = SecurityAgent()
        self.cost_agent = CostAgent()
        self.performance_agent = PerformanceAgent()
        
        self.system_prompt = """You are an expert Architecture Reviewer Agent.

Your reasoning process (ReAct):
1. THOUGHT: Think about what you need to analyze
2. ACTION: Use tools or sub-agents to gather information
3. OBSERVATION: Review the results
4. REFLECTION: Evaluate if analysis is complete
5. RESPONSE: Provide final recommendations

Available actions:
- RETRIEVE[query]: Search knowledge base for patterns/ADRs
- SECURITY_CHECK: Run security analysis
- COST_ANALYSIS: Run cost analysis  
- PERFORMANCE_CHECK: Run performance analysis

Format your response as:
THOUGHT: <your thinking>
ACTION: <action to take>
... (repeat until complete)
FINAL_ANSWER: <comprehensive review with recommendations>"""
    
    def review(self, architecture_description: str, max_iterations: int = 8) -> str:
        conversation = []
        conversation.append({
            "role": "user",
            "content": f"Review this architecture:\n\n{architecture_description}"
        })
        
        full_trace = []
        
        for iteration in range(max_iterations):
            print(f"\n--- Iteration {iteration + 1} ---")
            
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                temperature=0.2,
                system=self.system_prompt,
                messages=conversation
            )
            
            assistant_message = response.content[0].text
            print(f"\nAgent: {assistant_message[:500]}...")
            
            conversation.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            full_trace.append(assistant_message)
            
            if "FINAL_ANSWER:" in assistant_message:
                print("\n--- Review Complete ---")
                return "\n\n".join(full_trace)
            
            observation = self.execute_action(assistant_message, architecture_description)
            
            if observation:
                print(f"\nObservation: {observation[:300]}...")
                conversation.append({
                    "role": "user",
                    "content": f"OBSERVATION: {observation}\n\nContinue your analysis."
                })
            else:
                conversation.append({
                    "role": "user",
                    "content": "Continue your analysis or provide FINAL_ANSWER."
                })
        
        return "\n\n".join(full_trace)
    
    def execute_action(self, message: str, architecture_info: str) -> str:
        if "RETRIEVE[" in message:
            query_start = message.find("RETRIEVE[") + 9
            query_end = message.find("]", query_start)
            query = message[query_start:query_end]
            
            print(f"\nExecuting RAG retrieval: {query}")
            docs = self.rag.retrieve(query, top_k=3)
            
            result = "Retrieved documents:\n"
            for i, doc in enumerate(docs, 1):
                result += f"\n{i}. Source: {doc['source']}\n"
                result += f"   Content: {doc['text'][:500]}...\n"
            
            return result
        
        elif "SECURITY_CHECK" in message:
            print("\nExecuting Security Analysis...")
            return self.security_agent.analyze(architecture_info)
        
        elif "COST_ANALYSIS" in message:
            print("\nExecuting Cost Analysis...")
            return self.cost_agent.analyze(architecture_info)
        
        elif "PERFORMANCE_CHECK" in message:
            print("\nExecuting Performance Analysis...")
            return self.performance_agent.analyze(architecture_info)
        
        return ""