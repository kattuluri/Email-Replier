"""Generate an email reply using Claude with RAG context from past replies."""
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import anthropic
from rag_query import query_similar_emails

client = anthropic.Anthropic()


def generate_reply(email_data, user_email):
    email_text = (
        f"Subject: {email_data['subject']}\n"
        f"From: {email_data['from']}\n\n"
        f"{email_data['body'][:4000]}"
    )

    similar = query_similar_emails(email_text, user_email=user_email, n_results=5)

    examples_block = _build_examples(similar)

    system = (
        "You are an email assistant drafting replies on behalf of the user. "
        "Match their writing style and tone based on the examples provided. "
        "Write a natural, professional reply. "
        "Output only the reply body — no subject line, no sign-off label, just the text."
    )

    user_msg = f"""Here are examples of past emails and the user's replies:

{examples_block if examples_block else 'No past examples available yet — write a professional reply.'}

---

Draft a reply to this new email:

{email_text}"""

    response = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=1024,
        system=system,
        messages=[{'role': 'user', 'content': user_msg}],
    )

    return response.content[0].text


def _build_examples(similar):
    if not similar:
        return ''
    parts = []
    for i, s in enumerate(similar, 1):
        example = (
            f"Example {i}:\n"
            f"Email: {s['email_text'][:500]}\n"
            f"Reply: {s['reply_text'][:500]}"
        )
        if s['feedback']:
            example += f"\nFeedback on this reply: {s['feedback']}"
        parts.append(example)
    return '\n\n---\n\n'.join(parts)


if __name__ == '__main__':
    import sys as _sys
    user = _sys.argv[1] if len(_sys.argv) > 1 else 'test@example.com'
    test_email = {
        'subject': 'Quick question about the project',
        'from': 'someone@example.com',
        'body': 'Hi, just wanted to check in on the status of the project. Can you give me an update?',
    }
    reply = generate_reply(test_email, user_email=user)
    print('Generated reply:')
    print(reply)
