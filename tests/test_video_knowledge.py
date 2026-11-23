"""Video provenance must survive validation, import, queries and HTTP delivery."""

import copy
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from chuchariot.dataset_io import ROOT, TABLES, read_json, write_json
from chuchariot.importer import import_dataset
from chuchariot.preview import make_server, preview_data
from chuchariot.queries import KnowledgeStore
from chuchariot.validation import validate
from scripts.add_video_knowledge_v010 import build


class VideoKnowledgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.summary = build()
        cls.ontology = read_json(ROOT / "data/ontology/ontology.v0.6.json")

    def assert_invalid(self, data, text):
        errors = validate(data, self.ontology)
        self.assertTrue(any(text in message for message in errors), errors)

    def test_snapshot_is_reproducible_and_preserves_all_received_records(self):
        self.assertEqual(self.data, read_json(ROOT / "data/candidates/knowledge.v0.10.json"))
        base = read_json(ROOT / "data/candidates/teacher-pdf.v0.9.json")
        for table in TABLES:
            self.assertEqual(self.data[table][:len(base[table])], base[table])
        self.assertEqual(self.summary["added"], dict(sources=1, evidence=6, entities=6, facts=17, model_mappings=0))
        self.assertEqual(self.data["model_mappings"], base["model_mappings"])

    def test_video_evidence_has_time_bounds_and_explicit_case_scope(self):
        self.assertEqual(validate(self.data, self.ontology), [])
        new = self.data["evidence"][-6:]
        for item in new:
            self.assertNotIn("pdf_page", item)
            self.assertLess(item["start_seconds"], item["end_seconds"])
            self.assertIn("不是六号车确定属性", item["scope_note"])
        facts = self.data["facts"][-17:]
        self.assertTrue(all(f["subject_id"].startswith("record:video1-") for f in facts))
        self.assertTrue(all("knowledge_basis" in f for f in facts))
        self.assertTrue(all(f["review_status"] == "pending" for f in facts))

    def test_invalid_video_times_and_pdf_fields_are_rejected(self):
        for patch, expected in [({"start_seconds": -1}, "时间段"),
                                ({"end_seconds": 99999}, "时间段"),
                                ({"end_seconds": 1564}, "时间段"),
                                ({"start_seconds": True}, "有限数值"),
                                ({"end_seconds": float("nan")}, "有限数值"),
                                ({"pdf_page": 1}, "不能使用 PDF"),
                                ({"transcription": "embedded_text"}, "转录方式")]:
            with self.subTest(patch=patch):
                data = copy.deepcopy(self.data)
                data["evidence"][-6].update(patch)
                self.assert_invalid(data, expected)
        data = copy.deepcopy(self.data)
        del data["evidence"][-1]["start_seconds"]
        self.assert_invalid(data, "有限数值")

    def test_pdf_requirements_remain_enforced_in_new_schema(self):
        data = copy.deepcopy(self.data)
        del data["evidence"][0]["pdf_page"]
        self.assert_invalid(data, "pdf_page")
        data = copy.deepcopy(self.data)
        data["evidence"][0].update(start_seconds=1, end_seconds=2)
        self.assert_invalid(data, "PDF 证据不能")

    def test_video_source_requires_duration_hash_and_classification(self):
        for patch, expected in [({"duration_seconds": 0}, "有限正数"),
                                ({"duration_seconds": True}, "有限正数"),
                                ({"content_sha256": "unknown"}, "SHA256"),
                                ({"source_type": "historical_fact"}, "来源类型")]:
            with self.subTest(patch=patch):
                data = copy.deepcopy(self.data)
                data["sources"][-1].update(patch)
                self.assert_invalid(data, expected)

    def test_video_fact_cannot_lose_or_upgrade_inference_label(self):
        data = copy.deepcopy(self.data)
        del data["facts"][-1]["knowledge_basis"]
        self.assert_invalid(data, "视频知识必须")
        data = copy.deepcopy(self.data)
        fact = next(f for f in data["facts"] if f["id"] == "fact:video1-tenon-explanation-description")
        fact["origin"] = "documented"
        self.assert_invalid(data, "推测不能标为 documented")

    def test_query_and_import_preserve_hypothesis_and_timestamp(self):
        store = KnowledgeStore(self.data, self.ontology)
        entity = "record:video1-tenon-explanation"
        fact = next(f for f in store.facts(entity, True) if f["predicate"] == "DESCRIPTION")
        self.assertEqual(fact["origin"], "hypothesis")
        self.assertEqual(fact["knowledge_basis"], "modern_reconstruction_inference")
        self.assertTrue(store.evidence(entity, True)[0]["evidence"]["start_seconds"] > 1500)
        self.assertEqual(len(store.connection_path("type:001", "type:body", True)["hops"]), 4)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "knowledge.json"
            import_dataset(self.data, target, self.ontology)
            before = target.read_bytes()
            import_dataset(self.data, target, self.ontology)
            self.assertEqual(target.read_bytes(), before)
            imported = KnowledgeStore.load(target, ROOT / "data/ontology/ontology.v0.6.json")
            self.assertEqual(imported.facts(entity, True), store.facts(entity, True))

    def test_review_acceptance_does_not_erase_hypothesis(self):
        data = copy.deepcopy(self.data)
        fact = next(f for f in data["facts"] if f["id"] == "fact:video1-tenon-explanation-description")
        fact.update(review_status="confirmed", review={"reviewer": "test-fixture", "date": "2026-11-23",
                                                       "note": "测试审核通过不改变推测性质；非真实审核。"})
        visible = KnowledgeStore(data, self.ontology).facts(fact["subject_id"])
        self.assertEqual(len(visible), 1)
        self.assertEqual(visible[0]["origin"], "hypothesis")
        self.assertEqual(visible[0]["knowledge_basis"], "modern_reconstruction_inference")

    def test_preview_keeps_pdf_media_and_video_evidence(self):
        dataset = ROOT / "data/candidates/knowledge.v0.10.json"
        ontology = ROOT / "data/ontology/ontology.v0.6.json"
        result = preview_data(dataset, ontology, True,
                              media_manifest=ROOT / "data/sources/fusion-media.v0.10.json")
        self.assertEqual(result["stats"]["dimension_properties"], 54)
        self.assertEqual(len(result["evidence"]), 68)
        self.assertTrue(result["media"])
        self.assertEqual(len(preview_data(dataset, ontology)["evidence"]), 0)

    def test_registered_video_http_supports_seeking_and_rejects_invalid_ranges(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = copy.deepcopy(self.data)
            data["sources"][-1]["filename"] = "fixture.mp4"
            write_json(root / "data.json", data)
            content = b"video-fixture-for-http-tests"
            (root / "fixture.mp4").write_bytes(content)
            server = make_server(0, root / "data.json", ROOT / "data/ontology/ontology.v0.6.json", root,
                                 media_manifest=ROOT / "data/sources/fusion-media.v0.10.json")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                with urlopen(base + "/api/preview?review=1", timeout=3) as response:
                    result = json.load(response)
                    self.assertTrue(next(s for s in result["sources"] if s["id"] == "source:video1")["available"])
                url = base + "/api/sources/source%3Avideo1"
                for header, expected in [(None, content), ("bytes=3-8", content[3:9]),
                                         ("bytes=5-", content[5:]), ("bytes=-4", content[-4:])]:
                    request = Request(url, headers={"Range": header} if header else {})
                    with urlopen(request, timeout=3) as response:
                        self.assertEqual(response.status, 206 if header else 200)
                        self.assertEqual(response.headers["Content-Type"], "video/mp4")
                        self.assertEqual(response.read(), expected)
                for header in ["bytes=999-", "bytes=8-2", "bytes=-0", "bytes=0-1,4-5", "invalid"]:
                    with self.subTest(header=header), self.assertRaises(HTTPError) as error:
                        urlopen(Request(url, headers={"Range": header}), timeout=3)
                    self.assertEqual(error.exception.code, 416)
                with self.assertRaises(HTTPError) as error:
                    urlopen(base + "/api/sources/source%3Aunknown", timeout=3)
                self.assertEqual(error.exception.code, 404)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)
