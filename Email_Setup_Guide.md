# Email Setup Guide

## Manual Email Alert Import

1. Open TENDER_FINDER Launcher.
2. Go to `Email Alert Intake`.
3. Click `Create / Open Email Import Folder`.
4. Save or copy approved `.eml` alert files into the opened folder.
5. Click `Test Email Import`.
6. Review parsed and rejected counts.
7. Click `Run Demo With Email Alerts`.

## Alternate Folder Option

- You may click `Select Existing Email Folder` and choose a OneDrive or local folder instead.
- TENDER_FINDER saves that selection in `user_data/tenderfinder_user_config.json` inside the runtime package.

## Important Notes

- Real emails are not included in the ZIP package.
- TENDER_FINDER does not need mailbox passwords for manual import.
- Gmail OAuth, Microsoft OAuth, and IMAP are not implemented in this patch.
- Test Email Import is dry-run only and does not move, rename, or delete your `.eml` files.
