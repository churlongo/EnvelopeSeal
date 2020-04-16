import datetime
import os
import unittest

from envelopeseal import blast, graph, manifest, report, rotation, strength

SAMPLES = os.path.join(os.path.dirname(__file__), os.pardir, "samples")
HEALTHY = os.path.join(SAMPLES, "healthy.manifest")
BROKEN = os.path.join(SAMPLES, "broken.manifest")
AS_OF = datetime.date(2026, 9, 2)


class ManifestParseTests(unittest.TestCase):
    def test_healthy_parses(self):
        m = manifest.parse_file(HEALTHY)
        self.assertEqual(len(m.keys), 7)
        self.assertEqual(len(m.wraps), 6)
        self.assertTrue(m.keys["dek-orders"].is_data_key)
        self.assertTrue(m.keys["root-hsm"].is_kek)

    def test_unknown_role_rejected(self):
        with self.assertRaises(manifest.ManifestError):
            manifest.parse_text("key k1 root AES-GCM 256 2026-01-01 0")

    def test_bad_field_count_rejected(self):
        with self.assertRaises(manifest.ManifestError):
            manifest.parse_text("key k1 dek AES-GCM 256")

    def test_duplicate_key_rejected(self):
        text = (
            "key k1 dek AES-GCM 256 2026-01-01 0\n"
            "key k1 dek AES-GCM 256 2026-01-01 0\n"
        )
        with self.assertRaises(manifest.ManifestError):
            manifest.parse_text(text)

    def test_bad_date_rejected(self):
        with self.assertRaises(manifest.ManifestError):
            manifest.parse_text("key k1 dek AES-GCM 256 2026-13-40 0")

    def test_comments_and_blanks_ignored(self):
        text = "# comment\n\nkey k1 dek AES-GCM 256 2026-01-01 0\n"
        m = manifest.parse_text(text)
        self.assertEqual(len(m.keys), 1)


class GraphTests(unittest.TestCase):
    def test_edge_to_unknown_key_rejected(self):
        m = manifest.parse_text(
