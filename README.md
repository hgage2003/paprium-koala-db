# Paprium downloader database

MiSTer Downloader database for [thekoalakoa/Paprium_MiSTer](https://github.com/thekoalakoa/Paprium_MiSTer). It follows the latest `Paprium_MiSTer_*.zip` release and installs the core under **Custom Cores**:

```
_Custom Cores/Paprium.mgl
_Custom Cores/Cores/Paprium.rbf
```

`Paprium.md` and `paprium.pcm` stay yours, in `games/Paprium/`. The `cpu-mate-brain` zip is not installed.

This is a separate database from Update All's Paprium MegaDrive entry (`MultiDatabases/paprium`), which continues to install Pezz82's core.

## Use it on the MiSTer

1. Put your GitHub repository slug in `github_repository.txt`, for example `yourname/paprium-koala-db`.
2. Run `python generate_db.py` and push this repository to GitHub. The Actions workflow also rebuilds `dist/db.json` every day and whenever `main` changes.
3. Copy `downloader_paprium_koala.ini` to `/media/fat/` on the SD card. It contains:

```ini
[thekoalakoa/Paprium_MiSTer]
db_url = https://raw.githubusercontent.com/OWNER/paprium-koala-db/main/dist/db.json
```

4. Run Update All or the MiSTer Downloader. The section is not one of Update All's own databases, so later runs keep it.
5. Launch **Paprium** from the Custom Cores menu.

If a manual install left `_Console/Paprium.rbf` and `_Console/Paprium.mgl` on the card, delete those two files. This database does not replace them.
