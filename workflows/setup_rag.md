# Workflow: Setup RAG from Gmail Sent History

## Objective
Seed the RAG database with past email-reply pairs from the user's sent folder so the system has examples to draw from when generating replies.

## When to run
- Once during initial setup
- Again after 3+ months of new sent emails accumulate

## Prerequisites
- `credentials.json` in project root (downloaded from Google Cloud Console → OAuth 2.0 client)
- `ANTHROPIC_API_KEY` set in `.env`
- Dependencies installed: `pip install -r requirements.txt`

## Steps

### Step 1: Authenticate with Gmail
```
python tools/gmail_auth.py
```
This opens a browser for OAuth consent. Stores `token.json` in project root on success. Only needed once; subsequent runs use the saved token.

### Step 2: Seed the RAG database
```
python tools/rag_seed.py [max_results]
```
- Default: 100 most recent sent emails
- For more history: `python tools/rag_seed.py 300`

### Step 3: Verify
```
python tools/rag_query.py "can we schedule a meeting"
```
Expect: 3–5 results with non-zero distance scores.

## Expected output
- `data/chroma_db/` directory created and populated
- Console output: "Done. Added N pairs to RAG database."

## Edge cases
- **Empty sent folder**: seeding adds 0 pairs; system still works, just starts with no context
- **Very short emails** (< 20 chars): skipped automatically — too little signal for meaningful embeddings
- **Large sent history (500+)**: run in batches; if you see Gmail API errors, wait 60s and re-run with a smaller `max_results`
- **Already seeded**: `upsert` by message_id prevents duplicates — safe to re-run
- **HTML-only emails**: body extraction falls back to empty string and the pair is skipped
