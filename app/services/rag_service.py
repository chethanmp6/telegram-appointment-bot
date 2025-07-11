"""Agentic RAG service with graph intelligence integration."""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import hashlib
from dataclasses import dataclass
from pathlib import Path

# Vector database imports
try:
    import pinecone
    from pinecone import Pinecone, ServerlessSpec
    pinecone_available = True
except ImportError:
    pinecone = None
    Pinecone = None
    ServerlessSpec = None
    pinecone_available = False

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

try:
    import weaviate
except ImportError:
    weaviate = None

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
# Simplified without agents to avoid compatibility issues
# from langchain.agents import initialize_agent, Tool  
# from langchain.memory import ConversationBufferMemory

# Sentence transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from app.core.config import settings
from app.models.schemas import RAGQuery, RAGResponse, RAGDocument
from app.core.graph_db import GraphDatabase
from app.core.database import get_async_session, KnowledgeBase

logger = logging.getLogger(__name__)


@dataclass
class ProcessedDocument:
    """Processed document for RAG system."""
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    doc_id: Optional[str] = None


class VectorStore:
    """Abstract vector store interface."""
    
    async def add_documents(self, documents: List[ProcessedDocument]) -> List[str]:
        """Add documents to vector store."""
        raise NotImplementedError
    
    async def search(self, query: str, top_k: int = 5, filter_metadata: Dict = None) -> List[RAGDocument]:
        """Search for similar documents."""
        raise NotImplementedError
    
    async def delete_documents(self, doc_ids: List[str]) -> bool:
        """Delete documents from vector store."""
        raise NotImplementedError
    
    async def health_check(self) -> bool:
        """Check vector store health."""
        raise NotImplementedError


class PineconeStore(VectorStore):
    """Pinecone vector store implementation."""
    
    def __init__(self):
        self.client = None
        self.index = None
        self.index_name = settings.pinecone_index_name
    
    async def initialize(self):
        """Initialize Pinecone client."""
        if not pinecone_available:
            logger.warning("Pinecone not available, skipping vector store initialization")
            return
        
        try:
            self.client = Pinecone(api_key=settings.pinecone_api_key)
            
            # Create index if it doesn't exist
            if self.index_name not in self.client.list_indexes().names():
                self.client.create_index(
                    name=self.index_name,
                    dimension=settings.embedding_dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.pinecone_environment
                    )
                )
            
            self.index = self.client.Index(self.index_name)
            logger.info("Pinecone initialized successfully")
            
        except Exception as e:
            logger.error(f"Pinecone initialization failed: {e}")
            raise
    
    async def add_documents(self, documents: List[ProcessedDocument]) -> List[str]:
        """Add documents to Pinecone."""
        try:
            vectors = []
            for doc in documents:
                doc_id = doc.doc_id or hashlib.md5(doc.content.encode()).hexdigest()
                vectors.append({
                    "id": doc_id,
                    "values": doc.embedding,
                    "metadata": {
                        **doc.metadata,
                        "content": doc.content[:1000]  # Truncate content for metadata
                    }
                })
            
            self.index.upsert(vectors)
            return [v["id"] for v in vectors]
            
        except Exception as e:
            logger.error(f"Failed to add documents to Pinecone: {e}")
            raise
    
    async def search(self, query: str, top_k: int = 5, filter_metadata: Dict = None) -> List[RAGDocument]:
        """Search Pinecone for similar documents."""
        try:
            # Get query embedding (this would need to be implemented)
            # For now, returning empty list
            return []
            
        except Exception as e:
            logger.error(f"Pinecone search failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check Pinecone health."""
        try:
            self.index.describe_index_stats()
            return True
        except Exception:
            return False


class ChromaStore(VectorStore):
    """ChromaDB vector store implementation."""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self.collection_name = "appointment-bot-knowledge"
    
    async def initialize(self):
        """Initialize ChromaDB client."""
        if not chromadb:
            raise ImportError("ChromaDB not installed")
        
        try:
            self.client = chromadb.PersistentClient(
                path="./data/chromadb",
                settings=Settings(allow_reset=True)
            )
            
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info("ChromaDB initialized successfully")
            
        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {e}")
            raise
    
    async def add_documents(self, documents: List[ProcessedDocument]) -> List[str]:
        """Add documents to ChromaDB."""
        try:
            doc_ids = []
            embeddings = []
            metadatas = []
            contents = []
            
            for doc in documents:
                doc_id = doc.doc_id or hashlib.md5(doc.content.encode()).hexdigest()
                doc_ids.append(doc_id)
                embeddings.append(doc.embedding)
                metadatas.append(doc.metadata)
                contents.append(doc.content)
            
            self.collection.add(
                ids=doc_ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=contents
            )
            
            return doc_ids
            
        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {e}")
            raise
    
    async def search(self, query: str, top_k: int = 5, filter_metadata: Dict = None) -> List[RAGDocument]:
        """Search ChromaDB for similar documents."""
        try:
            # This would need query embedding implementation
            return []
            
        except Exception as e:
            logger.error(f"ChromaDB search failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check ChromaDB health."""
        try:
            self.collection.count()
            return True
        except Exception:
            return False


class EmbeddingService:
    """Service for generating embeddings."""
    
    def __init__(self):
        self.embeddings = None
        self.model = None
    
    async def initialize(self):
        """Initialize embedding service."""
        try:
            if settings.embedding_provider == "openai":
                self.embeddings = OpenAIEmbeddings(
                    openai_api_key=settings.openai_api_key,
                    model=settings.embedding_model
                )
            elif settings.embedding_provider == "sentence-transformers":
                if not SentenceTransformer:
                    raise ImportError("sentence-transformers not installed")
                self.model = SentenceTransformer(settings.embedding_model)
            else:
                raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")
            
            logger.info(f"Embedding service initialized with {settings.embedding_provider}")
            
        except Exception as e:
            logger.error(f"Embedding service initialization failed: {e}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text."""
        try:
            if settings.embedding_provider == "openai":
                return await self.embeddings.aembed_query(text)
            elif settings.embedding_provider == "sentence-transformers":
                return self.model.encode(text).tolist()
            else:
                raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")
                
        except Exception as e:
            logger.error(f"Text embedding failed: {e}")
            raise
    
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            if settings.embedding_provider == "openai":
                return await self.embeddings.aembed_documents(texts)
            elif settings.embedding_provider == "sentence-transformers":
                return self.model.encode(texts).tolist()
            else:
                raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")
                
        except Exception as e:
            logger.error(f"Document embedding failed: {e}")
            raise


class RAGService:
    """Agentic RAG service with graph intelligence."""
    
    def __init__(self):
        self.vector_store: Optional[VectorStore] = None
        self.embedding_service: Optional[EmbeddingService] = None
        self.graph_db: Optional[GraphDatabase] = None
        self.text_splitter = None
        self.agent = None
        self.memory = None
        self._healthy = False
    
    async def initialize(self):
        """Initialize RAG service."""
        try:
            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.rag_chunk_size,
                chunk_overlap=settings.rag_chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
            # Initialize embedding service
            self.embedding_service = EmbeddingService()
            await self.embedding_service.initialize()
            
            # Initialize vector store
            if settings.vector_db_provider == "pinecone":
                self.vector_store = PineconeStore()
            elif settings.vector_db_provider == "chroma":
                self.vector_store = ChromaStore()
            else:
                raise ValueError(f"Unsupported vector DB provider: {settings.vector_db_provider}")
            
            await self.vector_store.initialize()
            
            # Initialize conversation memory - simplified
            # self.memory = ConversationBufferMemory(
            #     memory_key="chat_history",
            #     return_messages=True
            # )
            self.memory = None
            
            # Initialize agent tools - simplified
            # self._initialize_agent()
            self.agent = None
            
            self._healthy = True
            logger.info("RAG service initialized successfully")
            
        except Exception as e:
            logger.error(f"RAG service initialization failed: {e}")
            raise
    
    def _initialize_agent(self):
        """Initialize the RAG agent with tools."""
        tools = [
            Tool(
                name="search_knowledge_base",
                description="Search the knowledge base for business information",
                func=self._search_knowledge_base_sync,
                coroutine=self._search_knowledge_base
            ),
            Tool(
                name="search_graph_knowledge",
                description="Search graph database for relationship-based information",
                func=self._search_graph_knowledge_sync,
                coroutine=self._search_graph_knowledge
            ),
            Tool(
                name="get_contextual_recommendations",
                description="Get contextual recommendations based on graph analysis",
                func=self._get_contextual_recommendations_sync,
                coroutine=self._get_contextual_recommendations
            )
        ]
        
        # Note: Agent initialization would need proper LLM integration
        # This is a placeholder implementation
        self.agent = None
    
    async def ingest_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ingest documents into the RAG system."""
        try:
            processed_docs = []
            
            for doc in documents:
                # Split document into chunks
                chunks = self.text_splitter.split_text(doc["content"])
                
                for i, chunk in enumerate(chunks):
                    # Generate embeddings
                    embedding = await self.embedding_service.embed_text(chunk)
                    
                    processed_doc = ProcessedDocument(
                        content=chunk,
                        metadata={
                            **doc.get("metadata", {}),
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "document_id": doc.get("id", "unknown"),
                            "ingested_at": datetime.utcnow().isoformat()
                        },
                        embedding=embedding
                    )
                    
                    processed_docs.append(processed_doc)
            
            # Add to vector store
            doc_ids = await self.vector_store.add_documents(processed_docs)
            
            # Store in PostgreSQL for metadata
            await self._store_document_metadata(documents)
            
            # Update graph database with document relationships
            if self.graph_db:
                await self._update_graph_knowledge(documents)
            
            return {
                "success": True,
                "documents_processed": len(documents),
                "chunks_created": len(processed_docs),
                "doc_ids": doc_ids
            }
            
        except Exception as e:
            logger.error(f"Document ingestion failed: {e}")
            raise
    
    async def search(self, query: str, context: str = None, top_k: int = None) -> RAGResponse:
        """Search the RAG system with graph intelligence."""
        try:
            start_time = datetime.utcnow()
            
            # Use configured top_k or default
            top_k = top_k or settings.rag_top_k
            
            # Step 1: Generate query embedding
            query_embedding = await self.embedding_service.embed_text(query)
            
            # Step 2: Search vector store
            vector_results = await self.vector_store.search(query, top_k)
            
            # Step 3: Search graph database for related concepts
            graph_results = []
            if self.graph_db:
                graph_results = await self.graph_db.search_knowledge_graph(query, context)
            
            # Step 4: Combine and rank results
            combined_results = self._combine_search_results(vector_results, graph_results)
            
            # Step 5: Generate contextual answer
            answer = await self._generate_contextual_answer(query, combined_results, context)
            
            # Step 6: Calculate processing time and score
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            retrieval_score = self._calculate_retrieval_score(combined_results)
            
            return RAGResponse(
                query=query,
                documents=combined_results,
                answer=answer,
                processing_time=processing_time,
                retrieval_score=retrieval_score
            )
            
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            raise
    
    async def _search_knowledge_base(self, query: str) -> str:
        """Search knowledge base tool for agent."""
        try:
            results = await self.vector_store.search(query, top_k=3)
            if results:
                return "\n\n".join([doc.content for doc in results])
            return "No relevant information found in knowledge base."
        except Exception as e:
            return f"Error searching knowledge base: {e}"
    
    def _search_knowledge_base_sync(self, query: str) -> str:
        """Synchronous wrapper for knowledge base search."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._search_knowledge_base(query))
    
    async def _search_graph_knowledge(self, query: str) -> str:
        """Search graph database tool for agent."""
        try:
            if self.graph_db:
                results = await self.graph_db.search_knowledge_graph(query)
                if results:
                    return "\n\n".join([
                        f"{result['concept']}: {result['description']}" 
                        for result in results
                    ])
            return "No relevant graph information found."
        except Exception as e:
            return f"Error searching graph knowledge: {e}"
    
    def _search_graph_knowledge_sync(self, query: str) -> str:
        """Synchronous wrapper for graph knowledge search."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._search_graph_knowledge(query))
    
    async def _get_contextual_recommendations(self, query: str) -> str:
        """Get contextual recommendations tool for agent."""
        try:
            if self.graph_db:
                # Extract customer context from query or use default
                # This is a simplified implementation
                recommendations = await self.graph_db.get_service_recommendations("default", limit=3)
                if recommendations:
                    return "\n".join([
                        f"- {rec['service_name']}: {rec['description']} (Score: {rec['score']})"
                        for rec in recommendations
                    ])
            return "No recommendations available."
        except Exception as e:
            return f"Error getting recommendations: {e}"
    
    def _get_contextual_recommendations_sync(self, query: str) -> str:
        """Synchronous wrapper for contextual recommendations."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._get_contextual_recommendations(query))
    
    def _combine_search_results(self, vector_results: List[RAGDocument], graph_results: List[Dict]) -> List[RAGDocument]:
        """Combine and rank search results from different sources."""
        combined = list(vector_results)
        
        # Add graph results as RAG documents
        for graph_result in graph_results:
            rag_doc = RAGDocument(
                content=graph_result.get("content", graph_result.get("description", "")),
                metadata={
                    "source": "graph",
                    "concept": graph_result.get("concept", ""),
                    "category": graph_result.get("category", ""),
                    "related_concepts": graph_result.get("related_concepts", [])
                },
                score=0.8  # Default score for graph results
            )
            combined.append(rag_doc)
        
        # Sort by score (descending)
        combined.sort(key=lambda x: x.score, reverse=True)
        
        return combined[:settings.rag_top_k]
    
    async def _generate_contextual_answer(self, query: str, documents: List[RAGDocument], context: str = None) -> str:
        """Generate contextual answer using retrieved documents."""
        if not documents:
            return "I don't have enough information to answer your question."
        
        # Combine document content
        document_content = "\n\n".join([doc.content for doc in documents])
        
        # Create context-aware prompt
        prompt = f"""
        Based on the following information, please answer the user's question:
        
        Question: {query}
        
        Context: {context if context else "General inquiry"}
        
        Relevant Information:
        {document_content}
        
        Please provide a helpful and accurate answer based on this information.
        """
        
        # This would integrate with the LLM service
        # For now, return a simple response
        return f"Based on the available information, here's what I found: {document_content[:200]}..."
    
    def _calculate_retrieval_score(self, documents: List[RAGDocument]) -> float:
        """Calculate overall retrieval score."""
        if not documents:
            return 0.0
        
        scores = [doc.score for doc in documents]
        return sum(scores) / len(scores)
    
    async def _store_document_metadata(self, documents: List[Dict[str, Any]]):
        """Store document metadata in PostgreSQL."""
        try:
            async with get_async_session() as session:
                for doc in documents:
                    knowledge_item = KnowledgeBase(
                        title=doc.get("title", "Untitled"),
                        content=doc["content"],
                        document_type=doc.get("document_type", "general"),
                        category=doc.get("category", "general"),
                        tags=doc.get("tags", []),
                        metadata=doc.get("metadata", {})
                    )
                    session.add(knowledge_item)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Failed to store document metadata: {e}")
            raise
    
    async def _update_graph_knowledge(self, documents: List[Dict[str, Any]]):
        """Update graph database with document relationships."""
        try:
            if self.graph_db:
                knowledge_data = []
                for doc in documents:
                    knowledge_item = {
                        "name": doc.get("title", "Untitled"),
                        "description": doc.get("content", "")[:500],
                        "category": doc.get("category", "general"),
                        "content": doc["content"],
                        "related_concepts": doc.get("related_concepts", [])
                    }
                    knowledge_data.append(knowledge_item)
                
                await self.graph_db.create_knowledge_graph(knowledge_data)
                
        except Exception as e:
            logger.error(f"Failed to update graph knowledge: {e}")
            raise
    
    def set_graph_db(self, graph_db: GraphDatabase):
        """Set graph database reference."""
        self.graph_db = graph_db
    
    def is_healthy(self) -> bool:
        """Check if RAG service is healthy."""
        return self._healthy and (
            self.vector_store and 
            asyncio.run(self.vector_store.health_check())
        )
    
    async def close(self):
        """Close RAG service."""
        if self.vector_store:
            # Close vector store connections if needed
            pass
        
        self._healthy = False
        logger.info("RAG service closed")