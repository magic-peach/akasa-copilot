import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.supabase: Client = create_client(self.url, self.key)
    
    def get_client(self):
        return self.supabase
    
    def create_bookings_table(self):
        """
        Create the bookings table in Supabase.
        This should be run once to set up the database schema.
        
        SQL to run in Supabase SQL editor:
        
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
        
        -- Create an index on customer_id for faster queries
        CREATE INDEX IF NOT EXISTS idx_bookings_customer_id ON bookings(customer_id);
        
        -- Create an index on flight_number for faster queries
        CREATE INDEX IF NOT EXISTS idx_bookings_flight_number ON bookings(flight_number);
        
        -- Create an index on depart_date for faster queries
        CREATE INDEX IF NOT EXISTS idx_bookings_depart_date ON bookings(depart_date);
        """
        pass

# Initialize database connection
db = Database()