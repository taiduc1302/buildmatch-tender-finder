# Source Status Explanation

`config/sources.csv` is the single runtime source registry. These dimensions
must not be conflated:

- **configured**: a row exists;
- **enabled**: `active=Y`;
- **runtime-eligible**: the row is enabled, supported, sufficiently configured,
  and not held by an operational status;
- **offline fixture pass**: its adapter parser normalized a sanitized fixture;
- **verified live**: an explicit current one-source live test reached a public
  endpoint and normalized relevant records.

Operational status vocabulary:

- `verified_live` — current structured live proof succeeded;
- `ready_for_live_test` — config is runnable but current live proof is absent;
- `config_valid_only` — schema is valid, operational/parser proof incomplete;
- `manual_only` — operator/manual portal workflow;
- `needs_configuration` — endpoint or required adapter details incomplete;
- `blocked` — known access/network policy hold;
- `wrong_source` — endpoint was shown to contain the wrong dataset/content;
- `deprecated` — intentionally retired.

Historical `LIVE`, `CONFIRMED`, or pull-count text is retained in legacy fields
for provenance but does not automatically become `verified_live`.

GUI actions are intentionally distinct:

- **Validate Configuration**: no parser, no network;
- **Offline Parser Test**: real parser/normalizer against a local fixture;
- **Live Source Test**: explicit selected-source network operation and the only
  path to `verified_live`.

The GUI summary is authoritative for current counts. Do not claim all 39
configured rows work merely because they exist or are enabled.

For ArcGIS development sources, `test_query_where` and
`test_query_order_by` may narrow the explicit bounded Live Source Test to a
representative current sample. They affect only the controlled test query, not
the source identity. `test_query_where` is length/control/semicolon validated;
`test_query_order_by` accepts only field names with optional `ASC`/`DESC`.
After a test, `last_good_endpoint` keeps the reusable base endpoint while the
result's `final_validated_url` records the full validated request URL for audit.

Email Alert Intake statuses remain separate from source operational status:

- `EMAIL_INTAKE_NO_FILES`
- `EMAIL_INTAKE_PARSED_ROWS`
- `EMAIL_INTAKE_PARSE_ZERO_ROWS`
- `EMAIL_INTAKE_REJECTED_FILES`
- `EMAIL_INTAKE_SKIPPED_NO_FOLDER`
