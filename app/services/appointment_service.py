"""Appointment management service with multi-database coordination."""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date, time, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session, Customer, Staff, Service, Appointment, BusinessRule
from app.core.graph_db import GraphDatabase
from app.models.schemas import (
    CustomerCreate, CustomerResponse, CustomerUpdate,
    StaffCreate, StaffResponse, StaffUpdate,
    ServiceCreate, ServiceResponse, ServiceUpdate,
    AppointmentCreate, AppointmentResponse, AppointmentUpdate,
    AvailabilityRequest, AvailabilityResponse, TimeSlot,
    AppointmentStatus, RecommendationRequest, RecommendationResponse
)

logger = logging.getLogger(__name__)


class AppointmentService:
    """Service for managing appointments with graph intelligence."""
    
    def __init__(self, graph_db: Optional[GraphDatabase] = None):
        self.graph_db = graph_db
    
    def set_graph_db(self, graph_db: GraphDatabase):
        """Set graph database reference."""
        self.graph_db = graph_db
    
    # Customer management
    async def create_customer(self, customer_data: CustomerCreate) -> CustomerResponse:
        """Create a new customer."""
        async with get_async_session() as session:
            try:
                # Check if customer already exists
                existing = await session.execute(
                    select(Customer).where(Customer.telegram_user_id == customer_data.telegram_user_id)
                )
                if existing.scalar_one_or_none():
                    raise ValueError("Customer already exists")
                
                # Create customer
                customer = Customer(
                    telegram_user_id=customer_data.telegram_user_id,
                    name=customer_data.name,
                    phone=customer_data.phone,
                    email=customer_data.email,
                    preferences=customer_data.preferences
                )
                
                session.add(customer)
                await session.commit()
                await session.refresh(customer)
                
                # Create customer node in graph database
                if self.graph_db:
                    await self.graph_db.create_customer_node({
                        "id": customer.id,
                        "telegram_user_id": customer.telegram_user_id,
                        "name": customer.name,
                        "phone": customer.phone,
                        "email": customer.email,
                        "preferences": customer.preferences,
                        "created_at": customer.created_at.isoformat(),
                        "updated_at": customer.updated_at.isoformat()
                    })
                
                return CustomerResponse.model_validate(customer)
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create customer: {e}")
                raise
    
    async def create_or_get_customer(self, customer_info: Dict[str, Any]) -> CustomerResponse:
        """Create customer or get existing one by telegram user ID."""
        telegram_user_id = customer_info.get("telegram_user_id")
        
        if telegram_user_id:
            # Try to get existing customer
            customer = await self.get_customer_by_telegram_id(telegram_user_id)
            if customer:
                return customer
        
        # Create new customer
        customer_data = CustomerCreate(
            telegram_user_id=telegram_user_id or 0,  # Will need proper handling
            name=customer_info["name"],
            phone=customer_info.get("phone"),
            email=customer_info.get("email"),
            preferences=customer_info.get("preferences", {})
        )
        
        return await self.create_customer(customer_data)
    
    async def get_customer_by_telegram_id(self, telegram_user_id: int) -> Optional[CustomerResponse]:
        """Get customer by Telegram user ID."""
        async with get_async_session() as session:
            result = await session.execute(
                select(Customer).where(Customer.telegram_user_id == telegram_user_id)
            )
            customer = result.scalar_one_or_none()
            return CustomerResponse.model_validate(customer) if customer else None
    
    async def update_customer(self, customer_id: str, update_data: CustomerUpdate) -> CustomerResponse:
        """Update customer information."""
        async with get_async_session() as session:
            try:
                customer = await session.get(Customer, customer_id)
                if not customer:
                    raise ValueError("Customer not found")
                
                # Update fields
                update_dict = update_data.model_dump(exclude_unset=True)
                for field, value in update_dict.items():
                    setattr(customer, field, value)
                
                customer.updated_at = datetime.utcnow()
                await session.commit()
                await session.refresh(customer)
                
                return CustomerResponse.model_validate(customer)
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update customer: {e}")
                raise
    
    # Staff management
    async def create_staff(self, staff_data: StaffCreate) -> StaffResponse:
        """Create a new staff member."""
        async with get_async_session() as session:
            try:
                staff = Staff(**staff_data.model_dump())
                session.add(staff)
                await session.commit()
                await session.refresh(staff)
                
                # Create staff node in graph database
                if self.graph_db:
                    # Create staff relationships would be implemented here
                    pass
                
                return StaffResponse.model_validate(staff)
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create staff: {e}")
                raise
    
    async def get_all_staff(self, active_only: bool = True) -> List[StaffResponse]:
        """Get all staff members."""
        async with get_async_session() as session:
            query = select(Staff)
            if active_only:
                query = query.where(Staff.is_active == True)
            
            result = await session.execute(query)
            staff_list = result.scalars().all()
            return [StaffResponse.model_validate(staff) for staff in staff_list]
    
    # Service management
    async def create_service(self, service_data: ServiceCreate) -> ServiceResponse:
        """Create a new service."""
        async with get_async_session() as session:
            try:
                service = Service(**service_data.model_dump())
                session.add(service)
                await session.commit()
                await session.refresh(service)
                
                # Create service relationships in graph database
                if self.graph_db:
                    await self.graph_db.create_service_relationships([{
                        "id": service.id,
                        "name": service.name,
                        "description": service.description,
                        "price": service.price,
                        "duration": service.duration,
                        "category": service.category
                    }])
                
                return ServiceResponse.model_validate(service)
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create service: {e}")
                raise
    
    async def get_all_services(self, active_only: bool = True) -> List[ServiceResponse]:
        """Get all services."""
        async with get_async_session() as session:
            query = select(Service)
            if active_only:
                query = query.where(Service.is_active == True)
            
            result = await session.execute(query)
            services = result.scalars().all()
            return [ServiceResponse.model_validate(service) for service in services]
    
    async def get_service_by_name(self, name: str) -> Optional[ServiceResponse]:
        """Get service by name."""
        async with get_async_session() as session:
            result = await session.execute(
                select(Service).where(
                    and_(
                        Service.name.ilike(f"%{name}%"),
                        Service.is_active == True
                    )
                )
            )
            service = result.scalar_one_or_none()
            return ServiceResponse.model_validate(service) if service else None
    
    # Appointment management
    async def check_availability(self, date: date, service_id: str, staff_id: Optional[str] = None, 
                                duration: Optional[int] = None) -> AvailabilityResponse:
        """Check availability for appointments."""
        async with get_async_session() as session:
            try:
                # Get service details
                service = await session.get(Service, service_id)
                if not service:
                    raise ValueError("Service not found")
                
                duration = duration or service.duration
                
                # Get business hours (simplified - would come from business rules)
                business_start = time(9, 0)  # 9 AM
                business_end = time(17, 0)   # 5 PM
                
                # Generate time slots
                slots = self._generate_time_slots(date, business_start, business_end, duration)
                
                # Get existing appointments
                query = select(Appointment).where(
                    and_(
                        func.date(Appointment.start_time) == date,
                        Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.RESCHEDULED]),
                        Appointment.service_id == service_id
                    )
                )
                
                if staff_id:
                    query = query.where(Appointment.staff_id == staff_id)
                
                result = await session.execute(query)
                existing_appointments = result.scalars().all()
                
                # Filter available slots
                available_slots = self._filter_available_slots(slots, existing_appointments)
                
                # Get staff availability if needed
                staff_availability = {}
                if not staff_id:
                    staff_list = await self.get_all_staff()
                    for staff in staff_list:
                        staff_slots = self._filter_available_slots(
                            slots, 
                            [apt for apt in existing_appointments if apt.staff_id == staff.id]
                        )
                        staff_availability[staff.id] = staff_slots
                
                return AvailabilityResponse(
                    date=date,
                    service_id=service_id,
                    available_slots=available_slots,
                    staff_availability=staff_availability
                )
                
            except Exception as e:
                logger.error(f"Failed to check availability: {e}")
                raise
    
    def _generate_time_slots(self, date: date, start_time: time, end_time: time, duration: int) -> List[TimeSlot]:
        """Generate time slots for a given date and duration."""
        slots = []
        current_datetime = datetime.combine(date, start_time)
        end_datetime = datetime.combine(date, end_time)
        
        while current_datetime + timedelta(minutes=duration) <= end_datetime:
            slot_end = current_datetime + timedelta(minutes=duration)
            slots.append(TimeSlot(
                start_time=current_datetime,
                end_time=slot_end,
                available=True
            ))
            current_datetime += timedelta(minutes=30)  # 30-minute intervals
        
        return slots
    
    def _filter_available_slots(self, slots: List[TimeSlot], appointments: List[Appointment]) -> List[TimeSlot]:
        """Filter out booked slots from available slots."""
        available_slots = []
        
        for slot in slots:
            is_available = True
            for appointment in appointments:
                if (slot.start_time < appointment.end_time and 
                    slot.end_time > appointment.start_time):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append(slot)
        
        return available_slots
    
    async def book_appointment(self, customer_id: str, service_id: str, start_time: str, 
                              end_time: str, staff_id: Optional[str] = None, 
                              notes: Optional[str] = None) -> AppointmentResponse:
        """Book a new appointment."""
        async with get_async_session() as session:
            try:
                # Parse datetime strings
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                
                # Validate customer, service, and staff
                customer = await session.get(Customer, customer_id)
                service = await session.get(Service, service_id)
                
                if not customer or not service:
                    raise ValueError("Customer or service not found")
                
                # Auto-assign staff if not provided
                if not staff_id:
                    staff_id = await self._find_available_staff(session, service_id, start_dt, end_dt)
                
                if not staff_id:
                    raise ValueError("No staff available for this time slot")
                
                # Check for conflicts
                conflicts = await session.execute(
                    select(Appointment).where(
                        and_(
                            Appointment.staff_id == staff_id,
                            Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.RESCHEDULED]),
                            or_(
                                and_(Appointment.start_time <= start_dt, Appointment.end_time > start_dt),
                                and_(Appointment.start_time < end_dt, Appointment.end_time >= end_dt)
                            )
                        )
                    )
                )
                
                if conflicts.scalar_one_or_none():
                    raise ValueError("Time slot is not available")
                
                # Create appointment
                appointment = Appointment(
                    customer_id=customer_id,
                    staff_id=staff_id,
                    service_id=service_id,
                    start_time=start_dt,
                    end_time=end_dt,
                    notes=notes,
                    status=AppointmentStatus.CONFIRMED
                )
                
                session.add(appointment)
                await session.commit()
                await session.refresh(appointment)
                
                # Create appointment node in graph database
                if self.graph_db:
                    await self.graph_db.create_appointment_node({
                        "id": appointment.id,
                        "customer_id": customer_id,
                        "staff_id": staff_id,
                        "service_id": service_id,
                        "start_time": start_dt.isoformat(),
                        "end_time": end_dt.isoformat(),
                        "status": appointment.status
                    })
                
                return AppointmentResponse.model_validate(appointment)
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to book appointment: {e}")
                raise
    
    async def _find_available_staff(self, session: AsyncSession, service_id: str, 
                                  start_time: datetime, end_time: datetime) -> Optional[str]:
        """Find available staff for a service and time slot."""
        # Get staff who can perform this service
        # This is simplified - would check specializations in practice
        result = await session.execute(
            select(Staff).where(Staff.is_active == True)
        )
        staff_list = result.scalars().all()
        
        if not staff_list:
            return None
        
        # Check availability for each staff member
        for staff in staff_list:
            conflicts = await session.execute(
                select(Appointment).where(
                    and_(
                        Appointment.staff_id == staff.id,
                        Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.RESCHEDULED]),
                        or_(
                            and_(Appointment.start_time <= start_time, Appointment.end_time > start_time),
                            and_(Appointment.start_time < end_time, Appointment.end_time >= end_time)
                        )
                    )
                )
            )
            
            if not conflicts.scalar_one_or_none():
                return staff.id
        
        return None
    
    async def cancel_appointment(self, appointment_id: str, reason: Optional[str] = None) -> bool:
        """Cancel an appointment."""
        async with get_async_session() as session:
            try:
                appointment = await session.get(Appointment, appointment_id)
                if not appointment:
                    raise ValueError("Appointment not found")
                
                # Check cancellation policy
                hours_until_appointment = (appointment.start_time - datetime.utcnow()).total_seconds() / 3600
                from app.core.config import settings
                
                if hours_until_appointment < settings.cancellation_hours:
                    logger.warning(f"Late cancellation for appointment {appointment_id}")
                
                # Update appointment
                appointment.status = AppointmentStatus.CANCELLED
                appointment.cancellation_reason = reason
                appointment.updated_at = datetime.utcnow()
                
                await session.commit()
                
                # Update graph relationships
                if self.graph_db:
                    # Update customer-service relationship based on cancellation
                    pass
                
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to cancel appointment: {e}")
                raise
    
    async def reschedule_appointment(self, appointment_id: str, new_datetime: str) -> AppointmentResponse:
        """Reschedule an appointment."""
        async with get_async_session() as session:
            try:
                appointment = await session.get(Appointment, appointment_id)
                if not appointment:
                    raise ValueError("Appointment not found")
                
                # Parse new datetime
                new_start = datetime.fromisoformat(new_datetime.replace('Z', '+00:00'))
                
                # Calculate new end time based on service duration
                service = await session.get(Service, appointment.service_id)
                new_end = new_start + timedelta(minutes=service.duration)
                
                # Check availability for new time
                conflicts = await session.execute(
                    select(Appointment).where(
                        and_(
                            Appointment.staff_id == appointment.staff_id,
                            Appointment.id != appointment_id,
                            Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.RESCHEDULED]),
                            or_(
                                and_(Appointment.start_time <= new_start, Appointment.end_time > new_start),
                                and_(Appointment.start_time < new_end, Appointment.end_time >= new_end)
                            )
                        )
                    )
                )
                
                if conflicts.scalar_one_or_none():
                    raise ValueError("New time slot is not available")
                
                # Update appointment
                appointment.start_time = new_start
                appointment.end_time = new_end
                appointment.status = AppointmentStatus.RESCHEDULED
                appointment.updated_at = datetime.utcnow()
                
                await session.commit()
                await session.refresh(appointment)
                
                return AppointmentResponse.model_validate(appointment)
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to reschedule appointment: {e}")
                raise
    
    async def get_customer_appointments(self, customer_id: str, 
                                      status_filter: Optional[List[AppointmentStatus]] = None) -> List[AppointmentResponse]:
        """Get appointments for a customer."""
        async with get_async_session() as session:
            query = select(Appointment).where(Appointment.customer_id == customer_id)
            
            if status_filter:
                query = query.where(Appointment.status.in_(status_filter))
            
            query = query.order_by(Appointment.start_time.desc())
            
            result = await session.execute(query)
            appointments = result.scalars().all()
            return [AppointmentResponse.model_validate(apt) for apt in appointments]
    
    async def get_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """Get personalized recommendations using graph intelligence."""
        if not self.graph_db:
            # Return basic recommendations without graph intelligence
            services = await self.get_all_services()
            return RecommendationResponse(
                customer_id=request.customer_id,
                service_recommendations=[],
                staff_recommendations=[]
            )
        
        try:
            # Get service recommendations from graph
            service_recs = await self.graph_db.get_service_recommendations(
                request.customer_id, 
                limit=request.limit
            )
            
            # Get staff recommendations if service is specified
            staff_recs = []
            if request.service_id:
                staff_recs = await self.graph_db.get_staff_recommendations(
                    request.service_id,
                    request.customer_id
                )
            
            return RecommendationResponse(
                customer_id=request.customer_id,
                service_recommendations=service_recs,
                staff_recommendations=staff_recs
            )
            
        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            return RecommendationResponse(
                customer_id=request.customer_id,
                service_recommendations=[],
                staff_recommendations=[]
            )
    
    async def complete_appointment(self, appointment_id: str, satisfaction: float = 1.0, 
                                 feedback: Optional[str] = None) -> bool:
        """Mark appointment as completed and update graph relationships."""
        async with get_async_session() as session:
            try:
                appointment = await session.get(Appointment, appointment_id)
                if not appointment:
                    raise ValueError("Appointment not found")
                
                # Update appointment
                appointment.status = AppointmentStatus.COMPLETED
                appointment.updated_at = datetime.utcnow()
                if feedback:
                    appointment.notes = f"{appointment.notes or ''}\nFeedback: {feedback}"
                
                await session.commit()
                
                # Update graph relationships with satisfaction data
                if self.graph_db:
                    await self.graph_db.update_customer_preferences(
                        appointment.customer_id,
                        appointment.service_id,
                        satisfaction
                    )
                    
                    await self.graph_db.update_appointment_feedback(
                        appointment_id,
                        appointment.customer_id,
                        appointment.staff_id,
                        satisfaction
                    )
                
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to complete appointment: {e}")
                raise