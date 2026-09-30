import tempfile
import unittest
import zipfile
from pathlib import Path

from jar_intake import scan_candidate


class JarIntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def make_jar(self, name: str, manifest: bytes, entries: dict[str, bytes]) -> Path:
        path = Path(self.temp_dir.name) / name
        with zipfile.ZipFile(path, "w") as jar:
            jar.writestr("META-INF/MANIFEST.MF", manifest)
            for entry_name, payload in entries.items():
                jar.writestr(entry_name, payload)
        return path

    def test_requires_manifest_and_internal_version_for_direct_match(self):
        jar = self.make_jar(
            "HZW_E62.jar",
            b"MIDlet-Name: HZW\nMIDlet-Version: 8.60.0\n",
            {
                "a.class": (
                    b"prefix 860.1HZ0000.NON5800.CT suffix "
                    b"http://example.invalid/gate"
                )
            },
        )

        report = scan_candidate(jar, source_url="https://example.invalid/archive")

        self.assertEqual(report["evidence_grade"], "V860_DIRECT_BINARY_MATCH")
        self.assertEqual(report["matched_internal_versions"], ["860.1HZ0000.NON5800.CT"])
        self.assertEqual(report["network_endpoints"], ["http://example.invalid/gate"])
        self.assertEqual(report["provenance"]["source_url"], "https://example.invalid/archive")

    def test_manifest_only_remains_unverified_candidate(self):
        jar = self.make_jar(
            "candidate.jar",
            b"MIDlet-Version: 8.60.0\n",
            {"a.class": b"no internal build marker"},
        )

        report = scan_candidate(jar)

        self.assertEqual(
            report["evidence_grade"],
            "JAR_CANDIDATE_NEEDS_INTERNAL_VERSION",
        )

    def test_conflicting_manifest_is_version_drift(self):
        jar = self.make_jar(
            "old.jar",
            b"MIDlet-Version: 8.59.0\n",
            {"a.class": b"859.1HZ0000.NON5800.CT"},
        )

        report = scan_candidate(jar)

        self.assertEqual(report["evidence_grade"], "VERSION_DRIFT")
        self.assertEqual(report["matched_internal_versions"], ["859.1HZ0000.NON5800.CT"])

    def test_unrelated_urls_and_duplicates_are_filtered(self):
        jar = self.make_jar(
            "candidate.jar",
            b"MIDlet-Version: 8.60.0\n",
            {
                "a.class": b"http://a.example/x\x00http://a.example/x",
                "readme.txt": b"visit https://b.example/y). not-a-url",
            },
        )

        report = scan_candidate(jar)

        self.assertEqual(
            report["network_endpoints"],
            ["http://a.example/x", "https://b.example/y"],
        )


if __name__ == "__main__":
    unittest.main()
