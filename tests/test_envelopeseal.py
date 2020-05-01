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
            "key k1 kek AES-KW 256 2026-01-01 0\nwrap k1 ghost\n"
        )
        with self.assertRaises(graph.GraphError):
            graph.build_graph(m)

    def test_healthy_has_no_cycles(self):
        m = manifest.parse_file(HEALTHY)
        g = graph.build_graph(m)
        self.assertEqual(graph.find_cycles(g), [])

    def test_cycle_detected_and_normalised(self):
        m = manifest.parse_file(BROKEN)
        g = graph.build_graph(m)
        cycles = graph.find_cycles(g)
        self.assertEqual(cycles, [["loop-a", "loop-b"]])

    def test_orphan_detected(self):
        m = manifest.parse_file(BROKEN)
        g = graph.build_graph(m)
        self.assertIn("lonely-kek", graph.orphans(g))

    def test_healthy_has_no_orphans(self):
        m = manifest.parse_file(HEALTHY)
        g = graph.build_graph(m)
        self.assertEqual(graph.orphans(g), [])

    def test_reachability_from_root(self):
        m = manifest.parse_file(HEALTHY)
        g = graph.build_graph(m)
        deks = blast.data_key_ids(m)
        reached = graph.reachable_data_keys(g, "root-hsm", deks)
        self.assertEqual(
            reached,
            {"dek-orders", "dek-invoices", "dek-events", "dek-metrics"},
        )


class StrengthTests(unittest.TestCase):
    def test_symmetric_level_is_bits(self):
        k = manifest.parse_text(
            "key k1 dek AES-GCM 256 2026-01-01 0"
        ).keys["k1"]
        self.assertEqual(strength.security_level(k), 256)

    def test_rsa_modulus_mapped(self):
        k = manifest.parse_text(
            "key k1 kek RSA-OAEP 2048 2026-01-01 0"
        ).keys["k1"]
        self.assertEqual(strength.security_level(k), 112)

    def test_unknown_algorithm_raises(self):
        k = manifest.parse_text(
            "key k1 dek MYSTERY 256 2026-01-01 0"
        ).keys["k1"]
        with self.assertRaises(strength.StrengthError):
            strength.security_level(k)

    def test_unmapped_modulus_raises(self):
        k = manifest.parse_text(
            "key k1 kek RSA-OAEP 999 2026-01-01 0"
        ).keys["k1"]
        with self.assertRaises(strength.StrengthError):
            strength.security_level(k)

    def test_inversion_detected(self):
        m = manifest.parse_file(BROKEN)
        self.assertTrue(
            strength.is_inversion(m.keys["weak-wrapper"], m.keys["dek-strong"])
        )

    def test_equal_strength_is_not_inversion(self):
        m = manifest.parse_file(HEALTHY)
        self.assertFalse(
            strength.is_inversion(m.keys["root-hsm"], m.keys["mid-payments-kek"])
        )


class RotationTests(unittest.TestCase):
    def test_exempt_never_overdue(self):
        m = manifest.parse_file(HEALTHY)
        s = rotation.status_for(m.keys["root-hsm"], AS_OF)
        self.assertTrue(s.exempt)
        self.assertFalse(s.overdue)

    def test_open_interval_not_overdue(self):
        m = manifest.parse_file(HEALTHY)
        s = rotation.status_for(m.keys["dek-orders"], AS_OF)
        self.assertFalse(s.overdue)

    def test_overdue_key_and_days(self):
        m = manifest.parse_file(BROKEN)
        s = rotation.status_for(m.keys["dek-stale"], AS_OF)
        self.assertTrue(s.overdue)
        # created 2026-01-01 + 30 days = due 2026-01-31; as-of 2026-09-02.
        self.assertEqual(s.due_date, datetime.date(2026, 1, 31))
        self.assertEqual(s.days_overdue, (AS_OF - datetime.date(2026, 1, 31)).days)

    def test_healthy_has_no_overdue(self):
        m = manifest.parse_file(HEALTHY)
        self.assertEqual(rotation.overdue(m, AS_OF), [])


class BlastTests(unittest.TestCase):
    def test_root_reaches_all_data_keys(self):
        m = manifest.parse_file(HEALTHY)
        g = graph.build_graph(m)
        radii = {b.key_id: b.count for b in blast.blast_radii(m, g)}
        self.assertEqual(radii["root-hsm"], 4)
        self.assertEqual(radii["mid-payments-kek"], 2)
        self.assertEqual(radii["mid-telemetry-kek"], 2)

    def test_widest_listed_first(self):
        m = manifest.parse_file(HEALTHY)
        g = graph.build_graph(m)
        radii = blast.blast_radii(m, g)
        self.assertEqual(radii[0].key_id, "root-hsm")


