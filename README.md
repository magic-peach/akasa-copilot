# Akasa Booking API

A resilient event-driven platform for managing flight bookings with centralized customer profiles and real-time flight data integration.

## Overview

This Flask-based API provides endpoints for creating and managing flight bookings using Supabase as the backend database. It's designed as the foundation for a larger event-driven platform that will include disruption detection, predictive analytics, and automated rebooking capabilities.

## Features

- ✅ **Booking Management**: Create and retrieve flight bookings
- ✅ **Change Requests**: Request booking changes with availability checking
- ✅ **Auto-Rebooking**: Automated rebooking with cost calculation
- ✅ **Flight Event Processing**: Real-time flight status tracking via webhooks
- ✅ **Disruption Detection**: Automated detection of delays and cancellations
- ✅ **Alert System**: Real-time notifications for flight disruptions
- ✅ **GenAI Agent**: Intelligent flight status retrieval with confidence scoring
- ✅ **Multi-Source Integration**: Combines internal data with external APIs
- ✅ **Background Processing**: Asynchronous event processing with queues
- ✅ **Data Validation**: Comprehensive input validation and error handling
- ✅ **Database Integration**: PostgreSQL via Supabase with optimized indexes
- ✅ **RESTful API**: Clean, well-documented REST endpoints
- ✅ **CORS Support**: Cross-origin resource sharing enabled
- ✅ **Health Monitoring**: Health check endpoint for system monitoring
- ✅ **Comprehensive Testing**: Full test suite included
- ✅ **Google Calendar Integration**: Sync with user's Google Calendar events
- ✅ **Smart Booking Alerts**: Conflict detection between flight bookings and calendar events
- ✅ **Travel Event Recognition**: AI-powered identification of travel-related calendar events

## Quick Start

### Prerequisites

- Python 3.8+
- Supabase account and project
- pip (Python package manager)

### Installation

1. **Clone and setup the project:**
   ```bash
   git clone <repository-url>
   cd akasa-booking-api
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials
   ```

3. **Set up the database:**
   ```bash
   python setup_database.py
   # Follow the instructions to create the database schema
   ```

4. **Start the application:**
   ```bash
   python app.py
   ```

The API will be available at `http://localhost:5000`

## API Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "service": "Akasa Booking API"
}
```

### Create Booking
```http
POST /bookings
Content-Type: application/json

{
  "customer_id": "CUST001",
  "flight_number": "QP1001",
  "origin": "DEL",
  "destination": "BOM",
  "depart_date": "2024-02-15",
  "status": "confirmed"
}
```

**Response (201 Created):**
```json
{
  "message": "Booking created successfully",
  "booking": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "customer_id": "CUST001",
    "flight_number": "QP1001",
    "origin": "DEL",
    "destination": "BOM",
    "depart_date": "2024-02-15",
    "status": "confirmed",
    "created_at": "2024-01-15T10:30:00.000Z",
    "updated_at": "2024-01-15T10:30:00.000Z"
  }
}
```

### Get Booking by ID
```http
GET /bookings/{booking_id}
```

**Response (200 OK):**
```json
{
  "booking": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "customer_id": "CUST001",
    "flight_number": "QP1001",
    "origin": "DEL",
    "destination": "BOM",
    "depart_date": "2024-02-15",
    "status": "confirmed",
    "created_at": "2024-01-15T10:30:00.000Z",
    "updated_at": "2024-01-15T10:30:00.000Z"
  }
}
```

### List Bookings
```http
GET /bookings?customer_id=CUST001&status=confirmed&limit=10&offset=0
```

**Query Parameters:**
- `customer_id` (optional): Filter by customer ID
- `flight_number` (optional): Filter by flight number
- `status` (optional): Filter by booking status
- `limit` (optional): Number of results to return (default: 100)
- `offset` (optional): Number of results to skip (default: 0)

**Response (200 OK):**
```json
{
  "bookings": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "customer_id": "CUST001",
      "flight_number": "QP1001",
      "origin": "DEL",
      "destination": "BOM",
      "depart_date": "2024-02-15",
      "status": "confirmed",
      "created_at": "2024-01-15T10:30:00.000Z",
      "updated_at": "2024-01-15T10:30:00.000Z"
    }
  ],
  "count": 1,
  "offset": 0,
  "limit": 10
}
```

### Request Booking Change
```http
POST /bookings/{booking_id}/request-change
Content-Type: application/json

{
  "new_date": "2024-03-15"
}
```

**Response (200 OK):**
```json
{
  "original_booking": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "flight_number": "QP1001",
    "depart_date": "2024-02-15",
    "origin": "DEL",
    "destination": "BOM"
  },
  "requested_date": "2024-03-15",
  "available_options": [
    {
      "flight_number": "QP1001",
      "departure_time": "09:30",
      "price": 4800,
      "seats_available": 25,
      "aircraft_type": "A320",
      "duration": "2h 15m",
      "depart_date": "2024-03-15",
      "cost_breakdown": {
        "original_price": 4500,
        "new_price": 4800,
        "price_difference": 300,
        "change_fee": 500,
        "total_cost": 800,
        "refund_amount": 0
      }
    }
  ],
  "message": "Found 3 available flights for your requested change"
}
```

### Auto-Rebook Flight
```http
POST /bookings/{booking_id}/auto-rebook
Content-Type: application/json

{
  "flight_number": "QP1001",
  "depart_date": "2024-03-15",
  "departure_time": "09:30",
  "price": 4800,
  "aircraft_type": "A320"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Flight successfully rebooked",
  "original_booking_id": "123e4567-e89b-12d3-a456-426614174000",
  "new_booking": {
    "id": "456e7890-e89b-12d3-a456-426614174001",
    "customer_id": "CUST001",
    "flight_number": "QP1001",
    "origin": "DEL",
    "destination": "BOM",
    "depart_date": "2024-03-15",
    "departure_time": "09:30",
    "status": "confirmed",
    "confirmation_code": "AK123456",
    "aircraft_type": "A320",
    "seat_number": "12A",
    "gate": "G5",
    "terminal": "T2"
  },
  "confirmation_code": "AK123456",
  "change_summary": {
    "original_flight": "QP1001",
    "new_flight": "QP1001",
    "original_date": "2024-02-15",
    "new_date": "2024-03-15",
    "cost_impact": {
      "original_price": 4500,
      "new_price": 4800,
      "price_difference": 300,
      "change_fee": 500,
      "total_cost": 800,
      "refund_amount": 0
    }
  }
}
```

## Data Model

### Booking Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Auto-generated | Unique booking identifier |
| `customer_id` | String(255) | Yes | Customer identifier |
| `flight_number` | String(20) | Yes | Flight number (e.g., "QP1001") |
| `origin` | String(10) | Yes | Origin airport code (e.g., "DEL") |
| `destination` | String(10) | Yes | Destination airport code (e.g., "BOM") |
| `depart_date` | Date | Yes | Departure date (YYYY-MM-DD format) |
| `status` | String(50) | No | Booking status (default: "confirmed") |
| `created_at` | Timestamp | Auto-generated | Creation timestamp |
| `updated_at` | Timestamp | Auto-updated | Last update timestamp |

### Valid Status Values
- `confirmed` - Booking is confirmed
- `pending` - Booking is pending confirmation
- `cancelled` - Booking has been cancelled
- `completed` - Flight has been completed

## Error Handling

The API returns structured error responses:

```json
{
  "error": "Validation failed",
  "details": {
    "customer_id": "Customer ID is required",
    "depart_date": "Departure date must be in YYYY-MM-DD format"
  }
}
```

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `404` - Not Found
- `500` - Internal Server Error

## Testing

Run the comprehensive test suite:

```bash
# Start the Flask application first
python app.py

# In another terminal, run tests
python test_api.py
```

The test suite covers:
- Health check endpoint
- Booking creation with valid data
- Booking retrieval by ID
- Handling of non-existent bookings
- Listing bookings with filters
- Validation of invalid data
- Booking change requests
- Auto-rebooking functionality
- Invalid change request handling
- Flight event webhook processing
- Disruption detection and alerting
- Alert management and resolution

### Flight Event Testing
Run the flight event test suite:

```bash
# Test flight event processing
python test_flight_events.py
```

The flight event test suite includes:
- Normal flight status updates
- Delay detection (>45 minutes)
- Cancellation alerts
- Flight state retrieval
- Alert management
- Complete disruption scenarios

## Database Setup

The application uses PostgreSQL via Supabase. Run the setup script for detailed instructions:

```bash
python setup_database.py
```

This will provide the SQL commands needed to create the database schema with proper indexes and triggers.

## Environment Variables

Create a `.env` file with the following variables:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
FLASK_ENV=development
FLASK_DEBUG=True
```

## Architecture Notes

## Rebooking System

The API includes a sophisticated rebooking system with the following capabilities:

### Change Request Process
1. **Availability Check**: Real-time flight availability checking for requested dates
2. **Cost Calculation**: Automatic calculation of price differences and change fees
3. **Option Presentation**: Multiple flight options with detailed cost breakdowns
4. **Validation**: Comprehensive validation of change requests

### Auto-Rebooking Features
- **Seamless Rebooking**: Automatic ticket reissue with new flight details
- **Status Management**: Original booking marked as cancelled, new booking created
- **Confirmation Codes**: New confirmation codes and seat assignments
- **Change Tracking**: Complete audit trail of booking changes

### Mock Services
The current implementation includes mock services for:
- **Flight Availability**: Simulated real-time availability checking
- **Pricing Engine**: Dynamic pricing with demand-based adjustments
- **Seat Assignment**: Automatic seat allocation
- **Gate/Terminal Assignment**: Airport resource allocation

## Google Calendar Integration

The application now includes comprehensive Google Calendar integration with intelligent conflict detection:

### Calendar Sync Features
- **Event Synchronization**: Automatically syncs user's Google Calendar events
- **Travel Event Detection**: AI-powered identification of travel-related events
- **Smart Filtering**: Filters out unimportant events (reminders, routine tasks)
- **Priority Scoring**: Assigns priority levels to events based on importance
- **Real-time Updates**: Refreshes calendar data on demand

### Conflict Detection
- **Booking Validation**: Checks flight bookings against calendar events before confirmation
- **Multiple Conflict Types**: Detects overlaps, insufficient travel time, and wrong destinations
- **Severity Assessment**: Categorizes conflicts as low, medium, high, or critical
- **Smart Suggestions**: Provides actionable recommendations to resolve conflicts
- **Visual Alerts**: User-friendly popup warnings with detailed conflict information

### API Endpoints

#### Get Calendar Events
```http
GET /calendar/events?days_ahead=30
```

**Response:**
```json
{
  "success": true,
  "events": [
    {
      "id": "event_123",
      "summary": "Business Meeting in Mumbai",
      "start_time": "2024-02-15T10:00:00Z",
      "end_time": "2024-02-15T12:00:00Z",
      "location": "Mumbai, India",
      "is_travel_related": true,
      "destination_city": "Mumbai",
      "destination_airport": "BOM",
      "travel_type": "business",
      "priority": 4
    }
  ],
  "total_events": 5,
  "travel_events": 2
}
```

#### Check Booking Conflicts
```http
POST /calendar/check-conflicts
Content-Type: application/json

{
  "id": "flight_123",
  "flight_number": "QP1001",
  "origin": "DEL",
  "destination": "BOM",
  "departure_time": "2024-02-15T08:00:00Z",
  "arrival_time": "2024-02-15T10:15:00Z",
  "date": "2024-02-15"
}
```

**Response:**
```json
{
  "success": true,
  "conflicts": [
    {
      "booking_id": "flight_123",
      "conflict_type": "overlap",
      "severity": "high",
      "conflicting_events": [
        {
          "id": "event_123",
          "summary": "Business Meeting in Mumbai",
          "start_time": "2024-02-15T10:00:00Z",
          "end_time": "2024-02-15T12:00:00Z",
          "location": "Mumbai, India",
          "travel_type": "business",
          "priority": 4
        }
      ],
      "suggested_actions": [
        "Book an earlier flight to arrive before the meeting",
        "Contact meeting organizers to reschedule",
        "Consider extending your trip to accommodate both events"
      ]
    }
  ],
  "has_conflicts": true,
  "total_conflicts": 1
}
```

#### Get Flight Suggestions
```http
GET /calendar/flight-suggestions?origin=DEL
```

**Response:**
```json
{
  "success": true,
  "suggestions": [
    {
      "event_id": "event_123",
      "event_summary": "Business Meeting in Mumbai",
      "destination": "Mumbai",
      "suggested_departure": "2024-02-15T08:00:00Z",
      "suggested_return": "2024-02-15T14:00:00Z",
      "flight_options": [
        {
          "flight_number": "QP1001",
          "airline": "Akasa Air",
          "departure_time": "08:00",
          "arrival_time": "10:15",
          "price": 8500,
          "duration": "2h 15m"
        }
      ],
      "conflict_warning": null,
      "priority_score": 85.5
    }
  ],
  "total_suggestions": 1
}
```

### Frontend Integration

The calendar integration includes a comprehensive frontend interface:

- **Calendar Events Display**: Shows upcoming events with travel-related highlighting
- **Conflict Warning Popup**: Detailed modal with conflict information and suggested actions
- **Real-time Sync**: Automatic calendar refresh and event updates
- **Visual Indicators**: Color-coded events based on type and priority
- **Responsive Design**: Mobile-friendly calendar event display

### Travel Event Classification

The system intelligently classifies calendar events as travel-related based on:

- **Keywords**: Business, personal, conference, meeting, travel, vacation
- **Location Indicators**: "in", "at", "to", "from", "travel to", "going to"
- **Destination Extraction**: Automatic city and airport code mapping
- **Priority Scoring**: Based on event type, attendees, and importance keywords

## Architecture Notes

This API is designed as the foundation for a larger event-driven platform that will include:

- **Event Sourcing**: All booking changes will be captured as events
- **Real-time Processing**: Integration with flight data feeds
- **Disruption Detection**: ML-based disruption prediction
- **Automated Actions**: Policy-driven rebooking and notifications
- **Customer Profiles**: Centralized customer data management
- **Rebooking Workflows**: Intelligent rebooking based on customer preferences

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License.# akasa-copilot
