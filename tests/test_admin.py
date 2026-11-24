"""Import triage against the project graph and publication controls."""

import unittest

try:
    from chuchariot.admin.ingestion import ImportReview, Proposal, UploadedText
except ModuleNotFoundError as exc:
    raise unittest.SkipTest("Install backend dependencies for admin tests") from exc

from chuchariot.dataset_io import ROOT, read_json


DATA = read_json(ROOT / "data/candidates/knowledge.v0.11.json")
ONTOLOGY = read_json(ROOT / "data/ontology/ontology.v0.7.json")
SAMPLE = "CH1：5轮右轮横径合1320毫米。\nCH1：5轮右轮横径复测为135厘米。\n轴通长276厘米。"


def dimension(subject, quantity, value, quote, unit="cm", **extra):
    return Proposal(subject=subject, predicate="HAS_DIMENSION", quote=quote,
                    value={"quantity": quantity, "unit": unit, "raw": quote, "approximate": False, "value": value},
                    **extra)


class ImportReviewTests(unittest.TestCase):
    def setUp(self):
        self.subject = {"id": "specimen:001", "label": "CH1：5轮标本"}
        self.review = ImportReview(DATA, ONTOLOGY, UploadedText(filename="校样.md", text=SAMPLE))

    def test_same_specimen_and_project_normalize_units(self):
        duplicate = dimension(self.subject, "右轮横径", 1320, SAMPLE.splitlines()[0], "mm")
        conflict = dimension(self.subject, "右轮横径", 135, SAMPLE.splitlines()[1])
        different = dimension({"label": "QA-TEST 新轮", "kind": "ReferenceSpecimen"},
                              "右轮横径", 135, SAMPLE.splitlines()[1])
        self.assertEqual(self.review.assess(duplicate).status, "duplicate")
        self.assertEqual(self.review.assess(conflict).status, "conflict")
        self.assertEqual(self.review.assess(different).status, "new")
        self.assertEqual(self.review.assess(duplicate).matches[0]["id"], "fact:006")
        self.assertEqual(self.review.assess(conflict).evidence["start_line"], 2)

    def test_unnumbered_axle_and_unsupported_numbers_require_review(self):
        unnumbered = next(e for e in DATA["entities"] if e["label"] == "第4页未编号轴记录")
        unscoped = dimension({"id": unnumbered["id"], "label": unnumbered["label"]},
                             "通长", 276, SAMPLE.splitlines()[2])
        self.assertEqual(self.review.assess(unscoped).status, "needs_review")
        checked = unscoped.model_copy(update={"scope_confirmed": True})
        self.assertEqual(self.review.assess(checked).status, "duplicate")
        fabricated = dimension(self.subject, "右轮横径", 999, SAMPLE.splitlines()[0])
        self.assertIn("出现在原文", self.review.assess(fabricated).message)
        false_quote = dimension(self.subject, "右轮横径", 999, "横径999厘米。")
        self.assertEqual(self.review.assess(false_quote).status, "needs_review")
