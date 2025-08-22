import asyncio
import json
import os
import unittest
from evaluation.run_evaluation import run_evaluation_pipeline, RESULTS_PATH

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