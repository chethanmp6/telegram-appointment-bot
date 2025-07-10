"""Knowledge base and RAG API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import logging
import json

from app.services.rag_service import RAGService
from app.models.schemas import RAGQuery, RAGResponse, RAGDocument

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_rag_service() -> RAGService:
    """Dependency to get RAG service from app state."""
    # This would be injected from the main app
    # For now, return a placeholder
    raise HTTPException(status_code=503, detail="RAG service not available")


@router.post("/search", response_model=RAGResponse)
async def search_knowledge_base(
    query_request: RAGQuery,
    rag_service: RAGService = Depends(get_rag_service)
):
    """Search the knowledge base using RAG."""
    try:
        result = await rag_service.search(
            query=query_request.query,
            context=json.dumps(query_request.context) if query_request.context else None,
            top_k=query_request.top_k
        )
        return result
    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/search")
async def search_knowledge_simple(
    q: str,
    context: Optional[str] = None,
    top_k: int = 5,
    rag_service: RAGService = Depends(get_rag_service)
):
    """Simple search endpoint with query parameters."""
    try:
        context_dict = json.loads(context) if context else None
        result = await rag_service.search(
            query=q,
            context=context,
            top_k=top_k
        )
        return result
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid context JSON")
    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.post("/documents/ingest")
async def ingest_documents(
    documents: List[Dict[str, Any]],
    rag_service: RAGService = Depends(get_rag_service)
):
    """Ingest documents into the knowledge base."""
    try:
        # Validate document format
        for doc in documents:
            if "content" not in doc:
                raise HTTPException(status_code=400, detail="Each document must have 'content' field")
        
        result = await rag_service.ingest_documents(documents)
        return result
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}")
        raise HTTPException(status_code=500, detail="Document ingestion failed")


@router.post("/documents/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    document_type: str = Form("general"),
    category: str = Form("general"),
    metadata: str = Form("{}"),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Upload and ingest document files."""
    try:
        # Parse metadata
        try:
            metadata_dict = json.loads(metadata)
        except json.JSONDecodeError:
            metadata_dict = {}
        
        documents = []
        
        for file in files:
            # Read file content
            content = await file.read()
            
            # Basic text extraction (would need proper document parsing for PDF, DOCX, etc.)
            if file.content_type == "text/plain":
                text_content = content.decode('utf-8')
            elif file.content_type == "application/json":
                json_content = json.loads(content.decode('utf-8'))
                text_content = json.dumps(json_content, indent=2)
            else:
                # For other file types, store as base64 or implement proper extraction
                text_content = f"File: {file.filename} (Content type: {file.content_type})"
            
            documents.append({
                "id": f"upload_{file.filename}",
                "title": file.filename,
                "content": text_content,
                "document_type": document_type,
                "category": category,
                "metadata": {
                    **metadata_dict,
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "size": len(content)
                }
            })
        
        result = await rag_service.ingest_documents(documents)
        return {
            "status": "success",
            "files_processed": len(files),
            "ingestion_result": result
        }
        
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")


@router.post("/ask")
async def ask_question(
    question: str = Form(...),
    context: str = Form("{}"),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Ask a question using the knowledge base."""
    try:
        # Parse context
        try:
            context_dict = json.loads(context)
        except json.JSONDecodeError:
            context_dict = {}
        
        result = await rag_service.search(
            query=question,
            context=json.dumps(context_dict) if context_dict else None
        )
        
        return {
            "question": question,
            "answer": result.answer,
            "sources": [
                {
                    "content": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                    "score": doc.score,
                    "metadata": doc.metadata
                }
                for doc in result.documents
            ],
            "processing_time": result.processing_time
        }
        
    except Exception as e:
        logger.error(f"Question answering failed: {e}")
        raise HTTPException(status_code=500, detail="Question answering failed")


@router.get("/documents/types")
async def get_document_types():
    """Get available document types."""
    return {
        "document_types": [
            "policy",
            "faq", 
            "service_info",
            "pricing",
            "procedure",
            "general"
        ],
        "categories": [
            "services",
            "policies", 
            "pricing",
            "procedures",
            "staff",
            "location",
            "general"
        ]
    }


@router.get("/health")
async def knowledge_health_check(
    rag_service: RAGService = Depends(get_rag_service)
):
    """Check knowledge base health."""
    try:
        is_healthy = rag_service.is_healthy()
        
        # Additional health checks
        health_status = {
            "status": "healthy" if is_healthy else "unhealthy",
            "rag_service": is_healthy,
            "vector_store": False,
            "embedding_service": False
        }
        
        # Check vector store health
        if rag_service.vector_store:
            try:
                vector_health = await rag_service.vector_store.health_check()
                health_status["vector_store"] = vector_health
            except Exception:
                health_status["vector_store"] = False
        
        # Check embedding service
        if rag_service.embedding_service:
            try:
                # Simple test embedding
                test_embedding = await rag_service.embedding_service.embed_text("test")
                health_status["embedding_service"] = len(test_embedding) > 0
            except Exception:
                health_status["embedding_service"] = False
        
        overall_healthy = all([
            health_status["rag_service"],
            health_status["vector_store"], 
            health_status["embedding_service"]
        ])
        
        health_status["status"] = "healthy" if overall_healthy else "unhealthy"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/stats")
async def get_knowledge_stats(
    rag_service: RAGService = Depends(get_rag_service)
):
    """Get knowledge base statistics."""
    try:
        # Get basic stats from database
        from app.core.database import get_async_session, KnowledgeBase
        from sqlalchemy import select, func
        
        async with get_async_session() as session:
            # Count documents by type
            result = await session.execute(
                select(
                    KnowledgeBase.document_type,
                    func.count(KnowledgeBase.id).label('count')
                ).group_by(KnowledgeBase.document_type)
            )
            
            document_types = {row.document_type: row.count for row in result}
            
            # Count total documents
            total_result = await session.execute(
                select(func.count(KnowledgeBase.id))
            )
            total_documents = total_result.scalar()
            
            # Count by category
            category_result = await session.execute(
                select(
                    KnowledgeBase.category,
                    func.count(KnowledgeBase.id).label('count')
                ).group_by(KnowledgeBase.category)
            )
            
            categories = {row.category: row.count for row in category_result}
        
        return {
            "total_documents": total_documents,
            "document_types": document_types,
            "categories": categories,
            "vector_store_provider": getattr(rag_service, 'vector_store', {}).get('provider', 'unknown'),
            "embedding_provider": getattr(rag_service, 'embedding_service', {}).get('provider', 'unknown')
        }
        
    except Exception as e:
        logger.error(f"Failed to get knowledge stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    rag_service: RAGService = Depends(get_rag_service)
):
    """Delete a document from the knowledge base."""
    try:
        # Delete from vector store
        if rag_service.vector_store:
            await rag_service.vector_store.delete_documents([document_id])
        
        # Delete from PostgreSQL
        from app.core.database import get_async_session, KnowledgeBase
        from sqlalchemy import select
        
        async with get_async_session() as session:
            result = await session.execute(
                select(KnowledgeBase).where(KnowledgeBase.id == document_id)
            )
            doc = result.scalar_one_or_none()
            
            if doc:
                await session.delete(doc)
                await session.commit()
                return {"status": "deleted", "document_id": document_id}
            else:
                raise HTTPException(status_code=404, detail="Document not found")
        
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")


@router.post("/reindex")
async def reindex_knowledge_base(
    rag_service: RAGService = Depends(get_rag_service)
):
    """Reindex the entire knowledge base."""
    try:
        # Get all documents from PostgreSQL
        from app.core.database import get_async_session, KnowledgeBase
        from sqlalchemy import select
        
        async with get_async_session() as session:
            result = await session.execute(select(KnowledgeBase))
            db_documents = result.scalars().all()
        
        # Convert to ingestion format
        documents = []
        for doc in db_documents:
            documents.append({
                "id": doc.id,
                "title": doc.title,
                "content": doc.content,
                "document_type": doc.document_type,
                "category": doc.category,
                "metadata": doc.metadata or {}
            })
        
        # Reingest all documents
        result = await rag_service.ingest_documents(documents)
        
        return {
            "status": "reindexed",
            "documents_processed": len(documents),
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Reindexing failed: {e}")
        raise HTTPException(status_code=500, detail="Reindexing failed")