"""Audience projection hides bookkeeping without changing knowledge or review."""

import copy
import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from chuchariot.dataset_io import ROOT, read_json
from chuchariot.presentation import project_presentation
from chuchariot.preview import make_server, preview_data
from chuchariot.queries import KnowledgeStore


class PresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = ROOT / "data/candidates/knowledge.v0.11.json"
        cls.ontology = ROOT / "data/ontology/ontology.v0.7.json"
        cls.data = read_json(cls.dataset)
        cls.store = KnowledgeStore.load(cls.dataset, cls.ontology)
        cls.raw = cls.store.snapshot(True)

    def test_internal_projection_keeps_every_record(self):
        view = project_presentation(self.data, self.raw, "internal")
        for name in ("entities", "facts", "evidence", "sources", "mappings", "stats"):
            self.assertEqual(view[name], self.raw[name])
        grouped = [ident for group in view["presentation"]["groups"] for ident in group["fact_ids"]]
        self.assertEqual(set(grouped), {f["id"] for f in self.raw["facts"] if "object_id" in f})
        self.assertEqual(len(grouped), len(set(grouped)))

    def test_public_mode_hides_management_nodes_and_relations(self):
        public = project_presentation(self.data, self.raw, "public")
        hidden = {"Subsystem", "EvidenceBasisClass", "Connection", "ModelVersion", "TermSense"}
        self.assertFalse(any(e["kind"] in hidden for e in public["entities"]))
        forbidden = {"INSTANCE_OF", "IN_SUBSYSTEM", "SUBCLASS_OF", "TEACHING_GROUPS_TYPE", "SCHEMATIC_NEXT",
                     "CONNECTION_FROM", "CONNECTION_TO", "HAS_EVIDENCE_BASIS", "USES_TERM", "TERM_DENOTES", "TERM_RELATED_TO", "DEPICTS"}
        self.assertFalse(any(f["predicate"] in forbidden for f in public["facts"]))
        self.assertEqual({g["id"] for g in public["presentation"]["groups"]}, {"structure", "appearance", "reconstruction"})
        self.assertEqual(public["mappings"], [])

    def test_public_cases_keep_inference_and_evidence(self):
        public = project_presentation(self.data, self.raw, "public")
        facts = {f["id"]: f for f in public["facts"]}
        hypothesis = "fact:video1-tenon-explanation-description"
        self.assertEqual(facts[hypothesis], next(f for f in self.data["facts"] if f["id"] == hypothesis))
        self.assertEqual(facts[hypothesis]["origin"], "hypothesis")
        self.assertEqual(facts[hypothesis]["review_status"], "pending")
        cases = [e for e in public["entities"] if e["kind"] == "ReferenceRecord"]
        self.assertEqual(len(cases), 6)
        for fact in public["facts"]:
            self.assertIn(fact["subject_id"], {e["id"] for e in public["entities"]})
            self.assertLessEqual(set(fact["evidence_ids"]), {e["id"] for e in public["evidence"]})
        self.assertTrue(any(e.get("start_seconds") == 1528 for e in public["evidence"]))
        group = next(g for g in public["presentation"]["groups"] if g["id"] == "reconstruction")
        self.assertIn("fact:video1-tenon-explanation-type-1", group["fact_ids"])

    def test_review_visibility_is_independent_and_source_is_not_modified(self):
        initial = copy.deepcopy(self.data)
        confirmed = project_presentation(self.data, self.store.snapshot(False), "public")
        self.assertEqual(confirmed["facts"], [])
        self.assertEqual(confirmed["evidence"], [])
        self.assertEqual(confirmed["stats"]["dimension_properties"], 0)
        public = project_presentation(self.data, self.raw, "public")
        public["entities"][0]["label"] = "mutation"
        self.assertEqual(self.data, initial)

    def test_unclassified_new_relations_are_internal_by_default(self):
        data, snapshot = copy.deepcopy(self.data), copy.deepcopy(self.raw)
        for collection in (data["facts"], snapshot["facts"]):
            next(f for f in collection if f["id"] == "fact:pdf-123")["predicate"] = "NEW_UNCLASSIFIED_RELATION"
        public = project_presentation(data, snapshot, "public")
        self.assertFalse(any(f["predicate"] == "NEW_UNCLASSIFIED_RELATION" for f in public["facts"]))

    def test_media_and_layout_hints_do_not_reintroduce_hidden_entities(self):
        result = preview_data(self.dataset, self.ontology, True, audience="public",
                              media_manifest=ROOT / "data/sources/fusion-media.v0.11.json")
        ids = {e["id"] for e in result["entities"]}
        self.assertEqual(set(result["presentation"]["regions"]), ids)
        self.assertEqual(result["presentation"]["regions"]["specimen:001"], "wheel")
        self.assertEqual(result["presentation"]["regions"]["component:ch15-spoke-inner"], "wheel")
        for media in result["media"]:
            self.assertEqual(media["kind"], "source_clip")
            self.assertLessEqual(set(media["entity_ids"]), ids)
        self.assertEqual(result["stats"]["facts"], len(result["facts"]))

    def test_http_audience_validation_and_projection(self):
        server = make_server(0, self.dataset, self.ontology)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}/api/preview?review=1"
        try:
            with urlopen(base + "&audience=public", timeout=3) as response:
                data = json.load(response)
            self.assertEqual(data["presentation"]["audience"], "public")
            self.assertLess(len(data["facts"]), 423)
            with urlopen(base + "&audience=internal", timeout=3) as response:
                self.assertEqual(len(json.load(response)["facts"]), 423)
            for suffix in ["&audience=invalid", "&audience=", "&audience=public&audience=internal"]:
                with self.subTest(suffix=suffix), self.assertRaises(HTTPError) as error:
                    urlopen(base + suffix, timeout=3)
                self.assertEqual(error.exception.code, 400)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
