"""Web client chat API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging
from datetime import datetime
import asyncio

from app.core.database import get_session
from app.core.graph_db import get_graph_db
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.appointment_service import AppointmentService

logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response Models
class ChatMessage(BaseModel):
    message: str
    session_id: str
    user_id: str = "web_user"
    platform: str = "web"
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: datetime
    context: Optional[Dict[str, Any]] = None
    actions: Optional[list] = None

class StatsResponse(BaseModel):
    total_appointments: int
    available_slots: int
    services_count: int
    customers_count: int

# Dependency functions
async def get_appointment_service() -> AppointmentService:
    """Dependency to get appointment service."""
    graph_db = await get_graph_db()
    service = AppointmentService(graph_db)
    return service

async def get_llm_service() -> LLMService:
    """Dependency to get LLM service."""
    from app.main import app
    return app.state.llm_service

async def get_rag_service() -> RAGService:
    """Dependency to get RAG service."""
    from app.main import app
    return app.state.rag_service

# Chat endpoints
@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    request: Request,
    db = Depends(get_session),
    llm_service: LLMService = Depends(get_llm_service),
    rag_service: RAGService = Depends(get_rag_service),
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """Process a chat message from the web client."""
    try:
        logger.info(f"Processing web chat message: {message.message[:50]}...")
        
        # Store conversation context
        conversation_context = {
            "session_id": message.session_id,
            "user_id": message.user_id,
            "platform": message.platform,
            "timestamp": datetime.now(),
            "user_message": message.message
        }
        
        # Get conversation history for context
        conversation_history = await get_conversation_history(db, message.session_id)
        
        # Create LLM request
        from app.models.schemas import LLMRequest
        llm_request = LLMRequest(
            message=message.message,
            user_id=message.user_id,
            session_id=message.session_id,
            context={
                "platform": "web",
                "conversation_history": conversation_history
            }
        )
        
        # Process message through LLM with function calling
        llm_response = await llm_service.generate_response(llm_request)
        
        # Convert LLM response to dict format
        response_dict = {
            "response": llm_response.content,
            "function_calls": [fc.model_dump() for fc in llm_response.function_calls] if llm_response.function_calls else [],
            "context": {
                "model": llm_response.model,
                "usage": llm_response.usage,
                "session_id": message.session_id,
                "platform": "web"
            }
        }
        
        # Store the conversation
        await store_conversation(db, conversation_context, response_dict)
        
        # Prepare response
        response = ChatResponse(
            response=response_dict["response"],
            session_id=message.session_id,
            timestamp=datetime.now(),
            context=response_dict["context"],
            actions=response_dict["function_calls"]
        )
        
        logger.info(f"Web chat response generated for session: {message.session_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing web chat message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )

@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = 20,
    db = Depends(get_session)
):
    """Get chat history for a session."""
    try:
        history = await get_conversation_history(db, session_id, limit)
        return {"history": history, "session_id": session_id}
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving chat history")

@router.delete("/history/{session_id}")
async def clear_chat_history(
    session_id: str,
    db = Depends(get_session)
):
    """Clear chat history for a session."""
    try:
        await clear_conversation_history(db, session_id)
        return {"message": "Chat history cleared", "session_id": session_id}
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        raise HTTPException(status_code=500, detail="Error clearing chat history")

# Stats endpoint
@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db = Depends(get_session),
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """Get basic statistics for the web client."""
    try:
        # Get basic stats
        stats = await get_basic_stats(db)
        
        # Get available slots for today
        from datetime import date
        today = date.today()
        available_slots = await appointment_service.get_available_slots(today)
        
        return StatsResponse(
            total_appointments=stats.get("total_appointments", 0),
            available_slots=len(available_slots) if available_slots else 0,
            services_count=stats.get("services_count", 0),
            customers_count=stats.get("customers_count", 0)
        )
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return StatsResponse(
            total_appointments=0,
            available_slots=0,
            services_count=0,
            customers_count=0
        )

# Helper functions
async def get_conversation_history(db, session_id: str, limit: int = 10):
    """Get conversation history from database."""
    try:
        query = """
        SELECT user_message, bot_response, created_at
        FROM conversations
        WHERE session_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        
        async with db.cursor() as cursor:
            await cursor.execute(query, (session_id, limit))
            rows = await cursor.fetchall()
            
            history = []
            for row in reversed(rows):  # Reverse to get chronological order
                history.extend([
                    {"role": "user", "content": row[0], "timestamp": row[2]},
                    {"role": "assistant", "content": row[1], "timestamp": row[2]}
                ])
            
            return history
            
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return []

async def store_conversation(db, context: Dict[str, Any], response_dict: Dict[str, Any]):
    """Store conversation in database."""
    try:
        query = """
        INSERT INTO conversations (session_id, user_id, platform, user_message, bot_response, context, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        async with db.cursor() as cursor:
            await cursor.execute(query, (
                context["session_id"],
                context["user_id"],
                context["platform"],
                context["user_message"],
                response_dict.get("response", ""),
                response_dict.get("context", {}),
                context["timestamp"]
            ))
            await db.commit()
            
    except Exception as e:
        logger.error(f"Error storing conversation: {e}")

async def clear_conversation_history(db, session_id: str):
    """Clear conversation history for a session."""
    try:
        query = "DELETE FROM conversations WHERE session_id = %s"
        
        async with db.cursor() as cursor:
            await cursor.execute(query, (session_id,))
            await db.commit()
            
    except Exception as e:
        logger.error(f"Error clearing conversation history: {e}")
        raise

async def get_basic_stats(db):
    """Get basic statistics from database."""
    try:
        stats = {}
        
        # Get total appointments
        async with db.cursor() as cursor:
            await cursor.execute("SELECT COUNT(*) FROM appointments")
            result = await cursor.fetchone()
            stats["total_appointments"] = result[0] if result else 0
            
            # Get services count
            await cursor.execute("SELECT COUNT(*) FROM services")
            result = await cursor.fetchone()
            stats["services_count"] = result[0] if result else 0
            
            # Get customers count
            await cursor.execute("SELECT COUNT(*) FROM customers")
            result = await cursor.fetchone()
            stats["customers_count"] = result[0] if result else 0
            
        return stats
        
    except Exception as e:
        logger.error(f"Error getting basic stats: {e}")
        return {}

# Session management
@router.post("/session")
async def create_session():
    """Create a new chat session."""
    import uuid
    session_id = f"web_{uuid.uuid4().hex[:12]}"
    
    return {
        "session_id": session_id,
        "created_at": datetime.now(),
        "platform": "web"
    }

@router.get("/session/{session_id}/info")
async def get_session_info(
    session_id: str,
    db = Depends(get_session)
):
    """Get session information."""
    try:
        query = """
        SELECT session_id, user_id, platform, created_at, COUNT(*) as message_count
        FROM conversations
        WHERE session_id = %s
        GROUP BY session_id, user_id, platform, created_at
        """
        
        async with db.cursor() as cursor:
            await cursor.execute(query, (session_id,))
            row = await cursor.fetchone()
            
            if row:
                return {
                    "session_id": row[0],
                    "user_id": row[1],
                    "platform": row[2],
                    "created_at": row[3],
                    "message_count": row[4]
                }
            else:
                return {
                    "session_id": session_id,
                    "user_id": "web_user",
                    "platform": "web",
                    "created_at": datetime.now(),
                    "message_count": 0
                }
                
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        return {
            "session_id": session_id,
            "user_id": "web_user",
            "platform": "web",
            "created_at": datetime.now(),
            "message_count": 0
        }