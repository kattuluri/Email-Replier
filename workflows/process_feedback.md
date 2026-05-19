# Workflow: Process User Feedback and Update RAG

## Objective
Check which pending drafts were sent, edited, or received feedback. Update the RAG database so future replies improve based on what the user actually sent.

## When to run
After reviewing and acting on drafts — typically once or twice a day, after you've handled your inbox.

## Prerequisites
- `.tmp/pending_drafts.json` exists (populated by `process_new_emails` workflow)
- `token.json` for Gmail auth

## Feedback mechanisms

The system recognizes three feedback signals:

| Signal | How | What's stored |
|--------|-----|---------------|
| **Sent as-is** | User sends the draft unchanged | Original email + generated reply → strong positive example |
| **Edited and sent** | User modifies draft before sending | Original email + edited reply → correct example replaces generated one |
| **[FEEDBACK] message** | User sends a reply in the thread starting with `[FEEDBACK]:` | Original email + generated reply + feedback text → used as context in future prompts |
| **Deleted draft** | User deletes without sending | Logged in console, nothing stored (insufficient signal) |

## Steps

### Run the feedback pipeline
```
python tools/run_feedback.py
```

This script:
1. Loads `.tmp/pending_drafts.json`
2. For each pending draft, checks if the draft still exists in Gmail
3. If draft is gone: checks sent folder for a sent reply in that thread
4. If draft exists: checks thread for a `[FEEDBACK]:` message
5. Updates RAG accordingly, removes resolved entries from `pending_drafts.json`

## Expected output
- Console: `[SENT] / [FEEDBACK] / [DELETED]` lines per resolved draft
- RAG database updated with new approved examples
- `.tmp/pending_drafts.json` shrinks as resolved items are removed

## Edge cases
- **No pending drafts**: script exits with "No feedback to process"
- **Draft still pending**: stays in `pending_drafts.json` until acted on
- **Gmail API draft lag**: Gmail sometimes keeps a draft ID valid briefly after sending. The checker detects sent replies by looking for SENT messages in the thread directly, so this doesn't cause missed feedback.
- **`[FEEDBACK]` message not found**: draft stays pending — check the thread or delete the draft to clear it
- **Multiple sent messages in one thread**: only the first `SENT`-labeled message is captured
- **Rate limits**: if you have 30+ threads to check, the Gmail API may throttle; re-run after a minute if you see errors

## Learning signal quality (best to worst)
1. Edited and sent — highest signal (stores the version you actually wanted)
2. Sent as-is — high signal (generated reply was good enough)
3. [FEEDBACK] text — medium signal (qualitative guidance improves future context)
4. Deleted — low signal (reason unknown; not stored)
