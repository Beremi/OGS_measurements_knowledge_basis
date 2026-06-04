# Gmail Gate Live-State Audit

This audit records a point-in-time Gmail connector check for the external gate drafts and CTE confirmation draft.
It does not send, archive, delete, or label any email.

## Summary

- Status: `gmail_gate_live_state_checked_drafts_still_not_sent_no_responses_found`
- Checked at: `2026-06-01T03:55:46+02:00`
- External request rows: 7
- Unique external drafts: 5
- Expected drafts including CTE: 6
- Expected drafts observed in Gmail DRAFT results: 6
- Sent-subject search results: 0
- Provider-reply search results: 0
- Recent CD-A/HERMES/TeamBeam non-draft results: 0

## Interpretation

The five external gate drafts and separate CTE confirmation draft are still observed as Gmail drafts. No sent copies of the generated subjects and no recent provider replies were found by the recorded searches, so the local response-intake status remains missing-response.

## Observed Draft IDs

- `r-4809950961900799564`
- `r-4984596174110032107`
- `r-8461584324877432346`
- `r1284411814726937591`
- `r2947727639429158073`
- `r6776618065355728003`

## Connector Observations

| Check | Tool | Results | Interpretation |
| --- | --- | ---: | --- |
| `list_drafts_gate_requests` | `list_drafts` | 6 | All five external-gate Gmail drafts plus the separate CTE confirmation draft are still present with Gmail DRAFT labels. |
| `sent_subject_search` | `search_email_ids` | 0 | No sent copies of the gate-request or CTE draft subjects were found in the last seven days. |
| `provider_reply_search` | `search_email_ids` | 0 | No recent reply from the named gate contacts was found for the gate topics. |
| `teambeam_context_search` | `search_email_ids` | 6 | The recent CD-A/HERMES/TeamBeam context search returned only the six generated drafts, not new provider or TeamBeam messages. |
