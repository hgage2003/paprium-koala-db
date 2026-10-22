import io
import json
import unittest
import zipfile
from pathlib import Path

import generate_db


def zip_bytes(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return buffer.getvalue()


class ChooseReleaseZipTest(unittest.TestCase):
    def test_skips_brain_zip_and_selects_core_zip(self) -> None:
        brain = zip_bytes({"cpu-mate-brain/brain.bin": b"brain"})
        core = zip_bytes(
            {
                "_Console/Paprium.rbf": b"core",
                "_Console/Paprium.mgl": b"<mistergamedescription/>",
            }
        )
        assets = [
            {"name": "cpu-mate-brain_0.2.6.zip", "browser_download_url": "https://example.com/brain.zip"},
            {"name": "Paprium_MiSTer_0.2.6.zip", "browser_download_url": "https://example.com/core.zip"},
        ]
        blobs = {
            "https://example.com/brain.zip": brain,
            "https://example.com/core.zip": core,
        }

        url, data, rbf_path = generate_db.choose_release_zip(assets, blobs.get)

        self.assertEqual("https://example.com/core.zip", url)
        self.assertEqual(core, data)
        self.assertEqual("_Console/Paprium.rbf", rbf_path)

    def test_database_installs_under_custom_cores(self) -> None:
        core = zip_bytes(
            {
                "_Console/Paprium.rbf": b"core-bytes",
                "_Console/Paprium.mgl": b"upstream",
            }
        )
        mgl = Path("Paprium.mgl").read_bytes().replace(b"\r\n", b"\n")
        database = generate_db.build_database(
            repository="OWNER/paprium-koala-db",
            tag="0.2.6",
            archive_url="https://github.com/thekoalakoa/Paprium_MiSTer/releases/download/0.2.6/Paprium_MiSTer_0.2.6.zip",
            archive_data=core,
            rbf_path="_Console/Paprium.rbf",
            rbf_data=b"core-bytes",
            mgl_data=mgl,
            timestamp=1,
        )

        self.assertEqual("thekoalakoa/Paprium_MiSTer", database["db_id"])
        self.assertIn("_Custom Cores/Cores/Paprium", mgl.decode())
        self.assertNotIn("_Console/Paprium", mgl.decode().split("paprium.pcm")[0])
        installed = database["archives"]["release"]["summary_inline"]["files"]
        self.assertIn("_Custom Cores/Cores/Paprium.rbf", installed)
        self.assertEqual("_Console/Paprium.rbf", installed["_Custom Cores/Cores/Paprium.rbf"]["arc_at"])
        self.assertTrue(installed["_Custom Cores/Cores/Paprium.rbf"]["reboot"])
        self.assertIn("_Custom Cores/Paprium.mgl", database["files"])
        self.assertIn("games/Paprium/Paprium", database["folders"])
        self.assertNotIn("_Console/Paprium.mgl", json.dumps(database))


if __name__ == "__main__":
    unittest.main()
