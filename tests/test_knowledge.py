"""Domain checks: prevent false provenance, wrong ownership, and unsafe imports."""

import copy
import tempfile
import unittest
from pathlib import Path

from chuchariot.knowledge import (DEFAULT_DATASET, DEFAULT_ONTOLOGY, KnowledgeError,
                                  KnowledgeStore, import_dataset, read_json, validate)
from chuchariot.resources import check_mapping_indices, inspect_glb, inventory


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.data = read_json(DEFAULT_DATASET)
        self.ontology = read_json(DEFAULT_ONTOLOGY)

    def assertInvalid(self, fragment):
        errors = validate(self.data, self.ontology)
        self.assertTrue(any(fragment in error for error in errors), errors)

    def test_source_backed_candidate_is_valid_but_not_confirmed(self):
        self.assertEqual(validate(self.data, self.ontology), [])
        store = KnowledgeStore(self.data, self.ontology)
        self.assertEqual(store.facts("type:001"), [])
        self.assertEqual(len(store.relations("type:001", True)), 4)
        self.assertEqual(store.mappings("type:001"), [])

    def test_unreviewed_dimension_hidden_by_default(self):
        store = KnowledgeStore(self.data, self.ontology)
        self.assertNotIn("measurement", store.entity("measurement:001"))
        self.assertEqual(store.entity("measurement:001")["fact_review_summary"]["pending"], 1)
        self.assertEqual(store.entity("measurement:001", True)["measurement"]["value"], 132)

    def test_reviewed_fact_is_visible_and_preserves_origin(self):
        self.data["facts"][5]["review_status"] = "confirmed"
        self.data["facts"][5]["review"] = {"reviewer": "test-fixture", "date": "2026-11-19", "note": "仅测试，不是内容审核"}
        store = KnowledgeStore(self.data, self.ontology)
        self.assertEqual(store.entity("measurement:001")["measurement"]["value"], 132)
        self.assertEqual(store.facts("measurement:001")[0]["origin"], "documented")

    def test_snapshot_and_queries_agree_for_mixed_review_states(self):
        review = {"reviewer": "test-fixture", "date": "2026-11-19", "note": "仅用于测试"}
        self.data["facts"][0].update(review_status="confirmed", review=review)
        self.data["facts"][1].update(review_status="disputed", review=review)
        self.data["model_mappings"][1].update(review_status="confirmed", review=review)
        store = KnowledgeStore(self.data, self.ontology)
        view = store.snapshot()
        self.assertEqual(view["facts"], store.facts("type:001"))
        self.assertEqual([fact["id"] for fact in view["facts"]], ["fact:001"])
        self.assertEqual([item["id"] for item in view["evidence"]], ["evidence:001"])
        self.assertEqual(view["mappings"], store.mappings("type:001"))
        self.assertEqual([item["id"] for item in view["mappings"]], ["mapping:002"])
        self.assertEqual(len(store.snapshot(include_pending=True)["facts"]), len(self.data["facts"]))

    def test_mapping_hash_and_range(self):
        model = next(e for e in self.data["entities"] if e["id"] == "model:001")
        report = {"model_resource_id": "res:005", "sha256": model["content_sha256"], "node_count": 709}
        self.assertEqual(check_mapping_indices(self.data, report), [])
        report["sha256"] = "0" * 64
        self.assertTrue(any("SHA256" in e for e in check_mapping_indices(self.data, report)))
        report["sha256"] = model["content_sha256"]
        report["node_count"] = 1
        self.assertTrue(any("越界" in e for e in check_mapping_indices(self.data, report)))

    def test_malformed_review_is_validation_error(self):
        self.data["facts"][0]["review_status"] = "confirmed"
        self.data["facts"][0]["review"] = {"reviewer": [], "date": 0, "note": ""}
        self.assertInvalid("review")

    def test_evidence_keeps_reference_specimen_and_pdf_page(self):
        store = KnowledgeStore(self.data, self.ontology)
        results = store.evidence("measurement:001", True)
        self.assertEqual(results[0]["evidence"]["pdf_page"], 6)
        self.assertIn("CH1", results[0]["evidence"]["scope_note"])
        self.assertEqual(results[0]["review_status"], "pending")

    def test_duplicate_id(self):
        self.data["entities"].append(copy.deepcopy(self.data["entities"][0]))
        self.assertInvalid("不唯一")

    def test_missing_evidence(self):
        self.data["facts"][0]["evidence_ids"] = ["evidence:missing"]
        self.assertInvalid("证据引用")

    def test_documented_fact_requires_evidence(self):
        self.data["facts"][0]["evidence_ids"] = []
        self.assertInvalid("必须附证据")

    def test_wrong_endpoint_kind(self):
        self.data["facts"][0]["object_id"] = "measurement:001"
        self.assertInvalid("两端类型")

    def test_reference_measurement_cannot_move_to_target_chariot(self):
        self.data["facts"][5]["subject_id"] = "object:001"
        self.assertInvalid("尺寸归属")

    def test_general_class_cannot_own_specific_chariot_component(self):
        self.data["entities"].append({"id": "component:test", "kind": "Component",
                                      "label": "测试夹具：部件", "aliases": [], "scope_id": "object:001"})
        self.data["facts"][0]["object_id"] = "component:test"
        self.assertInvalid("两端类型")

    def test_composition_cycle(self):
        fact = copy.deepcopy(self.data["facts"][0])
        fact.update(id="fact:cycle", subject_id="type:003", object_id="type:001")
        self.data["facts"].append(fact)
        self.assertInvalid("循环")

    def test_dependency_cycle(self):
        for index in (1, 2):
            self.data["entities"].append({"id": f"step:{index}", "kind": "AssemblyStep",
                                          "label": "测试夹具：步骤", "aliases": []})
        for index, target in ((1, 2), (2, 1)):
            fact = copy.deepcopy(self.data["facts"][0])
            fact.update(id=f"fact:step{index}", subject_id=f"step:{index}",
                        predicate="DEPENDS_ON", object_id=f"step:{target}")
            self.data["facts"].append(fact)
        self.assertInvalid("循环")

    def test_hypothesis_requires_explanation(self):
        self.data["facts"][0]["origin"] = "hypothesis"
        self.assertInvalid("理由及依据")

    def test_pending_cannot_be_called_reviewed(self):
        self.data["stage"] = "reviewed"
        self.assertInvalid("待审核事实")

    def test_confirmation_requires_reviewer(self):
        self.data["facts"][0]["review_status"] = "confirmed"
        self.assertInvalid("review.reviewer")

    def test_bad_units_zero_boolean_infinite_and_range(self):
        original = copy.deepcopy(self.data)
        for patch, expected in (({"unit": "unknown"}, "单位"), ({"value": 0}, "有限正数"),
                                ({"value": True}, "有限正数"), ({"value": float("inf")}, "有限正数"),
                                ({"min": 2, "max": 1}, "混用")):
            with self.subTest(patch=patch):
                self.data = copy.deepcopy(original)
                self.data["entities"][10]["measurement"].update(patch)
                self.assertInvalid(expected)

    def test_evidence_page_boundaries(self):
        self.data["evidence"][0]["pdf_page"] = 11
        self.assertInvalid("页码越界")

    def test_unknown_entity_and_alias_search(self):
        store = KnowledgeStore(self.data, self.ontology)
        self.assertEqual(store.list_entities("轮毂")[0]["id"], "type:003")
        with self.assertRaises(KnowledgeError):
            store.entity("type:missing")

    def test_returned_records_cannot_mutate_store(self):
        store = KnowledgeStore(self.data, self.ontology)
        store.entity("type:001")["aliases"].append("bad")
        self.assertNotIn("bad", store.entity("type:001")["aliases"])

    def test_import_is_idempotent_and_conflict_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "snapshot.json"
            import_dataset(self.data, path, self.ontology)
            original_bytes = path.read_bytes()
            import_dataset(self.data, path, self.ontology)
            self.assertEqual(path.read_bytes(), original_bytes)
            modified = copy.deepcopy(self.data)
            modified["entities"][0]["label"] = "冲突夹具"
            with self.assertRaisesRegex(KnowledgeError, "冲突记录"):
                import_dataset(modified, path, self.ontology)
            self.assertEqual(path.read_bytes(), original_bytes)

    def test_malformed_structure_and_unknown_fields(self):
        self.assertTrue(validate([], self.ontology))
        self.data["facts"][0]["evidences_ids"] = []
        self.assertInvalid("未定义字段")

    def test_duplicate_json_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.json"
            path.write_text('{"id":"a", "id":"b"}', encoding="utf-8")
            with self.assertRaisesRegex(KnowledgeError, "重复 JSON 字段"):
                read_json(path)

    def test_missing_resources_do_not_claim_availability(self):
        with tempfile.TemporaryDirectory() as temp:
            result = inventory(Path(temp), {"resources": [{"id": "res:test", "filename": "missing.pdf"}]})
            self.assertEqual(result["resources"][0]["availability"], "missing")
            self.assertNotIn("sha256", result["resources"][0])

    def test_glb_invalid_header(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.glb"
            path.write_bytes(b"not a glb")
            with self.assertRaises(KnowledgeError):
                inspect_glb(path)


if __name__ == "__main__":
    unittest.main()
