# Akasa Airlines FastAPI Flight Booking Service

A modern, intelligent flight booking platform built with FastAPI, featuring GenAI-powered flight search and automated booking workflows.

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.8+
- Supabase account and project
- Virtual environment (recommended)

### **Installation**
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Supabase credentials

# Setup database
python setup_database.py
# Run the SQL commands in your Supabase SQL editor
```

### **Start FastAPI Service**
```bash
python fastapi_app.py
```

The service will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🎯 **API Endpoints**

### **Flight Search**
```http
POST /flights/search
Content-Type: application/json

{
  "date": "2024-03-15",
  "time": "09:00:00",
  "origin": "DEL",
  "destination": "BOM",
  "occasion": "business",
  "budget": 6000,
  "preferred_airline": "Akasa Air",
  "passengers": 1
}
```

**Response:**
```json
{
  "best_flight": {
    "id": "flight-uuid",
    "airline": "Akasa Air",
    "flight_number": "QP1001",
    "origin": "DEL",
    "destination": "BOM",
    "departure_time": "2024-03-15T09:30:00",
    "arrival_time": "2024-03-15T11:45:00",
    "duration": "2h 15m",
    "price": 4800,
    "risk_factor": 0.25,
    "aircraft_type": "A320",
    "seats_available": 45
  },
  "alternatives": [...],
  "reasoning": "Selected Akasa Air flight QP1001 as it offers the best combination of competitively priced at ₹4800, optimal 2h 15m flight time, low disruption risk (0.25), matches your preferred airline, optimized for business travel (time priority). Overall score: 0.92/1.0",
  "total_results": 6,
  "processing_time_ms": 45.2
}
```

### **Flight Booking**
```http
POST /flights/book
Content-Type: application/json

{
  "customer_id": "CUST001",
  "flight_id": "flight-uuid",
  "passenger_details": {
    "name": "John Doe",
    "email": "john.doe@email.com",
    "phone": "+91-9876543210"
  }
}
```

**Response:**
```json
{
  "success": true,
  "booking": {
    "id": "booking-uuid",
    "customer_id": "CUST001",
    "flight_id": "flight-uuid",
    "status": "pending",
    "booking_link": "https://mock-airline.com/book/flight-uuid?booking_id=booking-uuid",
    "created_at": "2024-01-15T10:30:00Z",
    "flight_details": {...}
  },
  "message": "Flight booked successfully. Use the booking link to complete payment: https://mock-airline.com/book/..."
}
```

### **Flight Status**
```http
GET /flights/{booking_id}/status
```

**Response:**
```json
{
  "booking_id": "booking-uuid",
  "status": "On-Time",
  "departure_time": "2024-03-15T09:30:00Z",
  "gate_info": "Gate A12",
  "terminal": "Terminal 2",
  "delay_minutes": null,
  "flight_details": {...}
}
```

### **Cancel and Rebook**
```http
POST /flights/cancel-and-rebook
Content-Type: application/json

{
  "booking_id": "booking-uuid",
  "new_date": "2024-03-20",
  "new_time": "14:00:00",
  "budget": 7000
}
```

**Response:**
```json
{
  "cancelled_booking": {...},
  "new_options": [
    {
      "id": "new-flight-uuid",
      "airline": "Vistara",
      "flight_number": "UK955",
      "price": 5200,
      "booking_link": "https://mock-airline.com/book/new-flight-uuid?rebook=true"
    }
  ],
  "reasoning": "Cancelled original booking for QP1001. Found 4 alternative flights for 2024-03-20...",
  "total_alternatives": 4
}
```

## 🤖 **GenAI Flight Selection Algorithm**

### **Multi-Criteria Scoring**
The GenAI agent evaluates flights using weighted criteria:

- **Price (40%)**: Cost optimization with budget constraints
- **Duration (30%)**: Flight time efficiency
- **Risk Factor (20%)**: Weather, airline reliability, route risk
- **Preferences (10%)**: Airline preference, occasion-based priorities

### **Risk Factor Calculation**
```python
risk_factor = base_route_risk + time_risk + weather_risk + airline_risk
```

**Components:**
- **Route Risk**: Historical disruption patterns by route
- **Time Risk**: Early morning/late night flight penalties
- **Weather Risk**: Mock weather condition assessment
- **Airline Risk**: Reliability scoring by airline

### **Occasion-Based Optimization**
- **Business**: Prioritizes time efficiency, low risk tolerance
- **Leisure**: Prioritizes cost savings, higher risk tolerance
- **Emergency**: Prioritizes fastest available flights
- **Family**: Balanced approach with moderate risk tolerance

## 📊 **Database Schema**

### **Enhanced Tables for FastAPI**
The existing Supabase schema supports FastAPI with additional fields:

```sql
-- Enhanced flights table
ALTER TABLE flights ADD COLUMN IF NOT EXISTS price DECIMAL(10,2);
ALTER TABLE flights ADD COLUMN IF NOT EXISTS duration VARCHAR(20);
ALTER TABLE flights ADD COLUMN IF NOT EXISTS risk_factor DECIMAL(3,2);
ALTER TABLE flights ADD COLUMN IF NOT EXISTS seats_available INTEGER;

-- Enhanced bookings table  
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS booking_link TEXT;
```

## 🧪 **Testing**

### **Run FastAPI Tests**
```bash
# Start FastAPI service first
python fastapi_app.py

# In another terminal, run tests
python test_fastapi.py
```

### **Test Coverage**
- ✅ **Flight Search** - GenAI-powered intelligent selection
- ✅ **Flight Booking** - Mock booking link generation
- ✅ **Status Checking** - Real-time flight status simulation
- ✅ **Cancel & Rebook** - Automated rebooking workflow
- ✅ **Session Logging** - Complete interaction tracking
- ✅ **API Documentation** - Auto-generated OpenAPI docs

## 🎯 **Key Features**

### **Intelligent Flight Search**
- **Multi-criteria optimization** combining price, duration, and risk
- **Occasion-based preferences** (business, leisure, emergency)
- **Budget constraint handling** with over-budget penalties
- **Airline preference matching** with scoring bonuses
- **Real-time risk assessment** based on weather and historical data

### **Mock Booking Integration**
- **Realistic booking links** to external airline systems
- **Pending status management** for payment completion
- **Passenger detail storage** for booking records
- **Session tracking** for all booking interactions

### **Advanced Rebooking**
- **Automatic cancellation** of existing bookings
- **Intelligent rescheduling** with new search criteria
- **Multiple alternatives** with booking links
- **Cost comparison** and optimization

### **Comprehensive Logging**
- **Search sessions** - All flight searches logged
- **Booking sessions** - Complete booking workflow tracking
- **Status checks** - Flight status inquiry logging
- **Rebook sessions** - Cancel and rebook operation tracking

## 🔄 **Dual Platform Architecture**

### **Flask Platform (Port 5000)**
- **Voice-enabled chatbot** with conversational AI
- **Real-time event processing** with background workers
- **ML disruption prediction** with weather integration
- **Natural language processing** for booking changes
- **Multi-channel notifications** (SMS, email, push)

### **FastAPI Platform (Port 8000)**
- **Intelligent flight search** with GenAI selection
- **Mock booking integration** with external links
- **Advanced rebooking workflows** with automation
- **Interactive API documentation** with Swagger UI
- **High-performance async processing**

## 🚀 **Running Both Platforms**

### **Option 1: Flask Platform (Full AI Features)**
```bash
# Terminal 1: Flask with voice AI and real-time processing
python app.py  # Runs on port 5000
```

### **Option 2: FastAPI Platform (Flight Booking Focus)**
```bash
# Terminal 2: FastAPI with intelligent flight search
python fastapi_app.py  # Runs on port 8000
```

### **Option 3: Both Platforms Simultaneously**
```bash
# Terminal 1: Flask platform
python app.py

# Terminal 2: FastAPI platform  
python fastapi_app.py
```

## 📈 **Business Value**

### **Customer Experience**
- **Intelligent Flight Selection** - AI chooses optimal flights automatically
- **Transparent Reasoning** - Clear explanation of flight selection logic
- **Seamless Rebooking** - One-click cancel and rebook with alternatives
- **Real-time Status** - Live flight status with gate information

### **Operational Efficiency**
- **Automated Decision Making** - GenAI handles complex flight selection
- **Mock Integration Ready** - Prepared for real airline API integration
- **Comprehensive Logging** - Complete audit trail for all operations
- **Scalable Architecture** - FastAPI's async performance benefits

## 🔧 **Configuration**

### **Environment Variables**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
FLASK_ENV=development
FLASK_DEBUG=True
```

### **Airline Configuration**
The system supports multiple airlines with realistic pricing and risk factors:
- **Akasa Air** (QP) - Low risk, competitive pricing
- **IndiGo** (6E) - Reliable, moderate pricing
- **Vistara** (UK) - Premium service, higher pricing
- **Air India** (AI) - National carrier, variable pricing
- **SpiceJet** (SG) - Budget airline, higher risk

## 🎉 **Production Ready**

The FastAPI implementation provides:
- **Type Safety** - Pydantic models with validation
- **Auto Documentation** - Interactive API docs
- **Async Performance** - High-throughput request handling
- **Error Handling** - Comprehensive exception management
- **Session Tracking** - Complete interaction logging
- **Mock Integration** - Ready for real airline API connections

This creates a complete dual-platform solution for Akasa Airlines with both comprehensive AI capabilities (Flask) and high-performance flight booking (FastAPI)!