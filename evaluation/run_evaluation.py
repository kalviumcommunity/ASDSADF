import json
import asyncio
import logging
from typing import Dict, Any, Tuple

# This is a relative import. You must run this script as a module.
# python -m evaluation.run_evaluation
from src.models import UserQuery
from src.asdsadf_agent import ASASSDFAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_response(response: Dict, expected: Dict) -> Tuple[bool, str]:
    """Validate the agent's response against expected criteria."""
    if "error" in response:
        return False, f"Agent returned an error: {response['error']}"

    if "user_profile" in expected:
        profile = response.get("user_profile", {})
        for key, value in expected["user_profile"].items():
            if key not in profile or value not in profile[key]:
                return False, f"FAIL: Expected '{value}' in user_profile.{key}, got '{profile.get(key)}'"

    if "roadmap" in expected:
        roadmap = response.get("roadmap", {})
        phases = roadmap.get("phases", [])
        if "phases_count" in expected["roadmap"] and len(phases) < expected["roadmap"]["phases_count"]:
            return False, f"FAIL: Expected at least {expected['roadmap']['phases_count']} phases, got {len(phases)}"
        if "includes_module" in expected["roadmap"]:
            expected_module = expected["roadmap"]["includes_module"].lower()
            found = any(expected_module in m.get("module_name", "").lower() for p in phases for m in p.get("modules", []))
            if not found:
                return False, f"FAIL: Roadmap did not include module '{expected_module}'"
    
    if "reasoning_summary" in expected and expected["reasoning_summary"].get("exists"):
        if not response.get("reasoning_summary"):
            return False, "FAIL: Expected 'reasoning_summary' key to exist"

    return True, "PASS"

async def run_evaluation_pipeline(agent: ASASSDFAgent = None):
    """Run the evaluation pipeline against the dataset."""
    logger.info("====== STARTING EVALUATION PIPELINE ======")
    
    if agent is None:
        logger.info("Agent not passed, creating a new instance for evaluation.")
        agent = ASASSDFAgent()
        await agent.initialize()

    try:
        with open("evaluation/dataset.json", "r", encoding='utf-8') as f:
            dataset = json.load(f)
    except FileNotFoundError:
        logger.error("evaluation/dataset.json not found! Exiting.")
        return

    results = []
    for i, sample in enumerate(dataset["samples"]):
        logger.info(f"--- Running test ({i+1}/{len(dataset['samples'])}): {sample['id']} ---")
        
        query = UserQuery(message=sample["user_prompt"], prompt_type=sample["prompt_type"])
        response = await agent.process_query(query)

        is_valid, reason = validate_response(response, sample["expected"])
        results.append({"id": sample["id"], "status": "PASS" if is_valid else "FAIL", "reason": reason})
        logger.info(f"Status: {'PASS' if is_valid else 'FAIL'}. Reason: {reason}\n")

    logger.info("====== EVALUATION COMPLETE ======")
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    logger.info(f"Summary: {pass_count}/{len(results)} tests passed.")
    for res in results:
        logger.info(f"  - [{res['status']}] {res['id']}")

if __name__ == "__main__":
    asyncio.run(run_evaluation_pipeline())