"""Migration must keep measurements and joints while resolving source vocabulary."""

import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from chuchariot.dataset_io import ROOT, TABLES, read_json
from chuchariot.importer import import_dataset
from chuchariot.preview import preview_data, source_path
from chuchariot.queries import KnowledgeStore
from chuchariot.validation import validate
from scripts.normalize_terms_v011 import DATASET, ONTOLOGY, REGIONS, build


class NormalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.ontology, cls.summary = build()
        cls.base = read_json(ROOT / "data/candidates/knowledge.v0.10.json")
        cls.entities = {e["id"]: e for e in cls.data["entities"]}
        cls.facts = {f["id"]: f for f in cls.data["facts"]}
        cls.store = KnowledgeStore(cls.data, cls.ontology)

    def assert_invalid(self, data, expected):
        errors = validate(data, self.ontology)
        self.assertTrue(any(expected in error for error in errors), errors)

    def test_migration_replays_and_retains_every_original_id(self):
        self.assertEqual(self.data, read_json(DATASET))
        self.assertEqual(self.ontology, read_json(ONTOLOGY))
        for table in TABLES:
            self.assertFalse(self.summary["changes"][table]["removed_ids"])
            self.assertLessEqual({r["id"] for r in self.base[table]}, {r["id"] for r in self.data[table]})
        self.assertEqual(self.summary["totals"]["facts"], 423)
        self.assertEqual(self.summary["dimension_properties"], 54)
        self.assertEqual(self.data["model_mappings"], self.base["model_mappings"])
        self.assertEqual([f for f in self.data["facts"] if f["predicate"] == "HAS_DIMENSION"],
                         [f for f in self.base["facts"] if f["predicate"] == "HAS_DIMENSION"])
        self.assertEqual(self.data["evidence"][:len(self.base["evidence"])], self.base["evidence"])

    def test_regions_are_attached_to_the_original_parts_and_keep_specimen_scope(self):
        for type_id, (instance_id, _, _, part_fact, type_fact) in REGIONS.items():
            self.assertEqual(self.entities[type_id]["kind"], "StructuralRegionType")
            self.assertEqual(self.entities[instance_id]["kind"], "ComponentRegion")
            self.assertEqual(self.entities[instance_id]["scope_id"], "specimen:001")
            self.assertEqual(self.facts[part_fact]["predicate"], "HAS_REGION")
            if type_fact:
                self.assertEqual(self.facts[type_fact]["predicate"], "HAS_REGION")
        region_ids = {e["id"] for e in self.data["entities"] if e["kind"] in {"ComponentRegion", "StructuralRegionType"}}
        self.assertFalse(any(f["predicate"] == "HAS_PART" and f.get("object_id") in region_ids for f in self.data["facts"]))
        self.assertEqual(self.facts["fact:pdf-153"]["value"], "13道")
        self.assertIn("制作方式", self.entities["component:ch15-hub-ridges"]["note"])

    def test_the_two_tenon_joints_stay_on_spoke_regions(self):
        for ident, target in [("fact:pdf-144", "component:ch15-hub"), ("fact:pdf-145", "component:ch15-rim")]:
            fact = self.facts[ident]
            self.assertEqual(fact, next(f for f in self.base["facts"] if f["id"] == ident))
            self.assertEqual(self.entities[fact["subject_id"]]["kind"], "ComponentRegion")
            self.assertEqual(fact["object_id"], target)
        bad = copy.deepcopy(self.data)
        region = next(e for e in bad["entities"] if e["id"] == "component:ch15-spoke-inner")
        region["scope_id"] = "specimen:002"
        self.assert_invalid(bad, "不能跨标本")

    def test_a_region_cannot_be_reintroduced_as_an_independent_assembly_part(self):
        bad = copy.deepcopy(self.data)
        next(f for f in bad["facts"] if f["id"] == "fact:pdf-134")["predicate"] = "HAS_PART"
        self.assert_invalid(bad, "两端类型不允许")
        bad = copy.deepcopy(self.data)
        next(f for f in bad["facts"] if f["id"] == "fact:v09-tree-04")["predicate"] = "HAS_PART"
        self.assert_invalid(bad, "两端类型不允许")

    def test_teacher_term_is_not_an_extra_component_or_global_alias(self):
        term = self.entities["type:bridle"]
        self.assertEqual(term["kind"], "TermSense")
        self.assertEqual(term["source_id"], "source:001")
        self.assertEqual(term["scope_id"], "record:m2432-reconstruction")
        denotes = self.facts["fact:v09-functional-03"]
        self.assertEqual((denotes["subject_id"], denotes["predicate"], denotes["object_id"]),
                         ("type:bridle", "TERM_DENOTES", "type:horse-bridle"))
        self.assertEqual(self.facts["fact:pdf-195"]["predicate"], "USES_TERM")
        self.assertEqual(self.facts["fact:v09-le-source"]["object_id"], "type:horse-bridle")
        for entity in self.data["entities"]:
            if entity["kind"] == "ComponentType":
                self.assertNotIn("辔", entity["aliases"])
        self.assertFalse(any(f["subject_id"] == "type:horse-bridle" and f.get("object_id") == "type:bridle"
                             and f["predicate"] in {"HAS_PART", "TEACHING_GROUPS_TYPE", "SUBCLASS_OF"} for f in self.data["facts"]))

    def test_dictionary_senses_remain_distinct_and_have_source_bound_references(self):
        self.assertEqual(self.facts["fact:v11-pei-reins-denotes"]["object_id"], "type:reins")
        broad = self.store.facts("term:pei-broad", True)
        self.assertFalse(any(f["predicate"] == "TERM_DENOTES" for f in broad))
        self.assertEqual({f["object_id"] for f in broad if f["predicate"] == "TERM_RELATED_TO"},
                         {"type:reins", "type:horse-bridle"})
        bad = copy.deepcopy(self.data)
        next(f for f in bad["facts"] if f["id"] == "fact:v11-pei-reins-denotes")["evidence_ids"] = ["evidence:001"]
        self.assert_invalid(bad, "词义所属来源")
        bad = copy.deepcopy(self.data)
        del next(e for e in bad["entities"] if e["id"] == "term:pei-reins")["source_id"]
        self.assert_invalid(bad, "有效来源")

    def test_teaching_paths_use_canonical_bridle_without_routing_through_words(self):
        path = self.store.connection_path("type:bit", "type:body", True)
        self.assertTrue(path["found"])
        self.assertEqual([hop["to"]["id"] for hop in path["hops"]],
                         ["type:cheekpiece", "type:horse-bridle", "type:reins", "type:body"])
        self.assertFalse(self.store.connection_path("type:bridle", "type:body", True)["found"])
        self.assertFalse(self.store.connection_path("term:pei-reins", "type:body", True)["found"])
        self.assertEqual(len(self.store.connection_path("type:001", "type:body", True)["hops"]), 4)
        self.assertEqual(sum(f["predicate"] == "SCHEMATIC_NEXT" for f in self.data["facts"]), 13)
        self.assertTrue(all(hop["evidence_basis"]["label"] for hop in path["hops"]))

    def test_old_video_knowledge_is_unchanged_and_no_duplicate_claims_are_created(self):
        for fact in self.base["facts"]:
            if fact["id"].startswith("fact:video1-"):
                self.assertEqual(fact, self.facts[fact["id"]])
        import json
        keys = [(f["subject_id"], f["predicate"], json.dumps(f.get("value", f.get("object_id")), sort_keys=True)) for f in self.data["facts"]]
        self.assertEqual(len(keys), len(set(keys)))

    def test_dictionary_excerpts_are_bound_to_real_files_and_do_not_fake_pages(self):
        for source in self.data["sources"][-2:]:
            file = ROOT / "data/sources/terminology" / source["filename"]
            self.assertEqual(hashlib.sha256(file.read_bytes().replace(b"\r\n", b"\n")).hexdigest(), source["content_sha256"])
            self.assertEqual(source_path(source, file.parent), file.resolve())
        bad = copy.deepcopy(self.data)
        next(e for e in bad["evidence"] if e["id"] == "evidence:v11-pei-reins")["pdf_page"] = 1
        self.assert_invalid(bad, "词典条目不能")
        for url in ["javascript:alert(1)", "http://example.com", "https://user:secret@example.com", "https://["]:
            with self.subTest(url=url):
                bad = copy.deepcopy(self.data)
                bad["sources"][-1]["url"] = url
                self.assert_invalid(bad, "HTTPS官方条目URL")

    def test_queries_media_and_import_keep_new_kinds_and_provenance(self):
        data = preview_data(DATASET, ONTOLOGY, True, ROOT / "data/sources/terminology",
                            media_manifest=ROOT / "data/sources/fusion-media.v0.11.json")
        self.assertEqual(data["stats"]["dimension_properties"], 54)
        self.assertTrue(data["media"])
        self.assertTrue(all(s["available"] for s in data["sources"][-2:]))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "knowledge.json"
            import_dataset(self.data, output, self.ontology)
            initial = output.read_bytes()
            import_dataset(self.data, output, self.ontology)
            self.assertEqual(initial, output.read_bytes())
            imported = KnowledgeStore.load(output, ONTOLOGY)
            self.assertEqual(imported.entity("type:bridle", True)["kind"], "TermSense")
            self.assertEqual(imported.evidence("term:pei-reins", True)[0]["source"]["url"], self.data["sources"][-2]["url"])
