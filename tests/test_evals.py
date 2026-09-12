import runpy
import unittest
from pathlib import Path


class RetrievalEvaluations(unittest.TestCase):
    def test_task_evidence_is_retrievable_with_faithful_quotes_and_bounded_text(self):
        module = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'evals/run.py'))
        reports = module['evaluate']()
        self.assertEqual(len(reports), 5)
        for report in reports:
            with self.subTest(task=report['task']):
                self.assertTrue(report['retrieval_passed'], report)
                self.assertEqual(report['agent_answer_quality'], 'not_evaluated')
