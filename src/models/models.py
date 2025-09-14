from datetime import datetime
from typing import Optional, Dict, Any
import uuid

class Booking:
    def __init__(self, customer_id: str, flight_number: str, origin: str, 
                 destination: str, depart_date: str, status: str = "confirmed",
                 id: Optional[str] = None, created_at: Optional[str] = None,
                 updated_at: Optional[str] = None):
        self.id = id or str(uuid.uuid4())
        self.customer_id = customer_id
        self.flight_number = flight_number
        self.origin = origin
        self.destination = destination
        self.depart_date = depart_date
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert booking object to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'flight_number': self.flight_number,
            'origin': self.origin,
            'destination': self.destination,
            'depart_date': self.depart_date,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Booking':
        """Create booking object from dictionary"""
        return cls(
            id=data.get('id'),
            customer_id=data['customer_id'],
            flight_number=data['flight_number'],
            origin=data['origin'],
            destination=data['destination'],
            depart_date=data['depart_date'],
            status=data.get('status', 'confirmed'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def validate(self) -> Dict[str, str]:
        """Validate booking data and return errors if any"""
        errors = {}
        
        if not self.customer_id or not self.customer_id.strip():
            errors['customer_id'] = 'Customer ID is required'
        
        if not self.flight_number or not self.flight_number.strip():
            errors['flight_number'] = 'Flight number is required'
        elif len(self.flight_number) > 20:
            errors['flight_number'] = 'Flight number must be 20 characters or less'
        
        if not self.origin or not self.origin.strip():
            errors['origin'] = 'Origin is required'
        elif len(self.origin) > 10:
            errors['origin'] = 'Origin must be 10 characters or less'
        
        if not self.destination or not self.destination.strip():
            errors['destination'] = 'Destination is required'
        elif len(self.destination) > 10:
            errors['destination'] = 'Destination must be 10 characters or less'
        
        if not self.depart_date:
            errors['depart_date'] = 'Departure date is required'
        else:
            try:
                # Validate date format (YYYY-MM-DD)
                datetime.strptime(self.depart_date, '%Y-%m-%d')
            except ValueError:
                errors['depart_date'] = 'Departure date must be in YYYY-MM-DD format'
        
        if self.status not in ['confirmed', 'cancelled', 'completed', 'pending']:
            errors['status'] = 'Status must be one of: confirmed, cancelled, completed, pending'
        
        return errors