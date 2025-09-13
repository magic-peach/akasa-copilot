"""
Event models for flight state tracking and alert management
"""

from datetime import datetime
from typing import Optional, Dict, Any
import uuid

class FlightState:
    """Model for tracking flight state information"""
    
    def __init__(self, flight_number: str, status: str, estimated_arrival: str,
                 id: Optional[str] = None, created_at: Optional[str] = None,
                 updated_at: Optional[str] = None, scheduled_arrival: Optional[str] = None,
                 origin: Optional[str] = None, destination: Optional[str] = None):
        self.id = id or str(uuid.uuid4())
        self.flight_number = flight_number
        self.status = status
        self.estimated_arrival = estimated_arrival
        self.scheduled_arrival = scheduled_arrival
        self.origin = origin
        self.destination = destination
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert flight state object to dictionary"""
        return {
            'id': self.id,
            'flight_number': self.flight_number,
            'status': self.status,
            'estimated_arrival': self.estimated_arrival,
            'scheduled_arrival': self.scheduled_arrival,
            'origin': self.origin,
            'destination': self.destination,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FlightState':
        """Create flight state object from dictionary"""
        return cls(
            id=data.get('id'),
            flight_number=data['flight_number'],
            status=data['status'],
            estimated_arrival=data['estimated_arrival'],
            scheduled_arrival=data.get('scheduled_arrival'),
            origin=data.get('origin'),
            destination=data.get('destination'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def validate(self) -> Dict[str, str]:
        """Validate flight state data and return errors if any"""
        errors = {}
        
        if not self.flight_number or not self.flight_number.strip():
            errors['flight_number'] = 'Flight number is required'
        elif len(self.flight_number) > 20:
            errors['flight_number'] = 'Flight number must be 20 characters or less'
        
        valid_statuses = ['ON_TIME', 'DELAYED', 'CANCELLED', 'DEPARTED', 'ARRIVED', 'BOARDING']
        if not self.status or self.status not in valid_statuses:
            errors['status'] = f'Status must be one of: {", ".join(valid_statuses)}'
        
        if not self.estimated_arrival:
            errors['estimated_arrival'] = 'Estimated arrival is required'
        else:
            try:
                # Validate datetime format (ISO 8601)
                datetime.fromisoformat(self.estimated_arrival.replace('Z', '+00:00'))
            except ValueError:
                errors['estimated_arrival'] = 'Estimated arrival must be in ISO 8601 format'
        
        if self.scheduled_arrival:
            try:
                datetime.fromisoformat(self.scheduled_arrival.replace('Z', '+00:00'))
            except ValueError:
                errors['scheduled_arrival'] = 'Scheduled arrival must be in ISO 8601 format'
        
        return errors

class Alert:
    """Model for tracking flight disruption alerts"""
    
    def __init__(self, flight_number: str, alert_type: str, message: str,
                 severity: str = 'medium', customer_ids: Optional[list] = None,
                 id: Optional[str] = None, created_at: Optional[str] = None,
                 resolved: bool = False, resolved_at: Optional[str] = None):
        self.id = id or str(uuid.uuid4())
        self.flight_number = flight_number
        self.alert_type = alert_type
        self.message = message
        self.severity = severity
        self.customer_ids = customer_ids or []
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.resolved = resolved
        self.resolved_at = resolved_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert object to dictionary"""
        return {
            'id': self.id,
            'flight_number': self.flight_number,
            'alert_type': self.alert_type,
            'message': self.message,
            'severity': self.severity,
            'customer_ids': self.customer_ids,
            'created_at': self.created_at,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Alert':
        """Create alert object from dictionary"""
        return cls(
            id=data.get('id'),
            flight_number=data['flight_number'],
            alert_type=data['alert_type'],
            message=data['message'],
            severity=data.get('severity', 'medium'),
            customer_ids=data.get('customer_ids', []),
            created_at=data.get('created_at'),
            resolved=data.get('resolved', False),
            resolved_at=data.get('resolved_at')
        )
    
    def validate(self) -> Dict[str, str]:
        """Validate alert data and return errors if any"""
        errors = {}
        
        if not self.flight_number or not self.flight_number.strip():
            errors['flight_number'] = 'Flight number is required'
        
        valid_types = ['CANCELLATION', 'DELAY', 'GATE_CHANGE', 'SCHEDULE_CHANGE']
        if not self.alert_type or self.alert_type not in valid_types:
            errors['alert_type'] = f'Alert type must be one of: {", ".join(valid_types)}'
        
        if not self.message or not self.message.strip():
            errors['message'] = 'Message is required'
        
        valid_severities = ['low', 'medium', 'high', 'critical']
        if self.severity not in valid_severities:
            errors['severity'] = f'Severity must be one of: {", ".join(valid_severities)}'
        
        return errors
    
    def calculate_delay_minutes(self, scheduled_time: str, estimated_time: str) -> int:
        """Calculate delay in minutes between scheduled and estimated times"""
        try:
            scheduled = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
            estimated = datetime.fromisoformat(estimated_time.replace('Z', '+00:00'))
            delay = estimated - scheduled
            return max(0, int(delay.total_seconds() / 60))
        except ValueError:
            return 0