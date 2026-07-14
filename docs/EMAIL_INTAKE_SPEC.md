# TENDER_FINDER Email Intake Spec - Patch 5.7 Design

## Purpose

Portal tender volume for bidsandtenders.ca, BidCentral, and some BC Bid workflows is best accessed by user-approved email alerts rather than authenticated scraping. Patch 5.6 does not read inboxes. This spec defines how a future `tenderfinder_email_intake` module should parse alert emails after explicit user approval.

## Guardrails

- Do not store portal usernames or passwords.
- Do not log into bidsandtenders.ca, BidCentral, BC Bid, Bonfire, MERX, Ariba, or Jaggaer.
- Do not bypass CAPTCHA, browser checks, or authenticated pages.
- Read only alert emails that the user explicitly authorizes.
- Preserve one-click provenance: keep the original email message ID, sender, received date, and tender URL.

## Sender Patterns

| Portal | Expected Sender / Domain Pattern | Notes |
|---|---|---|
| BC Bid | `*@bcbid.gov.bc.ca`, `*@gov.bc.ca` | Public browse is no-login; registration may enable notifications. |
| bidsandtenders.ca | `*@bidsandtenders.ca`, owner-branded portal notifications | Common municipal source for Surrey, Maple Ridge, Township Langley, Richmond, Pitt Meadows, and Fraser Health-style alerts. |
| BidCentral | `*@bidcentral.ca` | Construction bid network and membership-driven alerts. |
| CivicInfo BC | `*@civicinfo.bc.ca` | Local-government aggregator if alerts are enabled or forwarded. |

## Fields To Extract

| BID NOW Column | Extraction Rule |
|---|---|
| `source` | Portal name inferred from sender/domain. |
| `issuer` | Municipality/public body from sender display name, subject prefix, or email body label. |
| `tender_title` | Subject line after removing alert prefixes, or body field labeled title/opportunity/project. |
| `civil_relevant` | Existing TENDER_FINDER civil keyword scoring over title, body snippet, and category text. |
| `status` | `open` unless email says closed/cancelled/awarded or closing date is past. |
| `closing_date` | Regex over subject/body for closing/deadline/submission date. |
| `contact_email` | Email regex over body; blank if not present. |
| `contact_phone` | North American phone regex over body; blank if not present. |
| `related_lead` | Same conservative municipality + address/keyword matching used by Track B. |
| `url` | First portal/opportunity URL in body; keep tracking URL only if no clean URL exists. |
| `found_via` | `email_alert`. |
| `snippet` | First 500 visible body characters after stripping signatures and boilerplate. |

## Mapping Flow

1. Search only approved alert labels or sender domains.
2. Parse each message into normalized tender fields.
3. Deduplicate by `source + issuer + tender_title + closing_date + url`.
4. Score civil relevance with the Patch 5.6 keyword set.
5. Route civil/open rows to BID NOW; keep non-civil rows available for audit.
6. Append provenance: message ID, received timestamp, sender, and URL.

## Recommended Patch 5.7 Work

- Add a dry-run parser using saved `.eml` fixtures supplied by the user.
- Add an explicit user approval step before connecting to any mailbox.
- Add a `found_via=email_alert` source log section.
- Add a workbook audit tab for parsed alert emails and rejected/non-civil alerts.
