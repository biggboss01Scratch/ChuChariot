"""Verify the recorded content audit and its deliberately limited repairs."""

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from chuchariot.dataset_io import ROOT, read_json, write_json
from chuchariot.preview import preview_data
from chuchariot.queries import KnowledgeStore
from chuchariot.validation import validate
from scripts.apply_source_audit_v07 import build, reports


class SourceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.ontology, cls.manifest, cls.summary, cls.audit = build()
        cls.previous = read_json(ROOT / "data/candidates/teacher-pdf.v0.6.json")
        cls.facts = {fact["id"]: fact for fact in cls.data["facts"]}
        cls.entities = {entity["id"]: entity for entity in cls.data["entities"]}

    def test_all_original_claims_are_adjudicated_exactly_once(self):
        rows = self.audit["fact_reviews"]
        self.assertEqual(len(rows), 272)
        self.assertEqual({row["fact_id"] for row in rows}, {fact["id"] for fact in self.previous["facts"]})
        self.assertEqual(self.summary["verdicts"], {"source_supported": 258, "needs_correction": 13, "insufficient_evidence": 1, "conflict": 0})
        self.assertTrue(all(row["auditor"] == "Codex" and not row["independent_review"] for row in rows))
        self.assertEqual(sum(len(source["reviewed_pages"]) for source in self.audit["source_reviews"]), 15)

    def test_dimensions_and_review_status_are_not_changed_by_content_repairs(self):
        old_dimensions = [fact for fact in self.previous["facts"] if fact["predicate"] == "HAS_DIMENSION"]
        self.assertEqual(len(old_dimensions), 54)
        for fact in old_dimensions:
            self.assertEqual(fact, self.facts[fact["id"]])
        self.assertTrue(all(fact["review_status"] == "pending" for fact in self.data["facts"]))
        self.assertEqual(KnowledgeStore(self.data, self.ontology).snapshot()["facts"], [])

    def test_diagram_membership_does_not_turn_into_unqualified_generic_composition(self):
        for ident in ["fact:001", "fact:002", "fact:003"]:
            self.assertEqual(self.facts[ident]["subject_id"], "record:wheel-axle-labels")
            self.assertEqual(self.facts[ident]["predicate"], "DEPICTS")
        self.assertFalse(any(fact["subject_id"] == "type:001" and fact["predicate"] == "HAS_PART" for fact in self.data["facts"]))

    def test_description_regions_are_not_physical_part_edges(self):
        for suffix in ["front", "middle", "rear"]:
            ident = "component:m1302-" + suffix
            self.assertEqual(self.entities[ident]["kind"], "ComponentRegion")
            self.assertEqual(self.entities[ident]["scope_id"], "specimen:004")
            links = [fact for fact in self.data["facts"] if fact.get("object_id") == ident]
            self.assertEqual([fact["predicate"] for fact in links], ["HAS_REGION"])
        wrong = copy.deepcopy(self.data)
        region = next(fact for fact in wrong["facts"] if fact["predicate"] == "HAS_REGION")
        region["subject_id"] = "specimen:001"
        self.assertTrue(any("跨标本" in error for error in validate(wrong, self.ontology)))

    def test_lacquer_and_motif_are_on_the_bone_cap_and_duplicates_remain_traceable(self):
        for retained in ["fact:035", "fact:038"]:
            self.assertEqual(self.facts[retained]["subject_id"], "component:m1257-bone-cap")
            self.assertEqual(set(self.facts[retained]["evidence_ids"]), {"evidence:019", "evidence:pdf-p07-t02"})
        self.assertNotIn("fact:pdf-191", self.facts)
        self.assertNotIn("fact:pdf-192", self.facts)
        self.assertEqual(len(self.data["facts"]), 270)
        self.assertEqual({merge["removed_fact_id"] for merge in self.summary["merged_duplicates"]}, {"fact:pdf-191", "fact:pdf-192"})
        for merge in self.summary["merged_duplicates"]:
            self.assertIn(merge["retained_fact_id"], self.facts)
            self.assertEqual(merge["removed_fact"]["id"], merge["removed_fact_id"])

    def test_unsupported_statistical_wording_is_removed_without_changing_counts(self):
        statement = self.facts["fact:pdf-089"]["value"]
        self.assertNotIn("登记", statement)
        self.assertIn("33件", statement)
        self.assertIn("现存22件", statement)
        self.assertIn("口径未注明", statement)

    def test_car_eight_identification_remains_pending_inference_with_explicit_limitation(self):
        fact = self.facts["fact:pdf-217"]
        self.assertEqual(fact["origin"], "inferred")
        self.assertEqual(fact["review_status"], "pending")
        self.assertIn("无独立", fact["rationale"])
        self.assertEqual(set(fact["evidence_ids"]), {"evidence:pdf-figure-02", "evidence:pdf-figure-03"})
        self.assertEqual(validate(self.data, self.ontology), [])

    def test_media_still_resolves_after_scoping_and_duplicate_merges(self):
        paths = ROOT / "data/candidates/teacher-pdf.v0.7.json", ROOT / "data/ontology/ontology.v0.5.json"
        manifest = ROOT / "data/sources/fusion-media.v0.7.json"
        visible = preview_data(*paths, review=True, media_manifest=manifest)
        self.assertEqual(len(visible["media"]), 25)
        self.assertEqual(len(visible["entities"]), 95)
        self.assertEqual(sum("object_id" in fact for fact in visible["facts"]), 107)
        hidden = preview_data(*paths, media_manifest=manifest)
        self.assertEqual(hidden["facts"], [])
        self.assertEqual(hidden["media"], [])

    def test_replay_refuses_missing_or_changed_original_audit_rows(self):
        for change in ["missing", "changed", "bad_verdict"]:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temporary:
                audit = copy.deepcopy(self.audit)
                if change == "missing":
                    audit["fact_reviews"].pop()
                elif change == "changed":
                    audit["fact_reviews"][0]["fact_before"]["predicate"] = "DESCRIPTION"
                else:
                    audit["fact_reviews"][0]["verdict"] = "unchecked"
                path = Path(temporary) / "audit.json"
                write_json(path, audit)
                with patch("scripts.apply_source_audit_v07.AUDIT_PATH", path), self.assertRaises(ValueError):
                    build()

    def test_report_lists_every_input_claim_and_does_not_claim_independent_review(self):
        report, coverage = reports(self.summary, self.audit)
        detail = report.split("## 全部272条逐条判定")[1]
        for fact in self.previous["facts"]:
            self.assertIn("`" + fact["id"] + "`", detail)
        self.assertIn("不是独立Agent", report)
        self.assertIn("不代表资料提取召回率100%", coverage)


if __name__ == "__main__":
    unittest.main()
