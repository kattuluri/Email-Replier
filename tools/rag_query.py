"""Query the ChromaDB vector store for similar past emails."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import chromadb
from chromadb.utils import embedding_functions

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'chroma_db')


def get_collection(user_email):
    from user_store import user_id
    client = chromadb.PersistentClient(path=DB_PATH)
    ef = embedding_functions.DefaultEmbeddingFunction()
    return client.get_or_create_collection(
        name=f'replies_{user_id(user_email)}', embedding_function=ef
    )


def query_similar_emails(email_text, user_email, n_results=5):
    collection = get_collection(user_email)
    count = collection.count()
    if count == 0:
        return []

    n_results = min(n_results, count)
    results = collection.query(
        query_texts=[email_text],
        n_results=n_results,
        include=['documents', 'metadatas', 'distances'],
    )

    similar = []
    for doc, meta, dist in zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0],
    ):
        similar.append({
            'email_text': doc,
            'reply_text': meta.get('reply_text', ''),
            'feedback': meta.get('feedback') or None,
            'distance': dist,
        })

    return similar


if __name__ == '__main__':
    user = sys.argv[1] if len(sys.argv) > 1 else 'test@example.com'
    query = sys.argv[2] if len(sys.argv) > 2 else 'Can we schedule a meeting to discuss the project?'
    results = query_similar_emails(query, user_email=user)
    print(f'Found {len(results)} similar emails for {user}: "{query}"')
    for r in results:
        print(f'  Distance: {r["distance"]:.3f}')
        print(f'  Email: {r["email_text"][:100].strip()}')
        print(f'  Reply: {r["reply_text"][:100].strip()}')
        print()
