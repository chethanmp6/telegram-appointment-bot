"""Appointment management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import date
import logging

from app.services.appointment_service import AppointmentService
from app.core.database import get_session
from app.core.graph_db import get_graph_db
from app.models.schemas import (
    CustomerCreate, CustomerResponse, CustomerUpdate,
    StaffCreate, StaffResponse, StaffUpdate,
    ServiceCreate, ServiceResponse, ServiceUpdate,
    AppointmentCreate, AppointmentResponse, AppointmentUpdate,
    AvailabilityRequest, AvailabilityResponse,
    RecommendationRequest, RecommendationResponse,
    AppointmentStatus
)

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_appointment_service() -> AppointmentService:
    """Dependency to get appointment service."""
    graph_db = await get_graph_db()
    service = AppointmentService(graph_db)
    return service


# Customer endpoints
@router.post("/customers", response_model=CustomerResponse)
async def create_customer(
    customer_data: CustomerCreate,
    service: AppointmentService = Depends(get_appointment_service)
):
    """Create a new customer."""
    try:
        return await service.create_customer(customer_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create customer: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/customers/telegram/{telegram_user_id}", response_model=CustomerResponse)
async def get_customer_by_telegram_id(
    telegram_user_id: int,
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get customer by Telegram user ID."""
    customer = await service.get_customer_by_telegram_id(telegram_user_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    update_data: CustomerUpdate,
    service: AppointmentService = Depends(get_appointment_service)
):
    """Update customer information."""
    try:
        return await service.update_customer(customer_id, update_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update customer: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Staff endpoints
@router.post("/staff", response_model=StaffResponse)
async def create_staff(
    staff_data: StaffCreate,
    service: AppointmentService = Depends(get_appointment_service)
):
    """Create a new staff member."""
    try:
        return await service.create_staff(staff_data)
    except Exception as e:
        logger.error(f"Failed to create staff: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/staff", response_model=List[StaffResponse])
async def get_all_staff(
    active_only: bool = Query(True, description="Return only active staff"),
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get all staff members."""
    try:
        return await service.get_all_staff(active_only)
    except Exception as e:
        logger.error(f"Failed to get staff: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Service endpoints
@router.post("/services", response_model=ServiceResponse)
async def create_service(
    service_data: ServiceCreate,
    service: AppointmentService = Depends(get_appointment_service)
):
    """Create a new service."""
    try:
        return await service.create_service(service_data)
    except Exception as e:
        logger.error(f"Failed to create service: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/services", response_model=List[ServiceResponse])
async def get_all_services(
    active_only: bool = Query(True, description="Return only active services"),
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get all services."""
    try:
        return await service.get_all_services(active_only)
    except Exception as e:
        logger.error(f"Failed to get services: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/services/search", response_model=ServiceResponse)
async def search_service_by_name(
    name: str = Query(..., description="Service name to search"),
    service: AppointmentService = Depends(get_appointment_service)
):
    """Search for a service by name."""
    result = await service.get_service_by_name(name)
    if not result:
        raise HTTPException(status_code=404, detail="Service not found")
    return result


# Availability endpoints
@router.post("/availability", response_model=AvailabilityResponse)
async def check_availability(
    availability_request: AvailabilityRequest,
    service: AppointmentService = Depends(get_appointment_service)
):
    """Check availability for appointments."""
    try:
        return await service.check_availability(
            date=availability_request.date,
            service_id=availability_request.service_id,
            staff_id=availability_request.staff_id,
            duration=availability_request.duration
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to check availability: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/availability/{service_id}")
async def get_availability_by_service(
    service_id: str,
    date: date = Query(..., description="Date to check availability"),
    staff_id: Optional[str] = Query(None, description="Specific staff member"),
    duration: Optional[int] = Query(None, description="Duration in minutes"),
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get availability for a specific service."""
    try:
        return await service.check_availability(
            date=date,
            service_id=service_id,
            staff_id=staff_id,
            duration=duration
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to check availability: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Appointment endpoints
@router.post("/appointments", response_model=AppointmentResponse)
async def book_appointment(
    appointment_data: AppointmentCreate,
    service: AppointmentService = Depends(get_appointment_service)
):
    """Book a new appointment."""
    try:
        return await service.book_appointment(
            customer_id=appointment_data.customer_id,
            service_id=appointment_data.service_id,
            start_time=appointment_data.start_time.isoformat(),
            end_time=appointment_data.end_time.isoformat(),
            staff_id=appointment_data.staff_id,
            notes=appointment_data.notes
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to book appointment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/appointments/customer/{customer_id}", response_model=List[AppointmentResponse])
async def get_customer_appointments(
    customer_id: str,
    status_filter: Optional[List[AppointmentStatus]] = Query(None, description="Filter by status"),
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get appointments for a specific customer."""
    try:
        return await service.get_customer_appointments(customer_id, status_filter)
    except Exception as e:
        logger.error(f"Failed to get customer appointments: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/appointments/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: str,
    reason: Optional[str] = Query(None, description="Cancellation reason"),
    service: AppointmentService = Depends(get_appointment_service)
):
    """Cancel an appointment."""
    try:
        success = await service.cancel_appointment(appointment_id, reason)
        if success:
            return {"status": "cancelled", "appointment_id": appointment_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to cancel appointment")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to cancel appointment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/appointments/{appointment_id}/reschedule", response_model=AppointmentResponse)
async def reschedule_appointment(
    appointment_id: str,
    new_datetime: str = Query(..., description="New appointment datetime (ISO format)"),
    service: AppointmentService = Depends(get_appointment_service)
):
    """Reschedule an appointment."""
    try:
        return await service.reschedule_appointment(appointment_id, new_datetime)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to reschedule appointment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/appointments/{appointment_id}/complete")
async def complete_appointment(
    appointment_id: str,
    satisfaction: float = Query(1.0, ge=0, le=1, description="Satisfaction score (0-1)"),
    feedback: Optional[str] = Query(None, description="Customer feedback"),
    service: AppointmentService = Depends(get_appointment_service)
):
    """Mark appointment as completed."""
    try:
        success = await service.complete_appointment(appointment_id, satisfaction, feedback)
        if success:
            return {"status": "completed", "appointment_id": appointment_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to complete appointment")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to complete appointment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Recommendation endpoints
@router.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    recommendation_request: RecommendationRequest,
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get personalized recommendations for a customer."""
    try:
        return await service.get_recommendations(recommendation_request)
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/recommendations/{customer_id}", response_model=RecommendationResponse)
async def get_customer_recommendations(
    customer_id: str,
    service_id: Optional[str] = Query(None, description="Specific service for staff recommendations"),
    limit: int = Query(5, ge=1, le=20, description="Number of recommendations"),
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get recommendations for a specific customer."""
    try:
        from app.models.schemas import RecommendationRequest
        recommendation_request = RecommendationRequest(
            customer_id=customer_id,
            service_id=service_id,
            limit=limit
        )
        return await service.get_recommendations(recommendation_request)
    except Exception as e:
        logger.error(f"Failed to get customer recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Analytics endpoints
@router.get("/analytics/customer/{customer_id}")
async def get_customer_analytics(
    customer_id: str,
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get analytics for a specific customer."""
    try:
        if service.graph_db:
            analytics = await service.graph_db.get_customer_analytics(customer_id)
            return analytics
        else:
            raise HTTPException(status_code=503, detail="Analytics service not available")
    except Exception as e:
        logger.error(f"Failed to get customer analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analytics/business")
async def get_business_insights(
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get overall business insights."""
    try:
        if service.graph_db:
            insights = await service.graph_db.get_business_insights()
            return insights
        else:
            raise HTTPException(status_code=503, detail="Analytics service not available")
    except Exception as e:
        logger.error(f"Failed to get business insights: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")