"""Add or update email-reply pairs in the ChromaDB vector store."""
import os
import uuid
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


def add_to_rag(email_text, reply_text, feedback=None, source='feedback', message_id=None):
    collection = get_collection()
    doc_id = message_id or str(uuid.uuid4())
    collection.upsert(
        ids=[doc_id],
        documents=[email_text],
        metadatas=[{
            'reply_text': reply_text[:2000],
            'feedback': feedback or '',
            'source': source,
        }],
    )
    return doc_id


if __name__ == '__main__':
    doc_id = add_to_rag(
        email_text='Test email about a project update',
        reply_text='Thanks for the update. I will review and get back to you.',
        source='test',
    )
    print(f'Added: {doc_id}')
    collection = get_collection()
    print(f'Total entries: {collection.count()}')
