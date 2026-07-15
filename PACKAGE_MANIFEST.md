# Clean Release Manifest

The authoritative release manifest is generated outside the repository by:

```powershell
.\.venv\Scripts\python.exe scripts\build_clean_release.py --output-dir C:\tenderfinder_out\release --require-clean
```

For release `internal-weekly-beta-v1`, the builder creates:

- `Tender_Finder_internal-weekly-beta-v1.zip`;
- `.zip.sha256` checksum sidecar;
- `.manifest.json` with release version, source commit SHA, clean/dirty source
  status, entry count, archive size, and checksum;
- inside the ZIP: `RELEASE_METADATA.json`,
  `INCLUDED_FILES_MANIFEST.txt`, and `EXCLUDED_CATEGORY_SUMMARY.txt`.

The allowlist includes only install/launch/config/operate/test/document files. It also
includes `run_tenderfinder_demo.bat` and `run_tenderfinder_demo_fast.bat` as tested
compatibility launchers; `Launch_TENDER_FINDER_GUI.bat` remains the sole recommended
double-click entry point.
It excludes Git metadata, virtual environments, Codex/test caches, runtime
outputs/state, user/email/browser data, source-page downloads, temporary/local
environment files, credentials, ZIPs, and historical generated output.

Validate CRC, paths, duplicate entries, included-file hashes, and extraction
with `scripts/verify_clean_release.py`. The release is a clickable Python
source application with first-run installation requirements, not an EXE.
