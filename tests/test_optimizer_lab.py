import json
import unittest

from src.optimizer_lab import (
    Measurement,
    break_even_runs,
    canonical_result_hash,
    decide,
    parse_proposal,
    validate_read_only_sql,
)


class OptimizerLabTests(unittest.TestCase):
    def test_parses_strict_proposal(self):
        proposal = parse_proposal(
            json.dumps(
                {
                    "engine": "Athena",
                    "sql": "SELECT category, sum(amount) FROM events GROUP BY 1",
                    "rationale": "Project only required columns.",
                    "assumptions": ["events is immutable during validation"],
                }
            )
        )
        self.assertEqual("athena", proposal.engine)

    def test_rejects_extra_proposal_fields(self):
        with self.assertRaises(ValueError):
            parse_proposal(
                json.dumps(
                    {
                        "engine": "athena",
                        "sql": "SELECT 1",
                        "rationale": "test",
                        "assumptions": [],
                        "execute": True,
                    }
                )
            )

    def test_rejects_destructive_sql(self):
        reasons = validate_read_only_sql(
            "DROP TABLE events",
            allowed_tables={"events"},
            engine="athena",
        )
        self.assertTrue(reasons)

    def test_rejects_multiple_statements(self):
        reasons = validate_read_only_sql(
            "SELECT * FROM events; DROP TABLE events",
            allowed_tables={"events"},
            engine="athena",
        )
        self.assertIn("comments and statement separators are prohibited", reasons)

    def test_rejects_unknown_table(self):
        reasons = validate_read_only_sql(
            "SELECT * FROM secrets",
            allowed_tables={"events"},
            engine="athena",
        )
        self.assertTrue(any("unknown tables" in reason for reason in reasons))

    def test_accepts_separately_quoted_qualified_table(self):
        reasons = validate_read_only_sql(
            'SELECT * FROM "catalog/bucket"."lab"."events"',
            allowed_tables={"catalog/bucket.lab.events"},
            engine="athena",
        )
        self.assertEqual((), reasons)

    def test_hash_is_order_independent_by_default(self):
        self.assertEqual(
            canonical_result_hash([[1, "a"], [2, "b"]]),
            canonical_result_hash([[2, "b"], [1, "a"]]),
        )

    def test_hash_can_be_order_sensitive(self):
        self.assertNotEqual(
            canonical_result_hash([[1], [2]], order_sensitive=True),
            canonical_result_hash([[2], [1]], order_sensitive=True),
        )

    def test_accepts_equivalent_lower_scan_candidate(self):
        baseline = Measurement("athena", 1000, 100, "same", 3)
        candidate = Measurement("athena", 400, 80, "same", 3)
        verdict = decide(baseline, candidate)
        self.assertTrue(verdict.accepted)
        self.assertAlmostEqual(0.6, verdict.savings_fraction)

    def test_rejects_semantic_change(self):
        baseline = Measurement("athena", 1000, 100, "a", 3)
        candidate = Measurement("athena", 100, 20, "b", 3)
        self.assertFalse(decide(baseline, candidate).accepted)

    def test_break_even_rounds_up(self):
        self.assertEqual(
            3,
            break_even_runs(
                ai_review_cost_usd=0.02,
                validation_cost_usd=0.01,
                savings_per_run_usd=0.012,
            ),
        )

    def test_no_break_even_without_savings(self):
        self.assertIsNone(
            break_even_runs(
                ai_review_cost_usd=0.02,
                validation_cost_usd=0.01,
                savings_per_run_usd=0,
            )
        )


if __name__ == "__main__":
    unittest.main()

