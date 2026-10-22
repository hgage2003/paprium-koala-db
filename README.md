# Paprium downloader database

MiSTer Downloader database for [thekoalakoa/Paprium_MiSTer](https://github.com/thekoalakoa/Paprium_MiSTer). It follows the latest `Paprium_MiSTer_*.zip` release and installs the core under **Custom Cores**:

```
_Custom Cores/Paprium.mgl
_Custom Cores/Cores/Paprium.rbf
```

`Paprium.md` and `paprium.pcm` stay yours, in `games/Paprium/`. The `cpu-mate-brain` zip is not installed.

This is a separate database from Update All's Paprium MegaDrive entry (`MultiDatabases/paprium`), which continues to install Pezz82's core.

## Use it on the MiSTer

1. Copy `downloader_paprium_koala.ini` to `/media/fat/` on the SD card. It contains:

```ini
[thekoalakoa/Paprium_MiSTer]
db_url = https://raw.githubusercontent.com/hgage2003/paprium-koala-db/main/dist/db.json
```

2. Run Update All or the MiSTer Downloader. The section is not one of Update All's own databases, so later runs keep it.
3. Launch **Paprium** from the Custom Cores menu.
