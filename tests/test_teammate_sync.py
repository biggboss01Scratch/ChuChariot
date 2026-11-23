"""Compatibility, provenance and review boundaries of the teammate's v0.9."""

import copy
import hashlib
import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from chuchariot.dataset_io import ROOT, KnowledgeError, read_json
from chuchariot.preview import make_server, preview_data
from chuchariot.queries import KnowledgeStore
from chuchariot.validation import validate


class TeammateSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = read_json(ROOT / "data/candidates/teacher-pdf.v0.9.json")
        cls.ontology = read_json(ROOT / "data/ontology/ontology.v0.6.json")
        cls.store = KnowledgeStore(cls.data, cls.ontology)

    def test_received_snapshots_match_recorded_checksums(self):
        report = read_json(ROOT / "data/run-summaries/2026-11-23-teammate-sync-v09.json")
        for item in report["inputs"]:
            raw = (ROOT / item["target"]).read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(hashlib.sha256(raw).hexdigest(), item["lf_sha256"])
        self.assertEqual(report["formal_confirmations"], 0)

    def test_both_versions_preserve_every_previous_record(self):
        previous = read_json(ROOT / "data/candidates/teacher-pdf.v0.7.json")
        for version, ontology in [(8, "0.5"), (9, "0.6")]:
            current = read_json(ROOT / f"data/candidates/teacher-pdf.v0.{version}.json")
            self.assertEqual(validate(current, read_json(ROOT / f"data/ontology/ontology.v{ontology}.json")), [])
            for table in ["entities", "facts", "evidence", "sources", "model_mappings"]:
                records = {row["id"]: row for row in current[table]}
                for row in previous[table]:
                    self.assertEqual(records[row["id"]], row)
            previous = current
        self.assertEqual(len(self.data["entities"]), 120)
        self.assertEqual(len(self.data["facts"]), 395)
        self.assertTrue(all(f["review_status"] == "pending" for f in self.data["facts"]))

    def test_dimensions_and_model_mappings_are_not_extended_by_teaching_concepts(self):
        dimensions = [f for f in self.data["facts"] if f["predicate"] == "HAS_DIMENSION"]
        old = read_json(ROOT / "data/candidates/teacher-pdf.v0.7.json")
        self.assertEqual(dimensions, [f for f in old["facts"] if f["predicate"] == "HAS_DIMENSION"])
        self.assertEqual(self.data["model_mappings"], old["model_mappings"])
        self.assertEqual(len(dimensions), 54)
        self.assertEqual(len(self.data["model_mappings"]), 7)

    def test_wheel_to_body_path_keeps_the_distinct_basis_at_each_hop(self):
        result = self.store.connection_path("type:001", "type:body", True)
        self.assertTrue(result["found"])
        self.assertEqual([h["to"]["label"] for h in result["hops"]], ["毂", "车轴", "伏兔", "舆"])
        self.assertEqual([h["evidence_basis"]["label"] for h in result["hops"]], ["对照标本", "教学方案", "对照标本", "教学方案"])
        self.assertEqual(result["hops"][-1]["fact"]["origin"], "hypothesis")
        self.assertTrue(all(h["fact"]["rationale"] and h["evidence"] for h in result["hops"]))
        self.assertIn("不是同车物理连接", result["note"])

    def test_paths_are_directed_bounded_and_never_route_through_composition(self):
        self.assertFalse(self.store.connection_path("type:body", "type:001", True)["found"])
        self.assertFalse(self.store.connection_path("type:001", "type:body", True, 3)["found"])
        self.assertTrue(self.store.connection_path("type:001", "type:body", True, 4)["found"])
        self.assertFalse(self.store.connection_path("specimen:001", "component:ch15-hub", True)["found"])
        for limit in [0, 17, True, "8"]:
            with self.assertRaises(KnowledgeError):
                self.store.connection_path("type:001", "type:body", True, limit)
        with self.assertRaises(KnowledgeError):
            self.store.connection_path("type:missing", "type:body", True)

    def test_confirmed_paths_require_visible_basis_metadata(self):
        self.assertFalse(self.store.connection_path("type:001", "type:body")["found"])
        data = copy.deepcopy(self.data)
        for fact in data["facts"]:
            fact.update(review_status="confirmed", review={"reviewer": "Test fixture", "date": "2026-11-23", "note": "Test only"})
        target = next(f for f in data["facts"] if f["id"] == "fact:v09-connection-wheel-hub-basis")
        target["review_status"] = "pending"
        target.pop("review")
        store = KnowledgeStore(data, self.ontology)
        self.assertFalse(store.connection_path("type:001", "type:body")["found"])
        self.assertTrue(store.connection_path("type:001", "type:body", True)["found"])

    def test_incomplete_or_inconsistent_hop_metadata_is_rejected(self):
        for mutation in ["missing", "endpoint", "anchor", "duplicate"]:
            data = copy.deepcopy(self.data)
            target = next(f for f in data["facts"] if f["id"] == "fact:v09-connection-wheel-hub-to")
            if mutation == "missing":
                data["facts"].remove(target)
            elif mutation == "endpoint":
                target["object_id"] = "type:002"
            elif mutation == "anchor":
                target["basis_fact_ids"] = ["fact:v09-path-hub-axle"]
            else:
                extra = copy.deepcopy(target)
                extra["id"] = "fact:test-duplicate-path-field"
                data["facts"].append(extra)
            self.assertTrue(validate(data, self.ontology), mutation)

    def test_query_results_cannot_modify_the_store(self):
        result = self.store.connection_path("type:001", "type:body", True)
        result["hops"][0]["evidence"][0]["evidence"]["quote"] = "changed"
        result["hops"][0]["fact"]["rationale"] = "changed"
        again = self.store.connection_path("type:001", "type:body", True)
        self.assertNotEqual(again["hops"][0]["evidence"][0]["evidence"]["quote"], "changed")
        self.assertNotEqual(again["hops"][0]["fact"]["rationale"], "changed")

    def test_preview_uses_new_catalogue_and_existing_media_with_review_filtering(self):
        args = ROOT / "data/candidates/teacher-pdf.v0.9.json", ROOT / "data/ontology/ontology.v0.6.json"
        manifest = ROOT / "data/sources/fusion-media.v0.9.json"
        visible = preview_data(*args, review=True, media_manifest=manifest)
        self.assertEqual(len(visible["entities"]), 120)
        self.assertEqual(sum("object_id" in f for f in visible["facts"]), 218)
        self.assertEqual(len(visible["evidence"]), 62)
        self.assertEqual(len(visible["media"]), 25)
        hidden = preview_data(*args, media_manifest=manifest)
        self.assertEqual(hidden["facts"], [])
        self.assertEqual(hidden["evidence"], [])
        self.assertEqual(hidden["media"], [])

    def test_http_path_query_and_error_boundaries(self):
        server = make_server(0, ROOT / "data/candidates/teacher-pdf.v0.9.json", ROOT / "data/ontology/ontology.v0.6.json")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}/api/connection-path"
        try:
            with urlopen(base + "?from=type:001&to=type:body&review=1", timeout=3) as response:
                self.assertEqual(len(json.load(response)["hops"]), 4)
            with urlopen(base + "?from=type:001&to=type:body", timeout=3) as response:
                self.assertFalse(json.load(response)["found"])
            for query, expected in [("", 400), ("?from=x&from=y&to=z", 400),
                                    ("?from=type:001&to=type:body&max_hops=0", 400),
                                    ("?from=type:001&to=type:body&max_hops=bad", 400),
                                    ("?from=type:missing&to=type:body", 404)]:
                with self.assertRaises(HTTPError) as error:
                    urlopen(base + query, timeout=3)
                self.assertEqual(error.exception.code, expected)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
