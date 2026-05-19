# Workflow: Process New Emails and Generate Draft Replies

## Objective
Fetch unread emails from Gmail, generate AI draft replies using RAG context from past replies, and save them as Gmail drafts for user review.

## When to run
Manually, whenever you want to process the inbox.

## Prerequisites
- `token.json` exists (run `setup_rag` workflow first)
- `ANTHROPIC_API_KEY` in `.env`
- RAG database seeded (run `setup_rag` at least once; works without it but quality is lower)

## Steps

### Run the full pipeline
```
python tools/run_pipeline.py
```

This script:
1. Fetches all unread emails not labeled `email-replier-processed`
2. For each email: queries RAG for 5 similar past emails, sends to Claude with those examples, generates a reply
3. Creates a Gmail draft in the same thread
4. Labels the original email `email-replier-processed` to prevent reprocessing
5. Appends draft metadata to `.tmp/pending_drafts.json`

## Expected output
- Gmail Drafts populated with AI-generated replies
- `.tmp/pending_drafts.json` updated
- Console: list of processed emails with draft IDs

## After running
Review drafts in Gmail. For each draft you can:
- **Send as-is** → system learns this was a good reply
- **Edit and send** → system learns the improved version
- **Reply in the thread with** `[FEEDBACK]: your note here` → system stores the qualitative feedback
- **Delete the draft** → logged but no signal stored

Run `process_feedback` workflow after reviewing to lock in the learning.

## Edge cases
- **Email body > 4000 chars**: truncated before sending to Claude — the most relevant content is usually at the top
- **No RAG examples yet**: Claude writes a generic professional reply; quality improves as the database grows
- **Reply-to-reply threads**: all unread emails are processed, including ongoing thread replies — intentional
- **No-reply / automated emails**: will get drafts generated; manually delete those drafts if unwanted
- **Gmail API quota**: if processing 20+ emails, the 0.3s delay between drafts keeps it within safe limits
