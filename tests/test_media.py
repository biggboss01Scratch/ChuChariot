"""Check that images follow evidence and model review visibility."""

import unittest

from chuchariot.dataset_io import DEFAULT_ONTOLOGY, ROOT, KnowledgeError, read_json
from chuchariot.media import project_media
from chuchariot.queries import KnowledgeStore


class MediaProjectionTests(unittest.TestCase):
    def setUp(self):
        self.data = read_json(ROOT / "data/candidates/wheel-axle.v0.3.json")
        self.manifest = read_json(ROOT / "data/sources/fusion-media.v0.1.json")
        self.ontology = read_json(DEFAULT_ONTOLOGY)

    def test_same_evidence_only_exposes_entities_from_visible_facts(self):
        review = {"reviewer": "test", "date": "2026-11-19", "note": "fixture"}
        first = next(f for f in self.data["facts"] if f["id"] == "fact:016")
        first.update(review_status="confirmed", review=review)
        store = KnowledgeStore(self.data, self.ontology)
        confirmed = project_media(self.data, store.snapshot(), self.manifest)
        self.assertEqual([(item["id"], item["entity_ids"]) for item in confirmed],
                         [("media:axle-cap-artifact", ["specimen:003"])])

    def test_rebound_model_mapping_rejects_stale_render(self):
        self.data["model_mappings"][0]["node_indices"] = [0]
        store = KnowledgeStore(self.data, self.ontology)
        with self.assertRaisesRegex(KnowledgeError, "节点或版本已变更"):
            project_media(self.data, store.snapshot(), self.manifest)
