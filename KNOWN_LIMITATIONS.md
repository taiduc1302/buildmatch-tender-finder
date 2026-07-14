# Known Limitations

- Manual Email Alert Import reads approved `.eml` files only. It does not connect directly to Gmail, Outlook, or IMAP in this patch.
- TENDER_FINDER does not move or delete user email files during dry-run or normal demo runs in this patch.
- Some tender emails may still lack contact details or exact closing dates if the portal email itself does not expose them.
- BC Bid live access can still be affected by browser-check or CAPTCHA behavior on the public site.
- `processed` and `rejected` folders are created now for UX clarity and future options, but TENDER_FINDER does not copy messages into them automatically in this patch.
