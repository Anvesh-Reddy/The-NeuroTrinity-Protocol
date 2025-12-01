# main.py
import os
import json
from google import genai
from data_models import SpecialistRecommendation, ConsolidatedPlan
from agent_prompts import ARCHITECT_PROMPT, ALCHEMIST_PROMPT, TRAINER_PROMPT, CONCIERGE_PROMPT
from dotenv import load_dotenv

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

class NeuroTrinityChat:
    def __init__(self):
        self.conversation_history = []
        self.specialist_history = {
            "architect": [],
            "alchemist": [],
            "trainer": []
        }
    
    def call_specialist_agent(self, name: str, system_prompt: str, user_input: str, search_results: str = "") -> SpecialistRecommendation:
        """Call a specialist agent with conversation history and optional search results."""
        history_key = name.lower().replace(" ", "_")
        
        if search_results:
            user_input = f"{user_input}\n\nInternet Research Data:\n{search_results}"
        
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
        """Execute the NeuroTrinity protocol with memory and internet search."""
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
        
        architect_output = self.call_specialist_agent("The Architect", ARCHITECT_PROMPT, full_prompt, search_results)
        alchemist_output = self.call_specialist_agent("The Alchemist", ALCHEMIST_PROMPT, full_prompt, search_results)
        trainer_output = self.call_specialist_agent("The Trainer", TRAINER_PROMPT, full_prompt, search_results)

        concierge_input = f"""
        Previous conversation context: {json.dumps(self.conversation_history[-2:]) if self.conversation_history else 'None'}
        
        Internet Research Data Used: {search_results[:500]}...
        
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
            "plan": final_plan.model_dump()
        })
        
        return final_plan
    
    def chat(self):
        """Interactive chat loop."""
        print("=== NeuroTrinity Protocol - Continuous Chat ===")
        print("Type 'quit' to exit, 'history' to see conversation history\n")
        
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
