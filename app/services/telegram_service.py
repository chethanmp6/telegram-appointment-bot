"""Telegram bot service with intelligent conversation management."""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import hashlib
from dataclasses import dataclass
from enum import Enum

from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.constants import ParseMode

from app.core.config import settings
from app.models.schemas import (
    TelegramUpdate, TelegramMessage, TelegramResponse, 
    ConversationState, ConversationContext, ConversationUpdate
)
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.appointment_service import AppointmentService
from app.core.graph_db import GraphDatabase
from app.core.database import get_async_session, Conversation

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation state and context."""
    
    def __init__(self):
        self.conversations: Dict[int, Dict[str, Any]] = {}
    
    async def get_conversation(self, user_id: int) -> Dict[str, Any]:
        """Get or create conversation context."""
        if user_id not in self.conversations:
            # Load from database
            async with get_async_session() as session:
                from sqlalchemy import select
                result = await session.execute(
                    select(Conversation).where(Conversation.user_id == user_id)
                )
                conv = result.scalar_one_or_none()
                
                if conv:
                    self.conversations[user_id] = {
                        "id": conv.id,
                        "state": conv.state,
                        "context": conv.context,
                        "last_message_id": conv.last_message_id,
                        "updated_at": conv.updated_at
                    }
                else:
                    # Create new conversation
                    self.conversations[user_id] = {
                        "id": None,
                        "state": ConversationState.IDLE,
                        "context": ConversationContext().model_dump(),
                        "last_message_id": None,
                        "updated_at": datetime.utcnow()
                    }
        
        return self.conversations[user_id]
    
    async def update_conversation(self, user_id: int, updates: Dict[str, Any]):
        """Update conversation state and context."""
        conversation = await self.get_conversation(user_id)
        conversation.update(updates)
        conversation["updated_at"] = datetime.utcnow()
        
        # Save to database
        await self._save_conversation(user_id, conversation)
    
    async def _save_conversation(self, user_id: int, conversation: Dict[str, Any]):
        """Save conversation to database."""
        async with get_async_session() as session:
            try:
                if conversation["id"]:
                    # Update existing
                    conv = await session.get(Conversation, conversation["id"])
                    if conv:
                        conv.state = conversation["state"]
                        conv.context = conversation["context"]
                        conv.last_message_id = conversation["last_message_id"]
                        conv.updated_at = conversation["updated_at"]
                else:
                    # Create new
                    conv = Conversation(
                        user_id=user_id,
                        state=conversation["state"],
                        context=conversation["context"],
                        last_message_id=conversation["last_message_id"]
                    )
                    session.add(conv)
                    await session.commit()
                    await session.refresh(conv)
                    conversation["id"] = conv.id
                
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to save conversation: {e}")


class IntelligentAppointmentAgent:
    """Intelligent agent for appointment booking with multi-database integration."""
    
    def __init__(self, llm_service: LLMService, rag_service: RAGService, 
                 appointment_service: AppointmentService, graph_db: GraphDatabase):
        self.llm_service = llm_service
        self.rag_service = rag_service
        self.appointment_service = appointment_service
        self.graph_db = graph_db
    
    async def process_query(self, user_query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process user query with intelligent multi-database coordination."""
        try:
            # Step 1: Analyze query intent and gather context
            query_analysis = await self._analyze_query_intent(user_query, context)
            
            # Step 2: Gather contextual information from graph
            if query_analysis.get("needs_personalization") and context.get("customer_id"):
                graph_context = await self.graph_db.get_customer_preferences(context["customer_id"])
                context.update({"graph_preferences": graph_context})
            
            # Step 3: Search knowledge base if needed
            if query_analysis.get("needs_knowledge_search"):
                rag_response = await self.rag_service.search(user_query, context)
                context.update({
                    "knowledge_results": rag_response.documents,
                    "knowledge_answer": rag_response.answer
                })
            
            # Step 4: Get recommendations if needed
            if query_analysis.get("needs_recommendations") and context.get("customer_id"):
                from app.models.schemas import RecommendationRequest
                rec_request = RecommendationRequest(customer_id=context["customer_id"])
                recommendations = await self.appointment_service.get_recommendations(rec_request)
                context.update({"recommendations": recommendations})
            
            # Step 5: Generate LLM response with function calling
            from app.models.schemas import LLMRequest
            llm_request = LLMRequest(message=user_query, context=context)
            llm_response = await self.llm_service.generate_response(llm_request)
            
            # Step 6: Update graph based on interactions
            if llm_response.function_calls and context.get("customer_id"):
                await self._update_graph_from_interactions(
                    llm_response.function_calls, 
                    context["customer_id"]
                )
            
            return {
                "response": llm_response.content,
                "function_calls": [fc.model_dump() for fc in llm_response.function_calls],
                "context_updates": context,
                "query_analysis": query_analysis
            }
            
        except Exception as e:
            logger.error(f"Agent query processing failed: {e}")
            return {
                "response": "I'm sorry, I encountered an error processing your request. Please try again.",
                "function_calls": [],
                "context_updates": context,
                "error": str(e)
            }
    
    async def _analyze_query_intent(self, query: str, context: Dict[str, Any]) -> Dict[str, bool]:
        """Analyze query intent to determine what services are needed."""
        query_lower = query.lower()
        
        # Simple intent detection (could be enhanced with ML)
        intents = {
            "needs_personalization": any(word in query_lower for word in [
                "recommend", "suggest", "best", "prefer", "like", "similar"
            ]),
            "needs_knowledge_search": any(word in query_lower for word in [
                "policy", "price", "cost", "hours", "location", "what", "how", "when", "where"
            ]),
            "needs_recommendations": any(word in query_lower for word in [
                "recommend", "suggest", "what should", "best for", "good for"
            ]),
            "needs_booking": any(word in query_lower for word in [
                "book", "schedule", "appointment", "reserve", "available"
            ]),
            "needs_cancellation": any(word in query_lower for word in [
                "cancel", "delete", "remove"
            ]),
            "needs_rescheduling": any(word in query_lower for word in [
                "reschedule", "change", "move", "different time"
            ])
        }
        
        return intents
    
    async def _update_graph_from_interactions(self, function_calls: List, customer_id: str):
        """Update graph database based on user interactions."""
        try:
            for func_call in function_calls:
                if func_call.name == "book_appointment" and hasattr(func_call, 'result'):
                    # Strengthen preference for booked service
                    service_id = func_call.arguments.get("appointment_details", {}).get("service_id")
                    if service_id:
                        await self.graph_db.update_customer_preferences(
                            customer_id, service_id, satisfaction=1.0
                        )
                
                elif func_call.name == "search_knowledge_base":
                    # Track knowledge interests
                    query = func_call.arguments.get("query", "")
                    # Could create concept relationships here
                    pass
        
        except Exception as e:
            logger.error(f"Failed to update graph from interactions: {e}")


class TelegramService:
    """Telegram bot service with intelligent conversation management."""
    
    def __init__(self):
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        self.conversation_manager = ConversationManager()
        self.agent: Optional[IntelligentAppointmentAgent] = None
        self._healthy = False
        
        # Service dependencies
        self.llm_service: Optional[LLMService] = None
        self.rag_service: Optional[RAGService] = None
        self.appointment_service: Optional[AppointmentService] = None
        self.graph_db: Optional[GraphDatabase] = None
    
    async def initialize(self):
        """Initialize Telegram bot service."""
        try:
            if not settings.telegram_bot_token:
                raise ValueError("Telegram bot token not configured")
            
            # Create bot and application
            self.application = Application.builder().token(settings.telegram_bot_token).build()
            self.bot = self.application.bot
            
            # Register handlers
            self._register_handlers()
            
            # Test bot connection
            await self.bot.get_me()
            
            self._healthy = True
            logger.info("Telegram bot service initialized successfully")
            
        except Exception as e:
            logger.error(f"Telegram bot initialization failed: {e}")
            raise
    
    def set_services(self, llm_service: LLMService, rag_service: RAGService, 
                    appointment_service: AppointmentService, graph_db: GraphDatabase):
        """Set service dependencies."""
        self.llm_service = llm_service
        self.rag_service = rag_service
        self.appointment_service = appointment_service
        self.graph_db = graph_db
        
        # Initialize intelligent agent
        self.agent = IntelligentAppointmentAgent(
            llm_service, rag_service, appointment_service, graph_db
        )
    
    def _register_handlers(self):
        """Register Telegram bot handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("help", self._handle_help))
        self.application.add_handler(CommandHandler("book", self._handle_book))
        self.application.add_handler(CommandHandler("cancel", self._handle_cancel))
        self.application.add_handler(CommandHandler("appointments", self._handle_appointments))
        self.application.add_handler(CommandHandler("services", self._handle_services))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(self._handle_callback))
    
    async def process_update(self, update_data: Dict[str, Any]):
        """Process incoming Telegram update."""
        try:
            update = Update.de_json(update_data, self.bot)
            if update:
                await self.application.process_update(update)
        except Exception as e:
            logger.error(f"Failed to process update: {e}")
    
    # Command handlers
    async def _handle_start(self, update: Update, context):
        """Handle /start command."""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Create or get customer
        if self.appointment_service:
            try:
                customer = await self.appointment_service.create_or_get_customer({
                    "telegram_user_id": user.id,
                    "name": user.first_name or "User",
                    "preferences": {}
                })
                
                # Update conversation context
                await self.conversation_manager.update_conversation(user.id, {
                    "context": {"customer_id": customer.id},
                    "state": ConversationState.IDLE
                })
                
            except Exception as e:
                logger.error(f"Failed to create customer: {e}")
        
        welcome_message = f"""
👋 Welcome to {settings.business_name}, {user.first_name}!

I'm your AI assistant for appointment booking. I can help you with:

🗓️ Book appointments
📋 Check availability  
❌ Cancel or reschedule
❓ Answer questions about services
💡 Provide personalized recommendations

Just tell me what you need in natural language, like:
• "I need a haircut next Friday"
• "What services do you offer?"
• "Cancel my appointment tomorrow"

How can I help you today?
"""
        
        keyboard = ReplyKeyboardMarkup([
            [KeyboardButton("📅 Book Appointment"), KeyboardButton("📋 My Appointments")],
            [KeyboardButton("🛍️ Services"), KeyboardButton("❓ Help")]
        ], resize_keyboard=True)
        
        await update.message.reply_text(welcome_message, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    async def _handle_help(self, update: Update, context):
        """Handle /help command."""
        help_message = f"""
🤖 <b>{settings.business_name} Assistant</b>

<b>Available Commands:</b>
/start - Start conversation
/book - Quick booking
/cancel - Cancel appointment
/appointments - View your appointments
/services - List all services
/help - Show this help

<b>Natural Language Examples:</b>
• "Book me a massage for tomorrow at 2 PM"
• "What are your cancellation policies?"
• "Show me appointments this week"
• "I need something relaxing"
• "What works well with a facial?"

<b>Quick Actions:</b>
Use the keyboard buttons below for common actions.

<b>Business Hours:</b>
Monday-Friday: 9:00 AM - 6:00 PM
Saturday: 10:00 AM - 4:00 PM
Sunday: Closed

Need more help? Just ask me anything! 😊
"""
        
        await update.message.reply_text(help_message, parse_mode=ParseMode.HTML)
    
    async def _handle_book(self, update: Update, context):
        """Handle /book command."""
        user_id = update.effective_user.id
        
        # Update conversation state
        await self.conversation_manager.update_conversation(user_id, {
            "state": ConversationState.BOOKING
        })
        
        # Get available services for quick selection
        services_keyboard = await self._get_services_keyboard()
        
        message = """
📅 <b>Book an Appointment</b>

You can either:
1. Choose a service below, or
2. Tell me what you need in natural language

Examples:
• "I need a haircut this Friday afternoon"
• "Book me for a massage with Sarah"
• "What's available tomorrow morning?"
"""
        
        await update.message.reply_text(
            message, 
            reply_markup=services_keyboard, 
            parse_mode=ParseMode.HTML
        )
    
    async def _handle_cancel(self, update: Update, context):
        """Handle /cancel command."""
        user_id = update.effective_user.id
        
        # Get user's appointments
        conversation = await self.conversation_manager.get_conversation(user_id)
        customer_id = conversation.get("context", {}).get("customer_id")
        
        if not customer_id or not self.appointment_service:
            await update.message.reply_text("Please start with /start first.")
            return
        
        try:
            from app.models.schemas import AppointmentStatus
            appointments = await self.appointment_service.get_customer_appointments(
                customer_id, 
                status_filter=[AppointmentStatus.CONFIRMED, AppointmentStatus.RESCHEDULED]
            )
            
            if not appointments:
                await update.message.reply_text("You don't have any upcoming appointments to cancel.")
                return
            
            # Create inline keyboard with appointments
            keyboard = []
            for apt in appointments[:5]:  # Limit to 5 recent appointments
                keyboard.append([InlineKeyboardButton(
                    f"{apt.start_time.strftime('%m/%d %H:%M')} - Service",
                    callback_data=f"cancel_{apt.id}"
                )])
            
            keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")])
            
            await update.message.reply_text(
                "Select an appointment to cancel:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            logger.error(f"Failed to get appointments: {e}")
            await update.message.reply_text("Sorry, I couldn't retrieve your appointments.")
    
    async def _handle_appointments(self, update: Update, context):
        """Handle /appointments command."""
        user_id = update.effective_user.id
        conversation = await self.conversation_manager.get_conversation(user_id)
        customer_id = conversation.get("context", {}).get("customer_id")
        
        if not customer_id or not self.appointment_service:
            await update.message.reply_text("Please start with /start first.")
            return
        
        try:
            appointments = await self.appointment_service.get_customer_appointments(customer_id)
            
            if not appointments:
                await update.message.reply_text("You don't have any appointments.")
                return
            
            message = "📅 <b>Your Appointments:</b>\n\n"
            
            for apt in appointments[:10]:  # Show last 10 appointments
                status_emoji = {
                    "confirmed": "✅",
                    "cancelled": "❌", 
                    "completed": "✅",
                    "rescheduled": "🔄",
                    "no_show": "❌"
                }.get(apt.status, "❓")
                
                message += f"{status_emoji} <b>{apt.start_time.strftime('%m/%d/%Y %H:%M')}</b>\n"
                message += f"   Status: {apt.status.title()}\n"
                if apt.notes:
                    message += f"   Notes: {apt.notes}\n"
                message += "\n"
            
            await update.message.reply_text(message, parse_mode=ParseMode.HTML)
            
        except Exception as e:
            logger.error(f"Failed to get appointments: {e}")
            await update.message.reply_text("Sorry, I couldn't retrieve your appointments.")
    
    async def _handle_services(self, update: Update, context):
        """Handle /services command."""
        if not self.appointment_service:
            await update.message.reply_text("Service information is not available.")
            return
        
        try:
            services = await self.appointment_service.get_all_services()
            
            if not services:
                await update.message.reply_text("No services are currently available.")
                return
            
            message = "🛍️ <b>Available Services:</b>\n\n"
            
            current_category = None
            for service in services:
                if service.category != current_category:
                    current_category = service.category
                    message += f"\n<b>{current_category.title()}:</b>\n"
                
                message += f"• <b>{service.name}</b>\n"
                message += f"  {service.description}\n"
                message += f"  Duration: {service.duration} minutes\n"
                message += f"  Price: ${service.price:.2f}\n\n"
            
            message += "To book any service, just tell me what you need! 😊"
            
            await update.message.reply_text(message, parse_mode=ParseMode.HTML)
            
        except Exception as e:
            logger.error(f"Failed to get services: {e}")
            await update.message.reply_text("Sorry, I couldn't retrieve the services list.")
    
    # Message handler
    async def _handle_message(self, update: Update, context):
        """Handle general text messages with intelligent processing."""
        user = update.effective_user
        message_text = update.message.text
        
        # Get conversation context
        conversation = await self.conversation_manager.get_conversation(user.id)
        
        # Handle quick reply buttons
        if message_text in ["📅 Book Appointment", "📋 My Appointments", "🛍️ Services", "❓ Help"]:
            if message_text == "📅 Book Appointment":
                await self._handle_book(update, context)
            elif message_text == "📋 My Appointments":
                await self._handle_appointments(update, context)
            elif message_text == "🛍️ Services":
                await self._handle_services(update, context)
            elif message_text == "❓ Help":
                await self._handle_help(update, context)
            return
        
        # Process with intelligent agent
        if self.agent:
            try:
                # Show typing indicator
                await update.message.chat.send_action("typing")
                
                # Process query with agent
                result = await self.agent.process_query(message_text, conversation["context"])
                
                # Update conversation context
                await self.conversation_manager.update_conversation(user.id, {
                    "context": result["context_updates"],
                    "last_message_id": update.message.message_id
                })
                
                # Send response
                response_text = result["response"]
                
                # Add action buttons if appropriate
                reply_markup = None
                if result.get("function_calls"):
                    reply_markup = self._get_context_keyboard(result["function_calls"])
                
                await update.message.reply_text(
                    response_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
                
            except Exception as e:
                logger.error(f"Agent processing failed: {e}")
                await update.message.reply_text(
                    "I'm sorry, I encountered an error. Please try rephrasing your request."
                )
        else:
            # Fallback response
            await update.message.reply_text(
                "I'm still initializing. Please try again in a moment."
            )
    
    # Callback handler
    async def _handle_callback(self, update: Update, context):
        """Handle inline keyboard callbacks."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = update.effective_user.id
        
        if data.startswith("cancel_"):
            appointment_id = data.split("_")[1]
            
            if self.appointment_service:
                try:
                    await self.appointment_service.cancel_appointment(
                        appointment_id, 
                        "Cancelled via Telegram bot"
                    )
                    await query.edit_message_text("✅ Appointment cancelled successfully.")
                except Exception as e:
                    logger.error(f"Failed to cancel appointment: {e}")
                    await query.edit_message_text("❌ Failed to cancel appointment.")
        
        elif data == "cancel_action":
            await query.edit_message_text("Cancellation aborted.")
        
        elif data.startswith("service_"):
            service_id = data.split("_")[1]
            # Handle service selection for booking
            await self.conversation_manager.update_conversation(user_id, {
                "context": {"selected_service_id": service_id},
                "state": ConversationState.BOOKING
            })
            await query.edit_message_text("Service selected! When would you like to book?")
    
    # Helper methods
    async def _get_services_keyboard(self) -> InlineKeyboardMarkup:
        """Get services inline keyboard."""
        if not self.appointment_service:
            return InlineKeyboardMarkup([])
        
        try:
            services = await self.appointment_service.get_all_services()
            keyboard = []
            
            for service in services[:10]:  # Limit to 10 services
                keyboard.append([InlineKeyboardButton(
                    f"{service.name} (${service.price})",
                    callback_data=f"service_{service.id}"
                )])
            
            return InlineKeyboardMarkup(keyboard)
            
        except Exception as e:
            logger.error(f"Failed to get services keyboard: {e}")
            return InlineKeyboardMarkup([])
    
    def _get_context_keyboard(self, function_calls: List[Dict]) -> Optional[InlineKeyboardMarkup]:
        """Get context-appropriate keyboard based on function calls."""
        keyboard = []
        
        for func_call in function_calls:
            if func_call["name"] == "check_availability":
                keyboard.append([InlineKeyboardButton("📅 Book This Slot", callback_data="book_slot")])
            elif func_call["name"] == "get_services":
                keyboard.append([InlineKeyboardButton("🛍️ View Details", callback_data="service_details")])
        
        if keyboard:
            return InlineKeyboardMarkup(keyboard)
        return None
    
    def is_healthy(self) -> bool:
        """Check if Telegram service is healthy."""
        return self._healthy
    
    async def close(self):
        """Close Telegram service."""
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
        
        self._healthy = False
        logger.info("Telegram service closed")