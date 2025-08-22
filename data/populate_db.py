# ...existing code...
import sys
import os
import asyncio
import uuid

# Ensure project root is on sys.path so `from src...` imports work when running this script directly.
# Project root is the parent directory of this file's directory.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.rag_system import RAGSystem
from src.models import KnowledgeDocument

async def main():
    rag = RAGSystem()
    await rag.initialize()
    docs = [
        {"title":"JS Fundamentals","content":"JavaScript basics: variables, functions, promises...","source":"MDN","document_type":"documentation","metadata":{"topics":["javascript"]}},
        {"title":"React Intro","content":"React: components, props, state, hooks...","source":"React Docs","document_type":"documentation","metadata":{"topics":["react"]}},
    ]
    added = 0
    for d in docs:
        kd = KnowledgeDocument(id=str(uuid.uuid4()), **d)
        ok = await rag.add_document(kd)
        if ok:
            added += 1
    print(f"Added {added} documents")

if __name__ == "__main__":
    asyncio.run(main())