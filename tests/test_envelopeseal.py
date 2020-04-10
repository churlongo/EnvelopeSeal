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
