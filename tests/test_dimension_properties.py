"""Protect numerical meaning, provenance and review filtering across migration."""

import copy
import tempfile
import unittest
from pathlib import Path

from chuchariot.dataset_io import ROOT, KnowledgeError, read_json
from chuchariot.importer import import_dataset
from chuchariot.preview import preview_data
from chuchariot.queries import KnowledgeStore
from chuchariot.validation import validate
from scripts.migrate_dimensions_v06 import build


class DimensionPropertyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.ontology, cls.manifest, cls.summary = build()
        cls.previous = read_json(ROOT / "data/candidates/teacher-pdf.v0.5.json")

    def dimension(self, data=None):
        return next(f for f in (data or self.data)["facts"] if f["predicate"] == "HAS_DIMENSION")

    def test_every_claim_and_original_value_survives_migration(self):
        old_entities = {e["id"]: e for e in self.previous["entities"]}
        self.assertEqual([f["id"] for f in self.data["facts"]], [f["id"] for f in self.previous["facts"]])
        for old, new in zip(self.previous["facts"], self.data["facts"]):
            expected = copy.deepcopy(old)
            if old["predicate"] == "HAS_MEASUREMENT":
                owner = old_entities[expected.pop("object_id")]
                self.assertEqual(owner["scope_id"], expected["subject_id"])
                expected.update(predicate="HAS_DIMENSION", value=owner["measurement"])
            self.assertEqual(new, expected)
        for table in ["sources", "evidence", "model_mappings"]:
            self.assertEqual(self.data[table], self.previous[table])
        self.assertEqual(self.summary["new_historical_claims"], 0)

    def test_only_dimension_nodes_are_removed_and_all_links_remain_valid(self):
        self.assertEqual(self.data["entities"], [e for e in self.previous["entities"] if e["kind"] != "Measurement"])
        self.assertEqual(len(self.data["entities"]), 95)
        self.assertEqual(sum("object_id" in f for f in self.data["facts"]), 109)
        self.assertEqual(len(self.summary["migrations"]), 54)
        self.assertEqual(validate(self.data, self.ontology), [])

    def test_range_approximation_and_measurement_kind_remain_distinct(self):
        values = {(f["subject_id"], f["value"]["quantity"]): f["value"]
                  for f in self.data["facts"] if f["predicate"] == "HAS_DIMENSION"}
        self.assertEqual(values["specimen:001", "右轮横径"]["value"], 132)
        self.assertEqual(values["specimen:001", "右轮竖径"]["value"], 119)
        self.assertEqual(values["specimen:ch14-beam", "残长"]["value"], 136)
        self.assertTrue(values["specimen:ch11-trace", "宽"]["approximate"])
        height = values["component:ch15-hub-ridges", "高"]
        self.assertEqual((height["min"], height["max"]), (.4, .6))
        self.assertTrue(all(value["raw"] and value["unit"] == "cm" for value in values.values()))

    def test_structured_dimensions_reject_bad_units_values_and_payload_shapes(self):
        for patch in [{"value": True}, {"value": 0}, {"value": float("inf")},
                      {"value": float("nan")}, {"unit": "kg"}, {"quantity": ""},
                      {"raw": ""}, {"min": 1, "max": 2}, {"undeclared": 1}]:
            with self.subTest(patch=patch):
                wrong = copy.deepcopy(self.data)
                self.dimension(wrong)["value"].update(patch)
                self.assertTrue(validate(wrong, self.ontology))
        wrong = copy.deepcopy(self.data)
        value = self.dimension(wrong)["value"]
        value.pop("value")
        value.update(min=3, max=1)
        self.assertTrue(any("上下界" in error for error in validate(wrong, self.ontology)))

    def test_properties_cannot_become_untyped_strings_or_category_dimensions(self):
        for change in [{"value": "132 cm"}, {"subject_id": "type:001"},
                       {"object_id": "specimen:002"}]:
            with self.subTest(change=change):
                wrong = copy.deepcopy(self.data)
                self.dimension(wrong).update(change)
                self.assertTrue(validate(wrong, self.ontology))

    def test_old_schema_cannot_silently_accept_structured_values(self):
        wrong = copy.deepcopy(self.data)
        wrong["schema_version"] = "0.1.0"
        self.assertTrue(any("value" in error for error in validate(wrong, self.ontology)))

    def test_multiple_source_claims_for_same_quantity_are_not_overwritten(self):
        data = copy.deepcopy(self.data)
        second = copy.deepcopy(self.dimension(data))
        second["id"] = "fact:conflicting-dimension-fixture"
        second["value"]["value"] = 140
        second["value"]["raw"] = "测试夹具：另一来源值，非历史资料"
        data["facts"].append(second)
        store = KnowledgeStore(data, self.ontology)
        same = [f for f in store.facts(second["subject_id"], True)
                if f["predicate"] == "HAS_DIMENSION" and f["value"]["quantity"] == second["value"]["quantity"]]
        self.assertEqual(len(same), 2)
        self.assertEqual({f["value"]["value"] for f in same}, {132, 140})

    def test_review_filtering_hides_whole_pending_property_facts(self):
        data = copy.deepcopy(self.data)
        confirmed = self.dimension(data)
        confirmed.update(review_status="confirmed", review={"reviewer": "测试夹具", "date": "2026-11-23", "note": "仅用于审核隔离测试"})
        store = KnowledgeStore(data, self.ontology)
        view = store.snapshot()
        self.assertEqual([f["id"] for f in view["facts"]], [confirmed["id"]])
        self.assertEqual(view["facts"][0]["value"]["value"], 132)
        self.assertEqual(view["stats"]["dimension_properties"], 54)
        self.assertEqual(store.relations(confirmed["subject_id"]), [])
        self.assertTrue(store.evidence(confirmed["subject_id"]))

    def test_properties_and_media_survive_preview_and_remain_hidden_until_review(self):
        paths = (ROOT / "data/candidates/teacher-pdf.v0.6.json", ROOT / "data/ontology/ontology.v0.4.json")
        manifest = ROOT / "data/sources/fusion-media.v0.6.json"
        review = preview_data(*paths, review=True, media_manifest=manifest)
        self.assertEqual(len(review["media"]), 25)
        self.assertEqual(sum(f["predicate"] == "HAS_DIMENSION" for f in review["facts"]), 54)
        hidden = preview_data(*paths, media_manifest=manifest)
        self.assertEqual(hidden["facts"], [])
        self.assertEqual(hidden["evidence"], [])
        self.assertEqual(hidden["media"], [])
        self.assertTrue(all("measurement" not in entity for entity in hidden["entities"]))

    def test_import_is_idempotent_and_conflicting_dimension_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "sixth.json"
            import_dataset(self.data, output, self.ontology)
            before = (output.read_bytes(), output.stat().st_mtime_ns)
            import_dataset(self.data, output, self.ontology)
            self.assertEqual(before, (output.read_bytes(), output.stat().st_mtime_ns))
            conflict = copy.deepcopy(self.data)
            self.dimension(conflict)["value"]["value"] = 140
            with self.assertRaisesRegex(KnowledgeError, "冲突记录"):
                import_dataset(conflict, output, self.ontology)
            self.assertEqual(before, (output.read_bytes(), output.stat().st_mtime_ns))


if __name__ == "__main__":
    unittest.main()
