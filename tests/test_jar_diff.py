import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

from jar_diff import compare_jars, inventory_jar, parse_manifest, write_report


class JarDiffTests(unittest.TestCase):
    def make_jar(self, name: str, entries: dict[str, bytes]) -> Path:
        path = Path(self.temp_dir.name) / name
        with zipfile.ZipFile(path, "w") as jar:
            for entry_name, payload in entries.items():
                jar.writestr(entry_name, payload)
        return path

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def test_parse_manifest_unfolds_continuation_lines(self):
        manifest = b"MIDlet-Name: HZW\r\nMIDlet-Version: 8.60.0\r\nLong: abc\r\n def\r\n\r\n"
        self.assertEqual(
            parse_manifest(manifest),
            {"MIDlet-Name": "HZW", "MIDlet-Version": "8.60.0", "Long": "abcdef"},
        )

    def test_inventory_records_hash_manifest_classes_and_resources(self):
        jar = self.make_jar(
            "e62.jar",
            {
                "META-INF/MANIFEST.MF": b"MIDlet-Name: HZW\nMIDlet-Version: 8.60.0\n",
                "a.class": b"class-a",
                "d/10.tij": b"tiles",
            },
        )

        inventory = inventory_jar(jar)

        self.assertEqual(inventory["manifest"]["MIDlet-Version"], "8.60.0")
        self.assertEqual(inventory["classes"], ["a.class"])
        self.assertEqual(inventory["resources"], ["META-INF/MANIFEST.MF", "d/10.tij"])
        self.assertEqual(len(inventory["sha256"]), 64)
        self.assertEqual(len(inventory["entries"]["a.class"]), 64)

    def test_compare_jars_separates_identical_changed_and_unique_paths(self):
        manifest = b"MIDlet-Name: HZW\nMIDlet-Version: 8.60.0\n"
        first = self.make_jar(
            "e62.jar",
            {
                "META-INF/MANIFEST.MF": manifest,
                "a.class": b"same",
                "d/10.tij": b"e62",
                "e62-only.png": b"e62-only",
            },
        )
        second = self.make_jar(
            "n73.jar",
            {
                "META-INF/MANIFEST.MF": manifest,
                "a.class": b"same",
                "d/10.tij": b"n73",
                "n73-only.png": b"n73-only",
            },
        )

        report = compare_jars([first, second])

        self.assertEqual(report["jar_count"], 2)
        self.assertEqual(
            report["identical_in_all"],
            ["META-INF/MANIFEST.MF", "a.class"],
        )
        self.assertEqual(report["changed_shared_paths"], ["d/10.tij"])
        self.assertEqual(report["unique_paths"]["e62.jar"], ["e62-only.png"])
        self.assertEqual(report["unique_paths"]["n73.jar"], ["n73-only.png"])

    def test_compare_three_jars_reports_paths_present_in_only_a_subset(self):
        first = self.make_jar(
            "e62.jar",
            {"shared.class": b"same", "large-screen.png": b"e62"},
        )
        second = self.make_jar(
            "n73.jar",
            {"shared.class": b"same", "large-screen.png": b"n73"},
        )
        third = self.make_jar(
            "s700.jar",
            {"shared.class": b"same", "small-screen.png": b"s700"},
        )

        report = compare_jars([first, second, third])

        self.assertEqual(
            report["partially_shared_paths"],
            {
                "large-screen.png": {
                    "present_in": ["e62.jar", "n73.jar"],
                    "content_identical": False,
                }
            },
        )
        self.assertEqual(report["unique_paths"]["s700.jar"], ["small-screen.png"])

    def test_duplicate_basenames_receive_distinct_stable_ids(self):
        first_dir = Path(self.temp_dir.name) / "e62"
        second_dir = Path(self.temp_dir.name) / "n73"
        first_dir.mkdir()
        second_dir.mkdir()
        first = first_dir / "client.jar"
        second = second_dir / "client.jar"
        with zipfile.ZipFile(first, "w") as jar:
            jar.writestr("e62-only", b"e62")
        with zipfile.ZipFile(second, "w") as jar:
            jar.writestr("n73-only", b"n73")

        report = compare_jars([first, second])

        ids = [jar["id"] for jar in report["jars"]]
        self.assertEqual(len(set(ids)), 2)
        self.assertEqual(set(report["unique_paths"]), set(ids))
        self.assertEqual(
            {tuple(paths) for paths in report["unique_paths"].values()},
            {("e62-only",), ("n73-only",)},
        )

    def test_report_refuses_to_overwrite_an_input_jar(self):
        first = self.make_jar("e62.jar", {"a": b"a"})
        second = self.make_jar("n73.jar", {"a": b"a"})
        with self.assertRaisesRegex(ValueError, "same file"):
            write_report([first, second], first)

    def test_compare_rejects_the_same_jar_path_twice(self):
        jar = self.make_jar("e62.jar", {"a": b"a"})
        with self.assertRaisesRegex(ValueError, "duplicate JAR input"):
            compare_jars([jar, jar])

    def test_inventory_rejects_duplicate_zip_entry_names(self):
        path = Path(self.temp_dir.name) / "duplicate.jar"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(path, "w") as jar:
                jar.writestr("a.class", b"first")
                jar.writestr("a.class", b"second")

        with self.assertRaisesRegex(ValueError, "duplicate JAR entry"):
            inventory_jar(path)


if __name__ == "__main__":
    unittest.main()
