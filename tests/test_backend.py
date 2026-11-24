"""Database/API tests. Real integration is opt-in and uses a separate container."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from unittest.mock import patch

try:
    from fastapi.testclient import TestClient
    from neo4j.exceptions import ServiceUnavailable
    import jsonschema
except ModuleNotFoundError as exc:
    raise unittest.SkipTest("Install requirements-backend.lock for backend tests") from exc

from chuchariot.dataset_io import ROOT, read_json
from chuchariot.backend.config import Settings
from chuchariot.backend.database import Repository, Conflict, flatten, unflatten, normalized, apply_operations, references
from chuchariot.backend.api import create_app

DATA = read_json(ROOT / "data/candidates/knowledge.v0.11.json")
ONTOLOGY = read_json(ROOT / "data/ontology/ontology.v0.7.json")
TOKEN = "unit-test-token-not-a-real-secret-0001"


class BackendUnitTests(unittest.TestCase):
    def test_flatten_roundtrip_all_records_without_payload_blob(self):
        for table in ("entities", "facts", "evidence", "sources", "model_mappings"):
            for record in DATA[table]:
                properties = flatten(record)
                self.assertEqual(unflatten(properties), record)
                self.assertTrue(all(not isinstance(v, dict) for v in properties.values()))
        dimension = next(f for f in DATA["facts"] if f["predicate"] == "HAS_DIMENSION")
        self.assertIn("data__value__quantity", flatten(dimension))

    def test_evidence_update_reopens_reviewed_facts_and_dependents(self):
        data = copy.deepcopy(DATA)
        target = data["facts"][0]
        target.update(review_status="confirmed", review={"reviewer": "test", "date": "2026-11-23", "note": "test"})
        evidence = next(e for e in data["evidence"] if e["id"] == target["evidence_ids"][0])
        record = {**evidence, "locator": evidence["locator"] + " test"}
        updated, changed, affected = apply_operations(data, [{"table": "evidence", "id": record["id"], "action": "update", "record": record}], "test", "2026-11-23T00:00:00Z")
        fact = next(f for f in updated["facts"] if f["id"] == target["id"])
        self.assertEqual(fact["review_status"], "pending")
        self.assertNotIn("review", fact)
        self.assertIn(target["id"], affected)
        self.assertEqual(data["facts"][0]["review_status"], "confirmed")

    def test_review_identity_is_server_supplied_and_hypothesis_stays_hypothesis(self):
        fact = next(f for f in DATA["facts"] if f["origin"] == "hypothesis")
        updated, _, _ = apply_operations(DATA, [{"table": "facts", "id": fact["id"], "action": "review",
                                               "review_status": "confirmed", "note": "test only"}], "trusted-actor", "2026-11-23T00:00:00Z")
        item = next(f for f in updated["facts"] if f["id"] == fact["id"])
        self.assertEqual(item["origin"], "hypothesis")
        self.assertEqual(item["review"]["reviewer"], "trusted-actor")

    def test_unconfigured_auth_denied_and_database_failure_is_503(self):
        class Offline:
            def snapshot(self):
                raise ServiceUnavailable("deliberate offline test")
            def ready(self):
                raise ServiceUnavailable("deliberate offline test")
        with TestClient(create_app(Settings(), Offline())) as client:
            self.assertEqual(client.get("/api/v1/internal/snapshot").status_code, 503)
            self.assertEqual(client.get("/api/v1/graph").status_code, 503)
            self.assertEqual(client.get("/api/v1/health/ready").status_code, 503)
            self.assertEqual(client.get("/api/v1/health/live").status_code, 200)


@unittest.skipUnless(os.environ.get("CHUCHARIOT_TEST_URI"), "requires disposable test database")
class BackendIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        uri = os.environ["CHUCHARIOT_TEST_URI"]
        if uri != "bolt://127.0.0.1:27687":
            raise RuntimeError("Integration tests may only reset the dedicated localhost:27687 database")
        cls.settings = replace(Settings.load(), uri=uri, operators={"test-actor": TOKEN}, publication_mode="candidate_preview")
        cls.repo = Repository(cls.settings)
        cls.repo.driver.verify_connectivity()

    @classmethod
    def tearDownClass(cls):
        cls.repo.close()

    def setUp(self):
        with self.repo.driver.session(database=self.repo.database) as session:
            session.run("MATCH (n) DETACH DELETE n").consume()
        self.repo.initialize()
        self.repo.import_baseline(DATA, ONTOLOGY)
        self.client = TestClient(create_app(self.settings, self.repo))
        self.auth = {"Authorization": "Bearer " + TOKEN}

    def draft(self, suffix="A", record=None):
        record = record or {"id": "type:test-" + suffix.lower(), "kind": "ComponentType", "label": "TEST " + suffix,
                            "aliases": [], "note": "Disposable database test only"}
        return {"base_graph_revision": "rev:00000001", "ontology_version": "0.7.0", "schema_version": "0.4.0",
                "reason": "Integration test only", "operations": [{"table": "entities", "id": record["id"], "action": "create", "record": record}]}

    def post_change(self, draft, key="test-change-0001"):
        response = self.client.post("/api/v1/internal/change-sets", json=draft,
                                    headers={**self.auth, "Idempotency-Key": key})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["id"]

    def validate_commit(self, ident, revision="rev:00000001"):
        result = self.client.post(f"/api/v1/internal/change-sets/{ident}/validate", headers=self.auth)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertTrue(result.json()["valid"], result.text)
        return self.client.post(f"/api/v1/internal/change-sets/{ident}/commit", json={"expected_graph_revision": revision}, headers=self.auth)

    def command(self, operations, revision="rev:00000001", key="lifecycle-test-0001"):
        draft = self.draft()
        draft.update(operations=operations, base_graph_revision=revision, reason="Correct mistaken knowledge; test database only")
        ident = self.post_change(draft, key)
        result = self.validate_commit(ident, revision)
        self.assertEqual(result.status_code, 200, result.text)
        return ident, result.json()["result_graph_revision"]

    def test_delete_and_restore_entity_recycle_bin_history_and_retry(self):
        _, revision = self.command(self.draft()["operations"], key="create-for-delete")
        op = {"table": "entities", "id": "type:test-a", "action": "delete"}
        ident, next_revision = self.command([op], revision, "delete-orphan-entity")
        self.assertEqual(self.client.get("/api/v1/entities/type:test-a").status_code, 404)
        for path in ("/api/v1/inspector", "/api/v1/internal/inspector"):
            self.assertNotIn("type:test-a", [e["id"] for e in self.client.get(path, headers=self.auth).json()["entities"]])
        self.assertEqual(self.client.get("/api/v1/internal/deleted").status_code, 401)
        page = self.client.get("/api/v1/internal/deleted?table=entities", headers=self.auth)
        self.assertEqual(page.status_code, 200, page.text)
        self.assertEqual(page.json()["total"], 1)
        archived = page.json()["items"][0]
        self.assertEqual(archived["deleted_by"], "test-actor")
        self.assertEqual(archived["deleted_revision"], next_revision)
        self.assertEqual(archived["record"]["label"], "TEST A")
        exported = self.client.get("/api/v1/internal/export", headers=self.auth).json()
        self.assertEqual(exported["deleted_records"], page.json()["items"])
        self.assertNotIn("type:test-a", [e["id"] for e in exported["dataset"]["entities"]])
        retry = self.client.post(f"/api/v1/internal/change-sets/{ident}/commit", headers=self.auth,
                                 json={"expected_graph_revision": revision})
        self.assertEqual(retry.status_code, 200, retry.text)
        self.assertEqual(len(self.repo.history("type:test-a")), 2)
        self.assertEqual(self.repo.history("type:test-a")[-1]["action"], "delete")
        self.assertIsNone(json.loads(self.repo.history("type:test-a")[-1]["after_json"]))
        with self.repo.driver.session(database=self.repo.database) as session:
            row = session.run("MATCH (r:Record {id:'type:test-a'}) RETURN r.deleted AS deleted, size([(r)-[]-() | 1]) AS links").single()
            self.assertTrue(row["deleted"])
            self.assertEqual(row["links"], 0)
        _, restored_revision = self.command([{**op, "action": "restore"}], next_revision, "restore-orphan-entity")
        self.assertEqual(self.client.get("/api/v1/entities/type:test-a").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/internal/deleted", headers=self.auth).json()["total"], 0)
        self.assertEqual(self.repo.history("type:test-a")[-1]["action"], "restore")
        self.command([{"table": "entities", "id": "type:test-a", "action": "review", "review_status": "confirmed",
                       "note": "Approve restored entity"}], restored_revision, "publish-orphan-entity")
        self.assertEqual(self.client.get("/api/v1/entities/type:test-a").status_code, 200)

    def test_delete_fact_is_hidden_in_all_modes_and_restore_requires_review(self):
        referenced = set().union(*(references(record) for table in ("sources", "evidence", "entities", "facts", "model_mappings") for record in DATA[table]))
        fact = next(f for f in DATA["facts"] if f["id"] not in referenced and f["id"] in
                    {e["fact_id"] for e in self.client.get("/api/v1/graph").json()["edges"]})
        ident = fact["id"]
        _, rev = self.command([{"table": "facts", "id": ident, "action": "review", "review_status": "confirmed", "note": "Test accepted"}], key="review-before-delete")
        _, rev = self.command([{"table": "facts", "id": ident, "action": "delete"}], rev, "delete-real-fact")
        self.assertEqual(self.client.get(f"/api/v1/facts/{ident}").status_code, 404)
        self.assertEqual(self.client.get(f"/api/v1/facts/{ident}/evidence").status_code, 404)
        self.assertNotIn(ident, [e["fact_id"] for e in self.client.get("/api/v1/graph").json()["edges"]])
        for path in ("/api/v1/inspector", "/api/v1/internal/inspector"):
            self.assertNotIn(ident, [f["id"] for f in self.client.get(path, headers=self.auth).json()["facts"]])
        self.command([{"table": "facts", "id": ident, "action": "restore"}], rev, "restore-real-fact")
        restored = next(f for f in self.repo.snapshot()[0]["facts"] if f["id"] == ident)
        self.assertEqual(restored["review_status"], "pending")
        self.assertNotIn("review", restored)
        self.assertEqual(restored["origin"], fact["origin"])

    def test_referenced_delete_is_blocked_for_all_reference_shapes(self):
        targets = [("sources", "source:001"), ("evidence", "evidence:001"),
                   ("entities", "specimen:001"), ("entities", "model:001")]
        basis = next(f["basis_fact_ids"][0] for f in DATA["facts"] if f.get("basis_fact_ids"))
        targets.append(("facts", basis))
        for i, (table, ident) in enumerate(targets):
            draft = self.draft()
            draft["operations"] = [{"table": table, "id": ident, "action": "delete"}]
            change = self.post_change(draft, "blocked-delete-" + str(i))
            result = self.client.post(f"/api/v1/internal/change-sets/{change}/validate", headers=self.auth)
            self.assertFalse(result.json()["valid"], (table, ident, result.text))
            self.assertIn("referenced", result.json()["errors"][0]["message"])
            commit = self.client.post(f"/api/v1/internal/change-sets/{change}/commit", headers=self.auth,
                                      json={"expected_graph_revision": "rev:00000001"})
            self.assertEqual(commit.status_code, 409, commit.text)
        self.assertEqual(self.repo.snapshot()[0], normalized(DATA))
        self.assertEqual(self.client.get("/api/v1/internal/deleted", headers=self.auth).json()["items"], [])

    def test_explicit_batch_delete_and_restore_closure_is_order_independent(self):
        ids = {"specimen:001"}
        rows = [(table, record) for table in ("sources", "evidence", "entities", "facts", "model_mappings") for record in DATA[table]]
        while True:
            previous = len(ids)
            ids |= {r["id"] for _, r in rows if references(r) & ids}
            if len(ids) == previous:
                break
        operations = [{"table": table, "id": r["id"], "action": "delete"} for table, r in rows if r["id"] in ids]
        _, rev = self.command(operations, key="delete-explicit-closure")
        self.assertTrue(all(r["id"] not in ids for t in ("sources", "evidence", "entities", "facts", "model_mappings") for r in self.repo.snapshot()[0][t]))
        self.command([{**op, "action": "restore"} for op in reversed(operations)], rev, "restore-explicit-closure")
        restored = self.repo.snapshot()[0]
        self.assertEqual(next(e for e in restored["entities"] if e["id"] == "specimen:001")["publication_status"], "draft")
        for record in restored["entities"]:
            record.pop("publication_status", None)
        for record in restored["facts"]:
            record.pop("publication_managed", None)
        self.assertEqual(restored, normalized(DATA))

    def test_deleted_id_cannot_be_recreated_updated_or_reviewed(self):
        _, rev = self.command(self.draft()["operations"], key="reserve-create")
        _, rev = self.command([{"table": "entities", "id": "type:test-a", "action": "delete"}], rev, "reserve-delete")
        for i, action in enumerate(("create", "update", "restore")):
            op = copy.deepcopy(self.draft()["operations"][0])
            op["action"] = action
            if action == "restore":
                op = {"table": "facts", "id": "type:test-a", "action": "restore"}
            draft = self.draft(); draft.update(base_graph_revision=rev, operations=[op])
            ident = self.post_change(draft, "reserved-check-" + str(i))
            result = self.client.post(f"/api/v1/internal/change-sets/{ident}/validate", headers=self.auth)
            self.assertFalse(result.json()["valid"])
        self.assertEqual(self.client.get("/api/v1/internal/deleted", headers=self.auth).json()["total"], 1)

    def test_delete_rollback_and_stale_update_cannot_resurrect(self):
        draft = self.draft(); original = copy.deepcopy(DATA["entities"][0])
        original["note"] = "Stale update test"
        draft["operations"] = [{"table": "entities", "id": original["id"], "action": "update", "record": original}]
        stale = self.post_change(draft, "prepare-stale-update")
        self.repo.process_change(stale, "test-actor")
        referenced = set().union(*(references(f) for f in DATA["facts"]))
        fact = next(f for f in DATA["facts"] if f["id"] not in referenced)
        deletion = self.draft(); deletion["operations"] = [{"table": "facts", "id": fact["id"], "action": "delete"}]
        ident = self.post_change(deletion, "delete-rollback")
        self.repo.process_change(ident, "test-actor")
        original_archive = Repository._archive_records
        def fail(*args):
            original_archive(*args)
            raise RuntimeError("delete rollback injection")
        with patch.object(Repository, "_archive_records", side_effect=fail):
            with self.assertRaises(RuntimeError):
                self.repo.process_change(ident, "test-actor", commit=True, expected_revision="rev:00000001")
        self.assertEqual(self.repo.snapshot()[0], normalized(DATA))
        self.assertEqual(self.repo.recycle_bin()[0], [])
        self.assertEqual(self.validate_commit(ident).status_code, 200)
        with self.assertRaises(Conflict):
            self.repo.process_change(stale, "test-actor", commit=True, expected_revision="rev:00000001")

    def test_all_five_record_tables_support_delete_restore_and_id_reservation(self):
        source = {**DATA["sources"][0], "id": "source:lifecycle-test"}
        evidence = {**DATA["evidence"][0], "id": "evidence:lifecycle-test", "source_id": source["id"]}
        entity = {"id": "type:lifecycle-test", "kind": "ComponentType", "label": "Disposable test", "aliases": []}
        fact = {"id": "fact:lifecycle-test", "subject_id": entity["id"], "predicate": "DESCRIPTION", "value": "Test only",
                "evidence_ids": [evidence["id"]], "origin": "documented", "review_status": "pending",
                "extraction": {"method": "test", "run_id": "run:lifecycle-test"}}
        mapping = {**DATA["model_mappings"][0], "id": "mapping:lifecycle-test", "entity_id": entity["id"]}
        rows = dict(sources=source, evidence=evidence, entities=entity, facts=fact, model_mappings=mapping)
        _, rev = self.command([{"table": t, "id": r["id"], "action": "create", "record": r} for t, r in rows.items()], key="create-all-tables")
        created = self.repo.snapshot()[0]
        _, rev = self.command([{"table": t, "id": r["id"], "action": "delete"} for t, r in rows.items()], rev, "delete-all-tables")
        self.assertEqual(self.repo.snapshot()[0], normalized(DATA))
        self.assertEqual({r["table"] for r in self.repo.recycle_bin()[0]}, set(rows))
        # Restoring a fact alone cannot refer to deleted subjects/evidence.
        draft = self.draft(); draft.update(base_graph_revision=rev, operations=[{"table": "facts", "id": fact["id"], "action": "restore"}])
        change = self.post_change(draft, "incomplete-restore")
        self.assertFalse(self.client.post(f"/api/v1/internal/change-sets/{change}/validate", headers=self.auth).json()["valid"])
        self.command([{"table": t, "id": r["id"], "action": "restore"} for t, r in reversed(list(rows.items()))], rev, "restore-all-tables")
        self.assertEqual(self.repo.snapshot()[0], created)
        self.assertEqual(self.repo.recycle_bin()[0], [])

    def test_delete_restore_payloads_and_unknown_targets(self):
        for i, extra in enumerate(({"record": None}, {"review_status": "confirmed"}, {"note": "forged metadata"})):
            draft = self.draft(); draft["operations"] = [{"table": "entities", "id": "type:001", "action": "delete", **extra}]
            result = self.client.post("/api/v1/internal/change-sets", json=draft,
                                      headers={**self.auth, "Idempotency-Key": "bad-delete-" + str(i)})
            self.assertEqual(result.status_code, 422)
        for i, action in enumerate(("delete", "restore")):
            draft = self.draft(); draft["operations"] = [{"table": "entities", "id": "type:missing", "action": action}]
            ident = self.post_change(draft, "unknown-target-" + str(i))
            self.assertFalse(self.client.post(f"/api/v1/internal/change-sets/{ident}/validate", headers=self.auth).json()["valid"])
            result = self.client.post(f"/api/v1/internal/change-sets/{ident}/commit", headers=self.auth,
                                      json={"expected_graph_revision": "rev:00000001"})
            self.assertEqual(result.status_code, 404)

    def test_baseline_roundtrip_idempotency_and_relational_projection(self):
        data, ontology, state = self.repo.snapshot()
        self.assertEqual(data, normalized(DATA))
        self.assertEqual(ontology, ONTOLOGY)
        self.assertFalse(self.repo.import_baseline(DATA, ONTOLOGY)["changed"])
        altered = copy.deepcopy(DATA)
        altered["description"] += " test"
        with self.assertRaises(Conflict):
            self.repo.import_baseline(altered, ONTOLOGY)
        with self.repo.driver.session(database=self.repo.database) as session:
            row = session.run("MATCH (:Entity)-[r:TENON_JOINT_WITH]->(:Entity) RETURN count(r) AS count").single()
            self.assertEqual(row["count"], 2)
            row = session.run("MATCH (f:Fact) WHERE f.data__predicate='HAS_DIMENSION' RETURN count(f) AS count").single()
            self.assertEqual(row["count"], 54)

    def test_public_routes_shapes_evidence_and_exact_counts(self):
        graph = self.client.get("/api/v1/graph").json()
        self.assertEqual(len(graph["edges"]), 76)
        self.assertFalse(graph["truncated"])
        self.assertEqual(len(self.client.get("/api/v1/graph?groups=structure").json()["edges"]), 27)
        self.assertTrue(self.client.get("/api/v1/graph?limit=3").json()["truncated"])
        self.assertEqual(self.client.get("/api/v1/graph?audience=internal").status_code, 422)
        self.assertEqual(self.client.get("/api/v1/graph?review=1").status_code, 422)
        self.assertEqual(self.client.get("/api/v1/graph?depth=4").status_code, 422)
        self.assertEqual(self.client.get("/api/v1/entities?page=1&page=2").status_code, 422)
        self.assertEqual(self.client.get("/api/v1/entities/connection:wheel-hub").status_code, 404)
        for path in ("/api/v1/entities/type:001", "/api/v1/entities/type:001/model-mappings", "/api/v1/sources/source:001"):
            self.assertEqual(self.client.get(path).status_code, 200, path)
        snapshot = self.client.get("/api/v1/inspector").json()
        by_id = {e["id"]: e for e in snapshot["evidence"]}
        sources = {s["id"]: s for s in DATA["sources"]}
        found = set()
        for f in snapshot["facts"]:
            if not f["evidence_ids"]:
                continue
            fmt = sources[by_id[f["evidence_ids"][0]]["source_id"]]["format"]
            if fmt in found:
                continue
            response = self.client.get(f"/api/v1/facts/{f['id']}/evidence")
            self.assertEqual(response.status_code, 200, response.text)
            found.add(fmt)
        self.assertEqual(found, {"pdf", "mp4", "md"})

    def test_authentication_and_export_and_teaching_basis(self):
        self.assertEqual(self.client.get("/api/v1/internal/snapshot").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/internal/snapshot", headers={"Authorization": "Bearer wrong"}).status_code, 403)
        response = self.client.get("/api/v1/internal/export", headers=self.auth)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["dataset"], normalized(DATA))
        response = self.client.get("/api/v1/internal/paths/teaching?from=type:001&to=type:body&include_pending=true", headers=self.auth)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()["hops"]), 4)
        self.assertTrue(all(h["evidence_basis"] and h["metadata_facts"] for h in response.json()["hops"]))
        raw = self.client.get("/openapi.json").json()
        self.assertTrue(all(raw["paths"][path][method].get("security") for path in raw["paths"] if "/internal/" in path
                            for method in raw["paths"][path] if method in {"get", "post"}))

    def test_review_endpoint_and_resource_range_and_dimension_details(self):
        hypothesis = next(f for f in DATA["facts"] if f["origin"] == "hypothesis")
        draft = self.draft()
        draft["operations"] = [{"table": "facts", "id": hypothesis["id"], "action": "review",
                                "review_status": "confirmed", "note": "Test acceptance, not historical proof"}]
        ident = self.post_change(draft)
        self.assertEqual(self.validate_commit(ident).status_code, 200)
        item = next(f for f in self.repo.snapshot()[0]["facts"] if f["id"] == hypothesis["id"])
        self.assertEqual(item["review"]["reviewer"], "test-actor")
        self.assertEqual(item["origin"], "hypothesis")
        detail = self.client.get("/api/v1/entities/specimen:001")
        self.assertEqual(detail.status_code, 200, detail.text)
        self.assertEqual(len(detail.json()["properties"]), 2)
        source = DATA["sources"][0]
        with tempfile.TemporaryDirectory() as directory:
            raw = b"%PDF-test-range-0123456789"
            (Path(directory) / source["filename"]).write_bytes(raw)
            with TestClient(create_app(replace(self.settings, resource_dirs=(Path(directory),)), self.repo)) as client:
                result = client.get("/api/v1/sources/source:001/content", headers={"Range": "bytes=0-8"})
                self.assertEqual(result.status_code, 206)
                self.assertEqual(result.content, raw[:9])
                self.assertEqual(client.get("/no-such-route").json()["error"]["code"], "http_error")

    def test_formal_public_mode_never_exposes_pending(self):
        with TestClient(create_app(replace(self.settings, publication_mode="confirmed_only"), self.repo)) as c:
            self.assertEqual(c.get("/api/v1/graph").json()["edges"], [])
            self.assertEqual(c.get("/api/v1/inspector?confirmed=false").json()["facts"], [])
            self.assertEqual(c.get("/api/v1/facts/fact:037").status_code, 404)
            self.assertEqual(c.get("/api/v1/sources/source:001").status_code, 404)

    def test_admin_ingestion_and_explicit_publication_with_private_original(self):
        from chuchariot.admin.api import DeepSeekExtractor
        from chuchariot.admin.ingestion import Proposal

        prefix = "/api/v1/internal/admin"
        self.assertEqual(self.client.get("/admin").status_code, 200)
        self.assertEqual(self.client.get(prefix + "/state").status_code, 401)
        original = "测试轮 R1 的右轮横径为100厘米。"
        unrelated = "周三参观签到。"
        upload = {"filename": "test-source.md", "text": original + "\n" + unrelated}
        proposal = Proposal(subject={"label": "测试轮 R1", "kind": "ReferenceSpecimen"},
                            predicate="HAS_DIMENSION", value={"quantity": "右轮横径", "value": 100,
                                                               "unit": "cm", "raw": original, "approximate": False},
                            quote=original)
        with patch.object(DeepSeekExtractor, "extract", return_value=([proposal], [{"quote": unrelated, "reason": "参观事宜"}], [])) as extract:
            result = self.client.post(prefix + "/imports/analyze", headers=self.auth, json=upload)
        self.assertEqual(result.status_code, 200, result.text)
        args = extract.call_args.args
        self.assertEqual(len(args[0]["facts"]), len(DATA["facts"]))
        self.assertTrue(any(f["predicate"] == "SCHEMATIC_NEXT" for f in args[0]["facts"]))
        analysis = result.json()
        self.assertEqual(analysis["items"][0]["status"], "new")
        self.assertEqual(analysis["unrelated"][0]["start_line"], 2)
        self.assertEqual(self.repo.current_revision(), "rev:00000001")
        request = {**upload, "candidates": analysis["candidates"], "base_graph_revision": analysis["graph_revision"],
                   "selections": [{"index": 0, "action": "add"}]}
        result = self.client.post(prefix + "/imports/commit", headers={**self.auth, "Idempotency-Key": "import-test-01"}, json=request)
        self.assertEqual(result.status_code, 200, result.text)
        fact_id = result.json()["fact_ids"][0]
        entity_id = analysis["items"][0]["subject_id"]
        source_id = analysis["items"][0]["evidence"]["source_id"]
        self.assertEqual(self.client.get(f"/api/v1/entities/{entity_id}").status_code, 404)
        self.assertEqual(self.client.get(f"/api/v1/facts/{fact_id}").status_code, 404)
        self.assertEqual(self.client.get(f"/api/v1/sources/{source_id}").status_code, 404)
        self.assertIn(fact_id, {f["id"] for f in self.client.get(prefix + "/state", headers=self.auth).json()["dataset"]["facts"]})
        checked = self.client.post(prefix + "/imports/check", headers=self.auth, json={**upload, "candidates": analysis["candidates"]})
        self.assertEqual(checked.json()["items"][0]["status"], "duplicate")
        _, revision = self.command(
            [{"table": table, "id": ident, "action": "review", "review_status": "confirmed", "note": "Accept test draft"}
             for table, ident in (("entities", entity_id), ("facts", fact_id))],
            result.json()["graph_revision"], "publish-import")
        self.assertEqual(revision, "rev:00000003")
        proof = self.client.get(f"/api/v1/facts/{fact_id}/evidence")
        self.assertEqual(proof.status_code, 200, proof.text)
        self.assertEqual(proof.json()["items"][0]["type"], "uploaded_text")
        self.assertEqual(proof.json()["items"][0]["quote"], original)
        self.assertEqual(self.client.get(f"/api/v1/sources/{source_id}/content").status_code, 404)
        text = self.client.get(f"/api/v1/internal/sources/{source_id}/content", headers=self.auth)
        self.assertEqual(text.text, upload["text"])
        with TestClient(create_app(replace(self.settings, publication_mode="confirmed_only"), self.repo)) as public:
            self.assertEqual(public.get(f"/api/v1/facts/{fact_id}").status_code, 200)

    def test_change_set_validate_commit_retry_history_and_restore(self):
        draft = self.draft()
        ident = self.post_change(draft)
        self.assertEqual(self.post_change(draft), ident)
        bad = self.draft("B")
        response = self.client.post("/api/v1/internal/change-sets", json=bad, headers={**self.auth, "Idempotency-Key": "test-change-0001"})
        self.assertEqual(response.status_code, 409)
        commit = self.validate_commit(ident)
        self.assertEqual(commit.status_code, 200, commit.text)
        retry = self.client.post(f"/api/v1/internal/change-sets/{ident}/commit", json={"expected_graph_revision": "rev:00000001"}, headers=self.auth)
        self.assertEqual(retry.status_code, 200, retry.text)
        self.assertEqual(retry.json()["result_graph_revision"], "rev:00000002")
        self.assertEqual(len(self.repo.history("type:test-a")), 1)
        self.assertEqual(self.repo.history("type:test-a")[0]["reason"], draft["reason"])
        self.assertEqual(self.client.get("/api/v1/entities/type:test-a").status_code, 404)
        state = self.client.get("/api/v1/internal/admin/state", headers=self.auth).json()["dataset"]
        self.assertIn("type:test-a", {entity["id"] for entity in state["entities"]})
        # Restoring a record is an explicit new revision, not erasure of history.
        record = copy.deepcopy(DATA["entities"][0]); before = copy.deepcopy(record)
        record["note"] = "test edit"
        update = {**draft, "base_graph_revision": "rev:00000002", "operations": [{"table": "entities", "id": record["id"], "action": "update", "record": record}]}
        second = self.post_change(update, "test-update-0002")
        self.assertEqual(self.validate_commit(second, "rev:00000002").status_code, 200)
        update["base_graph_revision"] = "rev:00000003"; update["operations"][0]["record"] = before
        third = self.post_change(update, "test-restore-0003")
        self.assertEqual(self.validate_commit(third, "rev:00000003").status_code, 200)
        self.assertEqual(len(self.repo.history(record["id"])), 2)

    def test_invalid_graph_and_forged_reviewer_are_not_committed(self):
        bad = self.draft(record={"id": "component:bad", "kind": "Component", "label": "Bad", "aliases": [], "scope_id": "chariot:missing"})
        ident = self.post_change(bad)
        response = self.client.post(f"/api/v1/internal/change-sets/{ident}/validate", headers=self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["valid"])
        commit = self.client.post(f"/api/v1/internal/change-sets/{ident}/commit", json={"expected_graph_revision": "rev:00000001"}, headers=self.auth)
        self.assertEqual(commit.status_code, 422)
        self.assertEqual(self.repo.snapshot()[0], normalized(DATA))
        forged = self.draft()
        forged["operations"][0]["reviewer"] = "forged"
        self.assertEqual(self.client.post("/api/v1/internal/change-sets", json=forged,
                         headers={**self.auth, "Idempotency-Key": "forged-00001"}).status_code, 422)

    def test_stale_concurrent_commit_has_one_winner(self):
        ids = [self.post_change(self.draft(suffix), "concurrent-" + suffix) for suffix in ("A", "B")]
        for ident in ids:
            self.assertTrue(self.repo.process_change(ident, "test-actor")["valid"])
        def commit(ident):
            try:
                return self.repo.process_change(ident, "test-actor", commit=True, expected_revision="rev:00000001")["status"]
            except Conflict:
                return "conflict"
        with ThreadPoolExecutor(2) as executor:
            outcomes = list(executor.map(commit, ids))
        self.assertCountEqual(outcomes, ["committed", "conflict"])
        self.assertEqual(len(self.repo.snapshot()[0]["entities"]), 129)

    def test_failure_after_record_write_rolls_back_everything(self):
        ident = self.post_change(self.draft())
        self.repo.process_change(ident, "test-actor")
        original = Repository._write_records
        def fail_after_write(tx, data):
            original(tx, data)
            raise RuntimeError("Injected failure before commit")
        with patch.object(Repository, "_write_records", side_effect=fail_after_write):
            with self.assertRaises(RuntimeError):
                self.repo.process_change(ident, "test-actor", commit=True, expected_revision="rev:00000001")
        data, _, state = self.repo.snapshot()
        self.assertEqual(data, normalized(DATA))
        self.assertEqual(state["revision"], 1)
        self.assertEqual(self.repo.history("type:test-a"), [])
