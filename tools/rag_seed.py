"""Seed the RAG database from Gmail sent email history."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from gmail_fetch_sent import fetch_sent_email_pairs
from rag_update import add_to_rag


def seed_rag_from_sent(max_results=100):
    print(f'Fetching up to {max_results} sent email pairs...')
    pairs = fetch_sent_email_pairs(max_results=max_results)
    print(f'Found {len(pairs)} pairs. Adding to RAG...')

    added = 0
    for pair in pairs:
        email_text = (
            f"Subject: {pair['original_email']['subject']}\n\n"
            f"{pair['original_email']['body'][:3000]}"
        )
        reply_text = pair['reply']['body']

        if len(email_text.strip()) < 20 or len(reply_text.strip()) < 10:
            continue

        add_to_rag(
            email_text=email_text,
            reply_text=reply_text,
            feedback=None,
            source='sent_history',
            message_id=pair['original_email']['id'],
        )
        added += 1

    print(f'Done. Added {added} pairs to RAG database.')
    return added


if __name__ == '__main__':
    max_results = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    seed_rag_from_sent(max_results)
