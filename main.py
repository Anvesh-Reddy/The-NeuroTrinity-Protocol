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

def call_specialist_agent(name: str, system_prompt: str, user_input: str) -> SpecialistRecommendation:
    """Call a specialist agent and return structured output."""
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=user_input,
        config=genai.types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_json_schema=SpecialistRecommendation.model_json_schema()
        )
    )
    return SpecialistRecommendation.model_validate_json(response.text)

def run_neuro_trinity_protocol(user_input: str, health_data: str) -> ConsolidatedPlan:
    """Executes the Parallel -> Synthesis multi-agent workflow."""
    full_prompt = f"""
    --- USER REQUEST ---
    {user_input}

    --- USER HEALTH DATA (Wearables/EHR) ---
    {health_data}

    Analyze the data and provide your specialized recommendation.
    """

    print("Running Parallel Agent Analysis...")
    architect_output = call_specialist_agent("The Architect", ARCHITECT_PROMPT, full_prompt)
    alchemist_output = call_specialist_agent("The Alchemist", ALCHEMIST_PROMPT, full_prompt)
    trainer_output = call_specialist_agent("The Trainer", TRAINER_PROMPT, full_prompt)

    concierge_input = f"""
    The following are the raw JSON recommendations from the three specialist agents. 
    Your task is to synthesize this into a single, cohesive, prioritized ConsolidatedPlan JSON object:

    Architect Output: {architect_output.model_dump_json()}
    Alchemist Output: {alchemist_output.model_dump_json()}
    Trainer Output: {trainer_output.model_dump_json()}
    """

    print("\nRunning Prime Concierge Synthesis...")
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
    return final_plan

if __name__ == "__main__":
    user_query = "I woke up groggy, and I have a huge presentation today. My doctor stressed managing my blood pressure."
    mock_health_data = """
    - Sleep Tracker: Deep Sleep: 15% (Target: 25%). Heart Rate Variability (HRV): Low.
    - Activity: 500 steps.
    - Vitals (Today AM): Blood Pressure 145/95 mmHg (High).
    - Diet Log (Yesterday): High sodium, high caffeine.
    """
    
    print(f"--- PROTOCOL START: Analyzing user request and health data... ---\n")
    final_result = run_neuro_trinity_protocol(user_query, mock_health_data)
    
    print("\n\n--- FINAL SYNTHESIZED NEUROTRINITY PLAN ---")
    print(f"**Executive Summary:** {final_result.executive_summary}\n")
    
    for i, rec in enumerate(final_result.prioritized_actions):
        print(f"**{i+1}. {rec.priority_level} ({rec.agent_name})**")
        print(f"   Instruction: {rec.instruction}")
        print(f"   Rationale: {rec.rationale} (Domain: {rec.domain_category})\n")
    
    print("--- PROTOCOL END ---")
