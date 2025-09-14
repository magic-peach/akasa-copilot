#!/usr/bin/env python3
"""
Database setup script for Akasa Booking API
Run this script to create the bookings table in Supabase
"""

import os
from dotenv import load_dotenv

load_dotenv()

def print_database_setup_instructions():
    """Print instructions for setting up the database"""
    print("=" * 60)
    print("AKASA BOOKING API - DATABASE SETUP")
    print("=" * 60)
    print()
    print("To set up your Supabase database, follow these steps:")
    print()
    print("1. Create a Supabase project at https://supabase.com")
    print("2. Copy your project URL and anon key")
    print("3. Create a .env file based on .env.example")
    print("4. Run the following SQL in your Supabase SQL editor:")
    print()
    print("-" * 60)
    print("SQL COMMANDS:")
    print("-" * 60)
    
    sql_commands = """
-- Create the bookings table
CREATE TABLE IF NOT EXISTS bookings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL,
    flight_number VARCHAR(20) NOT NULL,
    origin VARCHAR(10) NOT NULL,
    destination VARCHAR(10) NOT NULL,
    depart_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'confirmed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create the flight_state table for tracking flight status
CREATE TABLE IF NOT EXISTS flight_state (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    flight_number VARCHAR(20) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL,
    estimated_arrival TIMESTAMP WITH TIME ZONE NOT NULL,
    scheduled_arrival TIMESTAMP WITH TIME ZONE,
    origin VARCHAR(10),
    destination VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create the alerts table for tracking disruption alerts
CREATE TABLE IF NOT EXISTS alerts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    flight_number VARCHAR(20) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    customer_ids JSONB DEFAULT '[]',
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create the flights table for flight metadata
CREATE TABLE IF NOT EXISTS flights (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    flight_number VARCHAR(20) NOT NULL UNIQUE,
    origin VARCHAR(10) NOT NULL,
    destination VARCHAR(10) NOT NULL,
    aircraft_type VARCHAR(20),
    scheduled_departure TIMESTAMP WITH TIME ZONE,
    scheduled_arrival TIMESTAMP WITH TIME ZONE,
    gate VARCHAR(10),
    terminal VARCHAR(10),
    status VARCHAR(50) DEFAULT 'SCHEDULED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create the chatbot_sessions table for storing GenAI agent responses
CREATE TABLE IF NOT EXISTS chatbot_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    flight_id VARCHAR(50) NOT NULL,
    query_type VARCHAR(50) NOT NULL,
    request_data JSONB NOT NULL,
    response_data JSONB NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create the disruption_predictions table for storing ML predictions
CREATE TABLE IF NOT EXISTS disruption_predictions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    flight_id VARCHAR(50) NOT NULL,
    flight_number VARCHAR(20) NOT NULL,
    origin VARCHAR(10) NOT NULL,
    destination VARCHAR(10) NOT NULL,
    disruption_risk DECIMAL(5,3) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    risk_factors JSONB NOT NULL,
    contributing_factors JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    confidence DECIMAL(3,2) NOT NULL,
    model_version VARCHAR(10) DEFAULT '1.0',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create the customers table for customer preferences
CREATE TABLE IF NOT EXISTS customers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    seat_preference VARCHAR(50) DEFAULT 'no_preference',
    meal_preference VARCHAR(50) DEFAULT 'no_preference',
    notification_preference VARCHAR(50) DEFAULT 'email',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create the alerts_subscriptions table for managing alert subscriptions
CREATE TABLE IF NOT EXISTS alerts_subscriptions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    contact_info VARCHAR(255) NOT NULL,
    subscription_type VARCHAR(50) DEFAULT 'all_alerts',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_bookings_customer_id ON bookings(customer_id);
CREATE INDEX IF NOT EXISTS idx_bookings_flight_number ON bookings(flight_number);
CREATE INDEX IF NOT EXISTS idx_bookings_depart_date ON bookings(depart_date);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);

CREATE INDEX IF NOT EXISTS idx_flight_state_flight_number ON flight_state(flight_number);
CREATE INDEX IF NOT EXISTS idx_flight_state_status ON flight_state(status);
CREATE INDEX IF NOT EXISTS idx_flight_state_estimated_arrival ON flight_state(estimated_arrival);

CREATE INDEX IF NOT EXISTS idx_alerts_flight_number ON alerts(flight_number);
CREATE INDEX IF NOT EXISTS idx_alerts_alert_type ON alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts(resolved);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);

CREATE INDEX IF NOT EXISTS idx_flights_flight_number ON flights(flight_number);
CREATE INDEX IF NOT EXISTS idx_flights_origin ON flights(origin);
CREATE INDEX IF NOT EXISTS idx_flights_destination ON flights(destination);
CREATE INDEX IF NOT EXISTS idx_flights_status ON flights(status);
CREATE INDEX IF NOT EXISTS idx_flights_scheduled_departure ON flights(scheduled_departure);

CREATE INDEX IF NOT EXISTS idx_chatbot_sessions_flight_id ON chatbot_sessions(flight_id);
CREATE INDEX IF NOT EXISTS idx_chatbot_sessions_query_type ON chatbot_sessions(query_type);
CREATE INDEX IF NOT EXISTS idx_chatbot_sessions_confidence_score ON chatbot_sessions(confidence_score);
CREATE INDEX IF NOT EXISTS idx_chatbot_sessions_created_at ON chatbot_sessions(created_at);

CREATE INDEX IF NOT EXISTS idx_disruption_predictions_flight_id ON disruption_predictions(flight_id);
CREATE INDEX IF NOT EXISTS idx_disruption_predictions_flight_number ON disruption_predictions(flight_number);
CREATE INDEX IF NOT EXISTS idx_disruption_predictions_risk_level ON disruption_predictions(risk_level);
CREATE INDEX IF NOT EXISTS idx_disruption_predictions_disruption_risk ON disruption_predictions(disruption_risk);
CREATE INDEX IF NOT EXISTS idx_disruption_predictions_created_at ON disruption_predictions(created_at);

CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_customers_seat_preference ON customers(seat_preference);
CREATE INDEX IF NOT EXISTS idx_customers_meal_preference ON customers(meal_preference);

CREATE INDEX IF NOT EXISTS idx_alerts_subscriptions_user_id ON alerts_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_subscriptions_channel ON alerts_subscriptions(channel);
CREATE INDEX IF NOT EXISTS idx_alerts_subscriptions_active ON alerts_subscriptions(active);

-- Create a trigger to automatically update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_bookings_updated_at
    BEFORE UPDATE ON bookings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_flight_state_updated_at
    BEFORE UPDATE ON flight_state
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_flights_updated_at
    BEFORE UPDATE ON flights
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alerts_subscriptions_updated_at
    BEFORE UPDATE ON alerts_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert some sample data (optional)
INSERT INTO bookings (customer_id, flight_number, origin, destination, depart_date, status) VALUES
('CUST001', 'QP1001', 'DEL', 'BOM', '2024-01-15', 'confirmed'),
('CUST002', 'QP1002', 'BOM', 'BLR', '2024-01-16', 'confirmed'),
('CUST003', 'QP1003', 'BLR', 'HYD', '2024-01-17', 'pending');

-- Insert some sample flight states
INSERT INTO flight_state (flight_number, status, estimated_arrival, scheduled_arrival, origin, destination) VALUES
('QP1001', 'ON_TIME', '2024-01-15 14:30:00+00:00', '2024-01-15 14:30:00+00:00', 'DEL', 'BOM'),
('QP1002', 'DELAYED', '2024-01-16 16:45:00+00:00', '2024-01-16 15:30:00+00:00', 'BOM', 'BLR'),
('QP1003', 'ON_TIME', '2024-01-17 18:15:00+00:00', '2024-01-17 18:15:00+00:00', 'BLR', 'HYD');

-- Insert some sample flights metadata
INSERT INTO flights (flight_number, origin, destination, aircraft_type, scheduled_departure, scheduled_arrival, gate, terminal, status) VALUES
('QP1001', 'DEL', 'BOM', 'A320', '2024-01-15 12:00:00+00:00', '2024-01-15 14:30:00+00:00', 'G12', 'T3', 'SCHEDULED'),
('QP1002', 'BOM', 'BLR', 'B737', '2024-01-16 13:00:00+00:00', '2024-01-16 15:30:00+00:00', 'G8', 'T2', 'SCHEDULED'),
('QP1003', 'BLR', 'HYD', 'A321', '2024-01-17 16:00:00+00:00', '2024-01-17 18:15:00+00:00', 'G15', 'T1', 'SCHEDULED'),
('QP2001', 'DEL', 'GOA', 'A320', '2024-01-20 08:00:00+00:00', '2024-01-20 10:30:00+00:00', 'G5', 'T3', 'SCHEDULED'),
('QP2002', 'GOA', 'DEL', 'A320', '2024-01-20 18:00:00+00:00', '2024-01-20 20:30:00+00:00', 'G3', 'T1', 'SCHEDULED');

-- Insert some sample customers
INSERT INTO customers (name, email, phone, seat_preference, meal_preference, notification_preference) VALUES
('Rajesh Kumar', 'rajesh.kumar@email.com', '+91-9876543210', 'window', 'vegetarian', 'email'),
('Priya Sharma', 'priya.sharma@email.com', '+91-9876543211', 'aisle', 'non_vegetarian', 'sms'),
('Amit Patel', 'amit.patel@email.com', '+91-9876543212', 'window', 'jain', 'all'),
('Sneha Reddy', 'sneha.reddy@email.com', '+91-9876543213', 'front', 'vegan', 'push'),
('Vikram Singh', 'vikram.singh@email.com', '+91-9876543214', 'exit_row', 'no_preference', 'email');
"""
    
    print(sql_commands)
    print("-" * 60)
    print()
    print("5. After running the SQL, your database will be ready!")
    print("6. Start the Flask application with: python app.py")
    print()
    print("Environment Variables Required:")
    print("- SUPABASE_URL: Your Supabase project URL")
    print("- SUPABASE_KEY: Your Supabase anon key")
    print()
    print("=" * 60)

if __name__ == "__main__":
    print_database_setup_instructions()