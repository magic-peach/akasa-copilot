"""
Event processing service for flight events and disruption detection
"""

import threading
import time
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from src.models.event_models import FlightState, Alert
from src.utils.database import db
import logging

logger = logging.getLogger(__name__)

class EventProcessor:
    """Service for processing flight events and detecting disruptions"""
    
    def __init__(self):
        self.event_queue = queue.Queue()
        self.alerts_queue = queue.Queue()
        self.running = False
        self.worker_thread = None
        self.notification_thread = None
        
        # In-memory storage for flight states (in production, this would be Redis or similar)
        self.flight_states = {}
        
        # Alert thresholds
        self.DELAY_THRESHOLD_MINUTES = 45
        
    def start_background_worker(self):
        """Start the background worker thread"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._process_events, daemon=True)
            self.notification_thread = threading.Thread(target=self._process_notifications, daemon=True)
            
            self.worker_thread.start()
            self.notification_thread.start()
            
            logger.info("Event processing background workers started")
    
    def stop_background_worker(self):
        """Stop the background worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        if self.notification_thread:
            self.notification_thread.join(timeout=5)
        logger.info("Event processing background workers stopped")
    
    def add_flight_event(self, event_data: Dict[str, Any]) -> bool:
        """Add a flight event to the processing queue"""
        try:
            # Validate the event data
            flight_state = FlightState.from_dict(event_data)
            validation_errors = flight_state.validate()
            
            if validation_errors:
                logger.error(f"Invalid flight event data: {validation_errors}")
                return False
            
            # Add to processing queue
            self.event_queue.put(event_data)
            logger.info(f"Added flight event to queue: {flight_state.flight_number} - {flight_state.status}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding flight event to queue: {str(e)}")
            return False
    
    def _process_events(self):
        """Background worker to process flight events"""
        logger.info("Event processing worker started")
        
        while self.running:
            try:
                # Get event from queue with timeout
                event_data = self.event_queue.get(timeout=1)
                
                # Process the event
                self._handle_flight_event(event_data)
                
                # Mark task as done
                self.event_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing flight event: {str(e)}")
    
    def _handle_flight_event(self, event_data: Dict[str, Any]):
        """Handle a single flight event"""
        try:
            flight_state = FlightState.from_dict(event_data)
            flight_number = flight_state.flight_number
            
            # Get previous state if exists
            previous_state = self.flight_states.get(flight_number)
            
            # Store/update flight state in database
            self._store_flight_state(flight_state)
            
            # Update in-memory cache
            self.flight_states[flight_number] = flight_state
            
            # Check for disruptions
            alerts = self._detect_disruptions(flight_state, previous_state)
            
            # Process any alerts
            for alert in alerts:
                self.alerts_queue.put(alert)
                logger.info(f"Generated alert: {alert.alert_type} for flight {flight_number}")
            
        except Exception as e:
            logger.error(f"Error handling flight event: {str(e)}")
    
    def _store_flight_state(self, flight_state: FlightState):
        """Store flight state in database"""
        try:
            supabase = db.get_client()
            
            # Check if flight state already exists
            existing = supabase.table('flight_state').select('*').eq('flight_number', flight_state.flight_number).execute()
            
            flight_data = flight_state.to_dict()
            flight_data['updated_at'] = datetime.utcnow().isoformat()
            
            if existing.data:
                # Update existing record
                result = supabase.table('flight_state').update(flight_data).eq('flight_number', flight_state.flight_number).execute()
            else:
                # Insert new record
                flight_data['created_at'] = datetime.utcnow().isoformat()
                result = supabase.table('flight_state').insert(flight_data).execute()
            
            if not result.data:
                logger.error(f"Failed to store flight state for {flight_state.flight_number}")
                
        except Exception as e:
            logger.error(f"Error storing flight state: {str(e)}")
    
    def _detect_disruptions(self, current_state: FlightState, previous_state: Optional[FlightState]) -> List[Alert]:
        """Detect disruptions and generate alerts"""
        alerts = []
        
        try:
            # Check for cancellation
            if current_state.status == 'CANCELLED':
                alert = Alert(
                    flight_number=current_state.flight_number,
                    alert_type='CANCELLATION',
                    message=f"Flight {current_state.flight_number} has been cancelled",
                    severity='critical',
                    customer_ids=self._get_affected_customers(current_state.flight_number)
                )
                alerts.append(alert)
            
            # Check for significant delays
            elif current_state.status == 'DELAYED' and current_state.scheduled_arrival:
                delay_minutes = self._calculate_delay_minutes(
                    current_state.scheduled_arrival,
                    current_state.estimated_arrival
                )
                
                if delay_minutes >= self.DELAY_THRESHOLD_MINUTES:
                    severity = 'high' if delay_minutes >= 120 else 'medium'
                    
                    alert = Alert(
                        flight_number=current_state.flight_number,
                        alert_type='DELAY',
                        message=f"Flight {current_state.flight_number} is delayed by {delay_minutes} minutes",
                        severity=severity,
                        customer_ids=self._get_affected_customers(current_state.flight_number)
                    )
                    alerts.append(alert)
            
            # Check for status changes that might affect passengers
            if previous_state and previous_state.status != current_state.status:
                if current_state.status in ['BOARDING', 'DEPARTED']:
                    alert = Alert(
                        flight_number=current_state.flight_number,
                        alert_type='SCHEDULE_CHANGE',
                        message=f"Flight {current_state.flight_number} status changed to {current_state.status}",
                        severity='low',
                        customer_ids=self._get_affected_customers(current_state.flight_number)
                    )
                    alerts.append(alert)
            
        except Exception as e:
            logger.error(f"Error detecting disruptions: {str(e)}")
        
        return alerts
    
    def _calculate_delay_minutes(self, scheduled_time: str, estimated_time: str) -> int:
        """Calculate delay in minutes"""
        try:
            scheduled = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
            estimated = datetime.fromisoformat(estimated_time.replace('Z', '+00:00'))
            delay = estimated - scheduled
            return max(0, int(delay.total_seconds() / 60))
        except ValueError:
            return 0
    
    def _get_affected_customers(self, flight_number: str) -> List[str]:
        """Get list of customer IDs affected by a flight"""
        try:
            supabase = db.get_client()
            result = supabase.table('bookings').select('customer_id').eq('flight_number', flight_number).eq('status', 'confirmed').execute()
            
            if result.data:
                return [booking['customer_id'] for booking in result.data]
            return []
            
        except Exception as e:
            logger.error(f"Error getting affected customers: {str(e)}")
            return []
    
    def _process_notifications(self):
        """Background worker to process alert notifications"""
        logger.info("Notification processing worker started")
        
        while self.running:
            try:
                # Get alert from queue with timeout
                alert = self.alerts_queue.get(timeout=1)
                
                # Process the alert
                self._send_notification(alert)
                
                # Store alert in database
                self._store_alert(alert)
                
                # Mark task as done
                self.alerts_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing alert notification: {str(e)}")
    
    def _send_notification(self, alert: Alert):
        """Send notification for an alert (mock implementation)"""
        try:
            # Mock notification - in production, this would integrate with SMS, email, push notifications
            notification_message = f"""
🚨 FLIGHT ALERT - {alert.severity.upper()}
Flight: {alert.flight_number}
Type: {alert.alert_type}
Message: {alert.message}
Affected Customers: {len(alert.customer_ids)}
Time: {alert.created_at}
            """.strip()
            
            print("\n" + "="*60)
            print("FLIGHT DISRUPTION NOTIFICATION")
            print("="*60)
            print(notification_message)
            print("="*60)
            
            # Log the notification
            logger.info(f"Sent notification for alert {alert.id}: {alert.alert_type} - {alert.flight_number}")
            
            # In production, you would integrate with:
            # - SMS service (Twilio, AWS SNS)
            # - Email service (SendGrid, AWS SES)
            # - Push notification service (Firebase, OneSignal)
            # - Slack/Teams webhooks
            # - Customer mobile app notifications
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
    
    def _store_alert(self, alert: Alert):
        """Store alert in database"""
        try:
            supabase = db.get_client()
            alert_data = alert.to_dict()
            
            result = supabase.table('alerts').insert(alert_data).execute()
            
            if not result.data:
                logger.error(f"Failed to store alert {alert.id}")
            else:
                logger.info(f"Stored alert {alert.id} in database")
                
        except Exception as e:
            logger.error(f"Error storing alert: {str(e)}")
    
    def get_flight_state(self, flight_number: str) -> Optional[FlightState]:
        """Get current flight state"""
        return self.flight_states.get(flight_number)
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts from database"""
        try:
            supabase = db.get_client()
            result = supabase.table('alerts').select('*').order('created_at', desc=True).limit(limit).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting recent alerts: {str(e)}")
            return []

# Global event processor instance
event_processor = EventProcessor()