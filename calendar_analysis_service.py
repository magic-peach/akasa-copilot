"""Calendar Analysis Service for Akasa Airlines
Analyzes Google Calendar events to provide intelligent flight suggestions
and booking recommendations based on user's schedule.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from google_oauth_service import oauth_service
import re

logger = logging.getLogger(__name__)

@dataclass
class CalendarEvent:
    """Represents a calendar event with flight-relevant information"""
    id: str
    title: str
    start_date: datetime
    end_date: datetime
    location: str
    description: str
    is_travel_related: bool = False
    suggested_departure: Optional[datetime] = None
    suggested_return: Optional[datetime] = None
    destination_city: Optional[str] = None
    origin_city: Optional[str] = None

@dataclass
class FlightSuggestion:
    """Represents a flight suggestion based on calendar analysis"""
    event_id: str
    event_title: str
    origin: str
    destination: str
    departure_date: datetime
    return_date: Optional[datetime]
    confidence_score: float
    reasoning: str
    advance_booking_days: int
    estimated_savings: float

class CalendarAnalysisService:
    """Service to analyze calendar events and provide flight suggestions"""
    
    def __init__(self):
        self.travel_keywords = [
            'conference', 'meeting', 'workshop', 'seminar', 'training',
            'vacation', 'holiday', 'trip', 'visit', 'travel', 'flight',
            'hotel', 'business', 'client', 'interview', 'wedding',
            'event', 'summit', 'expo', 'fair', 'festival'
        ]
        
        self.city_keywords = {
            'delhi': ['delhi', 'new delhi', 'ncr', 'gurgaon', 'noida'],
            'mumbai': ['mumbai', 'bombay', 'bom', 'andheri', 'bandra'],
            'bangalore': ['bangalore', 'bengaluru', 'blr', 'whitefield'],
            'chennai': ['chennai', 'madras', 'maa', 'tambaram'],
            'hyderabad': ['hyderabad', 'hyd', 'secunderabad', 'cyberabad'],
            'pune': ['pune', 'pnq', 'hinjewadi', 'kharadi'],
            'kolkata': ['kolkata', 'calcutta', 'ccu', 'howrah'],
            'ahmedabad': ['ahmedabad', 'amd', 'gandhinagar'],
            'jaipur': ['jaipur', 'jai', 'pink city'],
            'kochi': ['kochi', 'cochin', 'cok', 'ernakulam'],
            'goa': ['goa', 'goi', 'panaji', 'margao'],
            'lucknow': ['lucknow', 'lko'],
            'indore': ['indore', 'idr'],
            'bhubaneswar': ['bhubaneswar', 'bbsr', 'bbi'],
            'coimbatore': ['coimbatore', 'cjb'],
            'nagpur': ['nagpur', 'nag'],
            'vadodara': ['vadodara', 'baroda', 'bdo'],
            'visakhapatnam': ['visakhapatnam', 'vizag', 'vtz'],
            'thiruvananthapuram': ['thiruvananthapuram', 'trivandrum', 'trv'],
            'srinagar': ['srinagar', 'srr', 'kashmir']
        }
    
    def analyze_calendar_events(self, max_events: int = 50) -> List[CalendarEvent]:
        """Analyze user's calendar events and extract travel-relevant information"""
        try:
            raw_events = oauth_service.list_upcoming_events(max_events)
            analyzed_events = []
            
            for event in raw_events:
                analyzed_event = self._analyze_single_event(event)
                if analyzed_event:
                    analyzed_events.append(analyzed_event)
            
            logger.info(f"Analyzed {len(analyzed_events)} calendar events")
            return analyzed_events
            
        except Exception as e:
            logger.error(f"Error analyzing calendar events: {str(e)}")
            return []
    
    def _analyze_single_event(self, event: Dict) -> Optional[CalendarEvent]:
        """Analyze a single calendar event for travel relevance"""
        try:
            # Extract basic event information
            event_id = event.get('id', '')
            title = event.get('summary', '').lower()
            description = event.get('description', '').lower()
            location = event.get('location', '').lower()
            
            # Parse start and end times
            start_info = event.get('start', {})
            end_info = event.get('end', {})
            
            start_date = self._parse_datetime(start_info)
            end_date = self._parse_datetime(end_info)
            
            if not start_date or not end_date:
                return None
            
            # Check if event is travel-related
            is_travel_related = self._is_travel_related(title, description, location)
            
            # Extract destination information
            destination_city = self._extract_destination(title, description, location)
            
            # Create calendar event object
            calendar_event = CalendarEvent(
                id=event_id,
                title=event.get('summary', ''),
                start_date=start_date,
                end_date=end_date,
                location=event.get('location', ''),
                description=event.get('description', ''),
                is_travel_related=is_travel_related,
                destination_city=destination_city
            )
            
            # Calculate suggested travel dates if travel-related
            if is_travel_related:
                self._calculate_travel_suggestions(calendar_event)
            
            return calendar_event
            
        except Exception as e:
            logger.error(f"Error analyzing single event: {str(e)}")
            return None
    
    def _parse_datetime(self, time_info: Dict) -> Optional[datetime]:
        """Parse datetime from Google Calendar event time information"""
        try:
            if 'dateTime' in time_info:
                # Event with specific time
                return datetime.fromisoformat(time_info['dateTime'].replace('Z', '+00:00'))
            elif 'date' in time_info:
                # All-day event
                date_str = time_info['date']
                return datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            return None
        except Exception as e:
            logger.error(f"Error parsing datetime: {str(e)}")
            return None
    
    def _is_travel_related(self, title: str, description: str, location: str) -> bool:
        """Determine if an event is travel-related"""
        text_to_check = f"{title} {description} {location}".lower()
        
        # Check for travel keywords
        for keyword in self.travel_keywords:
            if keyword in text_to_check:
                return True
        
        # Check for city names (indicating travel)
        for city, variations in self.city_keywords.items():
            for variation in variations:
                if variation in text_to_check:
                    return True
        
        # Check for common travel patterns
        travel_patterns = [
            r'\bfly\b', r'\bflight\b', r'\bairport\b', r'\btravel\b',
            r'\bvisit\b', r'\btrip\b', r'\bhotel\b', r'\bstay\b'
        ]
        
        for pattern in travel_patterns:
            if re.search(pattern, text_to_check):
                return True
        
        return False
    
    def _extract_destination(self, title: str, description: str, location: str) -> Optional[str]:
        """Extract destination city from event information"""
        text_to_check = f"{title} {description} {location}".lower()
        
        for city, variations in self.city_keywords.items():
            for variation in variations:
                if variation in text_to_check:
                    return city.title()
        
        return None
    
    def _calculate_travel_suggestions(self, event: CalendarEvent):
        """Calculate suggested departure and return dates for travel events"""
        try:
            # Suggest departure 1 day before event starts
            event.suggested_departure = event.start_date - timedelta(days=1)
            
            # Suggest return 1 day after event ends (or same day for short events)
            event_duration = (event.end_date - event.start_date).days
            
            if event_duration <= 1:
                # Same day or short event - return same day
                event.suggested_return = event.end_date
            else:
                # Multi-day event - return day after
                event.suggested_return = event.end_date + timedelta(days=1)
            
        except Exception as e:
            logger.error(f"Error calculating travel suggestions: {str(e)}")
    
    def generate_flight_suggestions(self, user_location: str = "Delhi") -> List[FlightSuggestion]:
        """Generate flight suggestions based on calendar analysis"""
        try:
            events = self.analyze_calendar_events()
            suggestions = []
            
            for event in events:
                if event.is_travel_related and event.destination_city:
                    suggestion = self._create_flight_suggestion(event, user_location)
                    if suggestion:
                        suggestions.append(suggestion)
            
            # Sort by departure date
            suggestions.sort(key=lambda x: x.departure_date)
            
            logger.info(f"Generated {len(suggestions)} flight suggestions")
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating flight suggestions: {str(e)}")
            return []
    
    def _create_flight_suggestion(self, event: CalendarEvent, user_location: str) -> Optional[FlightSuggestion]:
        """Create a flight suggestion from a calendar event"""
        try:
            if not event.suggested_departure or not event.destination_city:
                return None
            
            # Calculate advance booking days
            advance_days = (event.suggested_departure - datetime.now(timezone.utc)).days
            
            # Calculate confidence score based on various factors
            confidence = self._calculate_confidence_score(event, advance_days)
            
            # Estimate potential savings for advance booking
            estimated_savings = self._estimate_savings(advance_days)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(event, advance_days)
            
            return FlightSuggestion(
                event_id=event.id,
                event_title=event.title,
                origin=user_location,
                destination=event.destination_city,
                departure_date=event.suggested_departure,
                return_date=event.suggested_return,
                confidence_score=confidence,
                reasoning=reasoning,
                advance_booking_days=advance_days,
                estimated_savings=estimated_savings
            )
            
        except Exception as e:
            logger.error(f"Error creating flight suggestion: {str(e)}")
            return None
    
    def _calculate_confidence_score(self, event: CalendarEvent, advance_days: int) -> float:
        """Calculate confidence score for flight suggestion"""
        score = 0.5  # Base score
        
        # Higher confidence for events with clear location
        if event.location:
            score += 0.2
        
        # Higher confidence for business/professional events
        business_keywords = ['meeting', 'conference', 'business', 'client', 'interview']
        if any(keyword in event.title.lower() for keyword in business_keywords):
            score += 0.2
        
        # Adjust based on advance booking time
        if 7 <= advance_days <= 30:
            score += 0.1  # Optimal booking window
        elif advance_days > 30:
            score += 0.05  # Good advance booking
        
        return min(score, 1.0)
    
    def _estimate_savings(self, advance_days: int) -> float:
        """Estimate potential savings for advance booking"""
        if advance_days >= 21:
            return 2500.0  # High savings for 3+ weeks advance
        elif advance_days >= 14:
            return 1800.0  # Good savings for 2+ weeks advance
        elif advance_days >= 7:
            return 1200.0  # Moderate savings for 1+ week advance
        else:
            return 500.0   # Minimal savings for last-minute booking
    
    def _generate_reasoning(self, event: CalendarEvent, advance_days: int) -> str:
        """Generate human-readable reasoning for the suggestion"""
        reasons = []
        
        reasons.append(f"Event '{event.title}' scheduled for {event.start_date.strftime('%B %d, %Y')}")
        
        if event.destination_city:
            reasons.append(f"Destination identified as {event.destination_city}")
        
        if advance_days > 0:
            reasons.append(f"Booking {advance_days} days in advance can save money")
        else:
            reasons.append("Last-minute booking - limited options available")
        
        return ". ".join(reasons)
    
    def check_booking_conflicts(self, departure_date: datetime, return_date: datetime) -> Dict:
        """Check if proposed flight dates conflict with calendar events"""
        try:
            events = self.analyze_calendar_events()
            conflicts = []
            warnings = []
            
            for event in events:
                # Check for direct conflicts
                if (departure_date <= event.end_date and return_date >= event.start_date):
                    if event.is_travel_related:
                        conflicts.append({
                            'type': 'direct_conflict',
                            'event': event.title,
                            'date': event.start_date.strftime('%Y-%m-%d'),
                            'severity': 'high',
                            'message': f"Flight dates overlap with travel event: {event.title}"
                        })
                    else:
                        warnings.append({
                            'type': 'schedule_overlap',
                            'event': event.title,
                            'date': event.start_date.strftime('%Y-%m-%d'),
                            'severity': 'medium',
                            'message': f"Flight dates overlap with scheduled event: {event.title}"
                        })
            
            return {
                'has_conflicts': len(conflicts) > 0,
                'has_warnings': len(warnings) > 0,
                'conflicts': conflicts,
                'warnings': warnings,
                'total_issues': len(conflicts) + len(warnings)
            }
            
        except Exception as e:
            logger.error(f"Error checking booking conflicts: {str(e)}")
            return {'has_conflicts': False, 'has_warnings': False, 'conflicts': [], 'warnings': [], 'total_issues': 0}

    def analyze_events_for_travel(self, events: List[Dict]) -> List[CalendarEvent]:
        """Analyze provided events for travel opportunities"""
        try:
            analyzed_events = []
            
            for event in events:
                analyzed_event = self._analyze_single_event(event)
                if analyzed_event:
                    analyzed_events.append(analyzed_event)
            
            logger.info(f"Analyzed {len(analyzed_events)} events for travel")
            return analyzed_events
            
        except Exception as e:
            logger.error(f"Error analyzing events for travel: {str(e)}")
            return []
    
    def generate_travel_suggestions(self, events: List[CalendarEvent]) -> List[FlightSuggestion]:
        """Generate travel suggestions from analyzed events"""
        try:
            suggestions = []
            
            for event in events:
                if event.is_travel_related and event.destination_city:
                    suggestion = self._create_flight_suggestion(event, "Delhi")  # Default origin
                    if suggestion:
                        suggestions.append(suggestion)
            
            # Sort by departure date
            suggestions.sort(key=lambda x: x.departure_date)
            
            logger.info(f"Generated {len(suggestions)} travel suggestions")
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating travel suggestions: {str(e)}")
            return []

# Global calendar analysis service instance
calendar_service = CalendarAnalysisService()