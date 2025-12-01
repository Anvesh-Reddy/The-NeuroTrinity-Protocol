# main.py
import os
import json
from google import genai
from data_models import SpecialistRecommendation, ConsolidatedPlan
from agent_prompts import ARCHITECT_PROMPT, ALCHEMIST_PROMPT, TRAINER_PROMPT, CONCIERGE_PROMPT
from dotenv import load_dotenv
import numpy as np
from pathlib import Path
import chardet

load_dotenv("keys.env")

if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY must be set in environment variables.")

client = genai.Client()
MODEL_ID = "gemini-2.5-flash"

def search_internet(query: str, max_results: int = 3) -> str:
    """Search internet using DuckDuckGo and return results."""
    try:
        from duckduckgo_search import DDGS
        ddgs = DDGS()
        results = ddgs.text(query, max_results=max_results)
        
        search_summary = f"Search results for '{query}':\n"
        for i, result in enumerate(results, 1):
            search_summary += f"{i}. {result.get('title', 'N/A')}\n"
            search_summary += f"   {result.get('body', 'N/A')}\n"
        return search_summary
    except ImportError:
        return f"Search unavailable. Query was: {query}"
    except Exception as e:
        return f"Search error: {str(e)}"

class RAGDatabase:
    """Simple in-memory RAG database with embeddings."""
    def __init__(self):
        self.documents = []
        self.embeddings = []
    
    def add_document(self, text: str):
        """Add document and generate embedding."""
        self.documents.append(text)
        embedding = self.get_embedding(text)
        self.embeddings.append(embedding)
    
    def get_embedding(self, text: str) -> list:
        """Get embedding using Gemini API."""
        try:
            result = client.models.embed_content(
                model="models/text-embedding-004",
                content=text
            )
            return result['embedding']
        except:
            return [0] * 768
    
    def retrieve_relevant(self, query: str, top_k: int = 3) -> str:
        """Retrieve top-k relevant documents using cosine similarity."""
        if not self.documents:
            return "No documents in database."
        
        query_embedding = self.get_embedding(query)
        similarities = []
        
        for doc_embedding in self.embeddings:
            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding) + 1e-10
            )
            similarities.append(similarity)
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        relevant_docs = [self.documents[i] for i in top_indices if similarities[i] > 0.3]
        
        if not relevant_docs:
            return "No relevant documents found."
        
        return "Relevant user documents:\n" + "\n---\n".join(relevant_docs[:top_k])

class NeuroTrinityChat:
    def __init__(self):
        self.conversation_history = []
        self.specialist_history = {
            "architect": [],
            "alchemist": [],
            "trainer": []
        }
        self.rag_db = RAGDatabase()
    
    def load_user_documents(self, file_path: str):
        """Load documents from file with automatic encoding detection."""
        try:
            path = Path(file_path)
            if path.is_file():
                with open(path, 'rb') as f:
                    raw_data = f.read()
                
                detected = chardet.detect(raw_data)
                encoding = detected.get('encoding', 'utf-8') or 'utf-8'
                
                try:
                    content = raw_data.decode(encoding)
                except (UnicodeDecodeError, LookupError):
                    content = raw_data.decode('utf-8', errors='ignore')
                
                chunks = content.split('\n\n')
                for chunk in chunks:
                    if chunk.strip():
                        self.rag_db.add_document(chunk.strip())
                print(f"Loaded {len(chunks)} documents from {file_path}")
            else:
                print(f"File not found: {file_path}")
        except Exception as e:
            print(f"Error loading documents: {e}")
    
    def call_specialist_agent(self, name: str, system_prompt: str, user_input: str, search_results: str = "", rag_context: str = "") -> SpecialistRecommendation:
        """Call a specialist agent with conversation history, search results, and RAG context."""
        history_key = name.lower().replace(" ", "_")
        
        context_parts = [user_input]
        if search_results:
            context_parts.append(f"Internet Research Data:\n{search_results}")
        if rag_context:
            context_parts.append(f"User Knowledge Base:\n{rag_context}")
        
        user_input = "\n\n".join(context_parts)
        
        messages = self.specialist_history.get(history_key, [])
        messages.append({"role": "user", "parts": [{"text": user_input}]})
        
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=messages,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_json_schema=SpecialistRecommendation.model_json_schema()
            )
        )
        
        messages.append({"role": "model", "parts": [{"text": response.text}]})
        self.specialist_history[history_key] = messages[-2:]
        
        return SpecialistRecommendation.model_validate_json(response.text)
    
    def run_protocol(self, user_input: str, health_data: str) -> ConsolidatedPlan:
        """Execute the NeuroTrinity protocol with memory, internet search, and RAG."""
        full_prompt = f"""
        --- USER REQUEST ---
        {user_input}

        --- USER HEALTH DATA (Wearables/EHR) ---
        {health_data}

        Analyze the data and provide your specialized recommendation.
        """

        print("Running Parallel Agent Analysis...")
        
        print("  Searching internet for relevant data...")
        search_results = search_internet(user_input)
        
        print("  Retrieving relevant user documents...")
        rag_context = self.rag_db.retrieve_relevant(user_input)
        
        architect_output = self.call_specialist_agent("The Architect", ARCHITECT_PROMPT, full_prompt, search_results, rag_context)
        alchemist_output = self.call_specialist_agent("The Alchemist", ALCHEMIST_PROMPT, full_prompt, search_results, rag_context)
        trainer_output = self.call_specialist_agent("The Trainer", TRAINER_PROMPT, full_prompt, search_results, rag_context)

        concierge_input = f"""
        Previous conversation context: {json.dumps(self.conversation_history[-2:]) if self.conversation_history else 'None'}
        
        Internet Research Data Used: {search_results[:300]}...
        User Knowledge Base Used: {rag_context[:300]}...
        
        The following are the raw JSON recommendations from the three specialist agents. 
        Your task is to synthesize this into a single, cohesive, prioritized ConsolidatedPlan JSON object:

        Architect Output: {architect_output.model_dump_json()}
        Alchemist Output: {alchemist_output.model_dump_json()}
        Trainer Output: {trainer_output.model_dump_json()}
        """

        print("Running Prime Concierge Synthesis...")
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=concierge_input,
            config=genai.types.GenerateContentConfig(
                system_instruction=CONCIERGE_PROMPT,
                response_mime_type="application/json",
                response_json_schema=ConsolidatedPlan.model_json_schema()
            )
        )
        
        final_plan = ConsolidatedPlan.model_validate_json(response.text)
        
        self.conversation_history.append({
            "user_input": user_input,
            "health_data": health_data,
            "search_data": search_results[:200],
            "rag_data": rag_context[:200],
            "plan": final_plan.model_dump()
        })
        
        return final_plan
    
    def chat(self):
        """Interactive chat loop."""
        print("=== NeuroTrinity Protocol - Continuous Chat with RAG ===")
        print("Commands: 'quit' to exit, 'history' to see history, 'load <file>' to load documents\n")
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() == "quit":
                print("Goodbye!")
                break
            
            if user_input.lower() == "history":
                print("\n--- Conversation History ---")
                for i, entry in enumerate(self.conversation_history, 1):
                    print(f"\n[Session {i}]")
                    print(f"Request: {entry['user_input']}")
                    print(f"Summary: {entry['plan'].get('executive_summary', 'N/A')}")
                print()
                continue
            
            if user_input.lower().startswith("load "):
                file_path = user_input[5:].strip()
                self.load_user_documents(file_path)
                continue
            
            health_data = input("Health Data (or press Enter to skip): ").strip()
            if not health_data:
                health_data = "No specific health data provided."
            
            try:
                final_result = self.run_protocol(user_input, health_data)
                
                print("\n--- SYNTHESIZED PLAN ---")
                print(f"Executive Summary: {final_result.executive_summary}\n")
                
                for i, rec in enumerate(final_result.prioritized_actions, 1):
                    print(f"{i}. [{rec.priority_level}] {rec.instruction}")
                    print(f"   Agent: {rec.agent_name} | Domain: {rec.domain_category}")
                    print(f"   Rationale: {rec.rationale}\n")
                
            except Exception as e:
                print(f"Error: {e}\n")

if __name__ == "__main__":
    chat_app = NeuroTrinityChat()
    chat_app.chat()
