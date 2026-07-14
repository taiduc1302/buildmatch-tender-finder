# DISTRIBUTION NOTES — Tender Finder

Who can receive what, and what needs a human check first. This package passed
two independent sanitization audits (2026-07-03, 2026-07-04 — see
`SANITIZATION_REPORT.md` and `FINAL_HANDOFF_AUDIT.md`) with zero findings of
private company data, real names, real emails, secrets, or private paths. That
means it is clean of *confidential* content. It does not automatically mean
every file is cleared for *public* release — some already-public content was
kept deliberately (see below) and deserves a quick look before it leaves your
organization.

## OK to keep privately (no restriction)

- The entire sanitized package folder and its ZIP, as-is, for your own
  archive, study, or continued development.
- All documentation, code, tests, and synthetic demo data in the package.

## OK to share with a developer, after the manual review below

Share the package folder/ZIP with an external developer or contractor once
someone on your side has read `SANITIZATION_REPORT.md`'s "Manual review
items" and confirmed they're comfortable with:

1. **Test fixtures with public-record municipal data**
   (`01 Code\CONNECTOR_SWEEP\tests\fixtures\`) — real BC development
   application numbers, public applicant/developer company names, and one
   real closed tender title, all sourced from public municipal records. Public
   information, but a human should confirm your organization is fine handing
   it to a third party.
2. **Two PDF test fixtures** — checked 2026-07-04, contain no embedded
   metadata or hidden content beyond generic ReportLab defaults; low risk.
3. **Public developer/consultant brand names** in the parent-brand grouping
   logic and one classification test — functional code, uses real (public)
   company names as pattern examples.
4. **BC-region source registers** (`00 Master` Source_Register,
   `01 Code\CONNECTOR_SWEEP\data\` backlog, `04 RESEARCH REFERENCE\
   SOURCE_REGISTER_EXPANSION`) — ~300 public procurement/dev-app sources with
   operational access notes. Public information describing how to find public
   tenders; reveals your organization's research effort/methodology, not
   confidential data.
5. **Historical/Russian-language docs** (`02 Runbooks And Plans\`,
   `04 RESEARCH REFERENCE\`) — describe the original build's methodology and
   BC market context; personnel names and branding already removed.
6. **Synthetic demo emails** reuse real public alert-provider domains
   (`bidsandtenders.ca`, `bcbid.gov.bc.ca`) for realistic routing; all other
   content in them is fictitious.

None of the above are secrets. They're public-domain or your-own-methodology
content that a reasonable reviewer might still want eyes-on before an external
handoff, purely as a judgment call, not because sanitization missed anything.

## NOT OK to distribute publicly (open internet, public repo, etc.) without legal/IP review

- Anything under "OK to share with a developer" above, if your organization
  has any IP/competitive-advantage concern about disclosing your source
  research or methodology publicly (the region-specific source lists and
  research docs are the main candidate here — they represent real research
  effort, even though the underlying facts are public).
- The package as a whole, until someone with authority to make that call has
  reviewed item-by-item above. Nothing found in sanitization blocks public
  release on privacy/security grounds — this is a business/IP judgment call,
  not a technical one.

## The private sanitization records folder must NOT be distributed, ever

`Tender_Finder_Sanitization_Records_20260703_215523\` (delivered separately,
next to the ZIP, not inside it) contains the exact original→placeholder token
mapping and full file inventory used to prove sanitization. **This folder
exists purely so the original owner can verify/re-verify the sanitization
later — it must never be shared with anyone the sanitized package itself is
shared with**, since by definition it names things the sanitization was
designed to remove. Confirmed via two independent checks (2026-07-03 build-
time exclusion, 2026-07-04 adversarial re-scan of the actual ZIP) that this
folder is not present inside the distributable ZIP.

## Quick decision table

| Recipient | Package/ZIP | Records folder |
|---|---|---|
| Yourself / internal archive | Yes | Yes (keep together, privately) |
| Internal team member | Yes | Only if they need to verify sanitization; otherwise no |
| External developer/contractor | Yes, after manual review above | **Never** |
| Public repository / open internet | Not yet — needs explicit legal/IP sign-off | **Never** |
