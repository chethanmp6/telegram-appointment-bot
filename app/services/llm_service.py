"""LLM service with function calling capabilities."""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import openai
from anthropic import AsyncAnthropic
from dataclasses import dataclass

from app.core.config import settings
from app.models.schemas import LLMRequest, LLMResponse, FunctionCall
from app.services.appointment_service import AppointmentService
from app.services.rag_service import RAGService
from app.core.graph_db import GraphDatabase

logger = logging.getLogger(__name__)


@dataclass
class FunctionDefinition:
    """Function definition for LLM function calling."""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable


class LLMService:
    """LLM service with function calling and multi-database integration."""
    
    def __init__(self):
        self.client = None
        self.functions: Dict[str, FunctionDefinition] = {}
        self.appointment_service: Optional[AppointmentService] = None
        self.rag_service: Optional[RAGService] = None
        self.graph_db: Optional[GraphDatabase] = None
        self._healthy = False
    
    async def initialize(self):
        """Initialize LLM client and function definitions."""
        try:
            # Initialize LLM client
            if settings.llm_provider == "openai":
                self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            elif settings.llm_provider == "anthropic":
                self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            else:
                raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
            
            # Test connection
            await self._test_connection()
            
            # Register function definitions
            self._register_functions()
            
            self._healthy = True
            logger.info(f"LLM service initialized with provider: {settings.llm_provider}")
            
        except Exception as e:
            logger.error(f"LLM service initialization failed: {e}")
            raise
    
    async def _test_connection(self):
        """Test LLM connection."""
        try:
            if settings.llm_provider == "openai":
                response = await self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                logger.info("OpenAI connection test successful")
            elif settings.llm_provider == "anthropic":
                response = await self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=5,
                    messages=[{"role": "user", "content": "Hello"}]
                )
                logger.info("Anthropic connection test successful")
        except Exception as e:
            logger.error(f"LLM connection test failed: {e}")
            raise
    
    def _register_functions(self):
        """Register all available functions for LLM calling."""
        
        # Appointment management functions
        self.functions["check_availability"] = FunctionDefinition(
            name="check_availability",
            description="Check availability for a specific date, time, service, and duration",
            parameters={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "time": {"type": "string", "description": "Time in HH:MM format"},
                    "service_type": {"type": "string", "description": "Type of service"},
                    "duration": {"type": "integer", "description": "Duration in minutes"}
                },
                "required": ["date", "service_type"]
            },
            handler=self._check_availability
        )
        
        self.functions["book_appointment"] = FunctionDefinition(
            name="book_appointment",
            description="Book an appointment with customer and appointment details",
            parameters={
                "type": "object",
                "properties": {
                    "customer_info": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "phone": {"type": "string"},
                            "email": {"type": "string"}
                        },
                        "required": ["name"]
                    },
                    "appointment_details": {
                        "type": "object",
                        "properties": {
                            "service_id": {"type": "string"},
                            "staff_id": {"type": "string"},
                            "start_time": {"type": "string"},
                            "end_time": {"type": "string"},
                            "notes": {"type": "string"}
                        },
                        "required": ["service_id", "start_time", "end_time"]
                    }
                },
                "required": ["customer_info", "appointment_details"]
            },
            handler=self._book_appointment
        )
        
        self.functions["cancel_appointment"] = FunctionDefinition(
            name="cancel_appointment",
            description="Cancel an existing appointment",
            parameters={
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["appointment_id"]
            },
            handler=self._cancel_appointment
        )
        
        self.functions["reschedule_appointment"] = FunctionDefinition(
            name="reschedule_appointment",
            description="Reschedule an existing appointment to a new date/time",
            parameters={
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "string"},
                    "new_datetime": {"type": "string", "description": "New date and time in ISO format"}
                },
                "required": ["appointment_id", "new_datetime"]
            },
            handler=self._reschedule_appointment
        )
        
        # Service information functions
        self.functions["get_services"] = FunctionDefinition(
            name="get_services",
            description="Get list of available services",
            parameters={"type": "object", "properties": {}},
            handler=self._get_services
        )
        
        self.functions["get_business_hours"] = FunctionDefinition(
            name="get_business_hours",
            description="Get business operating hours",
            parameters={"type": "object", "properties": {}},
            handler=self._get_business_hours
        )
        
        self.functions["find_customer_appointments"] = FunctionDefinition(
            name="find_customer_appointments",
            description="Find appointments for a specific customer",
            parameters={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"}
                },
                "required": ["customer_id"]
            },
            handler=self._find_customer_appointments
        )
        
        # RAG and knowledge functions
        self.functions["search_knowledge_base"] = FunctionDefinition(
            name="search_knowledge_base",
            description="Search the knowledge base for business information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "context": {"type": "string"}
                },
                "required": ["query"]
            },
            handler=self._search_knowledge_base
        )
        
        self.functions["get_business_policies"] = FunctionDefinition(
            name="get_business_policies",
            description="Get business policies and rules",
            parameters={"type": "object", "properties": {}},
            handler=self._get_business_policies
        )
        
        # Graph database functions
        self.functions["get_customer_preferences"] = FunctionDefinition(
            name="get_customer_preferences",
            description="Get customer preferences from graph analysis",
            parameters={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"}
                },
                "required": ["customer_id"]
            },
            handler=self._get_customer_preferences
        )
        
        self.functions["recommend_services"] = FunctionDefinition(
            name="recommend_services",
            description="Get service recommendations based on customer preferences",
            parameters={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "context": {"type": "string"}
                },
                "required": ["customer_id"]
            },
            handler=self._recommend_services
        )
        
        self.functions["find_staff_recommendations"] = FunctionDefinition(
            name="find_staff_recommendations",
            description="Find recommended staff for a service and customer",
            parameters={
                "type": "object",
                "properties": {
                    "service_type": {"type": "string"},
                    "customer_preferences": {"type": "object"}
                },
                "required": ["service_type"]
            },
            handler=self._find_staff_recommendations
        )
        
        logger.info(f"Registered {len(self.functions)} functions for LLM calling")
    
    def set_services(self, appointment_service: AppointmentService, rag_service: RAGService, graph_db: GraphDatabase):
        """Set service dependencies."""
        self.appointment_service = appointment_service
        self.rag_service = rag_service
        self.graph_db = graph_db
    
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate LLM response with function calling."""
        try:
            # Prepare function definitions for the LLM
            function_definitions = self._get_function_definitions()
            
            # Generate response based on provider
            if settings.llm_provider == "openai":
                response = await self._generate_openai_response(request, function_definitions)
            elif settings.llm_provider == "anthropic":
                response = await self._generate_anthropic_response(request, function_definitions)
            else:
                raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
            
            # Execute function calls if present
            if response.function_calls:
                await self._execute_function_calls(response.function_calls)
            
            return response
            
        except Exception as e:
            logger.error(f"LLM response generation failed: {e}")
            raise
    
    async def _generate_openai_response(self, request: LLMRequest, functions: List[Dict]) -> LLMResponse:
        """Generate response using OpenAI API."""
        try:
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": request.message}
            ]
            
            # Add context if provided
            if request.context:
                context_message = f"Context: {json.dumps(request.context, indent=2)}"
                messages.insert(-1, {"role": "system", "content": context_message})
            
            # Make API call
            response = await self.client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                functions=functions if functions else None,
                function_call="auto" if functions else None,
                temperature=request.temperature or settings.llm_temperature,
                max_tokens=request.max_tokens or settings.llm_max_tokens
            )
            
            # Parse response
            message = response.choices[0].message
            function_calls = []
            
            if message.function_call:
                function_calls.append(FunctionCall(
                    name=message.function_call.name,
                    arguments=json.loads(message.function_call.arguments)
                ))
            
            return LLMResponse(
                content=message.content or "",
                function_calls=function_calls,
                usage=response.usage.dict() if response.usage else {},
                model=response.model
            )
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    async def _generate_anthropic_response(self, request: LLMRequest, functions: List[Dict]) -> LLMResponse:
        """Generate response using Anthropic API."""
        try:
            # Prepare system prompt
            system_prompt = self._get_system_prompt()
            
            # Add function information to system prompt
            if functions:
                function_info = "\n\nAvailable functions:\n"
                for func in functions:
                    function_info += f"- {func['name']}: {func['description']}\n"
                system_prompt += function_info
            
            # Prepare messages
            messages = [{"role": "user", "content": request.message}]
            
            # Add context if provided
            if request.context:
                context_message = f"Context: {json.dumps(request.context, indent=2)}"
                messages.insert(0, {"role": "user", "content": context_message})
            
            # Make API call
            response = await self.client.messages.create(
                model=settings.llm_model,
                max_tokens=request.max_tokens or settings.llm_max_tokens,
                temperature=request.temperature or settings.llm_temperature,
                system=system_prompt,
                messages=messages
            )
            
            # Parse response (Anthropic doesn't have native function calling like OpenAI)
            content = response.content[0].text if response.content else ""
            
            # Extract function calls from content if present
            function_calls = self._extract_function_calls_from_content(content)
            
            return LLMResponse(
                content=content,
                function_calls=function_calls,
                usage={"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens},
                model=response.model
            )
            
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the LLM."""
        return f"""You are an AI assistant for {settings.business_name}, a professional appointment booking system.

Your role is to:
1. Help customers book, cancel, and reschedule appointments
2. Answer questions about services, pricing, and policies
3. Provide personalized recommendations based on customer preferences
4. Handle natural language queries about availability and scheduling

Key instructions:
- Always be professional, helpful, and friendly
- Use the available functions to check availability, book appointments, and search for information
- When booking appointments, confirm all details with the customer
- If you need to search for information, use the search_knowledge_base function
- For personalized recommendations, use the graph database functions
- Always respect cancellation policies and business hours
- If you're unsure about something, ask for clarification

Business timezone: {settings.business_timezone}
Current date: {datetime.now().strftime('%Y-%m-%d')}
Current time: {datetime.now().strftime('%H:%M')}

Available functions: {', '.join(self.functions.keys())}
"""
    
    def _get_function_definitions(self) -> List[Dict]:
        """Get function definitions for LLM calling."""
        return [
            {
                "name": func.name,
                "description": func.description,
                "parameters": func.parameters
            }
            for func in self.functions.values()
        ]
    
    def _extract_function_calls_from_content(self, content: str) -> List[FunctionCall]:
        """Extract function calls from Anthropic response content."""
        # This is a simplified implementation
        # In practice, you might want to use a more sophisticated parsing method
        function_calls = []
        
        # Look for function call patterns in the content
        # This would need to be implemented based on your specific prompt engineering
        
        return function_calls
    
    async def _execute_function_calls(self, function_calls: List[FunctionCall]):
        """Execute function calls and update their results."""
        for func_call in function_calls:
            if func_call.name in self.functions:
                try:
                    handler = self.functions[func_call.name].handler
                    result = await handler(**func_call.arguments)
                    # Store result in function call for later use
                    func_call.result = result
                except Exception as e:
                    logger.error(f"Function call {func_call.name} failed: {e}")
                    func_call.error = str(e)
    
    # Function handlers
    async def _check_availability(self, date: str, service_type: str, time: str = None, duration: int = None) -> Dict:
        """Check availability for appointment booking."""
        if not self.appointment_service:
            return {"error": "Appointment service not available"}
        
        try:
            # Convert date string to datetime
            from datetime import datetime
            appointment_date = datetime.strptime(date, "%Y-%m-%d").date()
            
            # Get service information
            service = await self.appointment_service.get_service_by_name(service_type)
            if not service:
                return {"error": f"Service '{service_type}' not found"}
            
            # Check availability
            availability = await self.appointment_service.check_availability(
                date=appointment_date,
                service_id=service.id,
                duration=duration or service.duration
            )
            
            return {
                "available": len(availability.available_slots) > 0,
                "slots": [
                    {
                        "start_time": slot.start_time.strftime("%H:%M"),
                        "end_time": slot.end_time.strftime("%H:%M"),
                        "staff_id": slot.staff_id
                    }
                    for slot in availability.available_slots
                ],
                "service": {
                    "name": service.name,
                    "duration": service.duration,
                    "price": service.price
                }
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _book_appointment(self, customer_info: Dict, appointment_details: Dict) -> Dict:
        """Book an appointment."""
        if not self.appointment_service:
            return {"error": "Appointment service not available"}
        
        try:
            # Create or get customer
            customer = await self.appointment_service.create_or_get_customer(customer_info)
            
            # Book appointment
            appointment = await self.appointment_service.book_appointment(
                customer_id=customer.id,
                service_id=appointment_details["service_id"],
                start_time=appointment_details["start_time"],
                end_time=appointment_details["end_time"],
                staff_id=appointment_details.get("staff_id"),
                notes=appointment_details.get("notes")
            )
            
            return {
                "success": True,
                "appointment_id": appointment.id,
                "confirmation": f"Appointment booked for {appointment.start_time.strftime('%Y-%m-%d %H:%M')}"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _cancel_appointment(self, appointment_id: str, reason: str = None) -> Dict:
        """Cancel an appointment."""
        if not self.appointment_service:
            return {"error": "Appointment service not available"}
        
        try:
            result = await self.appointment_service.cancel_appointment(appointment_id, reason)
            return {
                "success": True,
                "message": "Appointment cancelled successfully"
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _reschedule_appointment(self, appointment_id: str, new_datetime: str) -> Dict:
        """Reschedule an appointment."""
        if not self.appointment_service:
            return {"error": "Appointment service not available"}
        
        try:
            result = await self.appointment_service.reschedule_appointment(appointment_id, new_datetime)
            return {
                "success": True,
                "message": f"Appointment rescheduled to {new_datetime}"
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_services(self) -> Dict:
        """Get available services."""
        if not self.appointment_service:
            return {"error": "Appointment service not available"}
        
        try:
            services = await self.appointment_service.get_all_services()
            return {
                "services": [
                    {
                        "id": service.id,
                        "name": service.name,
                        "description": service.description,
                        "duration": service.duration,
                        "price": service.price,
                        "category": service.category
                    }
                    for service in services
                ]
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_business_hours(self) -> Dict:
        """Get business operating hours."""
        # This would typically come from the database
        return {
            "hours": {
                "monday": "9:00 AM - 6:00 PM",
                "tuesday": "9:00 AM - 6:00 PM",
                "wednesday": "9:00 AM - 6:00 PM",
                "thursday": "9:00 AM - 6:00 PM",
                "friday": "9:00 AM - 6:00 PM",
                "saturday": "10:00 AM - 4:00 PM",
                "sunday": "Closed"
            },
            "timezone": settings.business_timezone
        }
    
    async def _find_customer_appointments(self, customer_id: str) -> Dict:
        """Find customer appointments."""
        if not self.appointment_service:
            return {"error": "Appointment service not available"}
        
        try:
            appointments = await self.appointment_service.get_customer_appointments(customer_id)
            return {
                "appointments": [
                    {
                        "id": apt.id,
                        "start_time": apt.start_time.isoformat(),
                        "end_time": apt.end_time.isoformat(),
                        "status": apt.status,
                        "service_name": apt.service.name if hasattr(apt, 'service') else "Unknown"
                    }
                    for apt in appointments
                ]
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _search_knowledge_base(self, query: str, context: str = None) -> Dict:
        """Search knowledge base."""
        if not self.rag_service:
            return {"error": "RAG service not available"}
        
        try:
            result = await self.rag_service.search(query, context)
            return {
                "answer": result.answer,
                "sources": [
                    {
                        "content": doc.content,
                        "score": doc.score,
                        "metadata": doc.metadata
                    }
                    for doc in result.documents
                ]
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_business_policies(self) -> Dict:
        """Get business policies."""
        # This would typically come from the knowledge base
        return {
            "cancellation_policy": f"Cancellations must be made at least {settings.cancellation_hours} hours in advance",
            "booking_policy": f"Appointments can be booked up to {settings.booking_advance_days} days in advance",
            "payment_policy": "Payment is due at the time of service",
            "no_show_policy": "No-shows will be charged 50% of the service cost"
        }
    
    async def _get_customer_preferences(self, customer_id: str) -> Dict:
        """Get customer preferences from graph database."""
        if not self.graph_db:
            return {"error": "Graph database not available"}
        
        try:
            preferences = await self.graph_db.get_customer_preferences(customer_id)
            return preferences
        except Exception as e:
            return {"error": str(e)}
    
    async def _recommend_services(self, customer_id: str, context: str = None) -> Dict:
        """Get service recommendations."""
        if not self.graph_db:
            return {"error": "Graph database not available"}
        
        try:
            recommendations = await self.graph_db.get_service_recommendations(customer_id, limit=5)
            return {
                "recommendations": recommendations
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _find_staff_recommendations(self, service_type: str, customer_preferences: Dict = None) -> Dict:
        """Find staff recommendations."""
        if not self.graph_db:
            return {"error": "Graph database not available"}
        
        try:
            # Get service ID from type
            if self.appointment_service:
                service = await self.appointment_service.get_service_by_name(service_type)
                if service:
                    recommendations = await self.graph_db.get_staff_recommendations(
                        service.id, 
                        customer_preferences.get("customer_id") if customer_preferences else None
                    )
                    return {"recommendations": recommendations}
            
            return {"error": "Service not found"}
        except Exception as e:
            return {"error": str(e)}
    
    def is_healthy(self) -> bool:
        """Check if LLM service is healthy."""
        return self._healthy
    
    async def close(self):
        """Close LLM service."""
        if self.client:
            # Close client connections if needed
            pass
        self._healthy = False
        logger.info("LLM service closed")