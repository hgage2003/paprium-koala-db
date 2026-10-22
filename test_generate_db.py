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
    def test_selects_paprium_zip_by_name(self) -> None:
        core = zip_bytes({"_Console/Paprium.rbf": b"core"})
        assets = [
            {"name": "cpu-mate-brain_0.2.6.zip", "browser_download_url": "https://example.com/brain.zip"},
            {"name": "Paprium_MiSTer_0.2.6.zip", "browser_download_url": "https://example.com/core.zip"},
        ]

        def fetch(url: str) -> bytes:
            self.assertEqual("https://example.com/core.zip", url)
            return core

        url, data = generate_db.choose_release_zip(assets, fetch)

        self.assertEqual("https://example.com/core.zip", url)
        self.assertEqual(core, data)

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
        self.assertNotIn("reboot", installed["_Custom Cores/Cores/Paprium.rbf"])
        self.assertIn("_Custom Cores/Paprium.mgl", database["files"])
        self.assertIn("games/Paprium", database["folders"])
        self.assertNotIn("games/Paprium/Paprium", database["folders"])
        self.assertNotIn("_Console/Paprium.mgl", json.dumps(database))


if __name__ == "__main__":
    unittest.main()
