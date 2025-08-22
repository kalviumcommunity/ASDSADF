import chromadb
from chromadb.config import Settings as ChromaSettings
import asyncio
from typing import List, Dict, Any, Optional
import logging
import uuid
from pathlib import Path
from sentence_transformers import SentenceTransformer

from src.config import settings
from src.models import KnowledgeDocument

logger = logging.getLogger(__name__)


class RAGSystem:
    """Retrieval-Augmented Generation system using ChromaDB."""

    def __init__(self):
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.initialized = False

    async def initialize(self):
        if self.initialized:
            return
        try:
            Path(settings.chroma_persist_directory).mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=settings.chroma_persist_directory,
                settings=ChromaSettings(anonymized_telemetry=False)
            )

            try:
                self.collection = self.client.get_collection("asdsadf_knowledge")
            except Exception:
                self.collection = self.client.create_collection(
                    name="asdsadf_knowledge",
                    metadata={"description": "ASDSADF knowledge base for RAG"}
                )

            # Load sentence-transformers model in thread to avoid blocking
            self.embedding_model = await asyncio.to_thread(SentenceTransformer, settings.embedding_model)
            self.initialized = True
            logger.info("RAG system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            raise

    async def add_document(self, document: KnowledgeDocument) -> bool:
        if not self.initialized:
            await self.initialize()

        try:
            emb = await asyncio.to_thread(self.embedding_model.encode, f"{document.title}\n{document.content}")
            emb_list = emb.tolist() if hasattr(emb, "tolist") else list(map(float, emb))

            self.collection.add(
                ids=[document.id],
                embeddings=[emb_list],
                documents=[document.content],
                metadatas=[{
                    "title": document.title,
                    "source": document.source,
                    "document_type": getattr(document, "document_type", "documentation"),
                    **(document.metadata or {})
                }]
            )

            logger.info(f"Added document: {document.title}")
            return True
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False

    async def add_documents_batch(self, documents: List[KnowledgeDocument]) -> int:
        if not self.initialized:
            await self.initialize()

        added = 0
        batch_size = 16
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            contents = [f"{d.title}\n{d.content}" for d in batch]
            try:
                embs = await asyncio.to_thread(self.embedding_model.encode, contents)
                embs_list = [e.tolist() if hasattr(e, "tolist") else list(map(float, e)) for e in embs]
                ids = [d.id for d in batch]
                metadatas = [{"title": d.title, "source": d.source, "document_type": getattr(d, "document_type", "documentation"), **(d.metadata or {})} for d in batch]
                self.collection.add(ids=ids, embeddings=embs_list, documents=[d.content for d in batch], metadatas=metadatas)
                added += len(batch)
            except Exception as e:
                logger.error(f"Batch add error: {e}")

        logger.info(f"Added {added}/{len(documents)} documents in batch")
        return added

    async def search(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        if not self.initialized:
            await self.initialize()

        try:
            top_k = min(top_k or settings.max_retrieval_results, settings.max_retrieval_results)
            q_emb = await asyncio.to_thread(self.embedding_model.encode, query)
            q_list = q_emb.tolist() if hasattr(q_emb, "tolist") else list(map(float, q_emb))

            results = self.collection.query(
                query_embeddings=[q_list],
                n_results=top_k,
                include=["documents", "metadatas", "distances", "ids"]
            )

            formatted = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] or {}
                    distance = results["distances"][0][i]
                    score = max(0.0, 1.0 - distance)
                    if score < settings.similarity_threshold:
                        continue

                    formatted.append({
                        "id": results["ids"][0][i],
                        "title": metadata.get("title", "Untitled"),
                        "content": doc,
                        "source": metadata.get("source", "unknown"),
                        "document_type": metadata.get("document_type", "unknown"),
                        "score": score,
                        "metadata": metadata
                    })

            return formatted

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()
        try:
            count = self.collection.count()
            return {"total_documents": count}
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {"error": str(e)}

    async def reset(self) -> bool:
        if not self.initialized:
            await self.initialize()
        try:
            self.client.delete_collection("asdsadf_knowledge")
            self.collection = self.client.create_collection("asdsadf_knowledge")
            return True
        except Exception as e:
            logger.error(f"Reset error: {e}")
            return False
import chromadb
from chromadb.config import Settings as ChromaSettings
import asyncio
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import logging
import uuid
import json
from pathlib import Path

from src.config import settings
from src.models import KnowledgeDocument

logger = logging.getLogger(__name__)

class RAGSystem:
    """Retrieval-Augmented Generation system using ChromaDB."""
    
    def __init__(self):
        """Initialize the RAG system."""
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize ChromaDB and embedding model."""
        try:
            # Create data directory if it doesn't exist
            data_dir = Path(settings.chroma_persist_directory)
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=settings.chroma_persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection("asdsadf_knowledge")
                logger.info("Loaded existing ChromaDB collection")
            except Exception:
                self.collection = self.client.create_collection(
                    name="asdsadf_knowledge",
                    metadata={"description": "ASDSADF knowledge base for RAG"}
                )
                logger.info("Created new ChromaDB collection")
            
            # Initialize embedding model
            self.embedding_model = await asyncio.to_thread(
                SentenceTransformer, 
                settings.embedding_model
            )
            
            self.initialized = True
            logger.info("RAG system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            raise
    
    async def add_document(self, document: KnowledgeDocument) -> bool:
        """
        Add a document to the knowledge base.
        
        Args:
            document: KnowledgeDocument to add
            
        Returns:
            True if successful, False otherwise
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Generate embedding
            embedding = await asyncio.to_thread(
                self.embedding_model.encode,
                document.content
            )
            
            # Prepare metadata
            metadata = {
                "title": document.title,
                "source": document.source,
                "document_type": document.document_type,
                **document.metadata
            }
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=[embedding.tolist()],
                documents=[document.content],
                metadatas=[metadata],
                ids=[document.id]
            )
            
            logger.debug(f"Added document: {document.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document {document.title}: {e}")
            return False
    
    async def add_documents_batch(self, documents: List[KnowledgeDocument]) -> int:
        """
        Add multiple documents in batch.
        
        Args:
            documents: List of KnowledgeDocument objects
            
        Returns:
            Number of documents successfully added
        """
        if not self.initialized:
            await self.initialize()
        
        successful_adds = 0
        batch_size = 10  # Process in batches to avoid memory issues
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            try:
                # Generate embeddings for batch
                contents = [doc.content for doc in batch]
                embeddings = await asyncio.to_thread(
                    self.embedding_model.encode,
                    contents
                )
                
                # Prepare batch data
                ids = [doc.id for doc in batch]
                metadatas = []
                for doc in batch:
                    metadata = {
                        "title": doc.title,
                        "source": doc.source,
                        "document_type": doc.document_type,
                        **doc.metadata
                    }
                    metadatas.append(metadata)
                
                # Add batch to ChromaDB
                self.collection.add(
                    embeddings=embeddings.tolist(),
                    documents=contents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                successful_adds += len(batch)
                logger.info(f"Added batch of {len(batch)} documents")
                
            except Exception as e:
                logger.error(f"Failed to add batch starting at index {i}: {e}")
        
        logger.info(f"Successfully added {successful_adds}/{len(documents)} documents")
        return successful_adds
    
    async def search(
        self, 
        query: str, 
        top_k: int = 5,
        document_type: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            document_type: Filter by document type
            difficulty: Filter by difficulty level
            
        Returns:
            List of relevant documents with scores
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Generate query embedding
            query_embedding = await asyncio.to_thread(
                self.embedding_model.encode,
                query
            )
            
            # Prepare where clause for filtering
            where_clause = {}
            if document_type:
                where_clause["document_type"] = document_type
            if difficulty:
                where_clause["difficulty"] = difficulty
            
            # Search in ChromaDB
            search_kwargs = {
                "query_embeddings": [query_embedding.tolist()],
                "n_results": min(top_k, settings.max_retrieval_results)
            }
            
            if where_clause:
                search_kwargs["where"] = where_clause
            
            results = self.collection.query(**search_kwargs)
            
            # Format results
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    result = {
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "title": results["metadatas"][0][i].get("title", "Untitled"),
                        "source": results["metadatas"][0][i].get("source", "Unknown"),
                        "document_type": results["metadatas"][0][i].get("document_type", "unknown"),
                        "score": 1 - results["distances"][0][i],  # Convert distance to similarity
                        "metadata": results["metadatas"][0][i]
                    }
                    
                    # Filter by similarity threshold
                    if result["score"] >= settings.similarity_threshold:
                        formatted_results.append(result)
            
            logger.debug(f"Search query: '{query}' returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    async def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID."""
        if not self.initialized:
            await self.initialize()
        
        try:
            result = self.collection.get(ids=[document_id])
            if result["documents"]:
                return {
                    "id": document_id,
                    "content": result["documents"][0],
                    "title": result["metadatas"][0].get("title", "Untitled"),
                    "source": result["metadatas"][0].get("source", "Unknown"),
                    "document_type": result["metadatas"][0].get("document_type", "unknown"),
                    "metadata": result["metadatas"][0]
                }
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
        
        return None
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document by ID."""
        if not self.initialized:
            await self.initialize()
        
        try:
            self.collection.delete(ids=[document_id])
            logger.info(f"Deleted document: {document_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        if not self.initialized:
            await self.initialize()
        
        try:
            count = self.collection.count()
            
            # Get sample of documents to analyze types
            sample_results = self.collection.query(
                query_embeddings=[[0.0] * 384],  # Dummy embedding
                n_results=min(100, count) if count > 0 else 0
            )
            
            document_types = {}
            difficulties = {}
            
            if sample_results["metadatas"]:
                for metadata in sample_results["metadatas"][0]:
                    doc_type = metadata.get("document_type", "unknown")
                    difficulty = metadata.get("difficulty", "unknown")
                    
                    document_types[doc_type] = document_types.get(doc_type, 0) + 1
                    difficulties[difficulty] = difficulties.get(difficulty, 0) + 1
            
            return {
                "total_documents": count,
                "document_types": document_types,
                "difficulties": difficulties,
                "embedding_model": settings.embedding_model,
                "initialized": self.initialized
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"error": str(e)}
    
    async def reset_collection(self) -> bool:
        """Reset (clear) the entire collection."""
        if not self.initialized:
            await self.initialize()
        
        try:
            self.client.delete_collection("asdsadf_knowledge")
            self.collection = self.client.create_collection(
                name="asdsadf_knowledge",
                metadata={"description": "ASDSADF knowledge base for RAG"}
            )
            logger.info("Collection reset successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            return False