"""Pydantic schemas for API requests and responses."""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date, time
from enum import Enum
import uuid


class AppointmentStatus(str, Enum):
    """Appointment status enumeration."""
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class ConversationState(str, Enum):
    """Conversation state enumeration."""
    IDLE = "idle"
    BOOKING = "booking"
    CANCELLING = "cancelling"
    RESCHEDULING = "rescheduling"
    ASKING = "asking"
    CONFIRMING = "confirming"


class LLMProvider(str, Enum):
    """LLM provider enumeration."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common fields."""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


# Customer schemas
class CustomerBase(BaseModel):
    """Base customer schema."""
    name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    preferences: Dict[str, Any] = Field(default_factory=dict)


class CustomerCreate(CustomerBase):
    """Customer creation schema."""
    telegram_user_id: int = Field(..., gt=0)


class CustomerUpdate(BaseModel):
    """Customer update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    preferences: Optional[Dict[str, Any]] = None


class CustomerResponse(CustomerBase, BaseSchema):
    """Customer response schema."""
    telegram_user_id: int
    is_active: bool = True
    
    class Config:
        from_attributes = True


# Staff schemas
class StaffBase(BaseModel):
    """Base staff schema."""
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    specializations: List[str] = Field(default_factory=list)
    working_hours: Dict[str, Any] = Field(default_factory=dict)
    calendar_id: Optional[str] = Field(None, max_length=255)


class StaffCreate(StaffBase):
    """Staff creation schema."""
    pass


class StaffUpdate(BaseModel):
    """Staff update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    specializations: Optional[List[str]] = None
    working_hours: Optional[Dict[str, Any]] = None
    calendar_id: Optional[str] = Field(None, max_length=255)


class StaffResponse(StaffBase, BaseSchema):
    """Staff response schema."""
    is_active: bool = True
    
    class Config:
        from_attributes = True


# Service schemas
class ServiceBase(BaseModel):
    """Base service schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    duration: int = Field(..., gt=0, le=480)  # max 8 hours
    price: float = Field(..., ge=0)
    category: str = Field(..., min_length=1, max_length=50)
    requirements: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ServiceCreate(ServiceBase):
    """Service creation schema."""
    pass


class ServiceUpdate(BaseModel):
    """Service update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1)
    duration: Optional[int] = Field(None, gt=0, le=480)
    price: Optional[float] = Field(None, ge=0)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    requirements: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ServiceResponse(ServiceBase, BaseSchema):
    """Service response schema."""
    is_active: bool = True
    
    class Config:
        from_attributes = True


# Appointment schemas
class AppointmentBase(BaseModel):
    """Base appointment schema."""
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v


class AppointmentCreate(AppointmentBase):
    """Appointment creation schema."""
    customer_id: str
    staff_id: str
    service_id: str


class AppointmentUpdate(BaseModel):
    """Appointment update schema."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if v and 'start_time' in values and values['start_time'] and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v


class AppointmentResponse(AppointmentBase, BaseSchema):
    """Appointment response schema."""
    customer_id: str
    staff_id: str
    service_id: str
    status: AppointmentStatus = AppointmentStatus.CONFIRMED
    cancellation_reason: Optional[str] = None
    reminder_sent: bool = False
    
    class Config:
        from_attributes = True


# Conversation schemas
class ConversationContext(BaseModel):
    """Conversation context schema."""
    customer_id: Optional[str] = None
    booking_data: Dict[str, Any] = Field(default_factory=dict)
    last_query: Optional[str] = None
    function_calls: List[Dict[str, Any]] = Field(default_factory=list)
    rag_context: Dict[str, Any] = Field(default_factory=dict)
    graph_context: Dict[str, Any] = Field(default_factory=dict)


class ConversationUpdate(BaseModel):
    """Conversation update schema."""
    context: Optional[ConversationContext] = None
    state: Optional[ConversationState] = None
    last_message_id: Optional[int] = None


class ConversationResponse(BaseSchema):
    """Conversation response schema."""
    user_id: int
    context: ConversationContext
    state: ConversationState = ConversationState.IDLE
    last_message_id: Optional[int] = None
    
    class Config:
        from_attributes = True


# LLM schemas
class FunctionCall(BaseModel):
    """Function call schema."""
    name: str
    arguments: Dict[str, Any]


class LLMRequest(BaseModel):
    """LLM request schema."""
    message: str
    context: Optional[Dict[str, Any]] = None
    functions: Optional[List[Dict[str, Any]]] = None
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, gt=0)


class LLMResponse(BaseModel):
    """LLM response schema."""
    content: str
    function_calls: List[FunctionCall] = Field(default_factory=list)
    usage: Dict[str, Any] = Field(default_factory=dict)
    model: str


# RAG schemas
class RAGQuery(BaseModel):
    """RAG query schema."""
    query: str
    context: Optional[Dict[str, Any]] = None
    top_k: Optional[int] = Field(default=5, ge=1, le=20)
    similarity_threshold: Optional[float] = Field(default=0.7, ge=0, le=1)


class RAGDocument(BaseModel):
    """RAG document schema."""
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: float = Field(ge=0, le=1)


class RAGResponse(BaseModel):
    """RAG response schema."""
    query: str
    documents: List[RAGDocument]
    answer: str
    processing_time: float
    retrieval_score: float


# Graph database schemas
class GraphNode(BaseModel):
    """Graph node schema."""
    id: str
    labels: List[str]
    properties: Dict[str, Any]


class GraphRelationship(BaseModel):
    """Graph relationship schema."""
    type: str
    start_node: str
    end_node: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphQuery(BaseModel):
    """Graph query schema."""
    query: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class GraphResponse(BaseModel):
    """Graph response schema."""
    nodes: List[GraphNode] = Field(default_factory=list)
    relationships: List[GraphRelationship] = Field(default_factory=list)
    data: List[Dict[str, Any]] = Field(default_factory=list)


# Recommendation schemas
class ServiceRecommendation(BaseModel):
    """Service recommendation schema."""
    service_id: str
    service_name: str
    description: str
    price: float
    duration: int
    score: float
    reasons: List[str] = Field(default_factory=list)


class StaffRecommendation(BaseModel):
    """Staff recommendation schema."""
    staff_id: str
    staff_name: str
    expertise_level: float
    previous_satisfaction: float
    total_score: float
    specializations: List[str] = Field(default_factory=list)


class RecommendationRequest(BaseModel):
    """Recommendation request schema."""
    customer_id: str
    service_id: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=5, ge=1, le=20)


class RecommendationResponse(BaseModel):
    """Recommendation response schema."""
    customer_id: str
    service_recommendations: List[ServiceRecommendation] = Field(default_factory=list)
    staff_recommendations: List[StaffRecommendation] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Telegram bot schemas
class TelegramUpdate(BaseModel):
    """Telegram update schema."""
    update_id: int
    message: Optional[Dict[str, Any]] = None
    callback_query: Optional[Dict[str, Any]] = None
    inline_query: Optional[Dict[str, Any]] = None


class TelegramMessage(BaseModel):
    """Telegram message schema."""
    text: str
    user_id: int
    chat_id: int
    message_id: int
    reply_markup: Optional[Dict[str, Any]] = None


class TelegramResponse(BaseModel):
    """Telegram response schema."""
    text: str
    reply_markup: Optional[Dict[str, Any]] = None
    parse_mode: Optional[str] = "HTML"


# Availability schemas
class TimeSlot(BaseModel):
    """Time slot schema."""
    start_time: datetime
    end_time: datetime
    available: bool = True
    staff_id: Optional[str] = None


class AvailabilityRequest(BaseModel):
    """Availability request schema."""
    date: date
    service_id: str
    staff_id: Optional[str] = None
    duration: Optional[int] = None


class AvailabilityResponse(BaseModel):
    """Availability response schema."""
    date: date
    service_id: str
    available_slots: List[TimeSlot]
    staff_availability: Dict[str, List[TimeSlot]] = Field(default_factory=dict)


# Analytics schemas
class BookingAnalytics(BaseModel):
    """Booking analytics schema."""
    total_bookings: int
    completion_rate: float
    cancellation_rate: float
    popular_services: List[Dict[str, Any]]
    peak_hours: List[int]
    customer_segments: Dict[str, int]


class CustomerAnalytics(BaseModel):
    """Customer analytics schema."""
    customer_id: str
    total_appointments: int
    favorite_services: List[str]
    preferred_staff: List[str]
    booking_frequency: float
    satisfaction_score: float
    preferences: Dict[str, Any]


class BusinessInsights(BaseModel):
    """Business insights schema."""
    popular_services: List[Dict[str, Any]]
    top_staff: List[Dict[str, Any]]
    customer_segments: List[Dict[str, Any]]
    revenue_trends: Dict[str, float]
    recommendation_accuracy: float


# Health check schemas
class HealthCheck(BaseModel):
    """Health check schema."""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    database: bool = True
    graph_db: bool = True
    vector_db: bool = True
    llm_service: bool = True
    telegram_bot: bool = True
    
    @validator('status')
    def validate_status(cls, v, values):
        if not all([
            values.get('database', True),
            values.get('graph_db', True),
            values.get('vector_db', True),
            values.get('llm_service', True),
            values.get('telegram_bot', True)
        ]):
            return "unhealthy"
        return v