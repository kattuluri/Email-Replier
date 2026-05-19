"""Query the ChromaDB vector store for similar past emails."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import chromadb
from chromadb.utils import embedding_functions

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'chroma_db')
COLLECTION_NAME = 'email_replies'


def get_collection():
    client = chromadb.PersistentClient(path=DB_PATH)
    ef = embedding_functions.DefaultEmbeddingFunction()
    return client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=ef)


def query_similar_emails(email_text, n_results=5):
    collection = get_collection()
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
    query = sys.argv[1] if len(sys.argv) > 1 else 'Can we schedule a meeting to discuss the project?'
    results = query_similar_emails(query)
    print(f'Found {len(results)} similar emails for: "{query}"')
    for r in results:
        print(f'  Distance: {r["distance"]:.3f}')
        print(f'  Email: {r["email_text"][:100].strip()}')
        print(f'  Reply: {r["reply_text"][:100].strip()}')
        print()
