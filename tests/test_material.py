"""Check the material lookup and retain each specimen's source evidence."""

import unittest

from chuchariot.dataset_io import ROOT, KnowledgeError, read_json
from chuchariot.media import project_media
from chuchariot.queries import KnowledgeStore


class MaterialRelationsTests(unittest.TestCase):
    def setUp(self):
        self.data = read_json(ROOT / "data/candidates/wheel-axle.v0.4.json")
        self.ontology = read_json(ROOT / "data/ontology/ontology.v0.2.json")

    def test_wood_lookup_finds_only_the_two_documented_specimens(self):
        store = KnowledgeStore(self.data, self.ontology)
        neighbors = store.relations("material:001", include_pending=True)
        self.assertEqual({(item["neighbor"]["id"], item["direction"]) for item in neighbors},
                         {("specimen:001", "incoming"), ("specimen:002", "incoming")})
        self.assertEqual({item["evidence"]["pdf_page"] for item in store.evidence("material:001", True)}, {4, 6})
        self.assertEqual(store.relations("material:001"), [])

    def test_material_assertion_does_not_apply_to_chariot_or_component_type(self):
        material_fact = next(fact for fact in self.data["facts"] if fact["id"] == "fact:029")
        for owner in ("object:001", "type:001"):
            with self.subTest(owner=owner):
                material_fact["subject_id"] = owner
                with self.assertRaisesRegex(KnowledgeError, "关系目标不存在或两端类型不允许"):
                    KnowledgeStore(self.data, self.ontology)

    def test_v04_keeps_existing_image_links_with_material_facts(self):
        store = KnowledgeStore(self.data, self.ontology)
        manifest = read_json(ROOT / "data/sources/fusion-media.v0.1.json")
        media = project_media(self.data, store.snapshot(include_pending=True), manifest)
        self.assertEqual(len(media), 15)
        cap = next(item for item in media if item["id"] == "media:axle-cap-artifact")
        self.assertEqual(cap["entity_ids"], ["specimen:003", "type:006"])

    def test_gleaning_binds_finish_and_motif_to_the_source_objects(self):
        store = KnowledgeStore(self.data, self.ontology)
        black_lacquer = store.relations("finish:002", include_pending=True)
        self.assertEqual({item["neighbor"]["id"] for item in black_lacquer}, {"specimen:004", "component:001"})
        self.assertEqual({item["evidence"]["pdf_page"] for item in store.evidence("finish:002", True)}, {3, 7})
        motif = store.relations("motif:001", include_pending=True)
        self.assertEqual([item["neighbor"]["id"] for item in motif], ["component:001"])
        self.assertEqual(motif[0]["neighbor"]["scope_id"], "specimen:005")
