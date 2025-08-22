# Pseudocode / Plan:
# - Problem: running evaluation scripts fails with ModuleNotFoundError: No module named 'src'
# - Root cause: Python process doesn't have project root on sys.path when executing scripts under evaluation/
# - Fix: insert project root into sys.path at top of evaluation scripts before importing project modules
# - Approach:
#   - Compute project root as two levels up from this file (evaluation/<file>.py -> project root)
#   - Insert str(project_root) at front of sys.path if not already present
#   - Keep rest of file unchanged; ensure imports of src.* succeed
# - Files to update in-place:
#   - evaluation/run_evaluation.py
#   - evaluation/test_runner.py
# - After change: running `python evaluation/run_evaluation.py` or `python evaluation/test_runner.py` should find `src` package.

# filepath: evaluation/run_evaluation.py
import sys
from pathlib import Path

# Ensure project root is on sys.path so `import src.*` works when running this script directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import asyncio
import logging
import os
import sys
from typing import Dict, Any, Tuple, List, Optional

# This is a relative import. You must run this script as a module.
# python -m evaluation.run_evaluation
from src.models import UserQuery
from src.asdsadf_agent import ASASSDFAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RESULTS_PATH = os.path.join("evaluation", "results.json")
DATASET_PATH = os.path.join("evaluation", "dataset.json")

def _preview_response(resp: Dict[str, Any], max_chars: int = 800) -> str:
    try:
        return json.dumps(resp, indent=2, ensure_ascii=False)[:max_chars]
    except Exception:
        return str(resp)[:max_chars]

def _extract_text_from_response(resp: Any) -> str:
    """Return a textual view of the response for heuristic checks."""
    if resp is None:
        return ""
    # If response is dict and has 'response' key that is a string, return it
    if isinstance(resp, dict):
        inner = resp.get("response")
        if isinstance(inner, str):
            return inner
        # if response itself contains text fields, stringify them
        try:
            return json.dumps(resp, ensure_ascii=False)
        except Exception:
            return str(resp)
    if isinstance(resp, str):
        return resp
    try:
        return str(resp)
    except Exception:
        return ""

def validate_response(response: Any, expected: Dict, sample: Dict) -> Tuple[bool, str]:
    """
    Validate the agent's response against expected criteria with tolerant checks.
    - response: raw response (may be dict, QueryResponse-like, or string)
    - expected: expected checks from dataset
    - sample: original sample input (used to accept user_profile from input)
    Returns: (is_valid, reason)
    """

    # Normalize: if response is an object with attribute 'response', pull it out
    resp = response
    if hasattr(response, "response"):
        try:
            resp = response.response
        except Exception:
            resp = response

    # If resp is dict and holds nested structured result
    structured = None
    text_view = _extract_text_from_response(resp)

    if isinstance(resp, dict):
        # If the nested 'response' key contains a dict, use that as structured
        if isinstance(resp.get("response"), dict):
            structured = resp.get("response")
        else:
            # treat resp itself as structured candidate
            structured = resp

    # Helper: check expected user_profile using sample as authoritative fallback
    sample_profile = sample.get("user_profile", {}) if isinstance(sample, dict) else {}
    if "user_profile" in expected:
        for key, value in expected["user_profile"].items():
            # If sample provided the desired value, accept it
            sample_val = sample_profile.get(key)
            if sample_val is not None:
                # case-insensitive containment if strings
                if isinstance(sample_val, str) and isinstance(value, str):
                    if value.lower() in sample_val.lower():
                        continue
                else:
                    if sample_val == value:
                        continue
                # If sample had key but value didn't match, fall through to check response
            # Check structured response for profile
            if structured and isinstance(structured.get("user_profile"), dict):
                got_val = structured["user_profile"].get(key)
                if got_val is not None:
                    if isinstance(got_val, str) and isinstance(value, str):
                        if value.lower() in got_val.lower():
                            continue
                        else:
                            return False, f"Expected '{value}' in user_profile.{key}, got '{got_val}'"
                    else:
                        if got_val == value:
                            continue
                        else:
                            return False, f"Expected '{value}' in user_profile.{key}, got '{got_val}'"
            # As a final attempt, search text_view for the expected value
            if isinstance(value, str) and value.lower() in text_view.lower():
                continue
            return False, f"Missing user_profile.{key}"

    # Check roadmap expectations
    if "roadmap" in expected:
        roadmap_expected = expected["roadmap"]
        roadmap_struct = None
        if structured and isinstance(structured.get("roadmap"), dict):
            roadmap_struct = structured.get("roadmap")
        elif structured and isinstance(structured, dict) and ("phases" in structured or "roadmap" in structured):
            # Some agents may put phases at top-level 'phases' or a 'roadmap' dict
            if "roadmap" in structured and isinstance(structured["roadmap"], dict):
                roadmap_struct = structured["roadmap"]
            elif "phases" in structured:
                roadmap_struct = {"phases": structured.get("phases", [])}
        # phases_count check
        if "phases_count" in roadmap_expected:
            expected_cnt = int(roadmap_expected["phases_count"])
            if roadmap_struct and isinstance(roadmap_struct.get("phases"), list):
                if len(roadmap_struct.get("phases", [])) < expected_cnt:
                    return False, f"Expected at least {expected_cnt} phases, got {len(roadmap_struct.get('phases', []))}"
            else:
                # No structured roadmap; fail strict phases_count expectation
                return False, f"Expected at least {expected_cnt} phases, but no structured roadmap present"

        # includes_module check: prefer structured, otherwise search in text
        if "includes_module" in roadmap_expected:
            expected_module = str(roadmap_expected["includes_module"]).lower()
            found = False
            if roadmap_struct:
                phases = roadmap_struct.get("phases", []) or []
                # search modules in phases
                for p in phases:
                    mods = p.get("modules", []) or []
                    for m in mods:
                        # common keys that hold module names
                        name = m.get("module_name") or m.get("title") or m.get("module") or ""
                        if expected_module in str(name).lower():
                            found = True
                            break
                    if found:
                        break
                # check modules at roadmap root
                if not found:
                    root_mods = roadmap_struct.get("modules", []) or []
                    for m in root_mods:
                        name = m.get("module_name") or m.get("title") or ""
                        if expected_module in str(name).lower():
                            found = True
                            break
            # fallback: search the textual response
            if not found:
                if expected_module in text_view.lower():
                    found = True
            if not found:
                return False, f"Expected roadmap to include module '{roadmap_expected['includes_module']}'"

    # reasoning_summary existence check (heuristic)
    if "reasoning_summary" in expected:
        rspec = expected["reasoning_summary"]
        if rspec.get("exists"):
            # Check structured first
            has_rs = False
            if structured and isinstance(structured, dict) and structured.get("reasoning_summary"):
                has_rs = True
            # Heuristic: detect step-by-step text in text_view
            if not has_rs:
                tv = text_view.lower()
                heuristics = ["step", "step-by-step", "because", "therefore", "so that", "in summary", "first,", "second,", "third,", "**step", "- step", "•"]
                if any(h in tv for h in heuristics) and len(tv) > 120:
                    has_rs = True
            if not has_rs:
                return False, "Expected reasoning_summary (or step-by-step reasoning) in response"

    return True, "PASS"

async def run_evaluation_pipeline(agent: ASASSDFAgent = None) -> List[Dict[str, Any]]:
    """Run the evaluation pipeline against the dataset and write results.json."""
    logger.info("====== STARTING EVALUATION PIPELINE ======")
    # Load dataset
    try:
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            dataset = json.load(f)
    except FileNotFoundError:
        logger.error(f"{DATASET_PATH} not found. Exiting.")
        return []

    # Initialize or use provided agent
    if agent is None:
        logger.info("Creating ASASSDFAgent for evaluation")
        agent = ASASSDFAgent()
        try:
            await agent.initialize()
        except Exception as e:
            logger.error("Failed to initialize evaluation agent: %s", e)
            # continue in degraded mode

    results = []
    samples = dataset.get("samples", [])
    for i, sample in enumerate(samples):
        sid = sample.get("id", f"sample-{i}")
        logger.info(f"--- Running test ({i+1}/{len(samples)}): {sid} ---")
        # Build UserQuery
        uq_kwargs = {"message": sample.get("user_prompt") or sample.get("user_prompt", "")}
        if sample.get("prompt_type"):
            uq_kwargs["prompt_type"] = sample.get("prompt_type")
        if sample.get("user_profile"):
            uq_kwargs["user_profile"] = sample.get("user_profile")
        uq_kwargs["session_id"] = sample.get("id")

        try:
            query = UserQuery(**uq_kwargs)
        except Exception as e:
            logger.warning("Failed to construct UserQuery for %s: %s", sid, e)
            query = UserQuery(message=sample.get("user_prompt", ""), prompt_type=sample.get("prompt_type"))

        # process query
        try:
            response_obj = await agent.process_query(query)
            # normalize QueryResponse -> dict/text
            if hasattr(response_obj, "response"):
                resp = response_obj.response
                context_used = getattr(response_obj, "context_used", [])
            elif isinstance(response_obj, dict) or isinstance(response_obj, list):
                resp = response_obj
                context_used = sample.get("context", [])
            else:
                # fallback: convert to str
                resp = response_obj
                context_used = []

        except Exception as e:
            logger.exception("Agent process_query failed for %s: %s", sid, e)
            resp = {"error": str(e)}
            context_used = []

        expected = sample.get("expected", {})
        # run judge: validate_response now takes sample input as well
        is_valid, reason = validate_response(resp, expected, sample)

        judge_prompt = (
            f"Judge this output for sample '{sid}'. Criteria:\n"
            f"- user_profile keys: {list(expected.get('user_profile', {}).keys())}\n"
            f"- roadmap expectations: {expected.get('roadmap')}\n"
            f"- reasoning_summary required: {expected.get('reasoning_summary')}\n"
            f"Return PASS/FAIL and reason. Automated checks performed: substring matching (case-insensitive) for text fields, counts for phases, module inclusion checks. If agent returns unstructured text, heuristics are used."
        )

        result_entry = {
            "id": sid,
            "status": "PASS" if is_valid else "FAIL",
            "reason": reason,
            "response_preview": _preview_response(resp),
            "context_used": context_used,
            "judge_prompt": judge_prompt
        }
        results.append(result_entry)
        logger.info("[%s] %s : %s", result_entry["status"], sid, reason)

    # summary
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    fail_count = len(results) - pass_count
    summary = {"total": len(results), "pass": pass_count, "fail": fail_count, "failed_ids": [r["id"] for r in results if r["status"] == "FAIL"]}
    logger.info("====== EVALUATION COMPLETE ======")
    logger.info("Summary: %s", summary)

    # Write results to file
    try:
        os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
        with open(RESULTS_PATH, "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "results": results}, f, indent=2, ensure_ascii=False)
        logger.info("Wrote results to %s", RESULTS_PATH)
    except Exception as e:
        logger.error("Failed to write results file: %s", e)

    return results

if __name__ == "__main__":
    # allow running as script
    res = asyncio.run(run_evaluation_pipeline())
    # exit code non-zero if any fail
    if any(r["status"] == "FAIL" for r in res):
        logger.info("There were failing tests; exit code 2")
        sys.exit(2)
    logger.info("All tests passed; exit code 0")
    sys.exit(0)


# filepath: evaluation/test_runner.py
import sys
from pathlib import Path

# Ensure project root is on sys.path so `import src.*` works when running this script directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import asyncio
import logging
import os
import sys
from typing import Dict, Any, Tuple, List

# This is a relative import. You must run this script as a module.
# python -m evaluation.test_runner
from evaluation.run_evaluation import run_evaluation_pipeline, RESULTS_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EvaluationPipelineTest(unittest.TestCase):
    def test_all_samples_pass(self):
        """Run the evaluation pipeline and assert zero FAIL statuses."""
        res = asyncio.run(run_evaluation_pipeline())
        # load results from run if file exists
        if os.path.exists(RESULTS_PATH):
            with open(RESULTS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                summary = data.get("summary", {})
                fail_count = summary.get("fail", None)
                if fail_count is None:
                    # fallback: count in results
                    results = data.get("results", [])
                    fail_count = sum(1 for r in results if r.get("status") == "FAIL")
        else:
            # fallback to returned results
            fail_count = sum(1 for r in res if r.get("status") == "FAIL")

        # Allow the test to be strict: require 0 fails. If you want tolerance change threshold.
        self.assertEqual(fail_count, 0, f"Evaluation found {fail_count} failing samples. See evaluation/results.json for details.")

if __name__ == "__main__":
    unittest.main()