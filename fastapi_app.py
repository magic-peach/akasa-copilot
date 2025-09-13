"""
FastAPI backend service for Akasa Airlines flight booking
Intelligent flight search and booking with GenAI agents
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import uuid
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from fastapi_models import (
    FlightSearchRequest, FlightSearchResponse, FlightBookRequest, FlightBookResponse,
    CancelAndRebookRequest, CancelAndRebookResponse, FlightStatusResponse,
    FlightInfo, BookingInfo, ErrorResponse, FlightStatusEnum, BookingStatusEnum
)
from flight_search_agent import flight_search_agent
from database import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Akasa Airlines Booking API",
    description="Intelligent flight search and booking platform with GenAI agents",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Akasa Airlines FastAPI",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/flights/search", response_model=FlightSearchResponse)
async def search_flights(search_request: FlightSearchRequest):
    """
    Intelligent flight search with GenAI agent
    Combines fastest duration + cheapest price with risk assessment
    """
    try:
        logger.info(f"Flight search request: {search_request.origin} -> {search_request.destination}")
        
        # Use GenAI agent to search and select flights
        search_result = flight_search_agent.search_flights(search_request)
        
        if search_result.get('error'):
            raise HTTPException(
                status_code=404,
                detail=f"Flight search failed: {search_result['error']}"
            )
        
        if not search_result['best_flight']:
            raise HTTPException(
                status_code=404,
                detail=f"No flights found for {search_request.origin} to {search_request.destination} on {search_request.date}"
            )
        
        # Convert to response model
        best_flight = FlightInfo(**search_result['best_flight'])
        alternatives = [FlightInfo(**alt) for alt in search_result['alternatives']]
        
        response = FlightSearchResponse(
            best_flight=best_flight,
            alternatives=alternatives,
            reasoning=search_result['reasoning'],
            search_criteria=search_request,
            total_results=search_result['total_results'],
            processing_time_ms=search_result['processing_time_ms']
        )
        
        logger.info(f"Flight search completed: {len(alternatives) + 1} options found")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in flight search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during flight search: {str(e)}"
        )

@app.post("/flights/book", response_model=FlightBookResponse)
async def book_flight(book_request: FlightBookRequest):
    """
    Book a flight and generate mock booking link
    """
    try:
        logger.info(f"Flight booking request: customer={book_request.customer_id}, flight={book_request.flight_id}")
        
        # Generate booking ID and mock booking link
        booking_id = str(uuid.uuid4())
        booking_link = f"https://mock-airline.com/book/{book_request.flight_id}?booking_id={booking_id}"
        
        # Get flight details
        flight_details = await _get_flight_details(book_request.flight_id)
        
        # Create booking record
        booking_data = {
            'id': booking_id,
            'customer_id': book_request.customer_id,
            'flight_id': book_request.flight_id,
            'status': 'pending',
            'booking_link': booking_link,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Save to Supabase
        supabase = db.get_client()
        result = supabase.table('bookings').insert(booking_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to save booking to database"
            )
        
        created_booking = result.data[0]
        
        # Create booking info
        booking_info = BookingInfo(
            id=created_booking['id'],
            customer_id=created_booking['customer_id'],
            flight_id=created_booking['flight_id'],
            status=BookingStatusEnum(created_booking['status']),
            booking_link=created_booking['booking_link'],
            created_at=datetime.fromisoformat(created_booking['created_at']),
            flight_details=flight_details
        )
        
        # Log booking session
        await _log_booking_session(book_request, booking_info, "booking_created")
        
        logger.info(f"Booking created successfully: {booking_id}")
        
        return FlightBookResponse(
            success=True,
            booking=booking_info,
            message=f"Flight booked successfully. Use the booking link to complete payment: {booking_link}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error booking flight: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during booking: {str(e)}"
        )

@app.get("/flights/{booking_id}/status", response_model=FlightStatusResponse)
async def get_flight_status(booking_id: str):
    """
    Get flight status for a booking
    """
    try:
        logger.info(f"Flight status request for booking: {booking_id}")
        
        # Get booking from database
        supabase = db.get_client()
        result = supabase.table('bookings').select('*').eq('id', booking_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=404,
                detail=f"Booking not found: {booking_id}"
            )
        
        booking = result.data[0]
        
        # Get flight details
        flight_details = await _get_flight_details(booking['flight_id'])
        
        if not flight_details:
            raise HTTPException(
                status_code=404,
                detail=f"Flight details not found for booking: {booking_id}"
            )
        
        # Generate mock flight status
        status_options = [FlightStatusEnum.ON_TIME, FlightStatusEnum.DELAYED, FlightStatusEnum.BOARDING]
        flight_status = random.choice(status_options)
        
        # Generate mock gate and delay info
        gate_info = f"Gate {random.choice(['A', 'B', 'C'])}{random.randint(1, 20)}"
        terminal = f"Terminal {random.randint(1, 3)}"
        delay_minutes = random.randint(0, 60) if flight_status == FlightStatusEnum.DELAYED else None
        
        response = FlightStatusResponse(
            booking_id=booking_id,
            status=flight_status,
            departure_time=datetime.fromisoformat(flight_details.departure_time),
            gate_info=gate_info,
            terminal=terminal,
            delay_minutes=delay_minutes,
            flight_details=flight_details
        )
        
        # Log status check session
        await _log_status_session(booking_id, response)
        
        logger.info(f"Flight status retrieved for booking {booking_id}: {flight_status}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting flight status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error getting flight status: {str(e)}"
        )

@app.post("/flights/cancel-and-rebook", response_model=CancelAndRebookResponse)
async def cancel_and_rebook(rebook_request: CancelAndRebookRequest):
    """
    Cancel existing booking and search for new flights
    """
    try:
        logger.info(f"Cancel and rebook request for booking: {rebook_request.booking_id}")
        
        # Get existing booking
        supabase = db.get_client()
        result = supabase.table('bookings').select('*').eq('id', rebook_request.booking_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=404,
                detail=f"Booking not found: {rebook_request.booking_id}"
            )
        
        existing_booking = result.data[0]
        
        # Cancel the existing booking
        cancel_result = supabase.table('bookings').update({
            'status': 'cancelled',
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', rebook_request.booking_id).execute()
        
        if not cancel_result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to cancel existing booking"
            )
        
        cancelled_booking_data = cancel_result.data[0]
        
        # Get original flight details to determine route
        original_flight = await _get_flight_details(existing_booking['flight_id'])
        
        if not original_flight:
            raise HTTPException(
                status_code=404,
                detail="Original flight details not found"
            )
        
        # Create new search request
        new_search = FlightSearchRequest(
            date=rebook_request.new_date,
            time=rebook_request.new_time,
            origin=original_flight.origin,
            destination=original_flight.destination,
            budget=rebook_request.budget,
            occasion="rebook"  # Special occasion for rebooking
        )
        
        # Search for new flights
        search_result = flight_search_agent.search_flights(new_search)
        
        if search_result.get('error') or not search_result['best_flight']:
            raise HTTPException(
                status_code=404,
                detail="No alternative flights found for the new date/time"
            )
        
        # Create new booking options with booking links
        new_options = []
        all_flights = [search_result['best_flight']] + search_result['alternatives']
        
        for flight in all_flights:
            # Generate booking link for each option
            flight['booking_link'] = f"https://mock-airline.com/book/{flight['id']}?rebook=true"
            new_options.append(FlightInfo(**flight))
        
        # Create cancelled booking info
        cancelled_booking = BookingInfo(
            id=cancelled_booking_data['id'],
            customer_id=cancelled_booking_data['customer_id'],
            flight_id=cancelled_booking_data['flight_id'],
            status=BookingStatusEnum(cancelled_booking_data['status']),
            booking_link=cancelled_booking_data['booking_link'],
            created_at=datetime.fromisoformat(cancelled_booking_data['created_at']),
            flight_details=original_flight
        )
        
        reasoning = f"Cancelled original booking for {original_flight.flight_number}. Found {len(new_options)} alternative flights for {rebook_request.new_date}. {search_result['reasoning']}"
        
        # Log cancel and rebook session
        await _log_rebook_session(rebook_request, cancelled_booking, new_options, reasoning)
        
        logger.info(f"Cancel and rebook completed: {len(new_options)} new options found")
        
        return CancelAndRebookResponse(
            cancelled_booking=cancelled_booking,
            new_options=new_options,
            reasoning=reasoning,
            total_alternatives=len(new_options)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in cancel and rebook: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during cancel and rebook: {str(e)}"
        )

@app.get("/chatbot-sessions/{user_id}")
async def get_user_sessions(user_id: str, limit: int = 10):
    """Get chatbot sessions for a user"""
    try:
        supabase = db.get_client()
        result = supabase.table('chatbot_sessions').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
        
        sessions = result.data or []
        
        return {
            "user_id": user_id,
            "sessions": sessions,
            "count": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"Error getting user sessions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving sessions: {str(e)}"
        )

# Helper functions
async def _get_flight_details(flight_id: str) -> Optional[FlightInfo]:
    """Get flight details by ID"""
    try:
        supabase = db.get_client()
        
        # Try to get from flights table
        result = supabase.table('flights').select('*').eq('id', flight_id).execute()
        
        if result.data:
            flight_data = result.data[0]
            return FlightInfo(
                id=flight_data['id'],
                airline=flight_data['airline'],
                flight_number=flight_data['flight_number'],
                origin=flight_data['origin'],
                destination=flight_data['destination'],
                departure_time=flight_data['departure_time'],
                arrival_time=flight_data['arrival_time'],
                duration=flight_data['duration'],
                price=flight_data['price'],
                risk_factor=flight_data.get('risk_factor', 0.3),
                aircraft_type=flight_data.get('aircraft_type'),
                seats_available=flight_data.get('seats_available')
            )
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting flight details: {str(e)}")
        return None

async def _log_booking_session(book_request: FlightBookRequest, booking_info: BookingInfo, action: str):
    """Log booking session to chatbot_sessions"""
    try:
        session_id = str(uuid.uuid4())
        
        supabase = db.get_client()
        
        session_data = {
            'id': session_id,
            'user_id': book_request.customer_id,
            'query': f"Book flight {book_request.flight_id}",
            'response': {
                'action': action,
                'booking_id': booking_info.id,
                'booking_link': booking_info.booking_link,
                'flight_details': booking_info.flight_details.dict() if booking_info.flight_details else None
            },
            'confidence_score': 1.0
        }
        
        result = supabase.table('chatbot_sessions').insert(session_data).execute()
        
        if result.data:
            logger.info(f"Logged booking session {session_id}")
        
    except Exception as e:
        logger.error(f"Error logging booking session: {str(e)}")

async def _log_status_session(booking_id: str, status_response: FlightStatusResponse):
    """Log status check session"""
    try:
        session_id = str(uuid.uuid4())
        
        supabase = db.get_client()
        
        session_data = {
            'id': session_id,
            'user_id': f"status_check_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'query': f"Check status for booking {booking_id}",
            'response': {
                'action': 'status_check',
                'booking_id': booking_id,
                'flight_status': status_response.status.value,
                'gate_info': status_response.gate_info,
                'delay_minutes': status_response.delay_minutes
            },
            'confidence_score': 0.9
        }
        
        result = supabase.table('chatbot_sessions').insert(session_data).execute()
        
        if result.data:
            logger.info(f"Logged status session {session_id}")
        
    except Exception as e:
        logger.error(f"Error logging status session: {str(e)}")

async def _log_rebook_session(rebook_request: CancelAndRebookRequest, cancelled_booking: BookingInfo, 
                            new_options: List[FlightInfo], reasoning: str):
    """Log cancel and rebook session"""
    try:
        session_id = str(uuid.uuid4())
        
        supabase = db.get_client()
        
        session_data = {
            'id': session_id,
            'user_id': cancelled_booking.customer_id,
            'query': f"Cancel and rebook for {rebook_request.new_date}",
            'response': {
                'action': 'cancel_and_rebook',
                'cancelled_booking_id': cancelled_booking.id,
                'new_options_count': len(new_options),
                'reasoning': reasoning,
                'new_date': rebook_request.new_date.isoformat()
            },
            'confidence_score': 0.8
        }
        
        result = supabase.table('chatbot_sessions').insert(session_data).execute()
        
        if result.data:
            logger.info(f"Logged rebook session {session_id}")
        
    except Exception as e:
        logger.error(f"Error logging rebook session: {str(e)}")

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    print("🚀 Starting Akasa Airlines FastAPI Service")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 ReDoc Documentation: http://localhost:8000/redoc")
    print("-" * 50)
    
    uvicorn.run(
        "fastapi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )