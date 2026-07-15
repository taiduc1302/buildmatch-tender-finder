# Baseline and protected-file evidence

Verified on 2026-07-15 (America/Vancouver).

## Git baseline

- Repository: `C:\Projects\buildmatch-tender-finder`.
- Starting local `main`: `1780ad6a112dd7ca398d705b1f8ffb348e7aaf6a`.
- Starting `origin/main`: `1780ad6a112dd7ca398d705b1f8ffb348e7aaf6a`.
- No pre-stabilization push or backup branch was required because local and
  remote main already matched.
- Remote annotated recovery tag:
  `internal-beta-pre-stabilization-1780ad6`.
- Stabilization branch: `stabilize/internal-weekly-beta`.
- Repository-local future author:
  `taiduc1302 <38831891+taiduc1302@users.noreply.github.com>`.
- Shared history was not rewritten; no force push or rebase was used.

## Protected files

The authoritative offline Self-Test hashed each protected file before and
after execution and found no change:

| File | SHA-256 |
| --- | --- |
| `config/keywords.xlsx` | `ea7e98097552d099f719b5a54b131386ed37a6202df3b904e07744aa11df429a` |
| `config/sources.csv` | `1901c7cc73e8e240d74d8e534924c7b814f5ad32b68ee442faa52138f40f0306` |
| `01 Code/tenderfinder_agent2.py` | `5042fae15f64ce3acf822f538749f67f2b2569e16c13e6b251c8434be9d97137` |
| `Launch_TENDER_FINDER_GUI.bat` | `ef9176ae45313e90858f9430eea11106e7062c35b7c9abf36070311a04206371` |

Self-Test manifest:
`C:\tenderfinder_out\self_test\self_test_20260715_101135_2ad06d9f\run_manifest.json`.
