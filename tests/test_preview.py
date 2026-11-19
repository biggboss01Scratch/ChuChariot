"""Verify read-only HTTP boundaries and review isolation on the actual UI API."""

import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from chuchariot.preview import make_server


class PreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server(port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def get_json(self, path):
        with urlopen(self.base + path, timeout=3) as response:
            return json.load(response)

    def test_real_page_and_assets_are_served(self):
        for path, expected in (("/", "text/html"), ("/app.js", "javascript"), ("/style.css", "text/css")):
            with self.subTest(path=path), urlopen(self.base + path, timeout=3) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(expected, response.headers["Content-Type"])

    def test_confirmed_mode_does_not_leak_candidate_dimensions(self):
        data = self.get_json("/api/preview")
        self.assertFalse(data["meta"]["review_mode"])
        self.assertEqual(data["facts"], [])
        self.assertEqual(data["evidence"], [])
        self.assertEqual(data["mappings"], [])
        measurement = next(e for e in data["entities"] if e["id"] == "measurement:001")
        self.assertNotIn("measurement", measurement)

    def test_explicit_review_mode_preserves_evidence_and_status(self):
        data = self.get_json("/api/preview?review=1")
        self.assertEqual(len(data["facts"]), 9)
        self.assertEqual(len(data["evidence"]), 4)
        self.assertTrue(all(f["review_status"] == "pending" for f in data["facts"]))
        self.assertTrue(all(not source["available"] for source in data["sources"]))

    def test_unregistered_files_and_sources_cannot_be_read(self):
        for path in ("/../README.md", "/%2e%2e/README.md", "/data/candidates/wheel-axle.v0.1.json", "/api/sources/source:missing"):
            with self.subTest(path=path), self.assertRaises(HTTPError) as error:
                urlopen(self.base + path, timeout=3)
            self.assertEqual(error.exception.code, 404)

    def test_writes_are_rejected(self):
        request = Request(self.base + "/api/preview", data=b"{}", method="POST")
        with self.assertRaises(HTTPError) as error:
            urlopen(request, timeout=3)
        self.assertEqual(error.exception.code, 405)


if __name__ == "__main__":
    unittest.main()
