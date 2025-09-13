"""
FastAPI Pydantic models for flight booking service
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from enum import Enum

class AirlineEnum(str, Enum):
    """Supported airlines"""
    AKASA = "Akasa Air"
    INDIGO = "IndiGo"
    SPICEJET = "SpiceJet"
    VISTARA = "Vistara"
    AIR_INDIA = "Air India"

class BookingStatusEnum(str, Enum):
    """Booking status options"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class FlightStatusEnum(str, Enum):
    """Flight status options"""
    ON_TIME = "On-Time"
    DELAYED = "Delayed"
    CANCELLED = "Cancelled"
    BOARDING = "Boarding"
    DEPARTED = "Departed"
    ARRIVED = "Arrived"

# Request Models
class FlightSearchRequest(BaseModel):
    """Flight search request model"""
    date: date = Field(..., description="Travel date")
    time: Optional[time] = Field(None, description="Preferred departure time")
    origin: str = Field(..., min_length=3, max_length=3, description="Origin airport code")
    destination: str = Field(..., min_length=3, max_length=3, description="Destination airport code")
    occasion: Optional[str] = Field(None, description="Travel occasion (business, leisure, emergency)")
    budget: Optional[float] = Field(None, gt=0, description="Maximum budget in INR")
    preferred_airline: Optional[AirlineEnum] = Field(None, description="Preferred airline")
    passengers: int = Field(1, ge=1, le=9, description="Number of passengers")

class FlightBookRequest(BaseModel):
    """Flight booking request model"""
    customer_id: str = Field(..., description="Customer identifier")
    flight_id: str = Field(..., description="Flight identifier to book")
    passenger_details: Optional[Dict[str, Any]] = Field(None, description="Passenger information")

class CancelAndRebookRequest(BaseModel):
    """Cancel and rebook request model"""
    booking_id: str = Field(..., description="Booking ID to cancel")
    new_date: date = Field(..., description="New travel date")
    new_time: Optional[time] = Field(None, description="New preferred time")
    budget: Optional[float] = Field(None, gt=0, description="Budget for new booking")

# Response Models
class FlightInfo(BaseModel):
    """Flight information model"""
    id: str
    airline: AirlineEnum
    flight_number: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    duration: str
    price: float
    risk_factor: float = Field(..., ge=0.0, le=1.0, description="Risk factor (0-1)")
    aircraft_type: Optional[str] = None
    seats_available: Optional[int] = None

class FlightSearchResponse(BaseModel):
    """Flight search response model"""
    best_flight: FlightInfo
    alternatives: List[FlightInfo]
    reasoning: str
    search_criteria: FlightSearchRequest
    total_results: int
    processing_time_ms: float

class BookingInfo(BaseModel):
    """Booking information model"""
    id: str
    customer_id: str
    flight_id: str
    status: BookingStatusEnum
    booking_link: str
    created_at: datetime
    flight_details: Optional[FlightInfo] = None

class FlightBookResponse(BaseModel):
    """Flight booking response model"""
    success: bool
    booking: BookingInfo
    message: str

class FlightStatusResponse(BaseModel):
    """Flight status response model"""
    booking_id: str
    status: FlightStatusEnum
    departure_time: datetime
    gate_info: Optional[str] = None
    terminal: Optional[str] = None
    delay_minutes: Optional[int] = None
    flight_details: FlightInfo

class CancelAndRebookResponse(BaseModel):
    """Cancel and rebook response model"""
    cancelled_booking: BookingInfo
    new_options: List[FlightInfo]
    reasoning: str
    total_alternatives: int

class ChatbotSession(BaseModel):
    """Chatbot session model"""
    id: str
    user_id: str
    query: str
    response: Dict[str, Any]
    confidence_score: float
    created_at: datetime

# Database Models (for Supabase)
class FlightDB(BaseModel):
    """Flight database model"""
    id: Optional[str] = None
    airline: str
    flight_number: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    duration: str
    price: float
    risk_factor: float
    aircraft_type: Optional[str] = None
    seats_available: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class BookingDB(BaseModel):
    """Booking database model"""
    id: Optional[str] = None
    customer_id: str
    flight_id: str
    status: str = "pending"
    booking_link: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ChatbotSessionDB(BaseModel):
    """Chatbot session database model"""
    id: Optional[str] = None
    user_id: str
    query: str
    response: Dict[str, Any]
    confidence_score: float = 0.0
    created_at: Optional[datetime] = None

# Error Models
class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

class ValidationErrorResponse(BaseModel):
    """Validation error response model"""
    error: str = "Validation failed"
    message: str
    details: List[Dict[str, Any]]
    timestamp: Optional[datetime] = None