# Final Architecture and Data Flow

## Product workflow

```
Contractor profile (preset)
      │
      ▼
Public opportunities  ──► deterministic filtering & scoring ──► ranked results
      │                                                              │
      │                                                              ▼
      │                                              OpenAI analysis of a selected opportunity
      │                                                              │
      ▼                                                              ▼
active dataset (provenance + data mode)              evidence-based recommendation (advisory)
                                                                     │
                                                                     ▼
                                                      estimator review / export
```

## Layers

1. **Scoring engine (unchanged authority)** — `tenderfinder_guards.score_civil_fit_breakdown`
   + `tenderfinder_demo_three_buckets` routing. Base 35 + weighted positive/negative
   + one geography + one client bonus, clamped 0–100; buckets by route with a
   fit≥50 gate. This remains the single source of truth for the fit score,
   matched terms, and routing bucket.

2. **Keyword configuration** — `tenderfinder_keywords_config`. Fully data-driven.
   Presets are alternate validated workbooks selected via the `path`/env-var it
   already honours; no scoring-code branching was added.

3. **Service/controller layer (new, GUI-independent, JSON-serializable)**
   - `tenderfinder_data_modes` — data modes, `DatasetProvenance`, `RunMetrics`,
     banner text, atomic active-dataset pointer.
   - `tenderfinder_presets` — contractor-profile registry over the keyword system.
   - `tenderfinder_refresh_service` — development-data refresh orchestration.
   - `tenderfinder_ai_analysis` / `tenderfinder_ai_controller` — OpenAI analysis.
   - `tenderfinder_snapshot` — public-snapshot demo.
   - `tenderfinder_engine` — existing run/self-test/source-test contract.

4. **Presentation (thin)** — `tenderfinder_launcher_gui` (tkinter). Calls the
   services through display-agnostic module-level helpers; no business logic in
   the widget layer.

## State layout (external, never inside the package)

```
<state-root>/                     # ~/tenderfinder_out on POSIX, C:\tenderfinder_out on Windows
  datasets/
    development_review_<run>.xlsx   # timestamped captured datasets
    dataset_<run>.json              # immutable per-dataset manifest
    active_dataset.json             # atomic pointer to the active dataset
    active_dataset.json.bak         # previous pointer (rollback/recovery)
    runs/<run>/run_manifest.json    # per-refresh run manifest
    runs/<run>/output/ranked.xlsx   # scored output workbook
  ai_analysis_cache/<key>.json      # cached AI analyses (never store the API key)
  state/…                           # existing engine/keyword state
```

The packaged synthetic input `inputs/all_live_review.xlsx` and the committed
config workbooks are read-only from the product's perspective and are never
overwritten by a refresh.
