"""Entry point: check draft feedback and update RAG database."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from gmail_check_feedback import check_feedback
from rag_update import add_to_rag


def run(user_email):
    print(f'[{user_email}] Checking draft feedback...')
    results = check_feedback(user_email)

    if not results:
        print(f'[{user_email}] No feedback to process.')
        return

    sent = feedback = deleted = 0

    for item in results:
        status = item['status']
        original = item['original_email']
        email_text = (
            f"Subject: {original['subject']}\n"
            f"From: {original['from']}\n\n"
            f"{original['body']}"
        )

        if status == 'sent':
            reply_text = item.get('actual_reply') or item['generated_reply']
            add_to_rag(
                email_text=email_text,
                reply_text=reply_text,
                user_email=user_email,
                feedback=None,
                source='approved',
                message_id=original['id'],
            )
            print(f"  [SENT]     {original['subject'][:60]}")
            sent += 1

        elif status == 'feedback':
            add_to_rag(
                email_text=email_text,
                reply_text=item['generated_reply'],
                user_email=user_email,
                feedback=item['feedback'],
                source='feedback',
                message_id=original['id'],
            )
            print(f"  [FEEDBACK] {original['subject'][:60]}")
            feedback += 1

        elif status == 'deleted':
            print(f"  [DELETED]  {original['subject'][:60]} (skipped)")
            deleted += 1

    print(f'[{user_email}] Done. {sent} sent, {feedback} with feedback, {deleted} deleted.')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python run_feedback.py <user_email>')
        sys.exit(1)
    run(sys.argv[1])
