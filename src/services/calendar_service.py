"""
Google Calendar Integration Service for Akasa Airlines
Handles calendar event syncing, flight booking suggestions, and conflict detection
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from src.services.google_oauth_service import oauth_service
from src.services.flight_search_service import flight_search_service
import re

logger = logging.getLogger(__name__)

@dataclass
class CalendarEvent:
    """Represents a calendar event with travel-related information"""
    id: str
    summary: str
    start_time: datetime
    end_time: datetime
    location: Optional[str]
    description: Optional[str]
    is_travel_related: bool
    destination_city: Optional[str]
    destination_airport: Optional[str]
    travel_type: Optional[str]  # 'business', 'personal', 'conference', etc.
    priority: int  # 1-5, higher is more important

@dataclass
class FlightSuggestion:
    """Represents a flight suggestion based on calendar events"""
    event_id: str
    event_summary: str
    destination: str
    suggested_departure: datetime
    suggested_return: datetime
    flight_options: List[Dict[str, Any]]
    conflict_warning: Optional[str]
    priority_score: float

@dataclass
class BookingConflict:
    """Represents a booking conflict with calendar events"""
    booking_id: str
    flight_details: Dict[str, Any]
    conflicting_events: List[CalendarEvent]
    conflict_type: str  # 'overlap', 'insufficient_time', 'wrong_destination'
    severity: str  # 'low', 'medium', 'high', 'critical'
    suggested_actions: List[str]

class CalendarService:
    """Service for Google Calendar integration and flight booking intelligence"""
    
    def __init__(self):
        self.oauth_service = oauth_service
        self.flight_service = flight_search_service
        
        # Travel-related keywords for event classification
        self.travel_keywords = {
            'business': ['meeting', 'conference', 'presentation', 'client', 'business', 'work', 'interview', 'appointment'],
            'personal': ['vacation', 'holiday', 'trip', 'visit', 'family', 'wedding', 'travel'],
            'conference': ['conference', 'summit', 'convention', 'seminar', 'workshop', 'event'],
            'location_indicators': ['in ', 'at ', 'to ', 'from ', 'travel to', 'going to']
        }
        
        # Keywords to filter out (unimportant events)
        self.filter_keywords = [
            'coursera', 'learning time', 'study time', 'practice', 'exercise', 'workout',
            'reminder', 'notification', 'alarm', 'break', 'lunch', 'dinner', 'coffee',
            'routine', 'daily', 'weekly', 'monthly', 'recurring', 'habit', 'task',
            'todo', 'checklist', 'note', 'memo', 'draft', 'temp', 'test', 'sample'
        ]
        
        # Event types to ignore
        self.ignore_event_types = [
            'out_of_office', 'focus_time', 'working_location', 'free_busy'
        ]
        
        # Airport and city mappings
        self.city_airport_mapping = {
            'mumbai': 'BOM', 'delhi': 'DEL', 'bangalore': 'BLR', 'hyderabad': 'HYD',
            'chennai': 'MAA', 'kolkata': 'CCU', 'pune': 'PNQ', 'ahmedabad': 'AMD',
            'kochi': 'COK', 'goa': 'GOI', 'jaipur': 'JAI', 'lucknow': 'LKO',
            'chandigarh': 'IXC', 'indore': 'IDR', 'bhubaneswar': 'BBI',
            'coimbatore': 'CJB', 'vadodara': 'BDQ', 'nagpur': 'NAG'
        }
        
        # Buffer times for travel (in hours)
        self.travel_buffers = {
            'domestic': 2,  # 2 hours before domestic flights
            'international': 3,  # 3 hours before international flights
            'business': 1,  # 1 hour buffer for business travel
            'personal': 2   # 2 hours buffer for personal travel
        }
    
    def sync_calendar_events(self, user_id: str, days_ahead: int = 30) -> List[CalendarEvent]:
        """
        Sync and analyze calendar events for travel planning
        
        Args:
            user_id: User identifier
            days_ahead: Number of days to look ahead
            
        Returns:
            List of analyzed calendar events
        """
        try:
            # Get calendar service
            calendar_service = self.oauth_service.get_calendar_service()
            if not calendar_service:
                logger.error("Calendar service not available")
                return []
            
            # Calculate date range
            now = datetime.now(timezone.utc)
            end_date = now + timedelta(days=days_ahead)
            
            # Fetch events from calendar
            events_result = calendar_service.events().list(
                calendarId='primary',
                timeMin=now.isoformat(),
                timeMax=end_date.isoformat(),
                singleEvents=True,
                orderBy='startTime',
                maxResults=100
            ).execute()
            
            events = events_result.get('items', [])
            logger.info(f"Retrieved {len(events)} calendar events")
            
            # Filter and analyze events
            filtered_events = self._filter_events(events)
            analyzed_events = []
            seen_events = set()  # Track seen events to prevent duplicates
            
            for event in filtered_events:
                analyzed_event = self._analyze_calendar_event(event)
                if analyzed_event and self._is_important_event(analyzed_event):
                    # Create a unique key for the event to prevent duplicates
                    event_key = f"{analyzed_event.summary}_{analyzed_event.start_time.date()}_{analyzed_event.end_time.date()}"
                    if event_key not in seen_events:
                        seen_events.add(event_key)
                        analyzed_events.append(analyzed_event)
            
            # Store events in database for future reference
            self._store_calendar_events(user_id, analyzed_events)
            
            logger.info(f"Analyzed {len(analyzed_events)} events, {len([e for e in analyzed_events if e.is_travel_related])} travel-related")
            return analyzed_events
            
        except Exception as e:
            logger.error(f"Error syncing calendar events: {str(e)}")
            return []
    
    def _analyze_calendar_event(self, event: Dict[str, Any]) -> Optional[CalendarEvent]:
        """Analyze a calendar event to determine if it's travel-related"""
        try:
            # Extract basic event information
            event_id = event.get('id', '')
            summary = event.get('summary', '')
            description = event.get('description', '')
            location = event.get('location', '')
            
            # Parse start and end times
            start_time, end_time = self._parse_event_times(event)
            if not start_time or not end_time:
                return None
            
            # Analyze if event is travel-related
            is_travel_related, travel_type, destination = self._classify_travel_event(
                summary, description, location
            )
            
            # Determine priority based on event type and timing
            priority = self._calculate_event_priority(event, is_travel_related)
            
            return CalendarEvent(
                id=event_id,
                summary=summary,
                start_time=start_time,
                end_time=end_time,
                location=location,
                description=description,
                is_travel_related=is_travel_related,
                destination_city=destination,
                destination_airport=self._get_airport_code(destination),
                travel_type=travel_type,
                priority=priority
            )
            
        except Exception as e:
            logger.error(f"Error analyzing calendar event: {str(e)}")
            return None
    
    def _parse_event_times(self, event: Dict[str, Any]) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Parse start and end times from calendar event"""
        try:
            start_data = event.get('start', {})
            end_data = event.get('end', {})
            
            # Handle both date and dateTime formats
            start_time = None
            end_time = None
            
            if 'dateTime' in start_data:
                start_time = datetime.fromisoformat(start_data['dateTime'].replace('Z', '+00:00'))
            elif 'date' in start_data:
                start_time = datetime.fromisoformat(start_data['date'] + 'T00:00:00+00:00')
            
            if 'dateTime' in end_data:
                end_time = datetime.fromisoformat(end_data['dateTime'].replace('Z', '+00:00'))
            elif 'date' in end_data:
                end_time = datetime.fromisoformat(end_data['date'] + 'T23:59:59+00:00')
            
            return start_time, end_time
            
        except Exception as e:
            logger.error(f"Error parsing event times: {str(e)}")
            return None, None
    
    def _filter_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out unimportant and repetitive events"""
        try:
            filtered_events = []
            
            for event in events:
                # Skip if event type should be ignored
                event_type = event.get('eventType', '')
                if event_type in self.ignore_event_types:
                    continue
                
                # Skip if it's a recurring event with no specific date
                if event.get('recurringEventId'):
                    # Only include if it's a specific instance
                    if not event.get('start', {}).get('dateTime'):
                        continue
                
                # Skip all-day events that are likely not important
                if event.get('start', {}).get('date') and not event.get('start', {}).get('dateTime'):
                    # Check if it's an important all-day event
                    summary = event.get('summary', '').lower()
                    if not any(keyword in summary for keyword in ['holiday', 'vacation', 'trip', 'conference', 'meeting']):
                        continue
                
                # Skip events with very short duration (likely reminders)
                start_time, end_time = self._parse_event_times(event)
                if start_time and end_time:
                    duration = (end_time - start_time).total_seconds() / 60  # minutes
                    if duration < 15:  # Skip events shorter than 15 minutes
                        continue
                
                filtered_events.append(event)
            
            logger.info(f"Filtered {len(events)} events down to {len(filtered_events)} important events")
            return filtered_events
            
        except Exception as e:
            logger.error(f"Error filtering events: {str(e)}")
            return events  # Return original events if filtering fails
    
    def _is_important_event(self, event: CalendarEvent) -> bool:
        """Determine if an event is important enough to include"""
        try:
            summary = event.summary.lower()
            description = (event.description or '').lower()
            location = (event.location or '').lower()
            
            # Check if event contains filter keywords (unimportant)
            text_to_check = f"{summary} {description} {location}"
            if any(keyword in text_to_check for keyword in self.filter_keywords):
                return False
            
            # Check if it's a travel-related event
            if event.is_travel_related:
                return True
            
            # Check if it's a business event
            if any(keyword in text_to_check for keyword in self.travel_keywords['business']):
                return True
            
            # Check if it has a specific location (likely important)
            if event.location and len(event.location.strip()) > 0:
                return True
            
            # Check if it's a conference or meeting
            if any(keyword in text_to_check for keyword in ['conference', 'meeting', 'seminar', 'workshop']):
                return True
            
            # Check if it's an appointment or interview
            if any(keyword in text_to_check for keyword in ['appointment', 'interview', 'consultation']):
                return True
            
            # Check if it's a personal event with location
            if any(keyword in text_to_check for keyword in ['wedding', 'birthday', 'anniversary', 'celebration']):
                return True
            
            # Skip if it's just a generic event without clear importance
            return False
            
        except Exception as e:
            logger.error(f"Error checking event importance: {str(e)}")
            return True  # Include event if check fails
    
    def _classify_travel_event(self, summary: str, description: str, location: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Classify if an event is travel-related and extract destination"""
        try:
            text_to_analyze = f"{summary} {description} {location}".lower()
            
            # Check for travel-related keywords
            is_travel_related = False
            travel_type = None
            destination = None
            
            # Check for business travel
            if any(keyword in text_to_analyze for keyword in self.travel_keywords['business']):
                is_travel_related = True
                travel_type = 'business'
            
            # Check for personal travel
            if any(keyword in text_to_analyze for keyword in self.travel_keywords['personal']):
                is_travel_related = True
                travel_type = 'personal'
            
            # Check for conferences
            if any(keyword in text_to_analyze for keyword in self.travel_keywords['conference']):
                is_travel_related = True
                travel_type = 'conference'
            
            # Check for location indicators
            if any(indicator in text_to_analyze for indicator in self.travel_keywords['location_indicators']):
                is_travel_related = True
                if not travel_type:
                    travel_type = 'general'
            
            # Extract destination from location or description
            if is_travel_related:
                destination = self._extract_destination(text_to_analyze)
            
            return is_travel_related, travel_type, destination
            
        except Exception as e:
            logger.error(f"Error classifying travel event: {str(e)}")
            return False, None, None
    
    def _extract_destination(self, text: str) -> Optional[str]:
        """Extract destination city from text"""
        try:
            # Look for city names in the text
            for city, airport_code in self.city_airport_mapping.items():
                if city in text:
                    return city.title()
            
            # Look for patterns like "in Mumbai", "to Delhi", etc.
            patterns = [
                r'in\s+([A-Za-z]+)',
                r'to\s+([A-Za-z]+)',
                r'at\s+([A-Za-z]+)',
                r'travel\s+to\s+([A-Za-z]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    city = match.group(1).lower()
                    if city in self.city_airport_mapping:
                        return city.title()
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting destination: {str(e)}")
            return None
    
    def _get_airport_code(self, city: str) -> Optional[str]:
        """Get airport code for a city"""
        if city:
            return self.city_airport_mapping.get(city.lower())
        return None
    
    def _calculate_event_priority(self, event: Dict[str, Any], is_travel_related: bool) -> int:
        """Calculate priority score for an event (1-5)"""
        try:
            priority = 1
            
            # Higher priority for travel-related events
            if is_travel_related:
                priority += 2
            
            # Check for important keywords
            summary = event.get('summary', '').lower()
            if any(keyword in summary for keyword in ['urgent', 'important', 'critical', 'meeting']):
                priority += 1
            
            # Check for attendees (more attendees = higher priority)
            attendees = event.get('attendees', [])
            if len(attendees) > 5:
                priority += 1
            
            return min(priority, 5)  # Cap at 5
            
        except Exception as e:
            logger.error(f"Error calculating event priority: {str(e)}")
            return 1
    
    def generate_flight_suggestions(self, user_id: str, origin: str = 'DEL') -> List[FlightSuggestion]:
        """
        Generate flight suggestions based on calendar events
        
        Args:
            user_id: User identifier
            origin: Origin airport code
            
        Returns:
            List of flight suggestions
        """
        try:
            # Get travel-related calendar events
            events = self.sync_calendar_events(user_id)
            travel_events = [e for e in events if e.is_travel_related and e.destination_airport]
            
            if not travel_events:
                logger.info("No travel-related events found for flight suggestions")
                return []
            
            suggestions = []
            for event in travel_events:
                # Calculate suggested departure and return times
                departure_time, return_time = self._calculate_suggested_times(event)
                
                # Search for flights
                flight_options = self._search_flights_for_event(
                    origin, event.destination_airport, departure_time, return_time
                )
                
                # Check for conflicts
                conflict_warning = self._check_flight_conflicts(event, departure_time, return_time)
                
                # Calculate priority score
                priority_score = self._calculate_suggestion_priority(event, flight_options)
                
                suggestion = FlightSuggestion(
                    event_id=event.id,
                    event_summary=event.summary,
                    destination=event.destination_city or event.destination_airport,
                    suggested_departure=departure_time,
                    suggested_return=return_time,
                    flight_options=flight_options,
                    conflict_warning=conflict_warning,
                    priority_score=priority_score
                )
                
                suggestions.append(suggestion)
            
            # Sort by priority score
            suggestions.sort(key=lambda x: x.priority_score, reverse=True)
            
            logger.info(f"Generated {len(suggestions)} flight suggestions")
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating flight suggestions: {str(e)}")
            return []
    
    def _calculate_suggested_times(self, event: CalendarEvent) -> Tuple[datetime, datetime]:
        """Calculate suggested departure and return times for an event"""
        try:
            # Calculate buffer time based on travel type
            buffer_hours = self.travel_buffers.get(event.travel_type, 2)
            
            # Suggested departure: event start time minus buffer
            suggested_departure = event.start_time - timedelta(hours=buffer_hours)
            
            # Suggested return: event end time plus buffer
            suggested_return = event.end_time + timedelta(hours=buffer_hours)
            
            # Ensure departure is not in the past
            now = datetime.now(timezone.utc)
            if suggested_departure < now:
                suggested_departure = now + timedelta(hours=1)
            
            return suggested_departure, suggested_return
            
        except Exception as e:
            logger.error(f"Error calculating suggested times: {str(e)}")
            return event.start_time, event.end_time
    
    def _search_flights_for_event(self, origin: str, destination: str, 
                                 departure: datetime, return_date: datetime) -> List[Dict[str, Any]]:
        """Search for flights for a specific event"""
        try:
            # Use existing flight search service
            search_params = {
                'origin': origin,
                'destination': destination,
                'departure_date': departure.strftime('%Y-%m-%d'),
                'return_date': return_date.strftime('%Y-%m-%d'),
                'passengers': 1
            }
            
            # This would integrate with your existing flight search service
            # For now, return mock data
            return [
                {
                    'flight_number': 'QP1001',
                    'airline': 'Akasa Air',
                    'departure_time': departure.strftime('%H:%M'),
                    'arrival_time': (departure + timedelta(hours=2)).strftime('%H:%M'),
                    'price': 8500,
                    'duration': '2h 15m',
                    'stops': 0
                },
                {
                    'flight_number': 'QP1002',
                    'airline': 'Akasa Air',
                    'departure_time': (departure + timedelta(hours=2)).strftime('%H:%M'),
                    'arrival_time': (departure + timedelta(hours=4, minutes=15)).strftime('%H:%M'),
                    'price': 7200,
                    'duration': '2h 15m',
                    'stops': 0
                }
            ]
            
        except Exception as e:
            logger.error(f"Error searching flights for event: {str(e)}")
            return []
    
    def _check_flight_conflicts(self, event: CalendarEvent, departure: datetime, return_date: datetime) -> Optional[str]:
        """Check for conflicts with other calendar events"""
        try:
            # This would check against other calendar events
            # For now, return a simple check
            now = datetime.now(timezone.utc)
            
            if departure < now:
                return "Suggested departure time is in the past"
            
            if return_date < departure:
                return "Return date is before departure date"
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking flight conflicts: {str(e)}")
            return "Error checking for conflicts"
    
    def _calculate_suggestion_priority(self, event: CalendarEvent, flight_options: List[Dict[str, Any]]) -> float:
        """Calculate priority score for a flight suggestion"""
        try:
            score = event.priority * 10  # Base score from event priority
            
            # Add score based on flight availability
            if flight_options:
                score += len(flight_options) * 2
            
            # Add score based on event timing (closer events get higher priority)
            days_until_event = (event.start_time - datetime.now(timezone.utc)).days
            if days_until_event < 7:
                score += 20
            elif days_until_event < 30:
                score += 10
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating suggestion priority: {str(e)}")
            return 0.0
    
    def detect_booking_conflicts(self, user_id: str, booking_details: Dict[str, Any]) -> List[BookingConflict]:
        """
        Detect conflicts between a flight booking and calendar events
        
        Args:
            user_id: User identifier
            booking_details: Flight booking details
            
        Returns:
            List of detected conflicts
        """
        try:
            # Get calendar events
            events = self.sync_calendar_events(user_id)
            
            # Parse booking details
            booking_id = booking_details.get('id', '')
            departure_time = datetime.fromisoformat(booking_details.get('departure_time', ''))
            arrival_time = datetime.fromisoformat(booking_details.get('arrival_time', ''))
            destination = booking_details.get('destination', '')
            
            conflicts = []
            
            # Check for overlapping events
            overlapping_events = []
            for event in events:
                if self._events_overlap(event, departure_time, arrival_time):
                    overlapping_events.append(event)
            
            if overlapping_events:
                conflict = BookingConflict(
                    booking_id=booking_id,
                    flight_details=booking_details,
                    conflicting_events=overlapping_events,
                    conflict_type='overlap',
                    severity=self._calculate_conflict_severity(overlapping_events),
                    suggested_actions=self._generate_conflict_actions(overlapping_events, booking_details)
                )
                conflicts.append(conflict)
            
            # Check for insufficient travel time
            insufficient_time_events = []
            for event in events:
                if self._insufficient_travel_time(event, departure_time, arrival_time):
                    insufficient_time_events.append(event)
            
            if insufficient_time_events:
                conflict = BookingConflict(
                    booking_id=booking_id,
                    flight_details=booking_details,
                    conflicting_events=insufficient_time_events,
                    conflict_type='insufficient_time',
                    severity='medium',
                    suggested_actions=['Consider booking an earlier flight', 'Reschedule conflicting events']
                )
                conflicts.append(conflict)
            
            # Check for wrong destination
            wrong_destination_events = []
            for event in events:
                if self._wrong_destination(event, destination):
                    wrong_destination_events.append(event)
            
            if wrong_destination_events:
                conflict = BookingConflict(
                    booking_id=booking_id,
                    flight_details=booking_details,
                    conflicting_events=wrong_destination_events,
                    conflict_type='wrong_destination',
                    severity='high',
                    suggested_actions=['Verify destination matches your calendar events', 'Consider rebooking to correct destination']
                )
                conflicts.append(conflict)
            
            logger.info(f"Detected {len(conflicts)} booking conflicts")
            return conflicts
            
        except Exception as e:
            logger.error(f"Error detecting booking conflicts: {str(e)}")
            return []
    
    def _events_overlap(self, event: CalendarEvent, departure: datetime, arrival: datetime) -> bool:
        """Check if a calendar event overlaps with flight times"""
        try:
            # Check if event overlaps with flight time
            return (event.start_time <= arrival and event.end_time >= departure)
            
        except Exception as e:
            logger.error(f"Error checking event overlap: {str(e)}")
            return False
    
    def _insufficient_travel_time(self, event: CalendarEvent, departure: datetime, arrival: datetime) -> bool:
        """Check if there's insufficient time between flight and event"""
        try:
            # Check if event starts too soon after flight arrival
            time_between = (event.start_time - arrival).total_seconds() / 3600  # hours
            
            # Require at least 2 hours between arrival and event start
            return time_between < 2 and time_between > 0
            
        except Exception as e:
            logger.error(f"Error checking insufficient travel time: {str(e)}")
            return False
    
    def _wrong_destination(self, event: CalendarEvent, booking_destination: str) -> bool:
        """Check if booking destination doesn't match event location"""
        try:
            if not event.destination_city or not booking_destination:
                return False
            
            # Simple string matching - could be improved with fuzzy matching
            return event.destination_city.lower() not in booking_destination.lower()
            
        except Exception as e:
            logger.error(f"Error checking wrong destination: {str(e)}")
            return False
    
    def _calculate_conflict_severity(self, conflicting_events: List[CalendarEvent]) -> str:
        """Calculate severity of conflicts"""
        try:
            if not conflicting_events:
                return 'low'
            
            # Check for high-priority events
            high_priority_events = [e for e in conflicting_events if e.priority >= 4]
            if high_priority_events:
                return 'critical'
            
            # Check for business events
            business_events = [e for e in conflicting_events if e.travel_type == 'business']
            if business_events:
                return 'high'
            
            return 'medium'
            
        except Exception as e:
            logger.error(f"Error calculating conflict severity: {str(e)}")
            return 'medium'
    
    def _generate_conflict_actions(self, conflicting_events: List[CalendarEvent], booking_details: Dict[str, Any]) -> List[str]:
        """Generate suggested actions for resolving conflicts"""
        try:
            actions = []
            
            # General actions
            actions.append("Review your calendar for the travel dates")
            actions.append("Consider rescheduling the flight")
            
            # Specific actions based on event types
            business_events = [e for e in conflicting_events if e.travel_type == 'business']
            if business_events:
                actions.append("Contact meeting organizers to reschedule")
                actions.append("Book an earlier flight to arrive before the meeting")
            
            personal_events = [e for e in conflicting_events if e.travel_type == 'personal']
            if personal_events:
                actions.append("Check if personal events can be rescheduled")
                actions.append("Consider extending your trip to accommodate both events")
            
            return actions
            
        except Exception as e:
            logger.error(f"Error generating conflict actions: {str(e)}")
            return ["Review your calendar and consider rescheduling"]
    
    def _store_calendar_events(self, user_id: str, events: List[CalendarEvent]):
        """Store calendar events in database for future reference"""
        try:
            # This would integrate with your database
            # For now, just log the events
            logger.info(f"Storing {len(events)} calendar events for user {user_id}")
            
            # In a real implementation, you would:
            # 1. Connect to your database
            # 2. Store/update events
            # 3. Handle duplicates and updates
            
        except Exception as e:
            logger.error(f"Error storing calendar events: {str(e)}")
    
    def send_conflict_warning(self, user_id: str, conflicts: List[BookingConflict]) -> bool:
        """Send warning messages about booking conflicts"""
        try:
            if not conflicts:
                return True
            
            # This would integrate with your notification system
            # For now, just log the warnings
            for conflict in conflicts:
                logger.warning(f"Booking conflict detected for user {user_id}: {conflict.conflict_type} - {conflict.severity}")
                logger.info(f"Suggested actions: {', '.join(conflict.suggested_actions)}")
            
            # In a real implementation, you would:
            # 1. Send email notifications
            # 2. Send SMS alerts
            # 3. Show in-app notifications
            # 4. Create calendar reminders
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending conflict warnings: {str(e)}")
            return False
    
    def analyze_events_for_travel(self, events):
        """Analyze events to determine travel-related ones"""
        travel_events = []
        
        for event in events:
            # Simple analysis - in production, this would be more sophisticated
            summary = event.get('summary', '').lower()
            location = event.get('location', '').lower()
            
            # Check for travel-related keywords
            travel_keywords = ['meeting', 'conference', 'business', 'travel', 'trip', 'visit']
            if any(keyword in summary for keyword in travel_keywords):
                travel_events.append({
                    'id': event.get('id'),
                    'summary': event.get('summary'),
                    'start': event.get('start'),
                    'end': event.get('end'),
                    'location': event.get('location'),
                    'is_travel_related': True
                })
        
        return travel_events
    
    def generate_travel_suggestions(self, analysis):
        """Generate travel suggestions based on calendar analysis"""
        suggestions = []
        
        for event in analysis:
            if event.get('is_travel_related'):
                suggestions.append({
                    'event_id': event.get('id'),
                    'event_summary': event.get('summary'),
                    'destination': event.get('location', 'Unknown'),
                    'suggested_departure': event.get('start', {}).get('dateTime', ''),
                    'suggested_return': event.get('end', {}).get('dateTime', ''),
                    'flight_options': [],
                    'conflict_warning': None,
                    'priority_score': 0.8
                })
        
        return suggestions

# Global calendar service instance
calendar_service = CalendarService()