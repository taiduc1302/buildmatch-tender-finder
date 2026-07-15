# Known Limitations

- Manual Email Alert Import reads approved `.eml` files only. It does not connect directly to Gmail, Outlook, or IMAP in this patch.
- TENDER_FINDER does not move or delete user email files during dry-run or normal runs.
- Some tender emails may still lack contact details or exact closing dates if the portal email itself does not expose them.
- BC Bid live access can still be affected by browser-check or CAPTCHA behavior on the public site.
- A historical Vancouver permit without the persisted `keyword_scoring_text`
  snapshot can refresh score and labels, but its old source-specific tier is
  retained and explicitly marked as a legacy exception. Newly collected rows
  persist the snapshot and are fully recalculated.
- A source using the `custom` adapter may be saved as a disabled draft, but it
  cannot be enabled until a compatible parser adapter is implemented.
- Live public pages can change structure, block automation, or expose no open
  opportunities. Source tests report those conditions; they do not prove that
  a portal will remain available later.
- The application is a single-user Windows desktop/Excel workflow. It has no
  hosted web UI, database-backed multi-user state, or automatic BuildMatch/
  Neon synchronization in this release.
- `processed` and `rejected` email folders are created for clarity and future options, but TENDER_FINDER does not copy messages into them automatically.
