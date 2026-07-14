from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tenderfinder_demo_three_buckets import mirror_name_for  # noqa: E402

# Patch 5.17 replaced a hardcoded if/elif chain (one manually-added constant
# per patch, P57_REPO_MIRROR ... P516_REPO_MIRROR) with a generic function
# that derives the mirror folder name from the out_dir text itself. This
# test proves the new function reproduces the OLD chain's output exactly
# for every historical patch number it used to handle (5.6 through 5.16),
# so this is a verified refactor, not a behavior change.
#
# Each entry: (out_dir name as it has actually been passed via --out-dir in
# past patches, expected mirror folder name the old hardcoded chain produced).
HISTORICAL_CASES = [
    ("demo_p57", "demo_p57"),
    ("demo_p57_fast", "demo_p57"),
    ("demo_p59", "demo_p59"),
    ("demo_p510", "demo_p510"),
    ("demo_p511", "demo_p511"),
    ("demo_p512", "demo_p512"),
    ("demo_p513", "demo_p513"),
    ("demo_p514", "demo_p514"),
    ("demo_p515", "demo_p515"),
    ("demo_p516", "demo_p516"),
    # Full path forms, matching how mirror_name_for(str(args.out_dir)) is
    # also called with the raw --out-dir argument, not just out_dir.name.
    (r"C:\tenderfinder_out\demo_p516", "demo_p516"),
    ("C:/tenderfinder_out/demo_p513", "demo_p513"),
]

# Alternate spellings the old chain also recognized via its "5_NN"/"5-NN"
# substring checks, even though no real out_dir has ever used them.
ALTERNATE_SPELLING_CASES = [
    ("patch5_16", "demo_p516"),
    ("5-16", "demo_p516"),
    ("something_5_9_here", "demo_p59"),
]

# Names with no recognizable patch-number pattern must NOT fall back to any
# existing historical folder (this was the actual bug in Patches 5.14/5.15):
# they must derive a name from themselves instead.
FALLBACK_CASES = [
    ("demo_gui_20260701_120000", "demo_gui_20260701_120000"),
    ("my_custom_run", "demo_my_custom_run"),
]


def main() -> int:
    for out_dir_name, expected in HISTORICAL_CASES:
        got = mirror_name_for(out_dir_name)
        assert got == expected, f"{out_dir_name!r}: expected {expected!r}, got {got!r}"

    for text, expected in ALTERNATE_SPELLING_CASES:
        got = mirror_name_for(text)
        assert got == expected, f"{text!r}: expected {expected!r}, got {got!r}"

    for out_dir_name, expected in FALLBACK_CASES:
        got = mirror_name_for(out_dir_name)
        assert got == expected, f"{out_dir_name!r}: expected {expected!r}, got {got!r}"
        assert got != "demo_p57", f"{out_dir_name!r} must not silently fall back to demo_p57"

    print(f"Checked {len(HISTORICAL_CASES)} historical patch names, "
          f"{len(ALTERNATE_SPELLING_CASES)} alternate spellings, "
          f"{len(FALLBACK_CASES)} no-pattern fallback cases.")
    print("Mirror name generic derivation test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
