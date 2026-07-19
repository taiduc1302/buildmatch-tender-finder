"""Dataset provenance, data-mode classification, truthful run metrics, and a
reliable active-dataset pointer for TENDER_FINDER / BuildMatch Tender Finder.

This module is deliberately GUI-independent and JSON-serializable so that the
desktop GUI, the CLI, run manifests, logs, and (later) a web front-end all
consume the same contract. It never imports tkinter.

Three responsibilities:

1. ``DataMode`` — the origin of the currently loaded records (synthetic demo,
   public snapshot, live public data, cached live, mixed, or unknown). A
   synthetic-only dataset can never be relabelled LIVE; a failed refresh can
   never advance the last-successful-live timestamp.
2. ``DatasetProvenance`` — everything known about one captured dataset, plus a
   ``RunMetrics`` contract whose fields always describe the *current* run (never
   a historical total) and which reconciles its own sub-totals.
3. The external active-dataset pointer — an atomically written
   ``active_dataset.json`` under the state root, with validation before
   promotion, retention of the previous pointer on failure, and recovery from a
   missing or corrupted pointer. It never overwrites the packaged synthetic
   input under ``inputs/``.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Any

from tenderfinder_package_paths import detect_package_root
from tenderfinder_runtime import (
    atomic_write_json,
    default_output_root,
    resolve_state_root,
    safe_component,
    sha256_file,
    timestamp_now,
)


# --------------------------------------------------------------------------- #
# Data modes
# --------------------------------------------------------------------------- #

MODE_SYNTHETIC = "SYNTHETIC"
MODE_PUBLIC_SNAPSHOT = "PUBLIC_SNAPSHOT"
MODE_LIVE = "LIVE"
MODE_CACHED_LIVE = "CACHED_LIVE"
MODE_MIXED = "MIXED"
MODE_UNKNOWN = "UNKNOWN"

DATA_MODES = frozenset(
    {
        MODE_SYNTHETIC,
        MODE_PUBLIC_SNAPSHOT,
        MODE_LIVE,
        MODE_CACHED_LIVE,
        MODE_MIXED,
        MODE_UNKNOWN,
    }
)

# Modes that represent (some) real public data. SYNTHETIC and UNKNOWN never do.
_REAL_DATA_MODES = frozenset({MODE_PUBLIC_SNAPSHOT, MODE_LIVE, MODE_CACHED_LIVE, MODE_MIXED})


class DataModeError(ValueError):
    """Raised when an invalid or unsafe data-mode transition is attempted."""


def normalize_mode(mode: str | None) -> str:
    value = str(mode or "").strip().upper()
    return value if value in DATA_MODES else MODE_UNKNOWN


def _humanize_date(value: str) -> str:
    # Built without platform-specific strftime codes (%-d / %#d) so the banner
    # renders identically on Windows and POSIX.
    if not value:
        return "an unknown date"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value
    return f"{parsed.strftime('%B')} {parsed.day}, {parsed.year}"


def _humanize_timestamp(value: str) -> str:
    if not value:
        return "unknown time"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value
    hour12 = parsed.hour % 12 or 12
    meridiem = "AM" if parsed.hour < 12 else "PM"
    return f"{_humanize_date(value)} at {hour12}:{parsed.minute:02d} {meridiem}"


def _age_phrase(value: str, *, now: datetime | None = None) -> str:
    if not value:
        return "an unknown time ago"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value
    reference = now or datetime.now(tz=parsed.tzinfo)
    delta = reference - parsed
    days = delta.days
    if days >= 2:
        return f"{days} days ago"
    if days == 1:
        return "1 day ago"
    hours = max(0, int(delta.total_seconds() // 3600))
    if hours >= 2:
        return f"{hours} hours ago"
    if hours == 1:
        return "1 hour ago"
    minutes = max(0, int(delta.total_seconds() // 60))
    return f"{minutes} minutes ago" if minutes else "just now"


# --------------------------------------------------------------------------- #
# Dataset provenance
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class DatasetProvenance:
    """Immutable description of one captured dataset."""

    dataset_id: str
    path: str
    data_mode: str
    capture_timestamp: str = ""
    source_ids: tuple[str, ...] = ()
    source_results: tuple[dict[str, Any], ...] = ()
    record_counts: dict[str, Any] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=lambda: {"passed": True, "errors": []})
    content_hash: str = ""
    preset_id: str = ""
    preset_version: str = ""
    last_successful_refresh: str = ""
    stale: bool = False
    created_at: str = ""
    parent_dataset_id: str = ""
    schema_version: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(self, "data_mode", normalize_mode(self.data_mode))

    @property
    def is_real_data(self) -> bool:
        return self.data_mode in _REAL_DATA_MODES

    @property
    def is_valid(self) -> bool:
        return bool(self.validation.get("passed", False))

    def banner_text(self, *, now: datetime | None = None) -> str:
        return banner_text(self, now=now)

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DatasetProvenance":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        data = {key: value for key, value in payload.items() if key in known}
        data["source_ids"] = tuple(data.get("source_ids", ()) or ())
        data["source_results"] = tuple(data.get("source_results", ()) or ())
        data.setdefault("record_counts", {})
        data.setdefault("validation", {"passed": True, "errors": []})
        return cls(**data)


def banner_text(provenance: DatasetProvenance, *, now: datetime | None = None) -> str:
    """Return the persistent, human-readable data-mode banner string."""
    mode = provenance.data_mode
    if mode == MODE_SYNTHETIC:
        return "SYNTHETIC DEMO DATA — no real opportunities"
    if mode == MODE_PUBLIC_SNAPSHOT:
        return f"PUBLIC SNAPSHOT — captured {_humanize_date(provenance.capture_timestamp)}"
    if mode == MODE_LIVE:
        return f"LIVE PUBLIC DATA — refreshed {_humanize_timestamp(provenance.capture_timestamp)}"
    if mode == MODE_CACHED_LIVE:
        anchor = provenance.last_successful_refresh or provenance.capture_timestamp
        return f"CACHED LIVE DATA — last successful refresh {_age_phrase(anchor, now=now)}"
    if mode == MODE_MIXED:
        return "MIXED DATA — live and synthetic rows are present"
    return "UNKNOWN DATA ORIGIN — review before use"


def classify_record_counts(record_counts: dict[str, Any]) -> str:
    """Infer a data mode from a per-origin record-count breakdown.

    Used when composing a dataset from multiple origins. Rules:
    * any synthetic rows mixed with real rows -> MIXED
    * only synthetic rows -> SYNTHETIC
    * only live rows -> LIVE
    * only snapshot rows -> PUBLIC_SNAPSHOT
    * only cached rows -> CACHED_LIVE
    * nothing recognizable -> UNKNOWN
    """
    synthetic = int(record_counts.get("synthetic", 0) or 0)
    live = int(record_counts.get("live", 0) or 0)
    snapshot = int(record_counts.get("snapshot", 0) or 0)
    cached = int(record_counts.get("cached", 0) or 0)
    real = live + snapshot + cached
    if synthetic and real:
        return MODE_MIXED
    if synthetic and not real:
        return MODE_SYNTHETIC
    if live and not (snapshot or cached):
        return MODE_LIVE
    if snapshot and not (live or cached):
        return MODE_PUBLIC_SNAPSHOT
    if cached and not (live or snapshot):
        return MODE_CACHED_LIVE
    if real:
        return MODE_MIXED
    return MODE_UNKNOWN


def mark_stale(provenance: DatasetProvenance) -> DatasetProvenance:
    """Return a copy re-labelled as cached/stale.

    A previously LIVE dataset that is being reused after a failed refresh
    becomes CACHED_LIVE (never stays LIVE). Snapshot/synthetic/unknown modes are
    left unchanged because "stale" is meaningless for them, but the ``stale``
    flag is still set so callers can warn.
    """
    new_mode = MODE_CACHED_LIVE if provenance.data_mode == MODE_LIVE else provenance.data_mode
    anchor = provenance.last_successful_refresh or (
        provenance.capture_timestamp if provenance.data_mode == MODE_LIVE else ""
    )
    return replace(provenance, data_mode=new_mode, stale=True, last_successful_refresh=anchor)


# --------------------------------------------------------------------------- #
# Truthful current-run metrics
# --------------------------------------------------------------------------- #


@dataclass
class RunMetrics:
    """Serializable, self-reconciling metrics for ONE operation.

    Every field describes the current run. Historical totals must live in a
    separate, explicitly labelled structure — never in these fields.
    """

    run_id: str = ""
    run_started: str = ""
    run_ended: str = ""
    # sources
    sources_selected: int = 0
    sources_attempted: int = 0
    sources_successful: int = 0
    sources_failed: int = 0
    # record flow
    records_fetched: int = 0            # newly fetched from a source this run
    records_loaded: int = 0            # replayed from an existing workbook
    records_before_dedup: int = 0
    duplicates_removed: int = 0
    normalized_records: int = 0
    records_scored: int = 0
    # routing buckets
    bid_now: int = 0
    bid_later: int = 0
    watch: int = 0
    skip: int = 0
    # per-origin breakdown
    records_synthetic: int = 0
    records_live: int = 0
    records_snapshot: int = 0
    records_cached: int = 0
    # active-dataset context
    active_dataset_id: str = ""
    active_dataset_path: str = ""
    capture_timestamp: str = ""
    data_mode: str = MODE_UNKNOWN
    stale: bool = False
    active_preset_id: str = ""
    active_preset_version: str = ""
    # outcome
    succeeded: bool = True
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RunMetrics":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        data = {key: value for key, value in payload.items() if key in known}
        if "errors" in data:
            data["errors"] = tuple(data["errors"] or ())
        return cls(**data)

    def reconciliation_errors(self) -> list[str]:
        """Return a list of internal-consistency problems (empty when truthful).

        These invariants are what prevent historical totals from silently
        leaking into current-run fields.
        """
        errors: list[str] = []
        if self.records_before_dedup != self.records_fetched + self.records_loaded:
            errors.append(
                "records_before_dedup "
                f"({self.records_before_dedup}) != records_fetched "
                f"({self.records_fetched}) + records_loaded ({self.records_loaded})"
            )
        if self.normalized_records != max(0, self.records_before_dedup - self.duplicates_removed):
            errors.append(
                "normalized_records "
                f"({self.normalized_records}) != records_before_dedup - duplicates_removed "
                f"({self.records_before_dedup - self.duplicates_removed})"
            )
        bucket_total = self.bid_now + self.bid_later + self.watch + self.skip
        if self.records_scored and bucket_total != self.records_scored:
            errors.append(
                f"bucket total ({bucket_total}) != records_scored ({self.records_scored})"
            )
        origin_total = (
            self.records_synthetic
            + self.records_live
            + self.records_snapshot
            + self.records_cached
        )
        if origin_total and self.normalized_records and origin_total != self.normalized_records:
            errors.append(
                f"origin breakdown total ({origin_total}) != normalized_records "
                f"({self.normalized_records})"
            )
        if self.sources_successful + self.sources_failed > self.sources_attempted:
            errors.append(
                "sources_successful + sources_failed exceeds sources_attempted"
            )
        if not self.succeeded and (self.records_fetched or self.records_live):
            errors.append(
                "a failed run must not report fetched/live records as its own result"
            )
        return errors

    def is_reconciled(self) -> bool:
        return not self.reconciliation_errors()


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


# --------------------------------------------------------------------------- #
# Active-dataset pointer (external, atomic, recoverable)
# --------------------------------------------------------------------------- #

_POINTER_NAME = "active_dataset.json"
_POINTER_BACKUP = "active_dataset.json.bak"


def datasets_root(*, state_root: str | Path | None = None, package_root: str | Path | None = None,
                  create: bool = False) -> Path:
    """Return ``<state-root>/datasets`` (outside the package repository)."""
    root = resolve_state_root(state_root, mode="datasets", package_root=package_root)
    path = root / "datasets"
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def _pointer_path(datasets_dir: Path) -> Path:
    return datasets_dir / _POINTER_NAME


def _backup_path(datasets_dir: Path) -> Path:
    return datasets_dir / _POINTER_BACKUP


def dataset_manifest_path(provenance: DatasetProvenance, datasets_dir: Path) -> Path:
    return datasets_dir / f"dataset_{safe_component(provenance.dataset_id)}.json"


def new_dataset_id(prefix: str = "dataset", *, now: datetime | None = None) -> str:
    stamp = (now or datetime.now()).strftime("%Y%m%d_%H%M%S")
    return f"{safe_component(prefix)}_{stamp}"


def validate_provenance_for_promotion(provenance: DatasetProvenance) -> list[str]:
    """Return a list of reasons the dataset must NOT be promoted (empty = ok)."""
    errors: list[str] = []
    if not provenance.dataset_id:
        errors.append("dataset_id is required")
    if provenance.data_mode not in DATA_MODES:
        errors.append(f"unknown data_mode: {provenance.data_mode!r}")
    if not provenance.is_valid:
        errors.append("dataset validation did not pass")
    total = int(provenance.record_counts.get("total", 0) or 0)
    if total <= 0:
        errors.append("dataset is empty (record_counts.total <= 0)")
    if provenance.path:
        path = Path(provenance.path)
        if not path.exists():
            errors.append(f"dataset file does not exist: {provenance.path}")
    return errors


@dataclass(frozen=True)
class PromotionResult:
    promoted: bool
    reason: str
    active: DatasetProvenance | None
    previous: DatasetProvenance | None
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "promoted": self.promoted,
            "reason": self.reason,
            "active": self.active.to_dict() if self.active else None,
            "previous": self.previous.to_dict() if self.previous else None,
            "errors": list(self.errors),
        }


def promote_dataset(
    provenance: DatasetProvenance,
    *,
    state_root: str | Path | None = None,
    package_root: str | Path | None = None,
    validate: bool = True,
) -> PromotionResult:
    """Atomically make ``provenance`` the active dataset.

    Validation runs first. On failure the previous active pointer is left
    untouched (the promotion is refused, not half-applied). On success the
    dataset manifest is written, the previous pointer is backed up, and the
    pointer is replaced atomically.
    """
    datasets_dir = datasets_root(state_root=state_root, package_root=package_root, create=True)
    previous = load_active_dataset(state_root=state_root, package_root=package_root)

    errors = validate_provenance_for_promotion(provenance) if validate else []
    if errors:
        return PromotionResult(
            promoted=False,
            reason="validation_failed",
            active=previous,
            previous=previous,
            errors=tuple(errors),
        )

    stamped = provenance
    if not stamped.created_at:
        stamped = replace(stamped, created_at=timestamp_now())
    if previous is not None and not stamped.parent_dataset_id:
        stamped = replace(stamped, parent_dataset_id=previous.dataset_id)

    # Write the immutable dataset manifest first.
    atomic_write_json(dataset_manifest_path(stamped, datasets_dir), stamped.to_dict())

    # Back up the current pointer so a corrupted write can be rolled back.
    pointer = _pointer_path(datasets_dir)
    if pointer.exists():
        try:
            _backup_path(datasets_dir).write_text(
                pointer.read_text(encoding="utf-8"), encoding="utf-8"
            )
        except OSError:
            pass

    atomic_write_json(pointer, stamped.to_dict())
    return PromotionResult(
        promoted=True,
        reason="promoted",
        active=stamped,
        previous=previous,
    )


def load_active_dataset(
    *,
    state_root: str | Path | None = None,
    package_root: str | Path | None = None,
) -> DatasetProvenance | None:
    """Load the active dataset pointer, recovering from corruption.

    * missing pointer -> ``None``
    * corrupted pointer -> restore from ``.bak`` if valid, else ``None``
    """
    datasets_dir = datasets_root(state_root=state_root, package_root=package_root, create=False)
    pointer = _pointer_path(datasets_dir)
    provenance = _read_pointer(pointer)
    if provenance is not None:
        return provenance
    # Attempt recovery from the backup pointer.
    backup = _backup_path(datasets_dir)
    recovered = _read_pointer(backup)
    if recovered is not None:
        try:
            atomic_write_json(pointer, recovered.to_dict())
        except OSError:
            pass
        return recovered
    return None


def _read_pointer(path: Path) -> DatasetProvenance | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or "dataset_id" not in payload:
        return None
    try:
        return DatasetProvenance.from_dict(payload)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- #
# Packaged synthetic input detection
# --------------------------------------------------------------------------- #


def packaged_synthetic_review_path(package_root: str | Path | None = None) -> Path:
    root = detect_package_root(Path(package_root).resolve() if package_root else None)
    return (root / "inputs" / "all_live_review.xlsx").resolve()


def is_packaged_synthetic(path: str | Path, *, package_root: str | Path | None = None) -> bool:
    """True when ``path`` is the packaged synthetic review workbook.

    The packaged ``inputs/all_live_review.xlsx`` is synthetic demo data and must
    never be presented as live.
    """
    try:
        return Path(path).resolve() == packaged_synthetic_review_path(package_root)
    except (OSError, ValueError):
        return False


def synthetic_provenance_for_packaged_input(
    *, package_root: str | Path | None = None, record_total: int = 0
) -> DatasetProvenance:
    """Build a SYNTHETIC provenance record for the packaged demo workbook."""
    path = packaged_synthetic_review_path(package_root)
    content_hash = sha256_file(path) if path.exists() else ""
    return DatasetProvenance(
        dataset_id="packaged_synthetic_all_live_review",
        path=str(path),
        data_mode=MODE_SYNTHETIC,
        capture_timestamp="",
        record_counts={"total": int(record_total), "synthetic": int(record_total)},
        validation={"passed": True, "errors": []},
        content_hash=content_hash,
    )
